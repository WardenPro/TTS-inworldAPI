# Sécurité

Ce document aborde les aspects de sécurité pour l'application TTS-inworldAPI.

## 1. Gestion des Secrets

### Clés API Inworld
*   **Risque** : Exposition des clés `INWORLD_KEY` et `INWORLD_SECRET`.
*   **Mitigation** :
    *   **Ne jamais hardcoder** les clés dans le code source commit.
    *   Utiliser des variables d'environnement (`.env` non versionné).
    *   Utiliser un fichier `.gitignore` pour exclure `.env`.

### Architecture Distribuée (Production)
Si l'application est distribuée à des utilisateurs finaux :
*   **Interdiction** : Ne pas embarquer vos clés API "serveur" dans l'application client.
*   **Solution** :
    1.  Mettre en place un Backend intermédiaire (Proxy).
    2.  L'app client s'authentifie auprès de votre Backend (Auth0, Firebase, etc.).
    3.  Votre Backend appelle Inworld pour générer un JWT (`generate_token`).
    4.  Votre Backend renvoie le JWT au client.
    5.  Le client utilise ce JWT pour appeler Inworld directement.

## 2. Données Audio

*   **Confidentialité** : L'audio de l'utilisateur est capturé et envoyé à un moteur STT local ou cloud.
    *   **STT Local** : Préférable pour la vie privée (aucune donnée voix ne quitte la machine pour la transcription).
    *   **STT Cloud** : Si utilisé, les données transitent. Chiffrer TLS 1.2+ obligatoire.
*   **Inworld** : Le texte est envoyé à Inworld. Inworld traite les données selon sa politique de confidentialité (vérifier la retention policy pour les données conversationnelles).

## 3. Dépendances

*   Utiliser des versions fixées dans `requirements.txt` ou `poetry.lock` pour éviter les attaques de type Supply Chain ou le typosquatting.
*   Scanner les vulnérabilités régulièrement (ex: `pip-audit`, `dependabot`).
