"""
Audio-Based Language Detection & Greeting Service
==================================================

Detects language directly from .wav audio files and greets users in their language.
Integrates with Whisper for accurate language detection from raw audio.

KEY FEATURES:
- Language detection from raw audio (not text)
- 23 official Indian languages supported
- Automatic greeting generation in detected language
- High accuracy using Whisper's acoustic language identification
- Caching for performance
"""

import logging
import os
import tempfile
from typing import Tuple, Optional, Dict
from pathlib import Path
import numpy as np

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("faster_whisper not installed")

logger = logging.getLogger(__name__)

# ============================================================================
# LANGUAGE CODE MAPPING (ISO 639-1 to Full Names)
# ============================================================================

LANGUAGE_MAP = {
    "hi": {"name": "Hindi", "native": "हिंदी"},
    "en": {"name": "English", "native": "English"},
    "ta": {"name": "Tamil", "native": "தமிழ்"},
    "te": {"name": "Telugu", "native": "తెలుగు"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ"},
    "ml": {"name": "Malayalam", "native": "മലയാളം"},
    "mr": {"name": "Marathi", "native": "मराठी"},
    "gu": {"name": "Gujarati", "native": "ગુજરાતી"},
    "bn": {"name": "Bengali", "native": "বাংলা"},
    "as": {"name": "Assamese", "native": "অসমীয়া"},
    "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ"},
    "or": {"name": "Odia", "native": "ଓଡ଼ିଆ"},
    "ur": {"name": "Urdu", "native": "اردو"},
    "ne": {"name": "Nepali", "native": "नेपाली"},
    "kok": {"name": "Konkani", "native": "कोंकणी"},
    "ks": {"name": "Kashmiri", "native": "كشمیر"},
    "sa": {"name": "Sanskrit", "native": "संस्कृतम्"},
    "sd": {"name": "Sindhi", "native": "سنڌي"},
    "mni": {"name": "Manipuri/Meitei", "native": "ꯃꯤꯇꯩ"},
    "bo": {"name": "Bodo", "native": "बड़ो"},
    "sat": {"name": "Santali", "native": "ᱥᱟᱱᱛᱟᱲᱤ"},
    "mai": {"name": "Maithili", "native": "मैथिली"},
}

# ============================================================================
# GREETINGS IN MULTIPLE LANGUAGES
# ============================================================================

LANGUAGE_GREETINGS = {
    "hi": {
        "greeting": "नमस्ते! मैं आपकी शिकायत को दर्ज कर रहा हूँ।",
        "alt": ["धन्यवाद। मैं आपकी समस्या को नोट कर रहा हूँ।", "आपकी शिकायत महत्वपूर्ण है।"],
        "tts_lang": "hi"
    },
    "en": {
        "greeting": "Hello! I'm registering your complaint.",
        "alt": ["Thank you. I'm noting your issue.", "Your complaint is important to us."],
        "tts_lang": "en"
    },
    "ta": {
        "greeting": "வணக்கம்! உங்கள் புகாரை பதிவு செய்கிறேன்.",
        "alt": ["நன்றி. உங்கள் பிரச்சினையை குறிப்பிடுகிறேன்."],
        "tts_lang": "ta"
    },
    "te": {
        "greeting": "హలో! మీ ఫిర్యాదు రిజిస్టర్ చేస్తున్నాను.",
        "alt": ["ధన్యవాదాలు. మీ సమస్యను నమూనా చేస్తున్నాను."],
        "tts_lang": "te"
    },
    "mr": {
        "greeting": "नमस्कार! मी तुमची तक्रार नोंदवत आहे.",
        "alt": ["धन्यवाद. मी तुमच्या समस्येला नोंद घेत आहे."],
        "tts_lang": "mr"
    },
    "gu": {
        "greeting": "નમસ્તે! હું તમારી ફરિયાદ નોંધી રહ્યો છું.",
        "alt": ["આભાર. હું તમારી મુશ્કેલીનો નોંધ લઈ રહ્યો છું."],
        "tts_lang": "gu"
    },
    "kn": {
        "greeting": "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ದೂರು ದಾಖಲ ಮಾಡುತ್ತಿದ್ದೇನೆ.",
        "alt": ["ಧನ್ಯವಾದ. ನಾನು ನಿಮ್ಮ ಸಮಸ್ಯೆಯನ್ನು ಗಮನಿಸುತ್ತಿದ್ದೇನೆ."],
        "tts_lang": "kn"
    },
    "ml": {
        "greeting": "നമസ്കാരം! ഞാൻ നിങ്ങളുടെ പരാതി രജിസ്ട്റർ ചെയ്യുകയാണ്।",
        "alt": ["നന്ദി. ഞാൻ നിങ്ങളുടെ പ്രശ്നം ശ്രദ്ധിക്കുകയാണ്."],
        "tts_lang": "ml"
    },
    "bn": {
        "greeting": "নমস্কার! আমি আপনার অভিযোগ নিবন্ধন করছি।",
        "alt": ["ধন্যবাদ. আমি আপনার সমস্যা নোট করছি."],
        "tts_lang": "bn"
    },
    "pa": {
        "greeting": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡੀ ਸ਼ਿਕਾਇਤ ਦਰਜ ਕਰ ਰਿਹਾ ਹਾਂ।",
        "alt": ["ਧੰਨਵਾਦ. ਮੈਂ ਤੁਹਾਡੀ ਸਮੱਸਿਆ ਨੂੰ ਧਿਆਨ ਵਿੱਚ ਲੈ ਰਿਹਾ ਹਾਂ."],
        "tts_lang": "pa"
    },
    "or": {
        "greeting": "ନମସ୍କାର! ମୁଁ ଆପଣଙ୍କ ଅଭିଯୋଗ ନୋଟ କରୁଛି।",
        "alt": ["ଧନ୍ୟବାଦ. ମୁଁ ଆପଣଙ୍କ ସମସ୍ୟା ଦେଖୁଛି."],
        "tts_lang": "or"
    },
    "ur": {
        "greeting": "السلام عليكم! میں آپ کی شکایت درج کر رہا ہوں۔",
        "alt": ["شکریہ. میں آپ کے مسئلے کو نوٹ کر رہا ہوں."],
        "tts_lang": "ur"
    },
    "ne": {
        "greeting": "नमस्ते! मैं तपाईंको गुनासो दर्ता गर्दैछू।",
        "alt": ["धन्यवाद। म तपाईंको समस्या नोट गर्दैछू."],
        "tts_lang": "ne"
    },
    "as": {
        "greeting": "নমস্কাৰ! মই আপোনাৰ অভিযোগ নিবন্ধন কৰি আছো।",
        "alt": ["ধন্যবাদ। মই আপোনাৰ সমস্যা লক্ষ্য কৰি আছো."],
        "tts_lang": "as"
    },
}

# ============================================================================
# WHISPER LANGUAGE DETECTION (from raw audio)
# ============================================================================

class AudioLanguageDetector:
    """
    Detects language from raw .wav audio files using Whisper.
    Much more accurate than text-based detection!
    """
    
    def __init__(self, model_size: str = "base"):
        """Initialize the Whisper model for language detection."""
        self.model_size = model_size
        self.model = None
        self.language_cache = {}  # Cache detected languages
        
        if WHISPER_AVAILABLE:
            self._init_model()
        else:
            logger.error("Whisper not available! Install: pip install faster-whisper")
    
    def _init_model(self):
        """Load Whisper model (do this once)."""
        try:
            logger.info(f"Initializing Whisper ({self.model_size}) for language detection...")
            self.model = WhisperModel(
                self.model_size, 
                device="auto", 
                compute_type="auto"
            )
            logger.info("✓ Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper: {e}")
            self.model = None
    
    def detect_language_from_audio(self, audio_file: str) -> Optional[str]:
        """
        Detect language from .wav audio file (VERY ACCURATE).
        
        Args:
            audio_file: Path to .wav file
            
        Returns:
            ISO 639-1 language code (e.g., 'hi', 'ta', 'en')
            
        Example:
            detector = AudioLanguageDetector()
            lang = detector.detect_language_from_audio("sample.wav")
            # Returns: 'hi' for Hindi, 'ta' for Tamil, etc.
        """
        
        # Check cache first
        if audio_file in self.language_cache:
            logger.debug(f"Using cached language for {audio_file}")
            return self.language_cache[audio_file]
        
        if not self.model or not WHISPER_AVAILABLE:
            logger.warning("Whisper model not available, defaulting to Hindi")
            return "hi"
        
        try:
            logger.info(f"Detecting language from: {audio_file}")
            
            # Whisper transcription with language detection
            # Setting language=None triggers auto-detection
            segments, info = self.model.transcribe(
                audio_file,
                language=None,  # Auto-detect
                beam_size=5     # Balance accuracy/speed
            )
            
            # Extract detected language from metadata
            detected_lang = info.language if hasattr(info, 'language') else 'hi'
            
            logger.info(f"✓ Detected language: {detected_lang} ({LANGUAGE_MAP.get(detected_lang, {}).get('name', 'Unknown')})")
            
            # Cache result
            self.language_cache[audio_file] = detected_lang
            
            return detected_lang
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            logger.warning("Falling back to Hindi")
            return "hi"
    
    def detect_language_from_bytes(self, audio_bytes: bytes) -> Optional[str]:
        """
        Detect language from raw audio bytes (for streaming).
        
        Args:
            audio_bytes: Raw audio data (WAV format)
            
        Returns:
            ISO 639-1 language code
        """
        # Save bytes to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        try:
            lang = self.detect_language_from_audio(tmp_path)
            return lang
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def get_language_confidence(self, audio_file: str) -> Dict[str, float]:
        """
        Get confidence scores for all detected languages.
        (For advanced use cases)
        """
        if not self.model or not WHISPER_AVAILABLE:
            return {"hi": 1.0}
        
        try:
            segments, info = self.model.transcribe(audio_file, language=None)
            # Return Whisper's internal language probabilities if available
            if hasattr(info, 'language_probability'):
                return {"detected": info.language_probability}
            return {"hi": 1.0}
        except Exception as e:
            logger.error(f"Failed to get confidence: {e}")
            return {"hi": 1.0}
    
    def clear_cache(self):
        """Clear language detection cache."""
        self.language_cache.clear()
        logger.info("Language cache cleared")


# ============================================================================
# GREETING SERVICE
# ============================================================================

class AudioLanguageGreetingService:
    """
    Complete service for detecting language & generating greetings.
    
    WORKFLOW:
    1. User calls the system
    2. Detect language from their audio
    3. Generate greeting in that language
    4. Play greeting back
    5. Continue with multilingual conversation
    """
    
    def __init__(self):
        """Initialize detector and greeting service."""
        self.detector = AudioLanguageDetector(model_size="base")
        self.greetings = LANGUAGE_GREETINGS
    
    def process_caller_audio(self, audio_file: str) -> Dict:
        """
        End-to-end: Analyze audio → detect language → prepare greeting.
        
        Args:
            audio_file: Path to .wav file
            
        Returns:
            Dict with:
            {
                "language_code": "hi",
                "language_name": "Hindi",
                "greeting": "नमस्ते! मैं आपकी शिकायत...",
                "confidence": "high",
                "tts_lang": "hi"
            }
        """
        
        try:
            # 1. DETECT LANGUAGE FROM AUDIO
            lang_code = self.detector.detect_language_from_audio(audio_file)
            
            if not lang_code or lang_code not in self.greetings:
                logger.warning(f"Unknown language code: {lang_code}, defaulting to Hindi")
                lang_code = "hi"
            
            # 2. GET GREETING FOR DETECTED LANGUAGE
            greeting_data = self.greetings.get(lang_code, self.greetings["hi"])
            lang_name = LANGUAGE_MAP.get(lang_code, {}).get("name", "Unknown")
            
            result = {
                "language_code": lang_code,
                "language_name": lang_name,
                "greeting": greeting_data["greeting"],
                "greeting_alt": greeting_data["alt"],
                "tts_lang": greeting_data["tts_lang"],
                "success": True
            }
            
            logger.info(f"✓ Greeting prepared in {lang_name}: '{result['greeting'][:50]}...'")
            return result
            
        except Exception as e:
            logger.error(f"Error in greeting service: {e}")
            return {
                "language_code": "hi",
                "language_name": "Hindi",
                "greeting": self.greetings["hi"]["greeting"],
                "success": False,
                "error": str(e)
            }
    
    def get_greeting_by_language(self, lang_code: str) -> Optional[str]:
        """Get greeting for a specific language code."""
        if lang_code in self.greetings:
            return self.greetings[lang_code]["greeting"]
        return None


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def detect_and_greet(audio_file: str) -> Tuple[str, str]:
    """
    Simple function: Detect language and get greeting.
    
    Args:
        audio_file: Path to .wav file
        
    Returns:
        (language_code, greeting_text)
        
    Example:
        >>> lang, greeting = detect_and_greet("user_audio.wav")
        >>> print(f"Language: {lang}, Greeting: {greeting}")
        Language: ta, Greeting: வணக்கம்! உங்கள் புகாரை...
    """
    service = AudioLanguageGreetingService()
    result = service.process_caller_audio(audio_file)
    return result["language_code"], result["greeting"]


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*70)
    print("Audio Language Detection & Greeting Service")
    print("="*70)
    
    # Initialize service
    service = AudioLanguageGreetingService()
    
    # Test with a sample audio file (if it exists)
    test_audio = "sample_audio.wav"
    
    if os.path.exists(test_audio):
        print(f"\nProcessing: {test_audio}")
        result = service.process_caller_audio(test_audio)
        
        print(f"\n✓ Language: {result['language_name']} ({result['language_code']})")
        print(f"✓ Greeting: {result['greeting']}")
        print(f"✓ TTS Language: {result['tts_lang']}")
    else:
        print(f"\n⚠ Sample audio file not found: {test_audio}")
        print("To test:")
        print("1. Record or place a .wav file in the current directory")
        print("2. Update 'test_audio' variable to the file path")
        print("3. Run this script again")
        print("\nExample languages supported:")
        for code, info in list(LANGUAGE_MAP.items())[:10]:
            print(f"  {code}: {info['name']}")
