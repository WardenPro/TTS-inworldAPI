# Pipeline Audio

Ce document décrit le flux de traitement audio de la capture micro à la sortie virtuelle.

## 1. Capture Micro (Input)

*   **Format** : PCM 16-bit, 48kHz, Mono.
*   **Frame Size** : 20ms (960 samples à 48kHz).
*   **Justification** : 20ms est un standard pour le VAD (WebRTC) et offre un bon compromis latence/CPU.

```python
# Exemple de configuration PyAudio
pa = pyaudio.PyAudio()
stream = pa.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=48000,
    input=True,
    frames_per_buffer=960
)
```

## 2. Voice Activity Detection (VAD)

Le VAD agit comme un filtre pour éviter d'envoyer du bruit de fond ou du silence au STT (ce qui coûterait cher et produirait des hallucinations).

*   **Algorithme** : WebRTC VAD ou Silero VAD (plus robuste aux bruits).
*   **Logique de déclenchement** :
    *   `min_speech_duration_ms` : 100ms (éviter les clics).
    *   `min_silence_duration_ms` : 400ms (détecter la fin de phrase).
    *   **Padding** : Garder 200-300ms de buffer "pré-parole" pour ne pas couper le début (ex: "B" de "Bonjour").

## 3. Buffering & Segmentation

Les frames "utiles" sont accumulées dans un `UtteranceBuffer`.
*   À `SpeechStart` : On commence à stocker (en incluant le padding).
*   À `SpeechEnd` : On ferme le buffer -> `wav_bytes` -> Envoi au STT.
*   **Gestion des débordements** : Si une phrase dure > 15s, on force la coupure pour garder la réactivité.

## 4. Playback (Output)

La sortie audio nécessite une gestion fine pour éviter les craquements (buffer underrun).

*   **Jitter Buffer** : Un buffer circulaire stocke les chunks reçus du TTS streaming.
*   **Lissage** : Si le buffer est vide, envoyer du silence (zéros) pour maintenir le flux actif vers le driver audio virtuel.
*   **Resampling** : Si Inworld renvoie du 24kHz et que le driver virtuel attend du 48kHz, un rééchantillonnage (ex: `librosa` ou `scipy.signal.resample` rapide) est nécessaire.
