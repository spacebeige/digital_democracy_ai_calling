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
    """Detect language of text. Returns language code (hi, en, etc)."""
    if not text.strip():
        return "unknown"
    
    # PRIORITY 1: Check for Devanagari script (pure Hindi indicator)
    devanagari_count = sum(1 for c in text if ord(c) >= 0x900 and ord(c) <= 0x97F)
    text_length = len(text)
    devanagari_ratio = devanagari_count / text_length if text_length > 0 else 0
    
    # If significant Devanagari content, it's Hindi (NOT Urdu/Arabic)
    if devanagari_ratio > 0.15:  # 15%+ Devanagari = Hindi
        logger.info(f"Language detection: Devanagari detected ({devanagari_ratio:.1%}) → Hindi")
        return "hi"
    
    # PRIORITY 2: Check for common romanized Hindi words (context clue)
    romanized_hindi_words = [
        "aag", "naar", "madad", "bachao", "help", "meri", "mere", "ghar", "ghare", 
        "nearby", "samne", "pani", "electricity", "bijli", "gayi", "nahi", "hai"
    ]
    text_lower = text.lower()
    
    # If text contains multiple Hindi romanized words, likely Hinglish/romanized Hindi
    hindi_word_count = sum(1 for word in romanized_hindi_words if word in text_lower)
    if text_length < 50 and hindi_word_count >= 1:  # Short text with Hindi words = likely Hinglish
        logger.info(f"Language detection: Romanized Hindi words detected ({hindi_word_count} words) → Hindi")
        return "hi"
    
    # PRIORITY 3: Use langdetect for ambiguous cases
    try:
        if LANGDETECT_AVAILABLE:
            detected = detect(text)
            
            # Sanity check: If langdetect says non-Indian language but context suggests Indian
            if detected in ["ur", "ar", "so", "fa"] and len(text) < 50:
                # For very short text in non-Indian scripts, default to Hindi (high probability in India context)
                logger.info(f"Language detection: langdetect said {detected} but short text + India context → defaulting to Hindi")
                return "hi"
            
            # Sanity check: If langdetect says Urdu/Arabic but we see Latin letters, it's likely Hinglish
            if detected in ["ur", "ar"] and re.search(r'[a-zA-Z]', text):
                logger.info(f"Language detection: {detected} detected but Latin letters found → English/Hinglish")
                return "en"  # Treat as English for keyword matching
            
            logger.info(f"Language detection (langdetect): {detected}")
            return detected
        else:
            # Fallback: Simple pattern matching
            if re.search(r'[a-zA-Z]', text):
                return "en"
            else:
                return "hi"  # Default to Hindi
    except Exception as e:
        logger.warning(f"Language detection failed: {e}, defaulting to 'hi'")
        return "hi"


def format_language(lang_code: str) -> str:
    """Convert language code to readable name."""
    lang_names = {
        "hi": "Hindi (हिंदी)",
        "en": "English", 
        "id": "Hindi/Hinglish (detected as ID)",  # langdetect quirk for Hinglish
        "no": "Hindi/Hinglish (detected as Norwegian)",  # langdetect quirk
        "mix": "Hinglish (Mixed)",
        "unknown": "Unknown"
    }
    # Default: capitalize language code or return as-is
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
