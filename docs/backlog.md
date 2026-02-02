# Backlog Simulateur (Issues GitHub)

Ceci est une liste de tâches formatée comme des issues GitHub pour l'import dans un outil de gestion de projet.

## Sprint 1 : Core & Pipeline

### [Core] Implémenter AudioDeviceManager
*   **Description** : Créer la classe permettant de lister et sélectionner les I/O audio.
*   **Priorité** : High
*   **Criteria** : `list_input_devices()` retourne les vrais devices système.

### [Core] Implémenter MicCapture avec VAD
*   **Description** : Capturer l'audio et découper les phrases basées sur le silence.
*   **Priorité** : High
*   **Criteria** : Callback déclenché avec un buffer WAV valide à la fin d'une phrase.

### [IA] Intégrer STT (Faster-Whisper)
*   **Description** : Transcrire l'audio buffer en texte.
*   **Priorité** : High
*   **Criteria** : `transcribe(audio)` retourne le texte fidèle.

### [IA] Client Inworld HTTP (MVP)
*   **Description** : Envoyer texte -> Recevoir Audio (Base64).
*   **Priorité** : Medium
*   **Criteria** : Le script de test joue la voix retournée.

### [Core] AudioOutput vers Virtual Cable
*   **Description** : Écrire le flux audio PCM vers le périphérique de sortie.
*   **Priorité** : High
*   **Criteria** : Le son est audible dans Discord/OBS (configuré sur le câble).

## Sprint 2 : Latence & UI

### [Perf] Migrer vers Inworld WebSocket
*   **Description** : Remplacer HTTP par WebSocket pour réduire le RTT.
*   **Priorité** : High

### [UI] Sélecteur de Voix (CLI ou GUI simple)
*   **Description** : Lister les voix `GET /voices` et permettre la sélection.
*   **Priorité** : Medium
