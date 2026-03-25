#!/usr/bin/env python3
"""
Language Detection Constraint Module
====================================

Ensures language detection only returns one of the 22 official Indian languages.
Constrains Whisper output to Indian languages only, with English as fallback.
"""

import logging
from typing import Optional
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

# 22 OFFICIAL INDIAN LANGUAGES (Constitutional Schedule VIII)
OFFICIAL_INDIAN_LANGUAGES = {
    "hi": "Hindi",
    "en": "English",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "gu": "Gujarati",
    "bn": "Bengali",
    "as": "Assamese",
    "pa": "Punjabi",
    "or": "Odia",
    "ur": "Urdu",
    "ne": "Nepali",
    "kok": "Konkani",
    "ks": "Kashmiri",
    "sa": "Sanskrit",
    "sd": "Sindhi",
    "mni": "Manipuri",
    "bo": "Bodo",
    "sat": "Santali",
    "mai": "Maithili",
}

# Whisper uses different language codes in some cases
# Map Whisper codes to our standardized ones
WHISPER_TO_STANDARD = {
    "hi": "hi",
    "en": "en",
    "ta": "ta",
    "te": "te",
    "kn": "kn",
    "ml": "ml",
    "mr": "mr",
    "gu": "gu",
    "bn": "bn",
    "as": "as",
    "pa": "pa",
    "or": "or",
    "ur": "ur",
    "ne": "ne",
    "kok": "kok",
    "ks": "ks",
    "sa": "sa",
    "sd": "sd",
    "mni": "mni",
    "bo": "bo",
    "sat": "sat",
    "mai": "mai",
    # Common non-Indian language mappings
    "zh": "hi",  # Chinese -> Hindi
    "ja": "hi",  # Japanese -> Hindi
    "ko": "hi",  # Korean -> Hindi
    "fr": "en",  # French -> English
    "es": "en",  # Spanish -> English
    "de": "en",  # German -> English
    "ru": "hi",  # Russian -> Hindi
    "px": "en",  # Unknown -> English
}


class ConstrainedLanguageDetector:
    """
    Detects language from audio and constrains to 22 official Indian languages only.
    Prevents erroneous detection of non-Indian languages.
    """

    def __init__(self, model_size: str = "base"):
        """Initialize detector with Whisper model."""
        self.model_size = model_size
        self.model = None
        self._init_model()

    def _init_model(self):
        """Load Whisper model."""
        try:
            logger.info(f"Loading Whisper ({self.model_size}) for constrained language detection...")
            self.model = WhisperModel(
                self.model_size,
                device="auto",
                compute_type="auto"
            )
            logger.info("✓ Whisper model loaded")
        except Exception as e:
            logger.error(f"Failed to load Whisper: {e}")
            self.model = None

    def detect_language_constrained(self, audio_file: str) -> str:
        """
        Detect language from audio, constrained to 22 official Indian languages.

        Args:
            audio_file: Path to .wav file

        Returns:
            ISO 639-1 language code from official Indian languages
        """
        if not self.model:
            logger.warning("Model not available, defaulting to Hindi")
            return "hi"

        try:
            logger.info(f"Detecting language from: {audio_file}")

            # Run Whisper transcription with language detection
            segments, info = self.model.transcribe(
                audio_file,
                language=None,  # Auto-detect
                beam_size=5
            )

            # Extract detected language
            detected_lang = info.language if hasattr(info, 'language') else 'en'

            logger.debug(f"Whisper detected: {detected_lang}")

            # Map to standard code if needed
            standard_lang = WHISPER_TO_STANDARD.get(detected_lang, detected_lang)

            # Validate - if not an official Indian language, fallback to English
            if standard_lang not in OFFICIAL_INDIAN_LANGUAGES:
                logger.warning(
                    f"Detected language '{detected_lang}' (mapped to '{standard_lang}') "
                    f"is not an official Indian language. Falling back to English."
                )
                standard_lang = "en"

            lang_name = OFFICIAL_INDIAN_LANGUAGES.get(standard_lang, "Unknown")
            logger.info(f"✓ Constrained detection: {standard_lang} ({lang_name})")

            return standard_lang

        except Exception as e:
            logger.error(f"Language detection error: {e}")
            logger.warning("Falling back to Hindi")
            return "hi"

    @staticmethod
    def is_valid_language(lang_code: str) -> bool:
        """Check if language code is one of 22 official Indian languages."""
        return lang_code in OFFICIAL_INDIAN_LANGUAGES

    @staticmethod
    def get_valid_languages() -> dict:
        """Get dictionary of all valid language codes and names."""
        return OFFICIAL_INDIAN_LANGUAGES.copy()


def constrain_detected_language(detected_lang: str, fallback: str = "en") -> str:
    """
    Utility function to constrain any detected language to 22 official Indian languages.

    Args:
        detected_lang: Language code from any source
        fallback: Fallback language if detection is invalid (default: English)

    Returns:
        Valid language code from 22 official Indian languages
    """
    # Try direct mapping first
    standard_lang = WHISPER_TO_STANDARD.get(detected_lang, detected_lang)

    # If still not valid, use fallback
    if standard_lang not in OFFICIAL_INDIAN_LANGUAGES:
        logger.warning(
            f"Language '{detected_lang}' is not an official Indian language, "
            f"using fallback: {fallback}"
        )
        standard_lang = fallback if fallback in OFFICIAL_INDIAN_LANGUAGES else "en"

    return standard_lang


if __name__ == "__main__":
    # Test the detector
    detector = ConstrainedLanguageDetector()
    print("\nValid Indian languages:")
    for code, name in detector.get_valid_languages().items():
        print(f"  {code}: {name}")

    print(f"\nDetected languages are constrained to these {len(detector.get_valid_languages())} languages only.")
