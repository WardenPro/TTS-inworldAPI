# TTS-inworldAPI - Voice Changer IA

Transformez votre voix en temps réel avec l'IA d'Inworld. Idéal pour Discord, OBS, Zoom et autres applications de streaming/chat.

## Comment ça marche

```
[Votre Micro] → [Détection Voix] → [Transcription IA] → [Synthèse Inworld] → [Discord/OBS]
```

1. **VAD** - Détecte quand vous parlez
2. **STT** - Transcrit votre voix en texte (Vosk, Whisper ou Windows SAPI)
3. **TTS** - Inworld génère une nouvelle voix avec votre texte
4. **Sortie** - L'audio va vers un câble virtuel utilisable dans Discord

## Prérequis

- **Python 3.11 ou 3.12** (3.14 non supporté pour Whisper)
- **Compte Inworld AI** avec clés API
- **Câble audio virtuel** (voir installation par OS)

---

## Installation Windows

### 1. Installer Python

Téléchargez Python 3.12 sur [python.org](https://www.python.org/downloads/)

> Cochez "Add Python to PATH" pendant l'installation

### 2. Installer VB-Cable (câble audio virtuel)

Téléchargez et installez: https://vb-audio.com/Cable/

Cela crée deux périphériques:
- **CABLE Input** - où le voice changer envoie l'audio
- **CABLE Output** - ce que Discord utilise comme micro

### 3. Cloner et configurer

```cmd
git clone https://github.com/votre-user/TTS-inworldAPI.git
cd TTS-inworldAPI

:: Créer l'environnement virtuel
python -m venv venv

:: Activer le venv
venv\Scripts\activate

:: Installer les dépendances
pip install -r requirements.txt
pip install setuptools

:: (Optionnel) Pour utiliser Whisper au lieu de Vosk
pip install faster-whisper torch

:: (Optionnel) Pour utiliser la reconnaissance vocale Windows (SAPI)
pip install SpeechRecognition

:: (Optionnel) Pour le mode push-to-talk
pip install pynput
```

> **Windows SAPI** : Si vous utilisez le moteur `windows`, assurez-vous que le language pack français est installé :
> Paramètres > Heure et langue > Langue > Ajouter une langue > Français > cocher "Reconnaissance vocale"

### 4. Télécharger le modèle Vosk

```cmd
python download_model.py
```

### 5. Configurer les clés API

```cmd
copy .env.example .env
notepad .env
```

Remplissez:
```ini
INWORLD_KEY=votre_jwt_key
INWORLD_SECRET=votre_jwt_secret
INWORLD_VOICE_ID=votre_voice_id
INWORLD_MODEL_ID=inworld-tts-1.5-mini
```

Pour trouver votre Voice ID:
```cmd
python src/main.py list-voices
```

### 6. Lancer le Voice Changer

```cmd
:: Lister les périphériques audio
python src/main.py list-devices

:: Lancer (remplacez X par l'ID de CABLE Input)
python src/main.py run --output-device X

:: Avec Whisper (plus précis)
python src/main.py run --stt whisper --output-device X

:: Avec Windows SAPI (rapide, pas de modèle à télécharger)
python src/main.py run --stt windows --output-device X
```

### 7. Configurer Discord

1. Ouvrez Discord → Paramètres → Voix & Vidéo
2. Périphérique d'entrée: **CABLE Output**
3. Parlez - votre voix est maintenant transformée!

---

## Installation macOS

### 1. Installer Homebrew (si pas déjà fait)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Installer les dépendances système

```bash
brew install python@3.12 portaudio ffmpeg
```

### 3. Installer BlackHole (câble audio virtuel)

Téléchargez: https://existential.audio/blackhole/

Installez **BlackHole 2ch**.

### 4. Cloner et configurer

```bash
git clone https://github.com/votre-user/TTS-inworldAPI.git
cd TTS-inworldAPI

# Créer l'environnement virtuel avec Python 3.12
/opt/homebrew/bin/python3.12 -m venv venv

# Activer le venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
pip install setuptools

# (Optionnel) Pour utiliser Whisper au lieu de Vosk
pip install faster-whisper torch

# (Optionnel) Pour le mode push-to-talk
pip install pynput
```

### 5. Télécharger le modèle Vosk

```bash
python download_model.py
```

Si erreur SSL:
```bash
mkdir -p models && cd models
curl -k -O https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip
unzip vosk-model-small-fr-0.22.zip
cd ..
```

### 6. Configurer les clés API

```bash
cp .env.example .env
nano .env  # ou utilisez votre éditeur préféré
```

Remplissez:
```ini
INWORLD_KEY=votre_jwt_key
INWORLD_SECRET=votre_jwt_secret
INWORLD_VOICE_ID=votre_voice_id
INWORLD_MODEL_ID=inworld-tts-1.5-mini
```

Pour trouver votre Voice ID:
```bash
python src/main.py list-voices
```

### 7. Lancer le Voice Changer

```bash
# Lister les périphériques audio
python src/main.py list-devices

# Lancer (remplacez X par l'ID de BlackHole 2ch)
python src/main.py run --output-device X

# Avec Whisper (plus précis)
python src/main.py run --stt whisper --whisper-model small --output-device X
```

> **Note** : Le moteur Windows SAPI (`--stt windows`) n'est pas disponible sur macOS.

### 8. Configurer Discord

1. Ouvrez Discord → Paramètres → Voix & Vidéo
2. Périphérique d'entrée: **BlackHole 2ch**
3. Parlez - votre voix est maintenant transformée!

---

## Commandes

> Pensez toujours à activer le venv avant de lancer une commande :
> - **Windows** : `venv\Scripts\activate`
> - **macOS/Linux** : `source venv/bin/activate`

### `list-devices` - Lister les périphériques audio

Affiche tous les périphériques audio (entrées et sorties) avec leur ID, nom et sample rate. Utile pour trouver l'ID de votre micro et de votre câble virtuel.

```bash
python src/main.py list-devices
```

### `list-voices` - Lister les voix Inworld

Interroge l'API Inworld et affiche toutes les voix disponibles avec leur Voice ID. Nécessite les clés API dans `.env`.

```bash
python src/main.py list-voices
```

### `test-tts` - Tester la synthèse vocale

Envoie un texte à l'API Inworld et sauvegarde l'audio généré. Permet de vérifier que la connexion API fonctionne.

```bash
# Sauvegarder dans un fichier
python src/main.py test-tts --text "Bonjour le monde"

# Sauvegarder et jouer directement
python src/main.py test-tts --text "Bonjour" --play

# Avec une voix spécifique (sinon utilise .env)
python src/main.py test-tts --text "Hello" --voice mon_voice_id --play

# Changer le fichier de sortie
python src/main.py test-tts --text "Test" --output mon_fichier.wav
```

| Option | Description | Défaut |
|--------|-------------|--------|
| `--text TEXT` | Texte à synthétiser | `"Hello from Inworld voice changer"` |
| `--voice ID` | Voice ID Inworld | valeur de `.env` |
| `--output FILE` | Fichier de sortie | `output.wav` |
| `--play` | Jouer l'audio après génération | non |

### `test-vad` - Tester la détection de voix

Capture le micro et sauvegarde chaque segment de parole détecté dans un fichier WAV. Utile pour vérifier que le VAD détecte bien votre voix.

```bash
# Avec le micro par défaut
python src/main.py test-vad

# Avec un micro spécifique
python src/main.py test-vad --input-device 2

# Sauvegarder dans un dossier spécifique
python src/main.py test-vad --output-dir mes_enregistrements
```

| Option | Description | Défaut |
|--------|-------------|--------|
| `--input-device ID` | ID du micro | défaut système |
| `--output-dir DIR` | Dossier de sauvegarde | `recordings/` |

### `test-stt` - Tester la transcription sur un fichier

Transcrit un fichier WAV avec Vosk. Utile pour tester la qualité de transcription sans micro.

```bash
python src/main.py test-stt --file recordings/utterance_0.wav

# Avec un modèle Vosk spécifique
python src/main.py test-stt --file audio.wav --model models/vosk-model-fr-0.22
```

| Option | Description | Défaut |
|--------|-------------|--------|
| `--file FILE` | Fichier WAV à transcrire (obligatoire) | - |
| `--model PATH` | Chemin vers le modèle Vosk | `models/vosk-model-small-fr-0.22` |

### `run` - Lancer le voice changer

Commande principale. Démarre le pipeline complet : capture micro -> VAD -> STT -> TTS Inworld -> sortie audio.

```bash
# Basique avec Vosk (défaut)
python src/main.py run

# Avec périphériques spécifiques
python src/main.py run --input-device 1 --output-device 3

# Avec Whisper (plus précis, plus lent)
python src/main.py run --stt whisper

# Whisper modèle small (meilleure qualité)
python src/main.py run --stt whisper --whisper-model small

# Avec Windows SAPI (Windows uniquement, rapide, pas de modèle)
python src/main.py run --stt windows

# En anglais
python src/main.py run --stt whisper --language en

# VAD moins agressif (capte plus de sons, y compris du bruit)
python src/main.py run --vad-aggressiveness 1

# Push-to-Talk (maintenir la touche pour parler)
python src/main.py run --ptt --output-device X

# Push-to-Talk avec touche F1
python src/main.py run --ptt --ptt-key f1 --output-device X
```

| Option | Description | Défaut |
|--------|-------------|--------|
| `--input-device ID` | ID du microphone | défaut système |
| `--output-device ID` | ID de la sortie (câble virtuel) | défaut système |
| `--voice ID` | Voice ID Inworld | valeur de `.env` |
| `--stt ENGINE` | Moteur STT : `vosk`, `whisper` ou `windows` | `vosk` |
| `--model PATH` | Chemin vers le modèle Vosk | `models/vosk-model-small-fr-0.22` |
| `--whisper-model SIZE` | Modèle Whisper : `tiny`, `base`, `small`, `medium` | `base` |
| `--language CODE` | Langue : `fr`, `en`, `es`, `de`, etc. | `fr` |
| `--vad-aggressiveness N` | Filtrage bruit 0-3 (0=laisse passer, 3=strict) | `3` |
| `--ptt` | Active le mode push-to-talk | désactivé |
| `--ptt-key KEY` | Touche PTT : `space`, `f1`-`f4`, `ctrl_r`, `caps_lock` | `space` |

> **Push-to-Talk** : La touche et l'activation peuvent aussi se configurer dans `.env` avec `PTT_ENABLED=true` et `PTT_KEY=space`. Le flag `--ptt` en CLI prend la priorité sur `.env`.

---

## Choix du moteur STT

| Moteur | Précision | Vitesse | GPU | Taille | Plateforme |
|--------|-----------|---------|-----|--------|------------|
| **Vosk** | ~85-90% | Très rapide | Non | 41 MB | Toutes |
| **Whisper tiny** | ~90% | Rapide | Recommandé | 75 MB | Toutes |
| **Whisper base** | ~93% | Moyen | Recommandé | 150 MB | Toutes |
| **Whisper small** | ~96% | Lent sur CPU | Oui | 500 MB | Toutes |
| **Windows SAPI** | ~90-95% | Rapide | Non | 0 MB (intégré) | Windows |

**Recommandation :**
- **Windows sans GPU** : utilisez **Windows SAPI** (`--stt windows`) - rien à télécharger, bonne qualité
- **Sans GPU (multi-plateforme)** : utilisez **Vosk**
- **Avec GPU NVIDIA** : utilisez **Whisper small**

---

## Troubleshooting

### "No module named 'xxx'"
```bash
# Vérifiez que le venv est activé
# Windows:
venv\Scripts\activate
# macOS:
source venv/bin/activate
```

### "portaudio.h not found" (macOS)
```bash
brew install portaudio
pip uninstall pyaudio
pip install pyaudio
```

### "pkg_resources" error
```bash
pip install setuptools
```

### Erreur Inworld 401
- Vérifiez vos clés dans `.env`
- Utilisez **JWT Key** et **JWT Secret** (pas le Basic Base64)

### Erreur Inworld 400 "model ID"
- Ajoutez `INWORLD_MODEL_ID=inworld-tts-1.5-mini` dans `.env`

### La voix se répète en boucle
- C'est un feedback: le micro capte les haut-parleurs
- **Solution**: utilisez un casque ou le câble virtuel en sortie

### Latence élevée
- Utilisez Vosk au lieu de Whisper
- Vérifiez votre connexion internet

### Python 3.14 + Whisper ne fonctionne pas
- Whisper nécessite Python 3.11 ou 3.12
- Créez un venv avec la bonne version de Python

---

## Architecture

```
src/
├── main.py                 # CLI principale
├── core/
│   └── audio.py            # Capture micro, sortie audio
├── processing/
│   ├── vad.py              # Détection d'activité vocale
│   └── stt.py              # Transcription (Vosk/Whisper/Windows SAPI)
├── client/
│   └── inworld.py          # API Inworld TTS
└── controller/
    └── orchestrator.py     # Pipeline principal
```

---

## Licence

MIT

---

## Crédits

- [Inworld AI](https://inworld.ai/) - Synthèse vocale
- [Vosk](https://alphacephei.com/vosk/) - STT léger
- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper) - STT précis
- [SpeechRecognition](https://github.com/Uberi/speech_recognition) - Wrapper Python pour Windows SAPI
- [pynput](https://github.com/moses-palmer/pynput) - Listener clavier pour le push-to-talk
