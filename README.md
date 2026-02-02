# TTS-inworldAPI - Voice Changer IA

Transformez votre voix en temps réel avec l'IA d'Inworld. Idéal pour Discord, OBS, Zoom et autres applications de streaming/chat.

## Comment ça marche

```
[Votre Micro] → [Détection Voix] → [Transcription IA] → [Synthèse Inworld] → [Discord/OBS]
```

1. **VAD** - Détecte quand vous parlez
2. **STT** - Transcrit votre voix en texte (Vosk ou Whisper)
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
```

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

### 8. Configurer Discord

1. Ouvrez Discord → Paramètres → Voix & Vidéo
2. Périphérique d'entrée: **BlackHole 2ch**
3. Parlez - votre voix est maintenant transformée!

---

## Commandes

```bash
# Toujours activer le venv d'abord!
# Windows: venv\Scripts\activate
# macOS:   source venv/bin/activate

# Lister les périphériques audio
python src/main.py list-devices

# Lister les voix Inworld disponibles
python src/main.py list-voices

# Tester le TTS
python src/main.py test-tts --text "Bonjour" --play

# Tester le micro + VAD
python src/main.py test-vad

# Tester le STT sur un fichier
python src/main.py test-stt --file audio.wav

# Lancer le voice changer
python src/main.py run [options]
```

### Options de `run`

| Option | Description | Défaut |
|--------|-------------|--------|
| `--input-device ID` | ID du microphone | défaut système |
| `--output-device ID` | ID de la sortie (câble virtuel) | défaut système |
| `--stt ENGINE` | Moteur STT: `vosk` ou `whisper` | `vosk` |
| `--whisper-model SIZE` | Modèle Whisper: `tiny`, `base`, `small`, `medium` | `base` |
| `--language CODE` | Langue: `fr`, `en`, etc. | `fr` |
| `--vad-aggressiveness N` | Filtrage bruit 0-3 (3=max) | `3` |

### Exemples

```bash
# Basique avec Vosk
python src/main.py run

# Avec périphériques spécifiques
python src/main.py run --input-device 1 --output-device 3

# Avec Whisper (plus précis, plus lent)
python src/main.py run --stt whisper

# Whisper modèle small (meilleure qualité)
python src/main.py run --stt whisper --whisper-model small

# En anglais
python src/main.py run --stt whisper --language en
```

---

## Choix du moteur STT

| Moteur | Précision | Vitesse | GPU | Taille |
|--------|-----------|---------|-----|--------|
| **Vosk** | ~85-90% | Très rapide | Non | 41 MB |
| **Whisper tiny** | ~90% | Rapide | Recommandé | 75 MB |
| **Whisper base** | ~93% | Moyen | Recommandé | 150 MB |
| **Whisper small** | ~96% | Lent sur CPU | Oui | 500 MB |

**Recommandation:**
- Sans GPU: utilisez **Vosk**
- Avec GPU NVIDIA: utilisez **Whisper small**

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
│   └── stt.py              # Transcription (Vosk/Whisper)
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
