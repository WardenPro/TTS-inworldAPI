# Architecture du Système

Ce document décrit l'architecture technique de **TTS-inworldAPI**. L'application est conçue de manière modulaire pour séparer la gestion audio bas niveau, la logique de traitement (IA), et l'interface utilisateur.

## Vue d'Ensemble

L'application suit un flux de données linéaire avec une machine à états pour l'orchestration.

```mermaid
graph TD
    subgraph "Core Audio Layer"
        Mic[Microphone Input]
        AudioOut[Virtual Output]
    end

    subgraph "Processing Layer"
        VAD[VAD\n(Voice Activity Detection)]
        Buffer[Utterance Buffer]
        STT[STT Engine\n(Whisper/Vosk)]
        TTS_Client[Inworld TTS Client]
    end

    subgraph "Orchestration"
        Controller[VoiceChanger Controller\n(State Machine)]
    end

    Mic --> VAD
    VAD -- "Speech Detected" --> Controller
    VAD -- "Audio Frames" --> Buffer
    Controller -- "Segment Ready" --> STT
    Buffer --> STT
    STT -- "Text" --> TTS_Client
    TTS_Client -- "PCM Stream" --> AudioOut
```

## Modules Principaux

### 1. Core Audio (`src/core/audio`)

Ce module gère les entrées/sorties audio brutes. Il utilise des bibliothèques comme `PyAudio` (PortAudio) ou similaires.

*   **AudioDeviceManager** : Liste et sélectionne les périphériques.
    *   `list_input_devices() -> list[AudioDevice]`
    *   `list_output_devices() -> list[AudioDevice]`
    *   `set_input_device(id)` / `set_output_device(id)`
*   **MicCapture** : Capture le flux audio en temps réel.
    *   Callback reçoit des frames PCM (ex: 20ms, 48kHz, 16-bit).
*   **AudioOutput** : Écrit le flux audio généré vers le périphérique virtuel.
    *   Gère un buffer circulaire pour lisser la lecture (jitter buffer).

### 2. Détection & Segmentation (`src/processing/vad`)

*   **VAD (VoiceActivityDetector)** : Analyse chaque frame pour déterminer s'il s'agit de parole ou de silence.
    *   Utilise `webrtcvad` ou `silero-vad`.
    *   Émet des événements : `SpeechStart`, `SpeechEnd`.
*   **UtteranceBuffer** : Accumule les frames audio pendant qu'on parle. Une fois le silence détecté (`SpeechEnd`), le buffer est finalisé et envoyé au STT.

### 3. Speech-to-Text (`src/processing/stt`)

Convertit l'audio enregistré en texte.

*   **STTEngine (Interface)** :
    *   `transcribe(audio_bytes) -> str`
*   **Implémentations possibles** :
    *   `LocalWhisperEngine` (via `faster-whisper` pour GPU/CPU optimisé).
    *   `VoskEngine` (très rapide, local, modèle léger).
    *   `CloudSTTEngine` (si besoin de décharger le CPU).

### 4. Client Inworld TTS (`src/client/inworld`)

Gère la communication avec l'API Inworld.

*   **InworldAuth** : Gestionnaire de tokens (Basic -> JWT).
*   **InworldTTSClient** :
    *   Supporte `HTTP Streaming` (`voice:stream`) pour une implémentation simple.
    *   Supporte `WebSocket` (`voice:streamBidirectional`) pour une latence minimale (connexion persistante).
    *   Gère le décodage des chunks audio (Base64 -> PCM).

### 5. Orchestration (`src/controller`)

*   **VoiceChangerController** : Le cerveau de l'application.
    *   Machine à états : `IDLE` -> `LISTENING` -> `RECORDING` -> `PROCESSING` -> `STREAMING` -> `IDLE`.
    *   Route les données entre les modules.
    *   Gère les erreurs (ex: échec STT, perte connexion).

## Flux de Données

1.  **Capture** : Le micro envoie des blocs de 20ms au VAD.
2.  **Détection** :
    *   Si Silence -> on ignore (ou on garde un petit buffer de pré-roll).
    *   Si Parole -> on commence à accumuler dans `UtteranceBuffer`.
3.  **Fin de Phrase** : Le VAD détecte un silence de X ms.
    *   Le buffer est clos.
    *   Le Controller envoie le buffer au STT.
4.  **Transcription** : Le STT retourne une chaîne de texte (ex: "Bonjour tout le monde").
5.  **Synthèse** :
    *   Le Controller envoie "Bonjour tout le monde" au `InworldTTSClient`.
    *   Optionnel : `TextPostProcessor` peut nettoyer le texte avant.
6.  **Streaming & Lecture** :
    *   Inworld renvoie des paquets audio (chunks) au fur et à mesure de la génération.
    *   Dès la réception du premier chunk, `AudioOutput` commence la lecture.


## Gestion des Erreurs et Résilience

Pour une expérience utilisateur fluide, l'application doit gérer les pannes silencieusement ou avec un feedback clair.

| Composant | Scénario d'Erreur | Stratégie de Résolution |
| :--- | :--- | :--- |
| **Microphone** | Déconnexion physique | Détecter l'événement OS -> Pause -> Tenter reconnexion ou switch sur device par défaut. |
| **STT** | Bruit incompréhensible | Si confidence score faible -> Ignorer (ne rien envoyer à Inworld). |
| **API Inworld** | Timeout / 5xx | 1. Retry exponentiel (max 3 essais).<br>2. Si échec -> Jouer un son "Glitch" local pour feedback utilisateur. |
| **API Inworld** | 401 Unauthorized | Arrêter le processing, notifier l'utilisateur (Log/UI) de vérifier les clés. |
| **Réseau** | Perte de connexion | Bufferiser localement ou dropper les paquets trop vieux (> 2s). |

## Choix Techniques

*   **Langage** : Python (MVP rapide, riche écosystème Audio/IA) ou C#/Rust (Performance/Robustesse).
    *   *Recommandation MVP* : Python pour la rapidité de dev.
*   **Audio** : 48kHz, 16-bit Mono (Standard Inworld & Discord).
