# Analyse de Latence

La latence est le défi critique de ce projet. Voici où elle se crée et comment la minimiser.

## Décomposition de la Latence

Latence Totale = T_input + T_vad + T_stt + T_network + T_tts_gen + T_output

1.  **T_input (Capture)** : ~20ms (taille du buffer). Négligeable.
2.  **T_vad (Détection Fin de Phrase)** : ~300-500ms.
    *   *Cause* : On doit attendre un silence confirmé pour savoir que la phrase est finie.
    *   *Optimisation* : Réduire `min_silence_duration_ms` (risque de couper au milieu). Utiliser un mode "streaming STT" qui envoie des hypothèses partielles (plus complexe).
3.  **T_stt (Transcription)** : ~200-1000ms.
    *   *Cause* : Temps d'inférence du modèle.
    *   *Optimisation* : Utiliser `faster-whisper` (CTranslate2) sur GPU. Utiliser des modèles "Tiny" ou "Base.en".
4.  **T_network (Aller-retour API)** : ~50-200ms.
    *   *Optimisation* : WebSocket persistant (évite le handshake TLS à chaque phrase). Serveurs proches (pas de notre contrôle).
5.  **T_tts_gen (Génération Inworld)** : ~200-500ms (Time To First Byte).
    *   *Optimisation* : Utiliser le paramètre `stream`. Désactiver `applyTextNormalization`. Utiliser des modèles "Turbo" si dispos.
6.  **T_output (Playback)** : ~20-50ms (buffer sécurité).

**Estimation Totale MVP** : 1.5s - 2.5s.
**Cible Optimisée** : < 1s.

## Stratégies d'Optimisation

1.  **TTS Streaming** : Ne pas attendre tout l'audio pour jouer. Jouer dès le premier chunk reçu.
2.  **Overlap** : Lancer le TTS dès qu'une prédiction STT "finale" est disponible, sans attendre la fermeture complète du VAD (si possible).
3.  **Pré-connexion** : Garder la WebSocket Inworld ouverte.
4.  **Local STT** : Élimine la latence réseau pour la partie STT.
