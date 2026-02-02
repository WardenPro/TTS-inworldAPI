#!/usr/bin/env python3
"""
Script pour télécharger le modèle Vosk français.
Compatible Windows, macOS, Linux.
"""
import os
import sys
import urllib.request
import zipfile
import shutil

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip"
MODEL_NAME = "vosk-model-small-fr-0.22"
MODELS_DIR = "models"


def download_with_progress(url, dest):
    """Télécharge un fichier avec barre de progression."""
    print(f"Downloading: {url}")

    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(100, downloaded * 100 // total_size) if total_size > 0 else 0
        bar_len = 40
        filled = int(bar_len * percent // 100)
        bar = '=' * filled + '-' * (bar_len - filled)
        mb_downloaded = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        sys.stdout.write(f'\r[{bar}] {percent}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)')
        sys.stdout.flush()

    urllib.request.urlretrieve(url, dest, progress_hook)
    print()  # New line after progress bar


def main():
    # Créer le dossier models si nécessaire
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
        print(f"Created directory: {MODELS_DIR}/")

    model_path = os.path.join(MODELS_DIR, MODEL_NAME)

    # Vérifier si le modèle existe déjà
    if os.path.exists(model_path):
        print(f"Model already exists: {model_path}")
        response = input("Re-download? [y/N]: ").strip().lower()
        if response != 'y':
            print("Aborted.")
            return
        shutil.rmtree(model_path)

    zip_path = os.path.join(MODELS_DIR, f"{MODEL_NAME}.zip")

    # Télécharger
    try:
        download_with_progress(MODEL_URL, zip_path)
    except Exception as e:
        print(f"\nError downloading: {e}")
        sys.exit(1)

    # Extraire
    print(f"Extracting to {MODELS_DIR}/...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(MODELS_DIR)
    except Exception as e:
        print(f"Error extracting: {e}")
        sys.exit(1)

    # Nettoyer le zip
    os.remove(zip_path)

    print(f"\nModel ready: {model_path}")
    print("\nYou can now run:")
    print("  python src/main.py run")


if __name__ == "__main__":
    main()
