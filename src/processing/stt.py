import json
import numpy as np


class STTEngine:
    """Interface de base pour les moteurs STT."""

    def transcribe(self, audio_bytes: bytes) -> str:
        raise NotImplementedError


class VoskSTTEngine(STTEngine):
    """
    Moteur STT léger utilisant Vosk.
    Gère le resampling 48kHz -> 16kHz automatiquement.
    """

    def __init__(self, model_path: str, input_sample_rate: int = 48000):
        """
        Args:
            model_path: Chemin vers le dossier du modèle Vosk
            input_sample_rate: Sample rate de l'audio entrant (48000 par défaut)
        """
        from vosk import Model, KaldiRecognizer

        self.model = Model(model_path)
        self.input_sample_rate = input_sample_rate
        self.target_sample_rate = 16000  # Vosk exige 16kHz
        self._recognizer_class = KaldiRecognizer

    def _resample(self, audio_bytes: bytes) -> bytes:
        """
        Resample de input_sample_rate vers 16kHz par décimation simple.
        Pour 48kHz -> 16kHz, on prend 1 échantillon sur 3.
        """
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
        ratio = self.input_sample_rate // self.target_sample_rate
        resampled = audio_np[::ratio]
        return resampled.tobytes()

    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcrit un segment audio complet.

        Args:
            audio_bytes: Audio PCM 16-bit mono à input_sample_rate

        Returns:
            Texte transcrit (vide si aucune parole détectée)
        """
        # Resample vers 16kHz
        audio_16k = self._resample(audio_bytes)

        # Nouveau recognizer pour chaque transcription
        recognizer = self._recognizer_class(self.model, self.target_sample_rate)

        # Envoyer l'audio par chunks (Vosk préfère ~4000 bytes)
        chunk_size = 4000
        for i in range(0, len(audio_16k), chunk_size):
            chunk = audio_16k[i:i + chunk_size]
            recognizer.AcceptWaveform(chunk)

        # Récupérer le résultat final
        result = json.loads(recognizer.FinalResult())
        return result.get("text", "").strip()


class WhisperSTTEngine(STTEngine):
    """
    Moteur STT utilisant Faster-Whisper.
    Plus précis que Vosk, mais nécessite plus de ressources (GPU recommandé).
    """

    def __init__(self, model_name: str = "base", language: str = "fr", input_sample_rate: int = 48000):
        """
        Args:
            model_name: Nom du modèle ("tiny", "base", "small", "medium", "large")
            language: Code langue ("fr", "en", etc.)
            input_sample_rate: Sample rate de l'audio entrant
        """
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ImportError(
                "faster-whisper n'est pas installé. "
                "Installez-le avec: pip install faster-whisper"
            )

        self.input_sample_rate = input_sample_rate
        self.target_sample_rate = 16000  # Whisper utilise 16kHz
        self.language = language

        # Déterminer le device (CUDA si disponible, sinon CPU)
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        print(f"[WHISPER] Chargement du modèle '{model_name}' sur {device}...")
        self.model = WhisperModel(model_name, device=device, compute_type=compute_type)
        print(f"[WHISPER] Modèle chargé.")

    def _resample(self, audio_bytes: bytes) -> np.ndarray:
        """
        Resample et convertit en float32 pour Whisper.
        """
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16)

        # Resample si nécessaire
        if self.input_sample_rate != self.target_sample_rate:
            ratio = self.input_sample_rate // self.target_sample_rate
            audio_np = audio_np[::ratio]

        # Convertir en float32 normalisé [-1, 1]
        audio_float = audio_np.astype(np.float32) / 32768.0
        return audio_float

    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcrit un segment audio complet.

        Args:
            audio_bytes: Audio PCM 16-bit mono à input_sample_rate

        Returns:
            Texte transcrit
        """
        audio_float = self._resample(audio_bytes)

        segments, info = self.model.transcribe(
            audio_float,
            language=self.language,
            beam_size=5,
            vad_filter=True,  # Filtre VAD intégré
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        # Concaténer tous les segments
        text = " ".join(segment.text for segment in segments)
        return text.strip()


def create_stt_engine(engine_type: str = "vosk", **kwargs) -> STTEngine:
    """
    Factory pour créer le bon moteur STT.

    Args:
        engine_type: "vosk" ou "whisper"
        **kwargs: Arguments spécifiques au moteur

    Returns:
        Instance de STTEngine
    """
    if engine_type == "vosk":
        model_path = kwargs.get("model_path", "models/vosk-model-small-fr-0.22")
        input_sample_rate = kwargs.get("input_sample_rate", 48000)
        return VoskSTTEngine(model_path=model_path, input_sample_rate=input_sample_rate)

    elif engine_type == "whisper":
        model_name = kwargs.get("model_name", "base")
        language = kwargs.get("language", "fr")
        input_sample_rate = kwargs.get("input_sample_rate", 48000)
        return WhisperSTTEngine(
            model_name=model_name,
            language=language,
            input_sample_rate=input_sample_rate
        )

    else:
        raise ValueError(f"Moteur STT inconnu: {engine_type}. Utilisez 'vosk' ou 'whisper'.")
