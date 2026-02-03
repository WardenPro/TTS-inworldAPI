# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TTS-inworldAPI is a real-time AI voice changer using Inworld's TTS API. It captures microphone input, transcribes speech (Vosk, Whisper, or Windows SAPI), and resynthesizes it with Inworld AI voices. Output goes to a virtual audio device for Discord, OBS, etc.

## Quick Commands

```bash
# Activate venv first!
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# List audio devices
python src/main.py list-devices

# List Inworld voices
python src/main.py list-voices

# Run voice changer (Vosk - fast)
python src/main.py run --output-device <ID>

# Run voice changer (Whisper - accurate)
python src/main.py run --stt whisper --whisper-model small --output-device <ID>

# Run voice changer (Windows SAPI - Windows only, no model download)
python src/main.py run --stt windows --output-device <ID>

# Run with push-to-talk (hold key to speak)
python src/main.py run --ptt --output-device <ID>

# Test TTS only
python src/main.py test-tts --text "Hello" --play
```

## Architecture

```
Microphone → VAD → STT (Vosk/Whisper/Windows) → Inworld TTS → Virtual Audio Output
```

### Key Files

- **`src/main.py`** - CLI entry point with all commands
- **`src/core/audio.py`** - PyAudio wrapper (MicCapture, AudioOutput, AudioDeviceManager)
- **`src/processing/vad.py`** - Voice Activity Detection (WebRTC VAD + UtteranceBuffer)
- **`src/processing/stt.py`** - Speech-to-Text engines (VoskSTTEngine, WhisperSTTEngine, WindowsSpeechEngine)
- **`src/client/inworld.py`** - Inworld API client (InworldAuth, InworldTTSClient)
- **`src/controller/orchestrator.py`** - Main pipeline (VoiceChangerOrchestrator, PipelineConfig)

### Threading Model

- **PyAudio callback thread**: Microphone capture + VAD
- **Processing thread**: STT transcription + TTS API calls
- **Playback thread**: Audio output to virtual device
- **pynput listener thread** (PTT mode only): Keyboard events for push-to-talk

### Audio Format

48kHz, 16-bit mono PCM (LINEAR16)

## Environment Variables

Required in `.env`:
- `INWORLD_KEY` - JWT Key from Inworld Studio
- `INWORLD_SECRET` - JWT Secret from Inworld Studio
- `INWORLD_VOICE_ID` - Voice ID (use `list-voices` to find)
- `INWORLD_MODEL_ID` - Model ID (default: `inworld-tts-1.5-mini`)

Optional in `.env`:
- `PTT_ENABLED` - Enable push-to-talk mode (`true`/`false`, default: `false`)
- `PTT_KEY` - Push-to-talk key (`space`, `f1`-`f4`, `ctrl_r`, `caps_lock`, default: `space`)

## STT Engines

| Engine | Accuracy | Speed | GPU Required | Platform |
|--------|----------|-------|--------------|----------|
| Vosk | ~85-90% | Very fast | No | All |
| Whisper tiny | ~90% | Fast | Recommended | All |
| Whisper base | ~93% | Medium | Recommended | All |
| Whisper small | ~96% | Slow on CPU | Yes | All |
| Windows SAPI | ~90-95% | Fast | No | Windows only |

## Dependencies

- Python 3.11 or 3.12 (3.14 not supported for Whisper)
- PortAudio (macOS: `brew install portaudio`)
- FFmpeg for Whisper (macOS: `brew install ffmpeg`)
- Virtual audio cable (VB-Cable on Windows, BlackHole on macOS)
- SpeechRecognition for Windows STT (`pip install SpeechRecognition`) - Windows only
- pynput for push-to-talk (`pip install pynput`)
