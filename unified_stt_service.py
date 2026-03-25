#!/usr/bin/env python3
"""
UNIFIED STT SERVICE
===================
Supports multiple transcription engines with intelligent fallback:
1. Whisper (faster-whisper) - Offline, multi-language
2. Google Cloud Speech-to-Text - Cloud-based, accurate
3. Mock - Fallback for testing

Priority: Whisper > Google Cloud > Mock
"""

import os
import json
import logging
import re
from typing import Optional, Dict, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================================================
# LANGUAGE DETECTION
# ============================================================================

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not installed. Install with: pip install langdetect")


def detect_language(text: str) -> str:
    """
    Detect language of text. Returns language code for 22 official Indian languages + English.
    
    22 Official Languages of India:
    1. Hindi (hi), 2. English (en), 3. Assamese (as), 4. Bengali (bn), 5. Gujarati (gu)
    6. Kannada (kn), 7. Kashmiri (ks), 8. Konkani (kok), 9. Malayalam (ml)
    10. Manipuri/Meitei (mni), 11. Marathi (mr), 12. Nepali (ne), 13. Odia (or)
    14. Punjabi (pa), 15. Sanskrit (sa), 16. Sindhi (sd), 17. Tamil (ta), 18. Telugu (te)
    19. Urdu (ur), 20. Bodo (bo), 21. Santali (sat), 22. Maithili (mai)
    """
    if not text.strip():
        return "hi"  # Default to Hindi
    
    # OFFICIAL INDIAN LANGUAGES - Script ranges
    text_length = len(text)
    
    # Check for regional script characters (ONLY Indian scripts)
    # Tamil script (0x0B80–0x0BFF)
    tamil_count = sum(1 for c in text if ord(c) >= 0x0B80 and ord(c) <= 0x0BFF)
    # Telugu script (0x0C00–0x0C7F)
    telugu_count = sum(1 for c in text if ord(c) >= 0x0C00 and ord(c) <= 0x0C7F)
    # Kannada script (0x0C80–0x0CFF)
    kannada_count = sum(1 for c in text if ord(c) >= 0x0C80 and ord(c) <= 0x0CFF)
    # Malayalam script (0x0D00–0x0D7F)
    malayalam_count = sum(1 for c in text if ord(c) >= 0x0D00 and ord(c) <= 0x0D7F)
    # Odia script (0x0B00–0x0B7F)
    odia_count = sum(1 for c in text if ord(c) >= 0x0B00 and ord(c) <= 0x0B7F)
    # Gujarati script (0x0A80–0x0AFF)
    gujarati_count = sum(1 for c in text if ord(c) >= 0x0A80 and ord(c) <= 0x0AFF)
    # Bengali script (0x0980–0x09FF)
    bengali_count = sum(1 for c in text if ord(c) >= 0x0980 and ord(c) <= 0x09FF)
    # Assamese script (0x0980–0x09FF, similar to Bengali)
    assamese_count = sum(1 for c in text if ord(c) >= 0x0980 and ord(c) <= 0x09FF)
    # Gurmukhi script (0x0A00–0x0A7F) - Punjabi
    punjabi_count = sum(1 for c in text if ord(c) >= 0x0A00 and ord(c) <= 0x0A7F)
    
    # Devanagari script (0x0900–0x097F) - Hindi, Marathi, Sanskrit, Nepali, etc.
    devanagari_count = sum(1 for c in text if ord(c) >= 0x0900 and ord(c) <= 0x097F)
    # Arabic script (0x0600–0x06FF) - Urdu uses Arabic script
    arabic_count = sum(1 for c in text if ord(c) >= 0x0600 and ord(c) <= 0x06FF)
    
    # Calculate ratios
    tamil_ratio = tamil_count / text_length if text_length > 0 else 0
    telugu_ratio = telugu_count / text_length if text_length > 0 else 0
    kannada_ratio = kannada_count / text_length if text_length > 0 else 0
    malayalam_ratio = malayalam_count / text_length if text_length > 0 else 0
    odia_ratio = odia_count / text_length if text_length > 0 else 0
    gujarati_ratio = gujarati_count / text_length if text_length > 0 else 0
    bengali_ratio = bengali_count / text_length if text_length > 0 else 0
    punjabi_ratio = punjabi_count / text_length if text_length > 0 else 0
    devanagari_ratio = devanagari_count / text_length if text_length > 0 else 0
    arabic_ratio = arabic_count / text_length if text_length > 0 else 0
    
    # Detection threshold
    SCRIPT_THRESHOLD = 0.15
    
    # Check for Tamil
    if tamil_ratio > SCRIPT_THRESHOLD:
        logger.info(f"Language detection: Tamil script detected ({tamil_ratio:.1%})")
        return "ta"
    
    # Check for Telugu
    if telugu_ratio > SCRIPT_THRESHOLD:
        logger.info(f"Language detection: Telugu script detected ({telugu_ratio:.1%})")
        return "te"
    
    # Check for Kannada
    if kannada_ratio > SCRIPT_THRESHOLD:
        logger.info(f"Language detection: Kannada script detected ({kannada_ratio:.1%})")
        return "kn"
    
    # Check for Malayalam
    if malayalam_ratio > SCRIPT_THRESHOLD:
        logger.info(f"Language detection: Malayalam script detected ({malayalam_ratio:.1%})")
        return "ml"
    
    # Check for Odia
    if odia_ratio > SCRIPT_THRESHOLD and not bengali_count > 0:
        logger.info(f"Language detection: Odia script detected ({odia_ratio:.1%})")
        return "or"
    
    # Check for Gujarati
    if gujarati_ratio > SCRIPT_THRESHOLD:
        logger.info(f"Language detection: Gujarati script detected ({gujarati_ratio:.1%})")
        return "gu"
    
    # Check for Bengali/Assamese
    if bengali_ratio > SCRIPT_THRESHOLD:
        # Bengali (bn) is more common than Assamese
        logger.info(f"Language detection: Bengali/Assamese script detected ({bengali_ratio:.1%})")
        return "bn"
    
    # Check for Punjabi
    if punjabi_ratio > SCRIPT_THRESHOLD:
        logger.info(f"Language detection: Punjabi (Gurmukhi) script detected ({punjabi_ratio:.1%})")
        return "pa"
    
    # Check for Urdu (uses Arabic script)
    if arabic_ratio > SCRIPT_THRESHOLD:
        logger.info(f"Language detection: Urdu (Arabic script) detected ({arabic_ratio:.1%})")
        return "ur"
    
    # PRIORITY 2: Check for Devanagari script and distinguish Hindi vs Marathi vs Sanskrit
    if devanagari_ratio > SCRIPT_THRESHOLD:  # 15%+ Devanagari
        # Marathi-specific words for detection
        marathi_words = ["तुम्ही", "आहे", "आहेत", "करून", "आणि", "मी", "तू", "हे", "ते", "ही", "त्या", "एक"]
        # Sanskrit-specific words
        sanskrit_words = ["नमस्ते", "वेदा", "अस्ति", "भवतु", "शास्त्रम्"]
        
        text_lower = text.lower()
        
        # Check for Marathi-specific words
        marathi_matches = sum(1 for word in marathi_words if word in text_lower)
        if marathi_matches > 0:
            logger.info(f"Language detection: Marathi words detected ({marathi_matches}) + Devanagari → Marathi")
            return "mr"  # It's Marathi!
        
        # Check for Sanskrit words
        sanskrit_matches = sum(1 for word in sanskrit_words if word in text_lower)
        if sanskrit_matches > 0:
            logger.info(f"Language detection: Sanskrit words detected ({sanskrit_matches}) + Devanagari → Sanskrit")
            return "sa"  # It's Sanskrit!
        
        # Default Devanagari to Hindi
        logger.info(f"Language detection: Devanagari detected ({devanagari_ratio:.1%}) → Hindi")
        return "hi"
    
    # PRIORITY 3: Check for common romanized Hindi/Marathi words (Hinglish)
    romanized_hindi_words = [
        "aag", "naar", "madad", "bachao", "help", "meri", "mere", "ghar", "ghare", 
        "nearby", "samne", "pani", "electricity", "bijli", "gayi", "nahi", "hai",
        "tum", "tumhi", "pan", "ahe", "karun"  # Marathi-like words
    ]
    text_lower = text.lower()
    
    # If text contains multiple Hindi romanized words, likely Hinglish/romanized Hindi
    hindi_word_count = sum(1 for word in romanized_hindi_words if word in text_lower)
    if text_length < 50 and hindi_word_count >= 1:
        logger.info(f"Language detection: Romanized Hindi words detected ({hindi_word_count} words) → Hindi")
        return "hi"
    
    # PRIORITY 4: Use langdetect for ambiguous cases (with Indian-only filtering)
    # Official Indian languages supported by langdetect
    OFFICIAL_INDIAN_LANGS = {"hi", "en", "mr", "ta", "te", "kn", "ml", "gu", "bn", "pa", "or", "ur", "ne", "kok", "ks", "sa", "sd", "as", "mni", "bo", "sat", "mai"}
    
    try:
        if LANGDETECT_AVAILABLE:
            detected = detect(text)
            
            # Filter: Only accept official Indian languages
            if detected in OFFICIAL_INDIAN_LANGS:
                logger.info(f"Language detection (langdetect): {detected}")
                return detected
            else:
                # Non-Indian language detected (like sk/Slovak, ko/Korean, cy/Welsh, etc.)
                logger.warning(f"Language detection: Non-Indian language detected '{detected}' - defaulting to Hindi")
                # Check if there's any Latin alphabet, default to English if so
                if re.search(r'^[a-zA-Z\\s0-9.,:!?]*$', text):
                    logger.info(f"Language detection: Latin-only text detected - defaulting to English")
                    return "en"
                else:
                    # Default to Hindi for Indian context
                    return "hi"
        else:
            # Fallback: Simple pattern matching (no langdetect)
            if re.search(r'[a-zA-Z]', text):
                return "en"
            else:
                return "hi"
    
    except Exception as e:
        logger.warning(f"Language detection failed: {e}, defaulting to 'hi'")
        return "hi"


def format_language(lang_code: str) -> str:
    """Convert language code to readable name (Official Indian Languages)."""
    lang_names = {
        # 22 Official Languages of India
        "hi": "Hindi (हिंदी)",
        "en": "English",
        "mr": "Marathi (मराठी)",
        "ta": "Tamil (தமிழ்)",
        "te": "Telugu (తెలుగు)",
        "gu": "Gujarati (ગુજરાતી)",
        "kn": "Kannada (ಕನ್ನಡ)",
        "ml": "Malayalam (മലയാളം)",
        "bn": "Bengali (বাংলা)",
        "as": "Assamese (অসমীয়া)",
        "pa": "Punjabi (ਪੰਜਾਬੀ)",
        "or": "Odia (ଓଡ଼ିଆ)",
        "ur": "Urdu (اردو)",
        "ne": "Nepali (नेपाली)",
        "kok": "Konkani (कोंकणी)",
        "ks": "Kashmiri (كشمیر)",
        "sa": "Sanskrit (संस्कृतम्)",
        "sd": "Sindhi (سنڌي)",
        "mni": "Manipuri/Meitei (ꯃꯤꯇꯩ)",
        "bo": "Bodo (बड़ो)",
        "sat": "Santali (ᱥᱟᱱᱛᱟᱲᱤ)",
        "mai": "Maithili (मैथिली)",
    }
    if lang_code in lang_names:
        return lang_names[lang_code]
    else:
        return f"{lang_code.upper()} Language"

# ============================================================================
# WHISPER (FASTER-WHISPER) - LOCAL OFFLINE
# ============================================================================

WHISPER_AVAILABLE = False
WHISPER_MODEL = None

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    logger.warning("faster_whisper not installed. Install with: pip install faster-whisper")


def init_whisper_model(model_size: str = "base") -> Optional[WhisperModel]:
    """Initialize Whisper model once (CPU or GPU)."""
    global WHISPER_MODEL
    if WHISPER_MODEL is not None:
        return WHISPER_MODEL
    
    if not WHISPER_AVAILABLE:
        logger.warning("Whisper not available")
        return None
    
    try:
        logger.info(f"Loading Whisper model: {model_size}...")
        WHISPER_MODEL = WhisperModel(model_size, device="auto", compute_type="auto")
        logger.info("✓ Whisper model loaded successfully")
        return WHISPER_MODEL
    except Exception as e:
        logger.error(f"Failed to load Whisper model: {e}")
        return None


def transcribe_with_whisper(audio_file: str) -> Optional[str]:
    """Transcribe using Whisper (faster-whisper)."""
    if not WHISPER_AVAILABLE:
        return None
    
    try:
        model = init_whisper_model("base")
        if model is None:
            return None
        
        logger.info(f"Transcribing with Whisper: {audio_file}")
        
        # First try: auto-detect language
        segments, info = model.transcribe(audio_file, language=None)
        
        # Combine all segments
        transcript = "".join(segment.text for segment in segments).strip()
        
        if transcript:
            logger.info(f"✓ Whisper transcription: {transcript[:100]}...")
            return transcript
        else:
            # Second try: force Hindi if first attempt was empty
            logger.warning("Whisper auto-detect returned empty, trying Hindi...")
            segments, info = model.transcribe(audio_file, language="hi")
            transcript = "".join(segment.text for segment in segments).strip()
            
            if transcript:
                logger.info(f"✓ Whisper (Hindi) transcription: {transcript[:100]}...")
                return transcript
            else:
                logger.warning("Whisper Hindi mode also returned empty")
                return None
            
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return None


# ============================================================================
# GOOGLE CLOUD SPEECH-TO-TEXT
# ============================================================================

GOOGLE_STT_AVAILABLE = False
GOOGLE_CREDENTIALS = None

try:
    from google.cloud import speech_v1
    GOOGLE_STT_AVAILABLE = True
except ImportError:
    logger.warning("google-cloud-speech not installed. Install with: pip install google-cloud-speech")


def init_google_credentials() -> bool:
    """Initialize Google Cloud credentials from environment."""
    global GOOGLE_CREDENTIALS
    
    if not GOOGLE_STT_AVAILABLE:
        return False
    
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path or not os.path.exists(cred_path):
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set or file missing")
        return False
    
    try:
        GOOGLE_CREDENTIALS = cred_path
        logger.info(f"✓ Google Cloud credentials loaded: {cred_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to load Google credentials: {e}")
        return False


def transcribe_with_google(audio_file: str) -> Optional[str]:
    """Transcribe using Google Cloud Speech-to-Text."""
    if not GOOGLE_STT_AVAILABLE or not GOOGLE_CREDENTIALS:
        return None
    
    try:
        from google.cloud import speech_v1
        
        client = speech_v1.SpeechClient()
        
        with open(audio_file, "rb") as audio_file_obj:
            content = audio_file_obj.read()
        
        audio = speech_v1.RecognitionAudio(content=content)
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="hi-IN",  # Hindi
        )
        
        logger.info(f"Transcribing with Google: {audio_file}")
        response = client.recognize(config=config, audio=audio)
        
        transcript = " ".join(
            result.alternatives[0].transcript for result in response.results
        ).strip()
        
        if transcript:
            logger.info(f"✓ Google transcription: {transcript[:100]}...")
            return transcript
        else:
            logger.warning("Google returned empty transcription")
            return None
            
    except Exception as e:
        logger.error(f"Google transcription failed: {e}")
        return None


# ============================================================================
# MOCK TRANSCRIPTION (FALLBACK)
# ============================================================================

MOCK_TRANSCRIPTIONS = {
    "water": "Mere ghar ke saamne pani ki pipeline tut gayi hai, bahut pani beh raha hai",
    "fire": "Emergency! Mere building mein fire lag gayi hai, please help quickly!",
    "electricity": "Hamaare mohalle mein bijli nahi aa rahi hai, transformer kharab hai",
    "road": "Main road pe bahut bada pothole hai, do accidents ho chuke hain",
    "dummy": "This is test audio for system testing purposes",
}


def transcribe_with_mock(audio_file: str) -> str:
    """Fallback mock transcription based on filename."""
    filename = Path(audio_file).stem.lower()
    
    # Try to match filename
    for key, text in MOCK_TRANSCRIPTIONS.items():
        if key in filename:
            logger.info(f"✓ Mock transcription (matched '{key}'): {text[:100]}...")
            return text
    
    # Default
    default = "Mock transcription: Unable to determine complaint type"
    logger.info(f"✓ Mock transcription (default): {default}")
    return default


# ============================================================================
# UNIFIED TRANSCRIPTION INTERFACE
# ============================================================================

def transcribe(audio_file: str, engine: str = "auto") -> Tuple[str, str, str]:
    """
    Transcribe audio with intelligent engine selection and language detection.
    
    Args:
        audio_file: Path to WAV/MP3 file
        engine: "auto" (try all), "whisper", "google", or "mock"
    
    Returns:
        (transcript, engine_used, language): Tuple of transcribed text, engine used, and detected language
    """
    
    if not os.path.exists(audio_file):
        logger.error(f"Audio file not found: {audio_file}")
        return "Error: File not found", "none", "unknown"
    
    transcript = None
    engine_used = None
    
    # Try engines in priority order
    engines_to_try = []
    
    if engine == "auto":
        engines_to_try = ["whisper", "google", "mock"]
    else:
        engines_to_try = [engine]
    
    for current_engine in engines_to_try:
        logger.info(f"Trying STT engine: {current_engine}")
        
        if current_engine == "whisper":
            transcript = transcribe_with_whisper(audio_file)
            if transcript:
                engine_used = "Whisper"
                break
                
        elif current_engine == "google":
            if init_google_credentials():
                transcript = transcribe_with_google(audio_file)
                if transcript:
                    engine_used = "Google Cloud STT"
                    break
            else:
                logger.warning("Google Cloud STT not configured, skipping")
                
        elif current_engine == "mock":
            transcript = transcribe_with_mock(audio_file)
            engine_used = "Mock"
            break
    
    if not transcript:
        logger.warning("All STT engines failed, using mock fallback")
        transcript = transcribe_with_mock(audio_file)
        engine_used = "Mock (fallback)"
    
    # Detect language of the transcript
    detected_language = detect_language(transcript) if transcript else "unknown"
    logger.info(f"Detected language: {detected_language}")
    
    return transcript, engine_used, detected_language


def get_status() -> Dict:
    """Get current STT availability status."""
    return {
        "whisper": {
            "available": WHISPER_AVAILABLE,
            "status": "✓ Ready" if WHISPER_AVAILABLE else "✗ Not installed"
        },
        "google_cloud": {
            "available": GOOGLE_STT_AVAILABLE and bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")),
            "status": "✓ Ready" if (GOOGLE_STT_AVAILABLE and os.getenv("GOOGLE_APPLICATION_CREDENTIALS")) else "✗ Not configured"
        },
        "mock": {
            "available": True,
            "status": "✓ Fallback available"
        }
    }


if __name__ == "__main__":
    # Quick test
    print("STT Service Status:")
    status = get_status()
    for engine, info in status.items():
        print(f"  {engine}: {info['status']}")
