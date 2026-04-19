#!/usr/bin/env python3
"""
Asterisk Audio Converter
Converts any audio file to Asterisk-compatible format (8kHz, mono, 16-bit PCM)

Usage:
    python convert_audio.py input.mp3 output_name
    python convert_audio.py input.mp3 output_name --install

Examples:
    python convert_audio.py voice.mp3 greeting
    python convert_audio.py /path/to/audio.wav myvoice --install
"""

import subprocess
import sys
import os
import shutil

# Asterisk sounds directory
ASTERISK_SOUNDS_DIR = "/var/lib/asterisk/sounds"


def check_ffmpeg():
    """Check if ffmpeg is installed."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def convert_audio(input_file, output_name, output_dir="."):
    """
    Convert audio file to Asterisk-compatible formats.
    Creates both .wav and .gsm versions.
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        return False

    if not check_ffmpeg():
        print("Error: ffmpeg is not installed!")
        print("Install it with: sudo apt install ffmpeg")
        return False

    # Output paths
    wav_output = os.path.join(output_dir, f"{output_name}.wav")
    gsm_output = os.path.join(output_dir, f"{output_name}.gsm")

    # Convert to WAV (8kHz, mono, 16-bit PCM)
    print(f"Converting to WAV: {wav_output}")
    wav_cmd = [
        "ffmpeg", "-y", "-i", input_file,
        "-ar", "8000",      # 8kHz sample rate
        "-ac", "1",         # Mono
        "-acodec", "pcm_s16le",  # 16-bit PCM
        wav_output
    ]

    # Convert to GSM (most compatible with Asterisk)
    print(f"Converting to GSM: {gsm_output}")
    gsm_cmd = [
        "ffmpeg", "-y", "-i", input_file,
        "-ar", "8000",
        "-ac", "1",
        "-acodec", "gsm",
        gsm_output
    ]

    try:
        subprocess.run(wav_cmd, capture_output=True, check=True)
        subprocess.run(gsm_cmd, capture_output=True, check=True)
        print("\n✓ Conversion successful!")
        print(f"  - {wav_output}")
        print(f"  - {gsm_output}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        return False


def install_to_asterisk(output_name, source_dir="."):
    """Copy converted files to Asterisk sounds directory."""
    wav_file = os.path.join(source_dir, f"{output_name}.wav")
    gsm_file = os.path.join(source_dir, f"{output_name}.gsm")

    if not os.path.exists(wav_file) or not os.path.exists(gsm_file):
        print("Error: Converted files not found!")
        return False

    print(f"\nInstalling to {ASTERISK_SOUNDS_DIR}...")

    try:
        # Copy files (requires sudo)
        for src in [wav_file, gsm_file]:
            filename = os.path.basename(src)
            dest = os.path.join(ASTERISK_SOUNDS_DIR, filename)
            subprocess.run(["sudo", "cp", src, dest], check=True)
            subprocess.run(["sudo", "chown", "asterisk:asterisk", dest], check=True)
            print(f"  ✓ Installed: {dest}")

        # Reload Asterisk dialplan
        print("\nReloading Asterisk dialplan...")
        subprocess.run(["sudo", "asterisk", "-rx", "dialplan reload"], check=True)
        print("✓ Asterisk reloaded!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error installing: {e}")
        print("Make sure you have sudo access and Asterisk is running.")
        return False


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    input_file = sys.argv[1]
    output_name = sys.argv[2]
    install = "--install" in sys.argv

    print("=" * 50)
    print("Asterisk Audio Converter")
    print("=" * 50)
    print(f"Input:  {input_file}")
    print(f"Output: {output_name}.wav, {output_name}.gsm")
    print("=" * 50 + "\n")

    # Convert the audio
    if convert_audio(input_file, output_name):
        if install:
            install_to_asterisk(output_name)
        else:
            print(f"\nTo install to Asterisk, run:")
            print(f"  python {sys.argv[0]} {input_file} {output_name} --install")
            print(f"\nOr manually copy to {ASTERISK_SOUNDS_DIR}")


if __name__ == "__main__":
    main()
