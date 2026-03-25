#!/usr/bin/env python3
"""
Audio-Based Greeting System
===========================

Uses pre-recorded audio files from awaaz folder for language-appropriate greetings.
Plays back audio files directly instead of generating TTS.

Features:
- 22 official Indian languages supported
- Pre-recorded native speaker greetings
- Accurate language detection from Whisper
- Audio file playback for greeting
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 22 OFFICIAL INDIAN LANGUAGES (Constitutional Schedule VIII)
OFFICIAL_INDIAN_LANGUAGES = {
    "hi": {"name": "Hindi", "native": "हिंदी", "code": "hi"},
    "en": {"name": "English", "native": "English", "code": "en"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "code": "ta"},
    "te": {"name": "Telugu", "native": "తెలుగు", "code": "te"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "code": "kn"},
    "ml": {"name": "Malayalam", "native": "മലയാളം", "code": "ml"},
    "mr": {"name": "Marathi", "native": "मराठी", "code": "mr"},
    "gu": {"name": "Gujarati", "native": "ગુજરાતી", "code": "gu"},
    "bn": {"name": "Bengali", "native": "বাংলা", "code": "bn"},
    "as": {"name": "Assamese", "native": "অসমীয়া", "code": "as"},
    "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "code": "pa"},
    "or": {"name": "Odia", "native": "ଓଡ଼ିଆ", "code": "or"},
    "ur": {"name": "Urdu", "native": "اردو", "code": "ur"},
    "ne": {"name": "Nepali", "native": "नेपाली", "code": "ne"},
    "kok": {"name": "Konkani", "native": "कोंकणी", "code": "kok"},
    "ks": {"name": "Kashmiri", "native": "کشمیری", "code": "ks"},
    "sa": {"name": "Sanskrit", "native": "संस्कृतम्", "code": "sa"},
    "sd": {"name": "Sindhi", "native": "سنڌي", "code": "sd"},
    "mni": {"name": "Manipuri/Meitei", "native": "ꯃꯤꯇꯩ", "code": "mni"},
    "bo": {"name": "Bodo", "native": "बड़ो", "code": "bo"},
    "sat": {"name": "Santali", "native": "ᱥᱟᱱᱛᱟᱲᱤ", "code": "sat"},
    "mai": {"name": "Maithili", "native": "मैथिली", "code": "mai"},
}

# Mapping of language codes to available greeting audio files
# These are pre-recorded greetings in the awaaz folder
LANGUAGE_AUDIO_MAPPING = {
    "hi": "multilang_test_hi.wav",
    "en": "multilang_test_en.wav",
    "ta": "multilang_test_ta.wav",
    "te": "multilang_test_te.wav",
    "kn": "multilang_test_kn.wav",
    "ml": "multilang_test_ml.wav",
    "mr": "multilang_test_mr.wav",
    "gu": "multilang_test_gu.wav",
    "bn": "multilang_test_bn.wav",
    "as": "multilang_test_as.wav",
    "pa": "multilang_test_pa.wav",
    "or": "multilang_test_or.wav",
    # For languages without specific greeting files, fallback to English
    "ur": "multilang_test_en.wav",
    "ne": "multilang_test_en.wav",
    "kok": "multilang_test_kok.wav",
    "ks": "multilang_test_en.wav",
    "sa": "multilang_test_en.wav",
    "sd": "multilang_test_en.wav",
    "mni": "multilang_test_en.wav",
    "bo": "multilang_test_bho.wav",
    "sat": "multilang_test_en.wav",
    "mai": "multilang_test_mai.wav",
}


class AudioGreetingHandler:
    """
    Handles language-aware greetings using pre-recorded audio files.
    """

    def __init__(self, awaaz_folder: str = None):
        """
        Initialize the audio greeting handler.

        Args:
            awaaz_folder: Path to awaaz folder containing audio files.
                         If None, will search common locations.
        """
        self.awaaz_folder = self._find_awaaz_folder(awaaz_folder)
        if not self.awaaz_folder:
            logger.warning("Awaaz folder not found!")
            self.awaaz_folder = ""
        else:
            logger.info(f"Found awaaz folder: {self.awaaz_folder}")

        # Check available audio files
        self.available_audio_files = self._check_available_audio_files()
        logger.info(f"Found {len(self.available_audio_files)} audio greeting files")

    def _find_awaaz_folder(self, provided_path: str = None) -> str:
        """Find the awaaz folder."""
        if provided_path and os.path.exists(provided_path):
            return provided_path

        # Search common locations
        possible_paths = [
            "/Users/devendrainamdar/Desktop/delhi/digital_democracy_ai_calling/awaaz",
            "./awaaz",
            "../awaaz",
            "../../awaaz",
        ]

        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                return os.path.abspath(path)

        return None

    def _check_available_audio_files(self) -> dict:
        """Check which audio greeting files are available."""
        available = {}
        if not self.awaaz_folder:
            return available

        for lang_code, audio_file in LANGUAGE_AUDIO_MAPPING.items():
            full_path = os.path.join(self.awaaz_folder, audio_file)
            if os.path.exists(full_path):
                available[lang_code] = full_path
                logger.debug(f"✓ Found greeting for {lang_code}: {audio_file}")
            else:
                logger.debug(f"✗ Missing greeting for {lang_code}: {audio_file}")

        return available

    def is_valid_language(self, language_code: str) -> bool:
        """Check if the language is one of the 22 official Indian languages."""
        return language_code in OFFICIAL_INDIAN_LANGUAGES

    def get_greeting_audio_path(self, language_code: str) -> Optional[str]:
        """
        Get the path to the greeting audio file for a language.

        Args:
            language_code: ISO 639-1 language code (e.g., 'hi', 'ta', 'en')

        Returns:
            Path to audio file, or None if not available
        """
        if not self.is_valid_language(language_code):
            logger.warning(
                f"Language {language_code} is not an official Indian language"
            )
            # Fallback to English
            language_code = "en"

        return self.available_audio_files.get(language_code)

    def play_greeting(self, language_code: str, display_only: bool = False) -> bool:
        """
        Play greeting audio for the detected language.

        Args:
            language_code: ISO 639-1 language code
            display_only: If True, only display info without playing

        Returns:
            True if greeting played/displayed successfully
        """
        audio_path = self.get_greeting_audio_path(language_code)

        if not audio_path:
            logger.warning(f"No audio file found for language {language_code}")
            self._print_fallback_greeting(language_code, display_only)
            return False

        language_name = OFFICIAL_INDIAN_LANGUAGES[language_code]["name"]
        print(f"\n🎙️  Greeting User:")
        print(f"  Language: {language_name}")
        print(f"  File: {os.path.basename(audio_path)}")

        if display_only:
            print(f"  ✓ Greeting ready to play")
            return True

        # Try to play audio
        try:
            self._play_audio_file(audio_path)
            print(f"  ✓ Greeting played")
            return True
        except Exception as e:
            logger.error(f"Error playing greeting audio: {e}")
            print(f"  ⚠️ Could not play audio: {e}")
            self._print_fallback_greeting(language_code, display_only=True)
            return False

    def _play_audio_file(self, audio_path: str) -> None:
        """Play audio file using available methods."""
        try:
            import sounddevice as sd
            import soundfile as sf

            data, sr = sf.read(audio_path)
            print(f"  Playing audio ({len(data) / sr:.1f}s)...")
            sd.play(data, samplerate=sr)
            sd.wait()
        except ImportError:
            logger.warning("sounddevice/soundfile not available, trying system command")
            # Fallback to system command
            os.system(f"afplay '{audio_path}'")  # macOS
            # For Linux: os.system(f"aplay '{audio_path}'")

    def _print_fallback_greeting(self, language_code: str, display_only: bool = True):
        """Print a text-based fallback greeting."""
        language_name = OFFICIAL_INDIAN_LANGUAGES[language_code]["name"]
        print(f"\n🎙️  Greeting User (text fallback):")
        print(f"  Language: {language_name}")

        greetings = {
            "hi": "नमस्ते! आपकी शिकायत दर्ज की जा रही हैं।",
            "en": "Hello! Your complaint is being registered.",
            "ta": "வணக்கம்! உங்கள் புகாரை பதிவு செய்கிறோம்.",
            "te": "హలో! మీ ఫిర్యాదు రిజిస్టర్ చేస్తున్నాం.",
            "mr": "नमस्कार! तुमची तक्रार नोंदवत आहे.",
            "gu": "નમસ્તે! તમારી ફરિયાદ નોંધી રહ્યા છીએ.",
            "kn": "ನಮಸ್ಕಾರ! ನಿಮ್ಮ ದೂರು ದಾಖಲ ಮಾಡುತ್ತಿದ್ದೇವೆ.",
            "ml": "നമസ്കാരം! നിങ്ങളുടെ പരാതി രജിസ്ട്റർ ചെയ്യുകയാണ്.",
            "bn": "নমস্কার! আমরা আপনার অভিযোগ নিবন্ধন করছি।",
            "pa": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਤੁਹਾਡੀ ਸ਼ਿਕਾਇਤ ਦਰਜ ਕੀਤੀ ਜਾ ਰਹੀ ਹੈ।",
        }

        greeting_text = greetings.get(language_code, greetings["en"])
        print(f"  Message: {greeting_text}")
        print(f"  ✓ Greeting displayed")

    def detect_and_greet(
        self, language_code: str, display_only: bool = False
    ) -> bool:
        """
        Detect language from Whisper output and play appropriate greeting.

        Args:
            language_code: Language code from Whisper detection
            display_only: If True, only display info without playing

        Returns:
            True if successful
        """
        # Validate language is one of 22 official Indian languages
        if not self.is_valid_language(language_code):
            logger.warning(
                f"Detected language {language_code} is not an official Indian language, falling back to English"
            )
            language_code = "en"

        return self.play_greeting(language_code, display_only)


def create_greeting_handler(awaaz_folder: str = None) -> AudioGreetingHandler:
    """Factory function to create greeting handler."""
    return AudioGreetingHandler(awaaz_folder)


if __name__ == "__main__":
    # Test the greeting handler
    handler = AudioGreetingHandler()

    print("Available languages with greetings:")
    for lang_code in OFFICIAL_INDIAN_LANGUAGES:
        audio_path = handler.get_greeting_audio_path(lang_code)
        status = "✓" if audio_path else "✗"
        lang_name = OFFICIAL_INDIAN_LANGUAGES[lang_code]["name"]
        print(f"  {status} {lang_code}: {lang_name}")

    print("\nTesting greetings (display only):")
    for lang_code in ["hi", "en", "ta", "te"]:
        handler.detect_and_greet(lang_code, display_only=True)
