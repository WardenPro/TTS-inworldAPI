import webrtcvad
import collections
import sys

class VoiceActivityDetector:
    def __init__(self, aggressiveness=2, sample_rate=48000):
        """
        aggressiveness: 0-3 (0 is least aggressive about filtering out checks)
        """
        self.vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = sample_rate
        # webrtcvad accepte 8000, 16000, 32000, 48000 Hz
        if sample_rate not in [8000, 16000, 32000, 48000]:
            raise ValueError("Sample rate must be 8/16/32/48 kHz for WebRTC VAD")

    def is_speech(self, frame_bytes):
        try:
            return self.vad.is_speech(frame_bytes, self.sample_rate)
        except Exception:
            return False

class UtteranceBuffer:
    def __init__(self, min_speech_ms=100, min_silence_ms=400, padding_ms=200, chunk_ms=20):
        """
        Gère l'accumulation de frames et la détection de phrases complètes.
        """
        self.chunk_ms = chunk_ms
        self.min_speech_frames = int(min_speech_ms / chunk_ms)
        self.min_silence_frames = int(min_silence_ms / chunk_ms)
        self.padding_frames_count = int(padding_ms / chunk_ms)
        
        self.ring_buffer = collections.deque(maxlen=self.padding_frames_count)
        self.active_frames = []
        self.triggered = False
        self.silence_counter = 0

    def process_frame(self, frame_bytes, is_speech: bool):
        """
        Retourne des bytes (WAV content complet) si une phrase vient de se terminer, sinon None.
        """
        if not self.triggered:
            self.ring_buffer.append(frame_bytes)
            if is_speech:
                # Démarrage de parole
                sys.stdout.write('+')
                sys.stdout.flush()
                self.triggered = True
                self.active_frames = list(self.ring_buffer) # Copie le pré-roll
                self.silence_counter = 0
        else:
            self.active_frames.append(frame_bytes)
            if is_speech:
                sys.stdout.write('.')
                sys.stdout.flush()
                self.silence_counter = 0
            else:
                sys.stdout.write('-')
                sys.stdout.flush()
                self.silence_counter += 1
                
            # Fin de phrase détectée ?
            if self.silence_counter > self.min_silence_frames:
                print(" [END]")
                # On enlève le silence de fin (optionnel, mais propre)
                # Mais on peut aussi tout garder
                full_audio = b''.join(self.active_frames)
                self.reset()
                return full_audio
        return None

    def reset(self):
        self.triggered = False
        self.active_frames = []
        self.silence_counter = 0
        self.ring_buffer.clear()
