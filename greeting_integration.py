"""
Integration: Audio Language Detection → Greeting in Call Pipeline
==================================================================

Integrates the AudioLanguageGreetingService into the AWAAZ call handling.
Detects language from first audio segment and greets caller in their language.

WORKFLOW:
1. Caller speaks first words → audio received
2. Language detected from raw audio
3. Greeting generated in detected language
4. Greeting played back to caller
5. Continue call in detected language
"""

import logging
import tempfile
import os
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

try:
    from audio_language_greeting_service import AudioLanguageGreetingService
    GREETING_SERVICE_AVAILABLE = True
except ImportError:
    GREETING_SERVICE_AVAILABLE = False
    logger.warning("AudioLanguageGreetingService not available")


# ============================================================================
# EARLY LANGUAGE DETECTION FOR GREETING (before full transcription)
# ============================================================================

class GreetingHandler:
    """
    Manages greeting delivery based on detected language.
    Called on FIRST utterance to greet user in their language.
    """
    
    def __init__(self):
        """Initialize greeting handler."""
        if GREETING_SERVICE_AVAILABLE:
            self.greeting_service = AudioLanguageGreetingService()
        else:
            self.greeting_service = None
            logger.warning("Greeting service not available - using fallback")
    
    def should_greet(self, session) -> bool:
        """
        Determine if session needs greeting.
        
        Returns True only on FIRST turn.
        """
        return session.turn_number == 1 and session.state == "GREETING"
    
    def detect_and_greet(self, audio_file: str) -> Dict:
        """
        Detect language from audio and get greeting.
        
        Args:
            audio_file: Path to .wav file with caller's speech
            
        Returns:
            {
                "language_code": "ta",
                "language_name": "Tamil",
                "greeting": "வணக்கம்! உங்கள் புகாரை...",
                "tts_lang": "ta",
                "success": True
            }
        """
        if not GREETING_SERVICE_AVAILABLE:
            logger.warning("Greeting service unavailable, returning Hindi fallback")
            return {
                "language_code": "hi",
                "language_name": "Hindi",
                "greeting": "नमस्ते! मैं आपकी शिकायत को दर्ज कर रहा हूँ।",
                "tts_lang": "hi",
                "success": False,
                "error": "Service not available"
            }
        
        try:
            result = self.greeting_service.process_caller_audio(audio_file)
            logger.info(f"✓ Greeting detected and prepared: {result['language_name']}")
            return result
        except Exception as e:
            logger.error(f"Greeting detection failed: {e}")
            return {
                "language_code": "hi",
                "language_name": "Hindi",
                "greeting": "नमस्ते! मैं आपकी शिकायत को दर्ज कर रहा हूँ।",
                "tts_lang": "hi",
                "success": False,
                "error": str(e)
            }
    
    def update_session_language(self, session, greeting_result: Dict):
        """
        Update session with detected language from greeting detection.
        
        This ensures the rest of the call continues in the detected language.
        """
        if greeting_result["success"]:
            session.lang = greeting_result["language_code"]
            session.detected_language = greeting_result["language_code"]
            session.language_name = greeting_result["language_name"]
            
            logger.info(f"✓ Session {session.session_id} language set to: {session.language_name}")
        else:
            # Fallback to Hindi
            session.lang = "hi"
            session.detected_language = "hi"
            session.language_name = "Hindi"
            logger.warning(f"Session {session.session_id} defaulting to Hindi")


# ============================================================================
# MODIFIED UTTERANCE PROCESSOR
# ============================================================================

async def process_utterance_with_greeting(
    session,
    audio_bytes: bytes,
    vad,
    stt,
    model,
    tts,
    greeting_handler: Optional[GreetingHandler] = None,
    playback_mgr=None,
    ari=None
) -> Optional[str]:
    """
    Process utterance WITH early language detection and greeting.
    
    On first turn: Detects language → generates greeting
    On subsequent turns: Normal processing
    
    Args:
        session: AWAAZ session
        audio_bytes: Raw audio data
        vad: Voice Activity Detection handler
        stt: Speech-to-Text handler
        model: LLM model
        tts: Text-to-Speech handler
        greeting_handler: GreetingHandler instance
        playback_mgr: Audio playback manager
        ari: ARI client for Asterisk interaction
        
    Returns:
        Detected language code or None
    """
    
    if not greeting_handler:
        greeting_handler = GreetingHandler()
    
    try:
        # ── VAD + buffer ──────────────────────────────────────────────────
        utterance = vad.process_chunk(audio_bytes)
        if not utterance or len(utterance) == 0:
            return None
        
        # Save to temp audio file
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_wav.write(utterance.tobytes())
        temp_wav.close()
        
        try:
            # ── EARLY LANGUAGE DETECTION + GREETING (on first turn) ────────
            if greeting_handler.should_greet(session):
                logger.info(f"[{session.session_id}] First turn - detecting language for greeting...")
                
                greeting_result = greeting_handler.detect_and_greet(temp_wav.name)
                greeting_handler.update_session_language(session, greeting_result)
                
                # Play greeting if audio synthesis available
                if greeting_result["success"] and playback_mgr and tts:
                    try:
                        greeting_text = greeting_result["greeting"]
                        audio = tts.synthesize_to_bytes(
                            greeting_text,
                            session
                        )
                        
                        if audio:
                            logger.info(f"[{session.session_id}] Playing greeting in {greeting_result['language_name']}")
                            await playback_mgr.play_tts_file(session, audio, ari)
                            session.turn_number += 1
                    except Exception as e:
                        logger.error(f"Failed to play greeting: {e}")
                        # Continue without greeting
            
            # ── STANDARD STT PROCESSING ───────────────────────────────────
            stt_result = await stt.transcribe(
                temp_wav.name,
                "auto" if session.turn_number == 1 else session.lang
            )
            
            text = stt_result.text if stt_result else ""
            
            # Update language from STT if available
            if stt_result and stt_result.detected_language:
                detected_lang = stt_result.detected_language or session.lang
                session.lang = detected_lang
                session.confidence = stt_result.confidence
            
            if not text:
                logger.warning(f"No transcription for {session.session_id}")
                return session.lang
            
            logger.info(f"[{session.session_id}] Transcribed ({session.lang}): {text[:100]}")
            return session.lang
            
        finally:
            try:
                os.unlink(temp_wav.name)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Utterance processing error: {e}", exc_info=True)
        return session.lang


# ============================================================================
# INTEGRATION INSTRUCTIONS
# ============================================================================

"""
INTEGRATION GUIDE
=================

To integrate language detection greeting into awaaz/main.py:

1. Import at top of file:
   ─────────────────────────
   from voice_to_layer3_enhanced import GreetingHandler
   (or from your path to this file)

2. In AWAAZEngine.__init__, add:
   ──────────────────────────────
   self.greeting_handler = GreetingHandler()

3. Modify _process_utterance method:
   ──────────────────────────────────
   
   BEFORE:
   ```
   utterance = self.vad.process_chunk(audio_bytes)
   if not utterance or len(utterance) == 0:
       return
   
   temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
   temp_wav.write(utterance.tobytes())
   temp_wav.close()
   ```
   
   AFTER:
   ```
   # Include early language detection + greeting
   await process_utterance_with_greeting(
       session,
       audio_bytes,
       self.vad,
       self.stt,
       self.model,
       self.tts,
       self.greeting_handler,
       self.playback_mgr,
       self.ari
   )
   ```

4. Expected results:
   ─────────────────
   TURN 1: Caller speaks → Language detected → Greeting played in same language
   TURN 2+: Normal conversation in detected language

EXAMPLE LOG OUTPUT:
───────────────────
[abc123] First turn - detecting language for greeting...
✓ Detected language: ta (Tamil (தமிழ்))
✓ Greeting prepared in Tamil: 'வணக்கம்! உங்கள் புகாரை...'
[abc123] Playing greeting in Tamil
[abc123] Transcribed (ta): நீர் விநியோகம் இல்லை

✅ Greeting detected and prepared in correct language!
"""

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print(__doc__)
    print("\n✅ Integration module ready!")
    print("Follow the steps above to integrate into your call handler.")
