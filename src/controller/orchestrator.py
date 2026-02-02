import threading
import queue
import time
import sys
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Callable


class PipelineState(Enum):
    IDLE = auto()
    LISTENING = auto()
    RECORDING = auto()
    PROCESSING = auto()
    STREAMING = auto()
    STOPPING = auto()


@dataclass
class PipelineConfig:
    """Configuration du pipeline voice changer."""
    input_device: Optional[int] = None
    output_device: Optional[int] = None
    voice_id: str = ""
    # STT config
    stt_engine: str = "vosk"  # "vosk" ou "whisper"
    vosk_model_path: str = "models/vosk-model-small-fr-0.22"
    whisper_model: str = "base"  # "tiny", "base", "small", "medium"
    language: str = "fr"
    sample_rate: int = 48000
    chunk_ms: int = 20
    # Paramètres VAD
    vad_aggressiveness: int = 3  # Plus agressif pour filtrer le bruit
    min_speech_ms: int = 300     # Minimum 300ms de parole (évite les clics)
    min_silence_ms: int = 600    # 600ms de silence pour détecter fin de phrase
    padding_ms: int = 200


class VoiceChangerOrchestrator:
    """
    Contrôleur principal coordonnant le pipeline voice changer.

    Modèle de threading:
    - Thread principal: Contrôle, gestion utilisateur
    - Thread PyAudio: Callback capture micro
    - Thread Processing: Transcription STT + appel TTS
    - Thread Playback: Lecture audio vers sortie

    Communication:
    - audio_queue: Utterances depuis VAD -> Processing
    - tts_queue: Chunks audio TTS -> Playback
    """

    def __init__(self, config: PipelineConfig, auth):
        self.config = config
        self.auth = auth
        self.state = PipelineState.IDLE
        self._state_lock = threading.Lock()

        # Queues pour communication inter-threads
        self.audio_queue = queue.Queue(maxsize=5)
        self.tts_queue = queue.Queue(maxsize=50)

        # Composants (initialisés dans start())
        self.mic_capture = None
        self.vad = None
        self.utterance_buffer = None
        self.stt_engine = None
        self.tts_client = None
        self.audio_output = None

        # Threads
        self._processing_thread = None
        self._playback_thread = None
        self._stop_event = threading.Event()

        # Callbacks optionnels
        self.on_state_change: Optional[Callable[[PipelineState], None]] = None
        self.on_transcription: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

    def _set_state(self, new_state: PipelineState):
        """Transition d'état thread-safe."""
        with self._state_lock:
            old_state = self.state
            self.state = new_state
            if self.on_state_change:
                self.on_state_change(new_state)
            print(f"[STATE] {old_state.name} -> {new_state.name}")

    def start(self):
        """Initialise tous les composants et démarre le pipeline."""
        # Import local pour éviter les imports circulaires
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from core.audio import MicCapture, AudioOutput
        from processing.vad import VoiceActivityDetector, UtteranceBuffer
        from processing.stt import create_stt_engine
        from client.inworld import InworldTTSClient

        print("[ORCHESTRATOR] Initialisation des composants...")

        # Initialiser les composants
        self.vad = VoiceActivityDetector(
            aggressiveness=self.config.vad_aggressiveness,
            sample_rate=self.config.sample_rate
        )
        self.utterance_buffer = UtteranceBuffer(
            min_speech_ms=self.config.min_speech_ms,
            min_silence_ms=self.config.min_silence_ms,
            padding_ms=self.config.padding_ms,
            chunk_ms=self.config.chunk_ms
        )

        # Créer le moteur STT selon la config
        print(f"[ORCHESTRATOR] Chargement du moteur STT: {self.config.stt_engine}")
        self.stt_engine = create_stt_engine(
            engine_type=self.config.stt_engine,
            model_path=self.config.vosk_model_path,
            model_name=self.config.whisper_model,
            language=self.config.language,
            input_sample_rate=self.config.sample_rate
        )
        print(f"[ORCHESTRATOR] Moteur STT chargé.")

        self.tts_client = InworldTTSClient(self.auth)

        self.mic_capture = MicCapture(
            device_index=self.config.input_device,
            sample_rate=self.config.sample_rate,
            chunk_ms=self.config.chunk_ms
        )
        self.audio_output = AudioOutput(
            device_index=self.config.output_device,
            sample_rate=self.config.sample_rate
        )

        # Démarrer la sortie audio en premier
        self.audio_output.start()

        # Démarrer les threads workers
        self._stop_event.clear()
        self._processing_thread = threading.Thread(
            target=self._processing_loop, daemon=True, name="ProcessingThread"
        )
        self._playback_thread = threading.Thread(
            target=self._playback_loop, daemon=True, name="PlaybackThread"
        )
        self._processing_thread.start()
        self._playback_thread.start()

        # Démarrer la capture avec callback
        self._set_state(PipelineState.LISTENING)
        self.mic_capture.start(self._audio_callback)

        print("[ORCHESTRATOR] Pipeline démarré. Parlez dans le micro...")

    def _audio_callback(self, frame_bytes: bytes):
        """
        Appelé par PyAudio pour chaque chunk audio (20ms).
        Exécuté dans le thread callback de PyAudio - doit être rapide!
        """
        if self._stop_event.is_set():
            return

        # Détection VAD
        is_speech = self.vad.is_speech(frame_bytes)

        # Mettre à jour l'état selon la détection
        with self._state_lock:
            if is_speech and self.state == PipelineState.LISTENING:
                self.state = PipelineState.RECORDING

        # Traiter via le buffer d'utterance
        utterance = self.utterance_buffer.process_frame(frame_bytes, is_speech)

        if utterance:
            # Utterance complète - envoyer à la queue de processing
            try:
                self.audio_queue.put_nowait(utterance)
                with self._state_lock:
                    self.state = PipelineState.PROCESSING
            except queue.Full:
                print("[WARN] Queue de processing pleine, utterance ignorée")

    def _processing_loop(self):
        """
        Thread worker: Prend les utterances, exécute STT, envoie au TTS.
        """
        while not self._stop_event.is_set():
            try:
                utterance = self.audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                # Exécuter STT
                print("\n" + "=" * 50)
                print("[STT] Transcription en cours...")
                start_time = time.time()
                text = self.stt_engine.transcribe(utterance)
                stt_time = time.time() - start_time
                print(f"[STT] Résultat ({stt_time:.2f}s):")
                print(f"")
                print(f"    >>> {text} <<<")
                print(f"")

                if self.on_transcription:
                    self.on_transcription(text)

                # Filtrer les transcriptions inutiles
                if not text or len(text.strip()) < 3:
                    print("[STT] Transcription trop courte, ignorée")
                    self._set_state(PipelineState.LISTENING)
                    continue

                # Liste de mots/bruits parasites à ignorer
                noise_words = {
                    "hum", "euh", "ah", "oh", "hein", "hmm", "mm", "mh",
                    "oui", "non", "ok", "ouais", "bah", "ben", "eh",
                    "the", "a", "i", "you", "it", "is", "and"
                }
                if text.lower().strip() in noise_words:
                    print(f"[STT] Bruit parasite ignoré: '{text}'")
                    self._set_state(PipelineState.LISTENING)
                    continue

                # Envoyer au TTS (non-streaming pour plus de fiabilité)
                self._set_state(PipelineState.STREAMING)
                print(f"[TTS] Envoi à Inworld: '{text}'")

                start_time = time.time()
                try:
                    # Mode non-streaming (plus fiable)
                    audio_data = self.tts_client.synthesize(text, self.config.voice_id, stream=False)
                    ttfb = time.time() - start_time
                    print(f"[TTS] Audio reçu ({ttfb:.2f}s) - {len(audio_data)} bytes")

                    if audio_data:
                        self.tts_queue.put(audio_data)
                    else:
                        print("[TTS] Aucune donnée audio reçue!")

                except Exception as tts_error:
                    print(f"[TTS] Erreur: {tts_error}")

                # Marqueur de fin de stream
                self.tts_queue.put(None)

            except Exception as e:
                print(f"[ERROR] Échec du processing: {e}")
                if self.on_error:
                    self.on_error(e)

            finally:
                self._set_state(PipelineState.LISTENING)

    def _playback_loop(self):
        """
        Thread worker: Joue les chunks audio depuis la queue TTS.
        """
        while not self._stop_event.is_set():
            try:
                chunk = self.tts_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if chunk is None:
                # Marqueur de fin de stream
                print("[PLAYBACK] Fin du stream audio")
                continue

            try:
                print(f"[PLAYBACK] Lecture de {len(chunk)} bytes...")
                self.audio_output.write(chunk)
                print("[PLAYBACK] Lecture terminée")
            except Exception as e:
                print(f"[ERROR] Échec playback: {e}")

    def stop(self):
        """Arrête tous les composants et threads proprement."""
        print("[ORCHESTRATOR] Arrêt en cours...")
        self._set_state(PipelineState.STOPPING)
        self._stop_event.set()

        if self.mic_capture:
            self.mic_capture.stop()

        # Attendre les threads
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=2.0)
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=2.0)

        if self.audio_output:
            self.audio_output.stop()

        self._set_state(PipelineState.IDLE)
        print("[ORCHESTRATOR] Arrêté.")
