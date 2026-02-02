import os
import requests
import base64
import json

class InworldAuth:
    def __init__(self, key=None, secret=None):
        self.key = key or os.getenv("INWORLD_KEY")
        self.secret = secret or os.getenv("INWORLD_SECRET")
        if not self.key or not self.secret:
            raise ValueError("INWORLD_KEY and INWORLD_SECRET are required")

    def get_auth_header(self):
        # Pour le MVP, on utilise Basic Auth simple
        # Dans un environnement de prod, on génèrerait un JWT
        credentials = f"{self.key}:{self.secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}

class InworldTTSClient:
    def __init__(self, auth: InworldAuth, model_id=None):
        self.auth = auth
        self.model_id = model_id or os.getenv("INWORLD_MODEL_ID", "inworld-tts-1.5-mini")
        self.base_url = "https://api.inworld.ai/tts/v1"

    def synthesize(self, text, voice_id, stream=False):
        """
        Appelle l'endpoint TTS. Si stream=True, utilise l'endpoint stream et retourne un générateur.
        """
        url = f"{self.base_url}/voice:stream" if stream else f"{self.base_url}/voice"

        headers = self.auth.get_auth_header()
        headers["Content-Type"] = "application/json"

        payload = {
            "text": text,
            "voiceId": voice_id,
            "modelId": self.model_id,
            "audioConfig": {
                "audioEncoding": "LINEAR16",
                "sampleRateHertz": 48000,
                "speakingRate": 1.0
            },
            "config": {
                "applyTextNormalization": False
            }
        }

        response = requests.post(url, headers=headers, json=payload, stream=stream)
        
        if response.status_code != 200:
            raise Exception(f"Inworld API Error {response.status_code}: {response.text}")

        if stream:
            return self._stream_generator(response)
        else:
            # Pour l'endpoint standard, le format dépend, mais ici on vise le stream ou le standard
            # L'endpoint standard retourne un JSON avec audioContent
            res_json = response.json()
            return base64.b64decode(res_json.get("audioContent", ""))

    def _stream_generator(self, response):
        """Lit le flux JSON ligne par ligne (ou chunk par chunk)"""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    if "audioContent" in data:
                        yield base64.b64decode(data["audioContent"])
                except json.JSONDecodeError:
                    pass
