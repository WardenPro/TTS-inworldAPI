import argparse
import os
import sys
import time
from dotenv import load_dotenv
from core.audio import AudioDeviceManager, AudioOutput, MicCapture
from client.inworld import InworldAuth, InworldTTSClient
from processing.vad import VoiceActivityDetector, UtteranceBuffer

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="TTS-inworldAPI MVP")
    subparsers = parser.add_subparsers(dest="command")

    # Command: list-devices
    subparsers.add_parser("list-devices", help="List audio input/output devices")

    # Command: list-voices
    subparsers.add_parser("list-voices", help="List available Inworld voices")

    # Command: test-tts
    tts_parser = subparsers.add_parser("test-tts", help="Test Inworld TTS connection")
    tts_parser.add_argument("--text", type=str, default="Hello from Inworld voice changer", help="Text to synthesize")
    tts_parser.add_argument("--voice", type=str, help="Voice ID (overrides .env)")
    tts_parser.add_argument("--output", type=str, default="output.wav", help="Output file (test mode)")
    tts_parser.add_argument("--play", action="store_true", help="Play audio immediately")

    # Command: test-vad
    vad_parser = subparsers.add_parser("test-vad", help="Test Microphone Capture & VAD")
    vad_parser.add_argument("--input-device", type=int, help="Input Device ID (see list-devices)")
    vad_parser.add_argument("--output-dir", type=str, default="recordings", help="Directory to save utterances")

    # Command: test-stt
    stt_parser = subparsers.add_parser("test-stt", help="Test Vosk STT on a WAV file")
    stt_parser.add_argument("--file", type=str, required=True, help="WAV file to transcribe")
    stt_parser.add_argument("--model", type=str, default="models/vosk-model-small-fr-0.22", help="Path to Vosk model")

    # Command: run (pipeline complet)
    run_parser = subparsers.add_parser("run", help="Run the voice changer pipeline")
    run_parser.add_argument("--input-device", type=int, help="Input device ID (microphone)")
    run_parser.add_argument("--output-device", type=int, help="Output device ID (virtual cable)")
    run_parser.add_argument("--voice", type=str, help="Inworld voice ID (overrides .env)")
    run_parser.add_argument("--stt", type=str, default="vosk", choices=["vosk", "whisper"], help="STT engine (vosk or whisper)")
    run_parser.add_argument("--model", type=str, default="models/vosk-model-small-fr-0.22", help="Path to Vosk model")
    run_parser.add_argument("--whisper-model", type=str, default="base", choices=["tiny", "base", "small", "medium"], help="Whisper model size")
    run_parser.add_argument("--language", type=str, default="fr", help="Language code for STT (fr, en, etc.)")
    run_parser.add_argument("--vad-aggressiveness", type=int, default=3, choices=[0, 1, 2, 3], help="VAD aggressiveness (0=least, 3=most)")

    args = parser.parse_args()

    if args.command == "list-devices":
        mgr = AudioDeviceManager()
        devices = mgr.list_devices()
        print(f"Found {len(devices)} devices:")
        for dev in devices:
            kind = "Input" if dev.is_input else "Output"
            print(f"[{kind}] ID: {dev.index} - {dev.name} (SR: {dev.sample_rate}Hz, Ch: {dev.channels})")
        mgr.terminate()

    elif args.command == "list-voices":
        import requests

        try:
            auth = InworldAuth()
            headers = auth.get_auth_header()

            print("Fetching voices from Inworld API...")
            response = requests.get(
                "https://api.inworld.ai/voices/v1/voices",
                headers=headers
            )

            if response.status_code != 200:
                print(f"Error {response.status_code}: {response.text}")
                sys.exit(1)

            data = response.json()
            voices = data.get("voices", [])

            if not voices:
                print("No voices found.")
            else:
                print(f"\nFound {len(voices)} voices:\n")
                print("-" * 80)
                for v in voices:
                    name = v.get("name", "")
                    # Extract short ID from full path like "workspaces/xxx/voices/yyy"
                    voice_id = name.split("/")[-1] if "/" in name else name

                    print(f"Voice ID:  {voice_id}")
                    print(f"Full name: {name}")
                    # Afficher tous les autres champs disponibles
                    for key, value in v.items():
                        if key != "name" and value:
                            print(f"  {key}: {value}")
                    print("-" * 80)

                print("\nUse the 'Voice ID' or 'Full name' in your .env file:")
                print("INWORLD_VOICE_ID=<voice_id>")

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "test-vad":
        if args.input_device is None:
            print("Warning: No input device specified, using system default.")
        
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)

        print(f"🎤 Starting VAD Capture test...")
        print(f"Device Index: {args.input_device}")
        print(f"Saving to: {args.output_dir}/")
        print("Press Ctrl+C to stop.")

        vad = VoiceActivityDetector(sample_rate=48000)
        # On garde 48kHz pour le sample_rate final, mais le VAD peut vouloir du 48kHz
        # Padding 300ms pour bien capter le début
        buffer = UtteranceBuffer(min_speech_ms=100, min_silence_ms=500, padding_ms=300) 
        
        utterance_count = 0

        def audio_callback(in_data):
            nonlocal utterance_count
            # Le VAD prend des frames de 10, 20 ou 30ms.
            # MicCapture est configuré par défaut à 20ms (chunk_ms=20).
            is_speech = vad.is_speech(in_data)
            
            wav_bytes = buffer.process_frame(in_data, is_speech)
            if wav_bytes:
                filename = os.path.join(args.output_dir, f"utterance_{utterance_count}.wav")
                # Ecriture simple d'un WAV header + PCM
                import wave
                with wave.open(filename, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2) # 16-bit
                    wf.setframerate(48000)
                    wf.writeframes(wav_bytes)
                
                print(f" [SAVED] {filename}")
                utterance_count += 1

        capture = MicCapture(device_index=args.input_device, sample_rate=48000, chunk_ms=20)
        
        try:
            capture.start(audio_callback)
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping capture...")
            capture.stop()

    elif args.command == "test-tts":
        voice_id = args.voice or os.getenv("INWORLD_VOICE_ID")
        if not voice_id:
            print("Error: No voice ID provided. Set INWORLD_VOICE_ID in .env or use --voice")
            sys.exit(1)
        
        print(f"Synthesizing: '{args.text}'...")
        print(f"Voice ID: '{voice_id}'")
        
        try:
            auth = InworldAuth()
            client = InworldTTSClient(auth)
            
            # Use stream=False for simple WAV dump in this test
            audio_data = client.synthesize(args.text, voice_id, stream=False)
            
            with open(args.output, "wb") as f:
                f.write(audio_data)
            print(f"✅ Success! Audio saved to {args.output} ({len(audio_data)} bytes)")
            
            if args.play:
                print("Playing audio...")
                out = AudioOutput() # default device
                out.start()
                out.write(audio_data)
                time.sleep(len(audio_data) / 2 / 48000 + 0.5) # approx wait
                out.stop()

        except Exception as e:
            print(f"❌ Error: {e}")
            if "INWORLD_KEY" in str(e):
                print("Tip: Check your .env file credentials.")

    elif args.command == "test-stt":
        import wave
        from processing.stt import VoskSTTEngine

        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}")
            sys.exit(1)

        if not os.path.exists(args.model):
            print(f"Error: Model not found: {args.model}")
            print("Download it with:")
            print(f"  mkdir -p models && cd models")
            print(f"  wget https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip")
            print(f"  unzip vosk-model-small-fr-0.22.zip")
            sys.exit(1)

        print(f"Loading model: {args.model}")
        stt = VoskSTTEngine(model_path=args.model, input_sample_rate=48000)

        print(f"Reading: {args.file}")
        with wave.open(args.file, 'rb') as wf:
            sample_rate = wf.getframerate()
            audio_bytes = wf.readframes(wf.getnframes())

        if sample_rate != 48000:
            print(f"Warning: File is {sample_rate}Hz, expected 48000Hz. Results may vary.")

        print("Transcribing...")
        start_time = time.time()
        text = stt.transcribe(audio_bytes)
        elapsed = time.time() - start_time

        print(f"Result ({elapsed:.2f}s): '{text}'")

    elif args.command == "run":
        from controller.orchestrator import VoiceChangerOrchestrator, PipelineConfig

        voice_id = args.voice or os.getenv("INWORLD_VOICE_ID")
        if not voice_id:
            print("Error: No voice ID. Set INWORLD_VOICE_ID in .env or use --voice")
            sys.exit(1)

        # Vérifier le modèle Vosk si utilisé
        if args.stt == "vosk" and not os.path.exists(args.model):
            print(f"Error: Vosk model not found: {args.model}")
            print("Download the French model with:")
            print(f"  python download_model.py")
            print("Or use Whisper instead:")
            print(f"  python src/main.py run --stt whisper")
            sys.exit(1)

        input_dev = args.input_device
        if input_dev is None and os.getenv("INPUT_DEVICE_INDEX"):
            input_dev = int(os.getenv("INPUT_DEVICE_INDEX"))

        output_dev = args.output_device
        if output_dev is None and os.getenv("OUTPUT_DEVICE_INDEX"):
            output_dev = int(os.getenv("OUTPUT_DEVICE_INDEX"))

        config = PipelineConfig(
            input_device=input_dev,
            output_device=output_dev,
            voice_id=voice_id,
            stt_engine=args.stt,
            vosk_model_path=args.model,
            whisper_model=args.whisper_model,
            language=args.language,
            vad_aggressiveness=args.vad_aggressiveness
        )

        print("=" * 50)
        print("    TTS-inworldAPI Voice Changer")
        print("=" * 50)
        print(f"Input device:  {input_dev or 'default'}")
        print(f"Output device: {output_dev or 'default'}")
        print(f"Voice ID:      {voice_id}")
        print(f"STT Engine:    {args.stt}" + (f" ({args.whisper_model})" if args.stt == "whisper" else f" ({args.model})"))
        print(f"Language:      {args.language}")
        print(f"VAD level:     {args.vad_aggressiveness}")
        print("=" * 50)
        print("Press Ctrl+C to stop.")
        print()

        auth = InworldAuth()
        orchestrator = VoiceChangerOrchestrator(config, auth)

        try:
            orchestrator.start()
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            orchestrator.stop()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
