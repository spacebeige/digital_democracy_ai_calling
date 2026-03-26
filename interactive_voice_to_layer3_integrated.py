#!/usr/bin/env python3
"""
✨ MULTILINGUAL INTEGRATED VOICE → AI ANALYSIS → INTELLIGENT ROUTING → ORGANIZED JSON
=======================================================================================
"""

import sys
import os
import json
import time
import logging
import asyncio
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from collections import defaultdict
from typing import Dict, Tuple, Optional
import tempfile
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'awaaz'))

load_dotenv(dotenv_path=os.path.join(BASE_DIR, "awaaz", ".env"))

# Import our organized system
try:
    from analytics.analytical_model import create_processor
    from models.grievance_models import create_session_id, UrgencyLevel
    from outputs.json_storage_manager import JSONStorageManager
    from core.emotion_detection import analyze_emotions
    import soundfile as sf
except ImportError as e:
    logger.error(f"Error importing core components: {e}")

# Import awaaz recorder
try:
    from awaaz.awaaz_recorder import MicCalibrator, VADEngine, Recorder, save_wav, TARGET_SR
    RECORDER_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ awaaz_recorder not available, mic recording will fail.")
    RECORDER_AVAILABLE = False
    TARGET_SR = 16000

# Import multilingual support from AWAAZ
try:
    from awaaz.src.pipeline.stt import STTProcessor
    from awaaz.src.pipeline.nlp import ModelProcessor as AWAAZNLPProcessor, LANGUAGE_CONFIG
    from awaaz.src.pipeline.tts import synthesize_speech, TTSProcessor
    from awaaz.src.pipeline.enhancements.tts_pipeline_v2 import enhanced_tts
    from awaaz.src.pipeline.phonetic_converter import PhoneticConverter
    from awaaz.src.session_store import AWAAZSession
    AWAAZ_AVAILABLE = True
except ImportError as e:
    AWAAZ_AVAILABLE = False
    logger.warning(f"AWAAZ multilingual modules not available: {e}")
    LANGUAGE_CONFIG = {
        "hi": {"name": "Hindi", "script": "Devanagari"},
        "en": {"name": "English", "script": "Latin"},
    }

GROQ_AVAILABLE = False
groq_client = None
try:
    from groq import AsyncGroq, Groq
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        groq_client_async = AsyncGroq(api_key=api_key)
        GROQ_AVAILABLE = True
    else:
        logger.warning("GROQ_API_KEY not set")
except ImportError:
    pass

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


async def generate_groq_response(transcript: str, language: str, urgency: str, intent: str, service_name: str) -> str:
    """
    Generate AI response using Groq in the detected language.
    Summarizes issue, gives immediate steps, and maps to government scheme.
    """
    if not GROQ_AVAILABLE or groq_client_async is None:
        return f"Complaint received: {transcript[:50]}..."
    
    try:
        lang_config = LANGUAGE_CONFIG.get(language, {})
        lang_name = lang_config.get('name', 'English')
        
        prompt = f"""You are a helpful AI assistant for Indian citizens reporting grievances.
        
User's issue: "{transcript}"
Detected Category: {intent}
Urgency Level: {urgency}
Routed Department/Service: {service_name}

Provide a short response directed to the user entirely in pure Indian native {lang_name} that:
1. Acknowledges their specific issue empathetically using a very smooth, human-like, Indian cultural conversational context.
2. Explains exactly what immediate actionable steps they can take right now based on fetching live details.
3. Explicitly mentions which Indian government scheme or specific department is mapped to this.

Keep your response highly conversational, extremely natural, reassuring, and concise (3-4 sentences max). Ensure any English technical/department jargon is properly transliterated and dynamically translated into Indian dialect smoothly. Respond ONLY with the clean spoken text to be synthesized to the user strictly in {lang_name}, in its native script without any bullet points or markdown."""
        
        message = await groq_client_async.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300
        )
        return message.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"Groq response generation failed: {e}")
        return f"Request registered. Steps are being evaluated."


def record_live_audio(duration_s: int = 15):
    """Record audio from microphone with VAD voice isolation"""
    if not RECORDER_AVAILABLE:
        print("❌ awaaz_recorder module not available. Cannot use microphone.")
        return None
    
    print_section("🎤 MICROPHONE CALIBRATION & RECORDING")
    
    print("[REC] Calibrating microphone...")
    try:
        calibrator = MicCalibrator()
        calibration = calibrator.calibrate()
        print("  ✓ Microphone calibrated")
    except Exception as e:
        print(f"  ⚠️  Calibration warning: {e}")
        calibration = None
    
    print(f"\n{Colors.GREEN}🔴 RECORDING IN PROGRESS...{Colors.END}")
    print(f"{Colors.YELLOW}📣 Please speak your complaint clearly.{Colors.END}")
    print(f"{Colors.CYAN}Ready — speak now (max {duration_s}s, silence cutoff 20s){Colors.END}")
    
    try:
        vad = VADEngine(aggressiveness=1)  # Less aggressive VAD (1 instead of 2)
        recorder = Recorder(vad=vad, device_index=None)
        
        audio = recorder.record(
            max_duration_s=duration_s,
            silence_ms=20000,  # 20 seconds silence before cutoff
            calibration=calibration
        )
        
        if audio is None or len(audio) == 0:
            print("  ❌ No audio captured")
            return None
        
        duration = len(audio) / TARGET_SR
        print(f"\n{Colors.GREEN}✓ Recording complete: {duration:.2f}s captured{Colors.END}")
        
        audio_path = tempfile.mktemp(suffix=".wav")
        save_wav(audio, TARGET_SR, audio_path)
        print(f"  ✓ Audio saved locally to temp file.")
        
        return audio_path, audio
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⏹️  Recording stopped{Colors.END}")
        return None
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.END}")
        return None

async def main():
    print_header("🎤 MULTILINGUAL INTEGRATED VOICE GRIEVANCE PROCESSING 🎤")
    
    processor = create_processor(use_groq=False)
    json_storage = JSONStorageManager(base_output_dir="outputs/json_results")
    
    recording_result = record_live_audio(duration_s=20)
    if not recording_result:
        return
    audio_file_path, audio_data = recording_result
    
    print_section("📝 STEP 2: STT TRANSCRIPTION & LANGUAGE DETECTION")
    stt = STTProcessor(preferred_provider="groq_whisper")
    await stt.load()
    
    stt_result = await stt.transcribe(audio_file_path, language="auto")
    if not stt_result or not stt_result.text:
        print("  ❌ STT failed")
        return
    
    lang_code = stt_result.detected_language or "hi"
    confidence = stt_result.confidence
    transcript = stt_result.text
    transcript_native = stt_result.native_script_text or transcript
    script = LANGUAGE_CONFIG.get(lang_code, {}).get('script', 'Unknown')
    lang_name = LANGUAGE_CONFIG.get(lang_code, {}).get('name', 'Unknown')
    
    print(f"  {Colors.CYAN}Detected transcript (native script):{Colors.END}")
    print(f"  \"{transcript_native}\"")
    print(f"\n  {Colors.CYAN}Language Detection:{Colors.END}")
    print(f"  • Language: {lang_name} ({lang_code})")
    print(f"  • Script: {script}")
    print(f"  • Confidence: {confidence*100:.1f}%\n")
    
    print_section("🧠 STEP 3: AI ANALYSIS & MULTILINGUAL ROUTING")
    session_id = create_session_id()
    print(f"  Session ID: {session_id}\n")
    
    analytical_model = processor.process_grievance(
        session_id=session_id,
        transcript=transcript_native,
        audio_data=audio_data,
        sample_rate=TARGET_SR,
        detected_language=lang_code,
        state="maharashtra",
    )
    
    print(f"  ✓ NLP Intent: {analytical_model.intent.primary_intent}")
    urgency_level = analytical_model.intent.urgency_level.name if analytical_model.intent.urgency_level else "MEDIUM"
    print(f"  ✓ Urgency: {urgency_level}")
    print(f"  ✓ Emotion: {analytical_model.emotion.detected_emotion.name}")
    print(f"  ✓ Anger Score: {analytical_model.emotion.anger_score:.2f}\n")
    
    print_section("🚦 STEP 4: INTELLIGENT ROUTING & ESCALATION")
    analytical_model, escalation_info = processor.apply_routing_and_escalation(
        analytical_model,
        transcript=transcript_native,
        time_since_filing_minutes=0,
        num_previous_calls=0,
    )
    
    service_mapped = analytical_model.routing.mapped_service.service_name if analytical_model.routing.mapped_service else "General Dept"
    print(f"  ✓ Department: {Colors.CYAN}{analytical_model.routing.primary_department.upper()}{Colors.END}")
    print(f"  ✓ Priority: P{analytical_model.routing.priority_level}")
    print(f"  ✓ Service: {service_mapped}")
    
    print_section("🤖 STEP 5: GROQ AI RESPONSE (STEPS & SCHEME IN NATIVE LANGUAGE)")
    groq_response = await generate_groq_response(
        transcript_native,
        lang_code,
        urgency_level,
        analytical_model.intent.primary_intent,
        service_mapped
    )
    print(f"  {Colors.CYAN}AI Actionable Response ({lang_name}):{Colors.END}")
    print(f"  \"{groq_response}\"\n")
    
    print_section("🔊 STEP 6: AUDIO SYNTHESIS (TTS - ENHANCED SARVAM MULTILINGUAL)")
    
    session = AWAAZSession(session_id=session_id)
    session.lang = lang_code
    session.lang_name = lang_name
    
    # Pass emotion and intent for human-like TTS adjustments
    session.anger_score = analytical_model.emotion.anger_score
    session.intent = analytical_model.intent.primary_intent
    session.emotion_name = analytical_model.emotion.detected_emotion.name
    session.is_emergency = (urgency_level == "CRITICAL")
    
    temp_wav = f"/tmp/{session_id}_reply.wav"
    
    print(f"  [TTS] Synthesizing human-like voice (Ritu) for {lang_name} using Sarvam AI...")
    
    # Initialize base_tts preferring sarvam for smooth "Ritu" voice
    base_tts = TTSProcessor(preferred_provider="sarvam")
    
    success = enhanced_tts(
        text=groq_response,
        session=session,
        output_path=temp_wav,
        existing_tts=base_tts
    )
    
    if success:
        print(f"  ✓ TTS Generated successfully: {temp_wav}")
        print("  🔊 Playing audio response...")
        os.system(f"afplay {temp_wav} 2>/dev/null")
    else:
        print(f"  ❌ [ERROR] TTS synthesis failed")
    
    print_section("📁 STEP 7: ORGANIZED JSON STORAGE")
    saved_paths = processor.save_result_organized(analytical_model, escalation_info=escalation_info)
    print(f"  ✓ Saved to by_urgency/{urgency_level}/... {saved_paths['by_urgency'].split('/')[-1]}")
    print(f"  ✓ Saved to by_department/{analytical_model.routing.primary_department}/... {saved_paths['by_department'].split('/')[-1]}")
    
    print_header("✅ SYSTEM OPERATING PERFECTLY")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⏹️  Interrupted{Colors.END}\n")
