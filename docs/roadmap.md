# Roadmap Produit

## Phase 1 : MVP (Minimum Viable Product)
**Objectif** : Prouver le concept "Parler -> STT -> TTS -> Entendre".
**Latence cible** : < 3s.

- [ ] **Setup** : Structure projet, env, dépendances.
- [ ] **IA Textuelle** : Script simple qui envoie du texte à Inworld et joue le WAV reçu.
- [ ] **Capture** : Script qui enregistre le micro et détecte le silence (VAD simple).
- [ ] **Pipeline Complet** : Micro -> VAD -> STT (Whisper Local) -> Inworld (HTTP) -> Speaker.
- [ ] **Sortie Virtuelle** : Redirection de l'audio vers VB-Cable.

## Phase 2 : Optimisation Latence (La chasse aux ms)
**Objectif** : Rendre la conversation fluide.
**Latence cible** : < 1.5s.

- [ ] **WebSocket Inworld** : Migrer de HTTP à WebSocket persistant.
- [ ] **Streaming Playback** : Jouer les chunks audio dès réception (ne pas attendre la fin de la phrase).
- [ ] **Optimisation VAD** : Tuner les seuils pour détecter la fin de phrase plus vite.
- [ ] **Faster-Whisper** : Utiliser l'implémentation CTranslate2 pour le STT.

## Phase 3 : Fonctionnalités Utilisateur (v1.0)
**Objectif** : Une app utilisable par un streamer.

- [ ] **UI Simple** : Une interface (Tkinter/Electron/Web) pour choisir sa voix.
- [ ] **Catalogue de Voix** : Lister les voix dynamiquement depuis l'API.
- [ ] **Push-to-Talk** : Option pour ne déclencher le micro que sur appui touche.
- [ ] **Paramètres** : Gain micro, Volume sortie, Choix périphériques.

## Phase 4 : Raffinement (Post-v1)

- [ ] **Interruptions** : Si je parle pendant que l'IA parle, l'IA s'arrête (Echo Cancellation / Barge-in).
- [ ] **Filtres Audio** : Ajouter de la reverb ou du pitch shifting léger en post-process.
