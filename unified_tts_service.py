#!/usr/bin/env python3
"""
UNIFIED TEXT-TO-SPEECH SERVICE
==============================
Supports gTTS (Google Text-to-Speech) with language-aware responses.

Features:
- Multi-language greeting generation
- Language-specific responses
- Audio playback
- Easy Layer 1 integration (calling service)

Architecture Note:
This service is designed to be Layer 2 (Voice Processing).
Layer 1 (Calling Service) will pipe audio through this module.
"""

import os
import logging
import tempfile
from typing import Optional, Dict, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================================================
# GTTS INTEGRATION
# ============================================================================

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logger.warning("gTTS not installed. Install with: pip install gtts")

try:
    import pyaudio
    import wave
    AUDIO_PLAYBACK_AVAILABLE = True
except ImportError:
    AUDIO_PLAYBACK_AVAILABLE = False
    logger.warning("pyaudio not installed. Install with: pip install pyaudio")


# ============================================================================
# GREETING MESSAGES - MULTI-LANGUAGE
# ============================================================================

GREETINGS = {
    "hi": {
        "language_name": "हिंदी (Hindi)",
        "greeting": "नमस्ते! मैं आपकी शिकायत को दर्ज कर रहा हूँ।",
        "language_code": "hi",
        "greetings_alt": [
            "धन्यवाद। मैं आपकी समस्या को नोट कर रहा हूँ।",
            "आपकी शिकायत महत्वपूर्ण है। मैं इसे सम्भाल रहा हूँ।",
        ]
    },
    "en": {
        "language_name": "English",
        "greeting": "Hello! I'm registering your complaint.",
        "language_code": "en",
        "greetings_alt": [
            "Thank you. I'm noting your issue.",
            "Your complaint is important. I'm handling it.",
        ]
    },
    "id": {
        # Hinglish (romanized Hindi) - treat as Hindi
        "language_name": "हिंदी (Hindi)",
        "greeting": "नमस्ते! मैं आपकी शिकायत को दर्ज कर रहा हूँ।",
        "language_code": "hi",
        "greetings_alt": []
    },
    "ta": {
        "language_name": "Tamil",
        "greeting": "வணக்கம்! உங்கள் புகாரை பதிவு செய்கிறேன்.",
        "language_code": "ta",
        "greetings_alt": []
    },
    "te": {
        "language_name": "Telugu",
        "greeting": "హలో! మీ ఫిర్యాదు రిజిస్టర్ చేస్తున్నాను.",
        "language_code": "te",
        "greetings_alt": []
    },
    "mr": {
        "language_name": "Marathi",
        "greeting": "नमस्कार! मी तुमची तक्रार नोंदवत आहे.",
        "language_code": "mr",
        "greetings_alt": []
    },
    "gu": {
        "language_name": "Gujarati",
        "greeting": "નમસ્તે! હું તમારી ફરિયાદ નોંધી રહ્યો છું.",
        "language_code": "gu",
        "greetings_alt": []
    },
}

# Fallback greeting if language not supported
DEFAULT_GREETING_LANG = "hi"


def get_greeting(language_code: str) -> Dict:
    """Get greeting for detected language."""
    if language_code in GREETINGS:
        return GREETINGS[language_code]
    else:
        logger.warning(f"Language {language_code} not in greeting database, using default (Hindi)")
        return GREETINGS[DEFAULT_GREETING_LANG]


def generate_speech_response(text: str, language_code: str) -> Optional[str]:
    """
    Generate speech audio file from text using gTTS.
    
    Args:
        text: Text to convert to speech
        language_code: Language code (hi, en, ta, te, etc.)
    
    Returns:
        Path to temporary audio file, or None if failed
    """
    
    if not GTTS_AVAILABLE:
        logger.error("gTTS not available")
        return None
    
    try:
        # Map language codes if necessary (handle edge cases)
        gtts_lang_code = language_code
        if language_code in ["id", "ur", "cy", "so", "no", "sv"]:  # Edge case detections → Hindi
            gtts_lang_code = "hi"
            logger.warning(f"Language edge case detected ({language_code}), mapping to Hindi")
        
        logger.info(f"Generating speech: '{text}' in language {gtts_lang_code}")
        
        # Create gTTS object
        tts = gTTS(text=text, lang=gtts_lang_code, slow=False)
        
        # Save to temporary file
        temp_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_path = temp_audio.name
        temp_audio.close()
        
        tts.save(temp_path)
        
        logger.info(f"✓ Speech generated: {temp_path}")
        return temp_path
        
    except Exception as e:
        logger.error(f"Failed to generate speech: {e}")
        return None


def play_audio_file(audio_path: str, method: str = "display") -> bool:
    """
    Play audio file using system player or built-in method.
    
    Args:
        audio_path: Path to audio file
        method: 'system' (OS player), 'pyaudio' (direct), or 'display' (return path)
    
    Returns:
        True if successful, False otherwise
        
    Note:
        For Layer 1 (calling service) integration:
        - Layer 1 will provide its own audio handling
        - This method defaults to 'display' for now
        - Layer 1 can override this by using 'system' or 'stream'
    """
    
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return False
    
    try:
        if method == "system":
            # Use OS default audio player
            os.system(f"play {audio_path}")  # SoX
            return True
            
        elif method == "pyaudio":
            if not AUDIO_PLAYBACK_AVAILABLE:
                logger.warning("pyaudio not available, falling back to display mode")
                return False
            
            # Direct audio playback with pyaudio
            with wave.open(audio_path, 'rb') as wav_file:
                params = wav_file.getparams()
                frames = wav_file.readframes(params.nframes)
                
                p = pyaudio.PyAudio()
                stream = p.open(format=p.get_format_from_width(params.sampwidth),
                              channels=params.nchannels,
                              rate=params.framerate,
                              output=True)
                stream.write(frames)
                stream.stop_stream()
                stream.close()
                p.terminate()
            
            return True
            
        elif method == "display":
            # Just return the path (useful for testing/Layer 1)
            logger.info(f"Audio ready for playback: {audio_path}")
            return True
        
        else:
            logger.error(f"Unknown playback method: {method}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to play audio: {e}")
        return False


def respond_to_user(language_code: str, playback_method: str = "display") -> Optional[str]:
    """
    Generate and play greeting response to user.
    
    Args:
        language_code: Language code detected from user input
        playback_method: How to play audio ('display', 'system', 'pyaudio')
    
    Returns:
        Path to audio file if successful, None otherwise
        
    Layer 1 Integration:
        Layer 1 calling service can call this function and:
        - Pass lang_code from speech-to-text
        - Use playback_method='stream' to get audio stream
        - Or playback_method='layer1' for custom handling
    """
    
    logger.info(f"Generating response for language: {language_code}")
    
    # Get greeting for language
    greeting_info = get_greeting(language_code)
    greeting_text = greeting_info["greeting"]
    greeting_lang = greeting_info["language_code"]
    
    print(f"\n🎙️  Greeting User:")
    print(f"  Language: {greeting_info['language_name']}")
    print(f"  Message: {greeting_text}")
    
    # Generate speech
    audio_path = generate_speech_response(greeting_text, greeting_lang)
    
    if not audio_path:
        logger.error("Failed to generate speech response")
        return None
    
    # Play audio (or prepare for Layer 1)
    if playback_method not in ["display", "system", "pyaudio"]:
        # Unknown method - just return path for caller to handle
        logger.info(f"Returning audio path for custom playback: {audio_path}")
        return audio_path
    
    success = play_audio_file(audio_path, method=playback_method)
    
    if success:
        logger.info("✓ Response played successfully")
        return audio_path
    else:
        logger.warning("Could not play audio, but file is ready")
        return audio_path


def cleanup_audio(audio_path: str) -> bool:
    """Clean up temporary audio files."""
    try:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
            logger.info(f"Cleaned up: {audio_path}")
            return True
    except Exception as e:
        logger.warning(f"Failed to cleanup {audio_path}: {e}")
    return False


def get_status() -> Dict:
    """Get TTS service status."""
    return {
        "gtts": {
            "available": GTTS_AVAILABLE,
            "status": "✓ Ready" if GTTS_AVAILABLE else "✗ Not installed"
        },
        "audio_playback": {
            "available": AUDIO_PLAYBACK_AVAILABLE,
            "status": "✓ Ready" if AUDIO_PLAYBACK_AVAILABLE else "✗ Not available (optional)"
        },
        "languages_supported": list(GREETINGS.keys()),
        "suggested_playback": "display" if not AUDIO_PLAYBACK_AVAILABLE else "pyaudio"
    }


if __name__ == "__main__":
    print("TTS Service Status:")
    status = get_status()
    for service, info in status.items():
        if isinstance(info, dict) and "status" in info:
            print(f"  {service}: {info['status']}")
    
    # Test greeting generation
    print("\nTest Greetings:")
    for lang_code in ["hi", "en", "ta"]:
        greeting = get_greeting(lang_code)
        print(f"  {greeting['language_name']}: {greeting['greeting']}")
