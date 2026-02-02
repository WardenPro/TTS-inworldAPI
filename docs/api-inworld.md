# API Inworld Integration

Ce document détaille l'intégration technique avec l'API Inworld AI pour la synthèse vocale (TTS).

## Authentification

Inworld utilise un système d'authentification basé sur des tokens.

1.  **Génération de clé** : Obtenez `INWORLD_KEY` et `INWORLD_SECRET` depuis le Studio Inworld.
2.  **Basic Auth** : Encodage Base64 de `key:secret` pour obtenir un token d'accès (JWT, optionnel mais recommandé) ou utilisation directe.
3.  **Client JWT** : Pour une application distribuée, ne jamais exposer le secret. Générer un JWT via un backend sécurisé.

**Header Requis :**
```http
Authorization: Basic <base64(key:secret)>
# ou
Authorization: Bearer <token_jwt>
```

## Endpoints

### 1. TTS Streaming (HTTP) - Recommandé pour MVP

*   **URL** : `POST https://api.inworld.ai/tts/v1/voice:stream`
*   **Content-Type** : `application/json`

**Payload Ex :**
```json
{
  "text": "Bonjour, je suis une voix artificielle.",
  "voiceId": "workspace-id__voice-name",
  "audioConfig": {
    "audioEncoding": "LINEAR16",
    "sampleRateHertz": 48000,
    "speakingRate": 1.0,
    "pitch": 0.0,
    "volumeGainDb": 0.0
  },
  "config": {
     "applyTextNormalization": false
  }
}
```

**Réponse (Stream JSON) :**
Chaque ligne du stream est un objet JSON contenant :
```json
{
  "audioContent": "UklGRi..." // Base64 encoded PCM/WAV
}
```

### 2. TTS WebSocket - Recommandé pour Latence Faible

*   **URL** : `wss://api.inworld.ai/tts/v1/voice:streamBidirectional`

**Flux de messages :**
1.  **Connect** : Ouverture de la WebSocket.
2.  **Create Context** : Envoyer un message de configuration.
    ```json
    {
      "config": {
        "voiceId": "...",
        "audioConfig": { ... }
      }
    }
    ```
    Réponse : `contextId`
3.  **Send Text** : Envoyer du texte en continu.
    ```json
    {
      "text": {
        "text": "Hello world",
        "contextId": "..."
      }
    }
    ```
4.  **Receive Audio** : Écouter les événements `audioChunk`.
5.  **Flush** : Forcer la génération si fin de phrase.

## Gestion des Limites

*   **Texte** : Max 2000 caractères par requête HTTP. Max 1000 caractères par message WebSocket.
*   **Rate Limits** : Voir documentation officielle Inworld (dépend du plan).

## Liste des Voix (Voices API)

L'ancien endpoint `/tts/v1/voices` est déprécié.

*   **URL** : `GET https://api.inworld.ai/voices/v1/voices`
*   **Filtre** : `?filter=language=en` (exemple)

Structure d'une voix :
```json
{
  "name": "workspaces/xxx/voices/yyy",
  "baseName": "masculine_deep",
  "gender": "MALE",
  "naturalSampleRateHertz": 24000
}
```
L'ID à utiliser dans le TTS est souvent la dernière partie ou une combinaison spécifique (vérifier le retour API).

## Codes Erreurs Communs

| Code | Signification | Cause Probable | Action |
| :--- | :--- | :--- | :--- |
| **400** | Bad Request | JSON mal formé, ou champ manquant (ex: `text` vide). | Vérifier le payload. |
| **401** | Unauthorized | Clé API invalide ou expirée. | Vérifier `.env` et les clés Base64. |
| **403** | Forbidden | Quota dépassé ou accès non autorisé à ce workspace. | Vérifier le plan Inworld. |
| **404** | Not Found | `voiceId` inconnu ou incorrect. | Vérifier l'ID de la voix via l'API Voices. |
| **429** | Too Many Requests | Rate limit atteint. | Implémenter un backoff exponentiel. |
| **500** | Internal Error | Erreur côté Inworld. | Tenter un retry après quelques secondes. |
