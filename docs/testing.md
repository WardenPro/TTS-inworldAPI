# Stratégie de Test

Garantir la stabilité d'une application audio temps réel est complexe. Voici l'approche recommandée.

## 1. Tests Unitaires (Logique Pure)

Tester les composants isolés qui ne dépendent pas du matériel.

*   **VAD** :
    *   Input : Générer des vecteurs de bytes (silence pur, bruit blanc, sinus).
    *   Assert : Vérifier que le VAD déclenche bien `SpeechStart` sur le sinus et `Silence` sur le silence.
*   **UtteranceBuffer** :
    *   Injecter des frames -> Vérifier que `finalize()` retourne la concaténation correcte.
    *   Tester le débordement (buffer full).
*   **TextPostProcessor** :
    *   Input : "euh... bonjour" -> Output : "Bonjour".

## 2. Tests d'Intégration (Mocks)

Tester la chaîne sans appeler les vraies API (pour ne pas payer/attendre).

*   **Mock Inworld** :
    *   Créer un faux serveur HTTP/WebSocket qui renvoie des chunks audio pré-enregistrés.
    *   Vérifier que le `InworldTTSClient` gère bien la connexion, les erreurs, et le parsing du stream.
*   **Mock STT** :
    *   Remplacer le moteur STT par une classe qui renvoie toujours "Ceci est un test" après 1 seconde.

## 3. Tests Audio (End-to-End Manuel & Automatisé)

*   **Loopback Test** :
    *   Jouer un fichier WAV connu dans le "Micro Virtuel" (via un autre outil).
    *   L'application le capture, transcrit, synthétise.
    *   Enregistrer la sortie de l'application.
    *   Comparer la transcription (WER - Word Error Rate) et vérifier la présence audio en sortie.
*   **Test de Latence** :
    *   Mesurer le delta temps entre "Input Signal >Seuil" et "Output Signal >Seuil".

## Outils

*   `pytest` (Runner de tests python)
*   `unittest.mock`
*   `numpy` (Génération de signaux audio de test)
