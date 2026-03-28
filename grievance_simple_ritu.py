#!/usr/bin/env python3
"""
✨ SIMPLIFIED VOICE → ROUTING → SARVAM RITU TTS (NO MEERA)
============================================================
Simple, direct flow:
1. Record voice or accept text
2. STT transcription
3. Department routing
4. Groq AI response generation
5. Sarvam Ritu TTS synthesis
6. JSON storage
"""

import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['OMP_NUM_THREADS'] = '1'

import sys
import json
import asyncio
import logging
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv
import tempfile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'awaaz'))

load_dotenv(dotenv_path=os.path.join(BASE_DIR, "awaaz", ".env"))

# Import core components
try:
    from analytics.analytical_model import create_processor
    from models.grievance_models import create_session_id, UrgencyLevel
    from outputs.json_storage_manager import JSONStorageManager
    from external_services.gov_services_map import detect_service_type
    from core.nlp_routing import classify_urgency, classify_intent
except ImportError as e:
    logger.error(f"Error importing core: {e}")
    sys.exit(1)

# Import AWAAZ modules
try:
    from awaaz.awaaz_recorder import MicCalibrator, VADEngine, Recorder, save_wav, TARGET_SR
    RECORDER_AVAILABLE = True
except ImportError:
    logger.warning("awaaz_recorder not available")
    RECORDER_AVAILABLE = False
    TARGET_SR = 16000

try:
    from awaaz.src.pipeline.stt import STTProcessor
    from awaaz.src.pipeline.tts import TTSProcessor
    from awaaz.src.pipeline.nlp import LANGUAGE_CONFIG
    from awaaz.src.session_store import AWAAZSession
    AWAAZ_AVAILABLE = True
except ImportError as e:
    AWAAZ_AVAILABLE = False
    logger.warning(f"AWAAZ modules: {e}")
    LANGUAGE_CONFIG = {"hi": {"name": "Hindi", "script": "Devanagari"}}

# Groq for AI response
try:
    from groq import AsyncGroq
    groq_client_async = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
    GROQ_AVAILABLE = True
except ImportError:
    logger.warning("Groq not available - using fallback responses")
    GROQ_AVAILABLE = False
    groq_client_async = None

# Color output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}\n")

def print_section(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'─'*80}{Colors.END}")
    print(f"{Colors.CYAN}  {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'─'*80}{Colors.END}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# SIMPLIFIED PIPELINE - NO MEERA ASSISTANT
# ═══════════════════════════════════════════════════════════════════════════════

async def generate_groq_response(transcript: str, language: str, urgency: str, 
                                department: str, service_name: str) -> str:
    """Generate response using Groq LLM"""
    
    if GROQ_AVAILABLE and groq_client_async:
        try:
            lang_name = LANGUAGE_CONFIG.get(language, {}).get('name', 'English')
            
            prompt = f"""You are a helpful Indian government grievance resolution assistant.

User's complaint: "{transcript}"
Department: {department}
Service: {service_name}
Urgency: {urgency}

Provide a SHORT, empathetic response in pure {lang_name} (native script only):
1. Acknowledge their issue
2. Confirm which department will handle it
3. Provide next steps

Keep it 2-3 sentences max. No English, no markdown."""
            
            message = await groq_client_async.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            return message.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Groq failed: {e}")
    
    # Fallback
    fallback = {
        'en': f"Your complaint about {department} has been received. Our team will contact you soon.",
        'hi': f"आपकी {department} से संबंधित शिकायत दर्ज की गई है। हमारी टीम जल्द से जल्द आपसे संपर्क करेगी।",
        'ta': "உங்கள் குறை பதிவு செய்யப்பட்டுவிட்டது. விரைவில் தகவல் பெறுவீர்கள்.",
        'te': "మీ ఫిర్యాదు నమోదు చేయబడింది. త్వరలో సమాధానం పోస్తాము.",
        'mr': "आपली तक्रार नोंदणी केली गेली आहे. लगेच संपर्क साधेल."
    }
    return fallback.get(language, fallback['en'])


def record_audio(duration_s: int = 15):
    """Record audio from microphone"""
    if not RECORDER_AVAILABLE:
        print("❌ Microphone not available")
        return None
    
    print_section("🎤 RECORDING")
    print("[REC] Calibrating...")
    
    try:
        calibrator = MicCalibrator()
        calibration = calibrator.calibrate()
    except Exception as e:
        logger.warning(f"Calibration warning: {e}")
        calibration = None
    
    print(f"{Colors.GREEN}🔴 RECORDING IN PROGRESS...{Colors.END}")
    print(f"{Colors.YELLOW}📣 Speak your complaint clearly{Colors.END}\n")
    
    try:
        vad = VADEngine(aggressiveness=1)
        recorder = Recorder(vad=vad)
        
        audio = recorder.record(
            max_duration_s=duration_s,
            silence_ms=20000,
            calibration=calibration
        )
        
        if not audio or len(audio) == 0:
            return None
        
        audio_path = tempfile.mktemp(suffix=".wav")
        save_wav(audio, TARGET_SR, audio_path)
        
        duration = len(audio) / TARGET_SR
        print(f"{Colors.GREEN}✓ {duration:.2f}s recorded{Colors.END}\n")
        
        return audio_path, audio
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⏹️  Stopped{Colors.END}")
        return None
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        return None


async def main():
    print_header("🗣️ SIMPLIFIED GRIEVANCE SYSTEM (SARVAM RITU + GROQ)")
    
    processor = create_processor(use_groq=False)
    json_storage = JSONStorageManager(base_output_dir="outputs/json_results")
    
    # STEP 1: Get input (voice or text)
    print_section("STEP 1: VOICE/TEXT INPUT")
    
    recording_result = record_audio(duration_s=20)
    
    if not recording_result:
        print(f"{Colors.YELLOW}No audio. Text input mode:{Colors.END}")
        user_input = input(f"{Colors.CYAN}Enter complaint: {Colors.END}").strip()
        
        if not user_input:
            return
        
        transcript = user_input
        audio_data = None
        audio_file_path = None
        lang_code = "auto"
    else:
        audio_file_path, audio_data = recording_result
        
        # STEP 2: STT
        print_section("STEP 2: STT TRANSCRIPTION")
        
        stt = STTProcessor(preferred_provider="groq_whisper")
        await stt.load()
        
        if hasattr(stt, 'confidence_threshold'):
            stt.confidence_threshold = 0.3
        
        stt_result = await stt.transcribe(audio_file_path, language="auto")
        
        if not stt_result or not stt_result.text:
            print("❌ STT failed")
            return
        
        transcript = stt_result.text
        lang_code = stt_result.detected_language or "hi"
        
        print(f"✓ Transcript: {transcript[:60]}...")
        print(f"✓ Language: {lang_code}\n")
    
    # STEP 3: Language detection (from text if no audio)
    if lang_code == "auto":
        script_markers = {
            'hi': ['\u0915', '\u0916'],
            'ta': ['\u0BA4', '\u0BA5'],
            'te': ['\u0C24', '\u0C25'],
            'kn': ['\u0C95', '\u0C96'],
            'ml': ['\u0D15', '\u0D16'],
            'bn': ['\u0985', '\u0986'],
            'en': None,
        }
        
        detected = 'en'
        for code, markers in script_markers.items():
            if markers and any(m in transcript for m in markers):
                detected = code
                break
        lang_code = detected
    
    # STEP 4: Routing
    print_section("STEP 3: DEPARTMENT ROUTING")
    
    urgency, matched_keywords, conf = classify_urgency(transcript)
    service_type, service_keywords, may_escalate = detect_service_type(transcript, matched_keywords)
    intent = classify_intent(transcript, urgency, matched_keywords, lang_code)
    
    print(f"✓ Department: {service_type.upper()}")
    print(f"✓ Urgency: {urgency.name}")
    print(f"✓ Intent: {intent.primary_intent}\n")
    
    # STEP 5: Full analysis
    print_section("STEP 4: FULL ANALYSIS")
    
    session_id = create_session_id()
    
    analytical_model = processor.process_grievance(
        session_id=session_id,
        transcript=transcript,
        audio_data=audio_data,
        sample_rate=TARGET_SR if audio_data else 0,
        detected_language=lang_code,
        state="maharashtra",
    )
    
    service_name = analytical_model.routing.mapped_service.service_name \
        if analytical_model.routing.mapped_service else "General"
    urgency_str = analytical_model.intent.urgency_level.name \
        if analytical_model.intent.urgency_level else "MEDIUM"
    
    print(f"✓ Dept: {analytical_model.routing.primary_department}")
    print(f"✓ Priority: P{analytical_model.routing.priority_level}")
    print(f"✓ Service: {service_name}\n")
    
    # STEP 6: Generate response
    print_section("STEP 5: GROQ RESPONSE GENERATION")
    
    response = await generate_groq_response(
        transcript,
        lang_code,
        urgency_str,
        analytical_model.routing.primary_department,
        service_name
    )
    
    print(f"✓ Response: {response}\n")
    
    # STEP 7: TTS with Sarvam Ritu
    print_section("STEP 6: TTS SYNTHESIS (SARVAM RITU VOICE)")
    
    session = AWAAZSession(session_id=session_id)
    session.lang = lang_code
    session.lang_name = LANGUAGE_CONFIG.get(lang_code, {}).get('name', 'English')
    session.speaker = "ritu"  # Use Ritu female voice
    session.emotion = "warm"
    
    tts = TTSProcessor(preferred_provider="sarvam")
    temp_wav = f"/tmp/{session_id}_ritu_response.wav"
    
    try:
        success = await tts.synthesize(
            text=response,
            language=lang_code,
            session=session,
            output_path=temp_wav
        )
        
        if success and os.path.exists(temp_wav) and os.path.getsize(temp_wav) > 1000:
            print(f"✓ Ritu TTS generated: {temp_wav}")
            print(f"✓ Playing audio...")
            os.system(f"afplay {temp_wav} 2>/dev/null || mpv {temp_wav} 2>/dev/null")
    except Exception as e:
        logger.warning(f"TTS failed: {e}")
        print(f"⚠️  TTS unavailable, showing text: {response}")
    
    # STEP 8: Save to JSON
    print_section("STEP 7: JSON STORAGE")
    
    result_doc = {
        'session_id': session_id,
        'timestamp': datetime.now().isoformat(),
        'input': {
            'transcript': transcript,
            'language': lang_code,
            'input_mode': 'voice' if audio_data else 'text',
        },
        'analysis': {
            'department': analytical_model.routing.primary_department,
            'priority': analytical_model.routing.priority_level,
            'urgency': urgency_str,
            'intent': analytical_model.intent.primary_intent,
            'emotion': analytical_model.emotion.detected_emotion.name,
            'anger_score': analytical_model.emotion.anger_score,
        },
        'routing': {
            'service': service_name,
            'has_gov_service': analytical_model.routing.has_gov_service_match,
        },
        'response': response,
    }
    
    saved_paths = processor.save_result_organized(analytical_model)
    
    print(f"✓ Saved to by_urgency/{urgency_str}/")
    print(f"✓ Saved to by_department/{service_type}/\n")
    
    print_header("✅ GRIEVANCE PROCESSED SUCCESSFULLY")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⏹️  Interrupted{Colors.END}\n")
