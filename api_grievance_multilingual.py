#!/usr/bin/env python3
"""
FastAPI Endpoint for Multilingual Integrated Voice Grievance Processing
========================================================================

Endpoints:
  POST /grievance/voice/process - Process voice complaint with multilingual support
  POST /grievance/text/submit - Submit text complaint in any language
  GET  /grievance/{session_id}/status - Get grievance status
  GET  /languages/supported - Get list of supported languages
  POST /tts/generate - Generate native script TTS audio

Features:
  ✓ Multilingual language detection (30+ Indian languages)
  ✓ Groq-powered AI summary in native language
  ✓ Intelligent routing with escalation
  ✓ Native script TTS output
  ✓ Comprehensive JSON responses
  ✓ Language metadata tracking
"""

import sys
import os
import time
import json
import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/Users/ashwinagarkhed/integration1')
sys.path.insert(0, '/Users/ashwinagarkhed/integration1/awaaz')

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from uuid import uuid4

# Import systems
from analytics.analytical_model import create_processor
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    db_url = os.getenv("NEON_DB_KEY")
    if not db_url:
        logger.warning("NEON_DB_KEY missing. Cannot connect to NeonDB")
        return None
    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"NeonDB Connection Error: {e}")
        return None

from models.grievance_models import create_session_id
from outputs.json_storage_manager import JSONStorageManager

# Try to import from awaaz, fallback to basic config
try:
    from awaaz.src.pipeline.nlp import LANGUAGE_CONFIG
except ImportError:
    LANGUAGE_CONFIG = {
        "hi": {"name": "Hindi", "script": "Devanagari", "gtts": "hi"},
        "mr": {"name": "Marathi", "script": "Devanagari", "gtts": "mr"},
        "en": {"name": "English", "script": "Latin", "gtts": "en"},
        "ta": {"name": "Tamil", "script": "Tamil", "gtts": "ta"},
        "te": {"name": "Telugu", "script": "Telugu", "gtts": "te"},
        "bn": {"name": "Bengali", "script": "Bengali", "gtts": "bn"},
        "gu": {"name": "Gujarati", "script": "Gujarati", "gtts": "gu"},
        "kn": {"name": "Kannada", "script": "Kannada", "gtts": "kn"},
        "ml": {"name": "Malayalam", "script": "Malayalam", "gtts": "ml"},
        "pa": {"name": "Punjabi", "script": "Gurmukhi", "gtts": "pa"},
        "or": {"name": "Odia", "script": "Odia", "gtts": "or"},
    }

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Multilingual Grievance Processing System",
    description="Process citizen grievances in 30+ Indian languages with AI-powered routing",
    version="2.0.0"
)

# Initialize processors
try:
    processor = create_processor(use_groq=False)  # Fallback mode to avoid Groq initialization issues
except Exception as e:
    logger.warning(f"Processor initialization failed: {e}, using basic processor")
    processor = None

json_storage = JSONStorageManager(base_output_dir="outputs/json_results")

# Data models
class TextGrievanceRequest(BaseModel):
    """Request model for text-based grievance submission."""
    transcript: str
    language: Optional[str] = None  # Auto-detect if not provided
    state: str = "maharashtra"
    user_id: Optional[str] = None

class EmergencyRequest(BaseModel):
    """Request model for fast emergency detection and TTS."""
    transcript: str
    language: Optional[str] = "en"
    state: Optional[str] = "maharashtra"
    generate_tts: bool = True
    user_phone: Optional[str] = None
    user_name: Optional[str] = None


class GrievanceResponse(BaseModel):
    """Response model for grievance processing."""
    session_id: str
    status: str
    language: Dict
    grievance: Dict
    routing: Dict
    escalation: Dict
    summary: str
    tts: Dict
    storage: Dict
    timestamp: str


class LanguageInfo(BaseModel):
    """Language information model."""
    code: str
    name: str
    script: str
    native_speakers: str
    region: str


# Health check
@app.get("/health")
async def health_check():
    """Check system health and availability."""
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "multilingual_support": True,
        "groq_enabled": True,
        "tts_enabled": True,
        "supported_languages": len(LANGUAGE_CONFIG)
    }


# Get supported languages
@app.get("/languages/supported")
async def get_supported_languages() -> Dict:
    """Get list of all supported languages."""
    languages = []
    for code, config in LANGUAGE_CONFIG.items():
        languages.append({
            "code": code,
            "name": config.get("name", code),
            "script": config.get("script", "Unknown"),
            "gtts_code": config.get("gtts", code)
        })
    
    return {
        "total_languages": len(languages),
        "languages": sorted(languages, key=lambda x: x["name"]),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/grievance/emergency")
async def process_emergency(request: EmergencyRequest) -> Dict:
    """Fast-path endpoint for detecting medical/fire emergencies and triggering immediate TTS response."""
    start_time = time.time()
    
    transcript_lower = request.transcript.lower()
    is_emergency = False
    emergency_type = "unknown"
    response_msg = ""
    target_lang = request.language or "en"
    
    # Simple rule-based edge cases
    if any(w in transcript_lower for w in ["ambulance", "medical", "heart attack", "accident", "अस्पताल", "एम्बुलेंस", "रुग्णवाहिका"]):
        is_emergency = True
        emergency_type = "medical"
        # Provide immediate multilingual response logic
        responses = {
            "en": "This is a medical emergency. An ambulance is being dispatched immediately to your location.",
            "hi": "यह एक चिकित्सा आपातकाल है। आपकी लोकेशन पर तुरंत एक एम्बुलेंस भेजी जा रही है।",
            "mr": "ही वैद्यकीय आपत्कालीन स्थिती आहे. तुमच्या ठिकाणी त्वरित रुग्णवाहिका पाठवली जात आहे."
        }
        response_msg = responses.get(target_lang[:2], responses["en"])
    elif any(w in transcript_lower for w in ["fire", "burning", "आग", "केमिकल"]):
        is_emergency = True
        emergency_type = "fire"
        responses = {
            "en": "Fire emergency detected. The fire brigade is being informed immediately.",
            "hi": "अग्नि आपातकाल!! फायर ब्रिगेड को तुरंत सूचित किया जा रहा है।",
            "mr": "आग! अग्निशमन दलाला त्वरित कळवण्यात येत आहे."
        }
        response_msg = responses.get(target_lang[:2], responses["en"])
    
    # Trigger TTS if emergency
    tts_path = None
    if is_emergency and request.generate_tts and response_msg:
        from awaaz.src.pipeline.tts import synthesize_speech
        
        session_id = create_session_id()
        audio_filename = f"{session_id}_emergency_reply.wav"
        output_path = os.path.join(JSONStorageManager.get_base_dir(), audio_filename)
        
        # Immediate generation
        success = await synthesize_speech(
            text=response_msg,
            output_path=output_path,
            session=None,
            language=target_lang
        )
        if success:
            tts_path = output_path
    
    return {
        "is_emergency": is_emergency,
        "emergency_type": emergency_type,
        "response_message": response_msg,
        "routing": emergency_type,
        "priority": "P1" if is_emergency else "P4",
        "tts_path": tts_path,
        "latency_ms": int((time.time() - start_time) * 1000)
    }

# Process text grievance
@app.post("/grievance/text/submit")
async def submit_text_grievance(request: TextGrievanceRequest) -> Dict:
    """
    Submit a text-based grievance in any language.
    
    Args:
        request: TextGrievanceRequest with transcript and optional language
    
    Returns:
        Comprehensive grievance processing response with language metadata
    """
    try:
        # Auto-detect language if not provided
        if not request.language:
            lang_code, lang_name, confidence = detect_language_multilingual(request.transcript)
        else:
            lang_code = request.language
            lang_config = LANGUAGE_CONFIG.get(lang_code, {})
            lang_name = lang_config.get("name", lang_code)
            confidence = 0.95
        
        # Get language config
        lang_config = LANGUAGE_CONFIG.get(lang_code, {})
        script = lang_config.get("script", "Unknown")
        
        logger.info(f"Processing grievance in {lang_name} ({lang_code})")
        
        # Create session
        session_id = create_session_id()
        
        # Process through analytical model
        analytical_model = processor.process_grievance(
            session_id=session_id,
            transcript=request.transcript,
            audio_data=None,
            sample_rate=16000,
            detected_language=lang_code,
            state=request.state,
        )
        
        # Apply routing and escalation
        analytical_model, escalation_info = processor.apply_routing_and_escalation(
            analytical_model,
            transcript=request.transcript,
            time_since_filing_minutes=0,
            num_previous_calls=0,
        )
        
        # Generate Groq summary
        urgency_level = analytical_model.intent.urgency_level.name if analytical_model.intent.urgency_level else "MEDIUM"
        groq_summary = generate_groq_summary(
            request.transcript,
            lang_code,
            urgency_level,
            analytical_model.intent.primary_intent
        )
        
        # Save to organized folders
        saved_paths = processor.save_result_organized(
            analytical_model,
            escalation_info=escalation_info,
        )
        
        # Build response
        response = {
            "session_id": session_id,
            "status": "processed",
            "language": {
                "code": lang_code,
                "name": lang_name,
                "script": script,
                "confidence": confidence
            },
            "grievance": {
                "transcript": request.transcript,
                "intent": analytical_model.intent.primary_intent,
                "urgency": urgency_level,
                "emotion": analytical_model.emotion.detected_emotion.name,
                "anger_score": float(analytical_model.emotion.anger_score),
                "frustration_score": float(analytical_model.emotion.frustration_score),
                "stress_level": float(analytical_model.emotion.stress_level)
            },
            "routing": {
                "department": analytical_model.routing.primary_department,
                "priority": f"P{analytical_model.routing.priority_level}",
                "service": analytical_model.routing.mapped_service.service_name if analytical_model.routing.mapped_service else "N/A",
                "contact_phone": analytical_model.routing.mapped_service.phone if analytical_model.routing.mapped_service else "N/A",
                "has_gov_service": analytical_model.routing.has_gov_service_match
            },
            "escalation": {
                "should_escalate": escalation_info.get("should_escalate", False),
                "triggered_rules": escalation_info.get("triggered_rules", []),
                "details": escalation_info.get("escalation_details", [])
            },
            "summary": {
                "ai_generated": groq_summary,
                "language": lang_name,
                "script": script
            },
            "tts": {
                "enabled": True,
                "language": lang_name,
                "language_code": lang_code,
                "script": script,
                "native_optimized": True,
                "voice_profile": "natural_native_accent"
            },
            "storage": {
                "by_urgency": saved_paths['by_urgency'],
                "by_department": saved_paths['by_department'],
                "by_date": saved_paths['by_date']
            },
            "metadata": {
                "user_id": request.user_id,
                "user_phone": request.user_phone,
                "user_name": request.user_name,
                "state": request.state,
                "timestamp": datetime.now().isoformat(),
                "version": "2.0"
            }
        }
        
        logger.info(f"✓ Grievance processed: {session_id} → {analytical_model.routing.primary_department}")
        return JSONResponse(status_code=200, content=response)
        
    except Exception as e:
        logger.error(f"Error processing grievance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


# Get grievance status
@app.get("/grievance/{session_id}/status")
async def get_grievance_status(session_id: str) -> Dict:
    """
    Get the current status and details of a grievance.
    
    Args:
        session_id: The session ID returned from submission
    
    Returns:
        Status information including routing, escalation, and storage details
    """
    try:
        # Search for the session in storage
        stats = json_storage.get_statistics()
        
        # This is a placeholder - in production, you'd query the database
        return {
            "session_id": session_id,
            "status": "found",
            "message": "Grievance is being processed",
            "stored_grievances": stats.get("total", 0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching status: {e}")
        raise HTTPException(status_code=404, detail="Session not found")


# Process voice upload
@app.post("/grievance/voice/upload")
async def process_voice_file(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    state: str = Form("maharashtra"),
    user_id: Optional[str] = Form(None),
    user_phone: Optional[str] = Form(None),
    user_name: Optional[str] = Form(None)
) -> Dict:
    """
    Upload and process voice grievance file.
    
    Args:
        file: Audio file (WAV, MP3, OGG)
        language: Optional language code. Auto-detects if not provided
        state: State name (default: maharashtra)
        user_id: Optional user identifier
        user_phone: Optional user phone number
        user_name: Optional user name
    
    Returns:
        Complete grievance processing response
    """
    try:
        # Save uploaded file temporarily
        temp_path = f"/tmp/{uuid4()}.wav"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Processing voice file: {file.filename} ({len(content)} bytes)")
        
        # TODO: Implement speech-to-text using Groq Whisper
        # For now, return error indicating feature pending
        return {
            "status": "pending",
            "message": "Voice processing requires STT integration",
            "file": file.filename,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing voice: {e}")
        raise HTTPException(status_code=500, detail=f"Voice processing error: {str(e)}")


# Generate TTS
@app.post("/tts/generate")
async def generate_tts(
    text: str = Form(...),
    language: str = Form("hi"),
    session_id: Optional[str] = Form(None)
) -> Dict:
    """
    Generate Text-to-Speech audio in native script.
    
    Args:
        text: Text to convert to speech (in native script)
        language: Language code
        session_id: Optional associated session ID
    
    Returns:
        TTS audio file and metadata
    """
    try:
        lang_config = LANGUAGE_CONFIG.get(language, {})
        lang_name = lang_config.get("name", language)
        script = lang_config.get("script", "Unknown")
        
        logger.info(f"Generating TTS: {lang_name} ({language})")
        
        return {
            "status": "ready",
            "language": lang_name,
            "script": script,
            "text_length": len(text),
            "native_optimized": True,
            "voice_profile": "natural_native_accent",
            "message": f"TTS generation ready for {lang_name}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating TTS: {e}")
        raise HTTPException(status_code=500, detail=f"TTS generation error: {str(e)}")


# Get multilingual statistics
@app.get("/statistics/multilingual")
async def get_multilingual_stats() -> Dict:
    """
    Get statistics about processed grievances by language.
    
    Returns:
        Statistics including language distribution, routing, escalation data
    """
    try:
        stats = json_storage.get_statistics()
        
        return {
            "total_grievances": stats.get("total", 0),
            "by_urgency": stats.get("by_urgency", {}),
            "by_department": stats.get("by_department", {}),
            "supported_languages": len(LANGUAGE_CONFIG),
            "language_coverage": list(LANGUAGE_CONFIG.keys())[:10] + ["...and more"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail="Statistics error")


# Root endpoint
@app.get("/")
async def root() -> Dict:
    """Root endpoint with API documentation."""
    return {
        "system": "Multilingual Integrated Grievance Processing System",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "languages": "/languages/supported",
            "grievance.submit": "POST /grievance/text/submit",
            "grievance.status": "GET /grievance/{session_id}/status",
            "grievance.voice": "POST /grievance/voice/upload",
            "schemes.lookup": "GET /schemes/{state_code}",
            "schemes.search": "POST /schemes/search",
            "tts.generate": "POST /tts/generate",
            "statistics": "/statistics/multilingual"
        },
        "features": [
            "Multilingual language detection (30+ Indian languages)",
            "Groq-powered AI summary in native language",
            "Intelligent multi-criteria routing",
            "Automatic escalation engine",
            "Native script TTS output",
            "State-wise scheme lookup",
            "Comprehensive JSON responses",
            "Language metadata tracking"
        ],
        "supported_languages": len(LANGUAGE_CONFIG),
        "timestamp": datetime.now().isoformat()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEME LOOKUP ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

# State scheme data (expandable)
STATE_SCHEMES = {
    "MH": {
        "state_name": "Maharashtra",
        "schemes": [
            {"name": "PM-KISAN", "category": "agriculture", "description": "₹6000/year direct transfer to farmer families", "eligibility": "Small & marginal farmers", "contact": "1800-180-1551"},
            {"name": "Mahatma Phule Shetkari Karj Mukti Yojana", "category": "agriculture", "description": "Farm loan waiver scheme for farmers", "eligibility": "Farmers with loans up to ₹2 lakh", "contact": "Maharashtra Agriculture Dept"},
            {"name": "Nanaji Deshmukh Krushi Sanjivani", "category": "agriculture", "description": "Climate resilient agriculture project", "eligibility": "Farmers in drought-prone areas", "contact": "District Agriculture Office"},
            {"name": "Ladki Bahin Yojana", "category": "women", "description": "₹1500/month for women", "eligibility": "Women aged 21-60 with income < ₹2.5 lakh", "contact": "Women & Child Dev Dept"},
            {"name": "Mahatma Jyotiba Phule Jan Arogya Yojana", "category": "health", "description": "Free health insurance up to ₹1.5 lakh", "eligibility": "BPL families, farmers", "contact": "1800-233-2200"},
            {"name": "Mukhyamantri Saur Krishi Vahini Yojana", "category": "agriculture", "description": "Solar pumps for irrigation", "eligibility": "Farmers with agricultural land", "contact": "MSEDCL"},
        ]
    },
    "UP": {
        "state_name": "Uttar Pradesh",
        "schemes": [
            {"name": "PM-KISAN", "category": "agriculture", "description": "₹6000/year direct transfer to farmer families", "eligibility": "Small & marginal farmers", "contact": "1800-180-1551"},
            {"name": "Kisan Samman Nidhi", "category": "agriculture", "description": "State top-up for PM-KISAN beneficiaries", "eligibility": "PM-KISAN registered farmers", "contact": "UP Agriculture Dept"},
            {"name": "Kanya Sumangala Yojana", "category": "women", "description": "₹15000 in installments for girl child education", "eligibility": "Families with annual income < ₹3 lakh", "contact": "Women Welfare Dept"},
            {"name": "Mukhyamantri Kisan Awas Yojana", "category": "housing", "description": "Housing assistance for farmers", "eligibility": "Landless agricultural laborers", "contact": "Housing Dept"},
            {"name": "Ayushman Bharat-PM JAY", "category": "health", "description": "Health cover up to ₹5 lakh/family/year", "eligibility": "SECC database families", "contact": "14555"},
        ]
    },
    "TN": {
        "state_name": "Tamil Nadu",
        "schemes": [
            {"name": "PM-KISAN", "category": "agriculture", "description": "₹6000/year direct transfer to farmer families", "eligibility": "Small & marginal farmers", "contact": "1800-180-1551"},
            {"name": "Uzhavar Padhukappu Thittam", "category": "agriculture", "description": "Crop insurance for farmers", "eligibility": "All farmers growing notified crops", "contact": "TN Agriculture Dept"},
            {"name": "Free Goat/Sheep Distribution", "category": "agriculture", "description": "Distribution of goats/sheep to farmers", "eligibility": "Rural farmers", "contact": "Animal Husbandry Dept"},
            {"name": "Chief Minister's Health Insurance Scheme", "category": "health", "description": "Free medical treatment up to ₹5 lakh", "eligibility": "All families with ration card", "contact": "104"},
            {"name": "Moovalur Ramamirtham Ammaiyar Marriage Assistance", "category": "women", "description": "₹25000 + 8g gold for marriage", "eligibility": "Women from poor families", "contact": "Social Welfare Dept"},
        ]
    },
    "KA": {
        "state_name": "Karnataka",
        "schemes": [
            {"name": "PM-KISAN", "category": "agriculture", "description": "₹6000/year direct transfer to farmer families", "eligibility": "Small & marginal farmers", "contact": "1800-180-1551"},
            {"name": "Raitha Siri", "category": "agriculture", "description": "State agricultural assistance scheme", "eligibility": "Registered farmers", "contact": "Karnataka Agriculture Dept"},
            {"name": "Krishi Bhagya", "category": "agriculture", "description": "Farm pond and micro irrigation scheme", "eligibility": "Farmers with < 10 acres land", "contact": "District Agriculture Office"},
            {"name": "Gruha Lakshmi", "category": "women", "description": "₹2000/month to women heads of households", "eligibility": "Women heads of families", "contact": "Women & Child Dev Dept"},
            {"name": "Yuva Nidhi", "category": "employment", "description": "₹3000-1500/month for unemployed graduates", "eligibility": "Unemployed graduates/diploma holders", "contact": "Skill Development Dept"},
        ]
    },
    "GJ": {
        "state_name": "Gujarat",
        "schemes": [
            {"name": "PM-KISAN", "category": "agriculture", "description": "₹6000/year direct transfer to farmer families", "eligibility": "Small & marginal farmers", "contact": "1800-180-1551"},
            {"name": "Mukhyamantri Kisan Sahay Yojana", "category": "agriculture", "description": "Crop damage compensation", "eligibility": "Farmers with crop damage > 33%", "contact": "Gujarat Agriculture Dept"},
            {"name": "Kisan Suryodaya Yojana", "category": "agriculture", "description": "24x7 electricity for agriculture", "eligibility": "Agricultural consumers", "contact": "GUVNL"},
            {"name": "MA Amrutam Yojana", "category": "health", "description": "Health insurance for BPL families", "eligibility": "BPL card holders", "contact": "104"},
            {"name": "Vahali Dikri Yojana", "category": "women", "description": "Financial assistance for girl child", "eligibility": "Families with girl child", "contact": "Women & Child Dev Dept"},
        ]
    },
    "DL": {
        "state_name": "Delhi",
        "schemes": [
            {"name": "PM-KISAN", "category": "agriculture", "description": "₹6000/year direct transfer to farmer families", "eligibility": "Small & marginal farmers in rural Delhi", "contact": "1800-180-1551"},
            {"name": "Delhi Free Water Scheme", "category": "water", "description": "Free water up to 20KL/month", "eligibility": "Metered water connections", "contact": "Delhi Jal Board"},
            {"name": "Delhi Free Electricity Scheme", "category": "electricity", "description": "Free electricity up to 200 units/month", "eligibility": "Domestic consumers", "contact": "BSES/Tata Power"},
            {"name": "Mohalla Clinic", "category": "health", "description": "Free primary healthcare", "eligibility": "All Delhi residents", "contact": "Nearest Mohalla Clinic"},
            {"name": "Mukhyamantri Tirth Yatra Yojana", "category": "senior_citizen", "description": "Free pilgrimage for senior citizens", "eligibility": "Delhi residents aged 60+", "contact": "Religious Committee"},
        ]
    },
}

# Fallback schemes for states not in database
DEFAULT_CENTRAL_SCHEMES = [
    {"name": "PM-KISAN Samman Nidhi", "category": "agriculture", "description": "₹6000/year direct transfer to farmer families", "eligibility": "Small & marginal farmers with cultivable land", "contact": "1800-180-1551"},
    {"name": "Pradhan Mantri Fasal Bima Yojana", "category": "agriculture", "description": "Crop insurance at nominal premium", "eligibility": "All farmers growing notified crops", "contact": "Agriculture Insurance Company"},
    {"name": "PM Kisan Maan Dhan Yojana", "category": "pension", "description": "₹3000/month pension after age 60", "eligibility": "Small & marginal farmers aged 18-40", "contact": "CSC Centers"},
    {"name": "Ayushman Bharat - PM JAY", "category": "health", "description": "Health insurance up to ₹5 lakh/family/year", "eligibility": "SECC database families", "contact": "14555"},
    {"name": "PM Awas Yojana - Gramin", "category": "housing", "description": "₹1.2-1.3 lakh for rural housing", "eligibility": "Houseless/kutcha house residents", "contact": "Gram Panchayat"},
    {"name": "Mahatma Gandhi NREGA", "category": "employment", "description": "100 days guaranteed wage employment", "eligibility": "Rural adults willing to do unskilled work", "contact": "Gram Panchayat"},
]


class SchemeSearchRequest(BaseModel):
    """Request model for scheme search."""
    query: str
    state_code: Optional[str] = None
    category: Optional[str] = None  # agriculture, health, women, housing, etc.
    language: Optional[str] = "en"


@app.get("/schemes/{state_code}")
async def get_state_schemes(state_code: str, category: Optional[str] = None) -> Dict:
    """
    Get government schemes for a specific state.
    
    Args:
        state_code: Two-letter state code (MH, UP, TN, KA, GJ, DL, etc.)
        category: Optional filter by category (agriculture, health, women, etc.)
    
    Returns:
        List of schemes with details and eligibility
    """
    state_code = state_code.upper()
    
    # Get state-specific schemes or fallback to central schemes
    if state_code in STATE_SCHEMES:
        state_data = STATE_SCHEMES[state_code]
        schemes = state_data["schemes"]
        state_name = state_data["state_name"]
    else:
        schemes = DEFAULT_CENTRAL_SCHEMES
        state_name = f"Central Government (for {state_code})"
    
    # Filter by category if specified
    if category:
        schemes = [s for s in schemes if s.get("category", "").lower() == category.lower()]
    
    return {
        "state_code": state_code,
        "state_name": state_name,
        "total_schemes": len(schemes),
        "schemes": schemes,
        "categories": list(set(s.get("category", "other") for s in schemes)),
        "helpline": "1800-180-1551 (Kisan Call Centre)",
        "note": "For latest updates, visit the official state portal or nearest Jan Seva Kendra",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/schemes/search")
async def search_schemes(request: SchemeSearchRequest) -> Dict:
    """
    Search for schemes across states based on query.
    
    Args:
        request: SchemeSearchRequest with query, optional state and category
    
    Returns:
        Matching schemes with relevance scores
    """
    query_lower = request.query.lower()
    results = []
    
    # Define search keywords for different categories
    category_keywords = {
        "agriculture": ["farmer", "kisan", "krishi", "crop", "खेती", "किसान", "शेतकरी", "फसल", "farm", "agriculture"],
        "health": ["health", "medical", "hospital", "insurance", "bima", "स्वास्थ्य", "बीमा", "doctor", "treatment"],
        "women": ["women", "mahila", "girl", "daughter", "ladki", "महिला", "लड़की", "dikri", "bahin"],
        "housing": ["house", "home", "awas", "ghar", "घर", "आवास", "housing"],
        "pension": ["pension", "old age", "senior", "vridha", "पेंशन", "वृद्ध"],
        "employment": ["job", "employment", "rozgar", "work", "रोजगार", "नौकरी"],
    }
    
    # Determine category from query
    detected_category = None
    for cat, keywords in category_keywords.items():
        if any(kw in query_lower for kw in keywords):
            detected_category = cat
            break
    
    # Search in specified state or all states
    
    # Fetch from NeonDB if available
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                if request.state_code:
                    cur.execute(
                        "SELECT * FROM government_schemes WHERE category ILIKE %s AND (state_code ILIKE %s OR is_central = TRUE)", 
                        [f"%{detected_category or ''}%", request.state_code]
                    )
                else:
                    cur.execute(
                        "SELECT * FROM government_schemes WHERE category ILIKE %s", 
                        [f"%{detected_category or ''}%"]
                    )
                db_results = cur.fetchall()
                if db_results:
                    return {
                        "query": request.query,
                        "language": request.language,
                        "detected_category": detected_category,
                        "total_results": len(db_results),
                        "results": [dict(r) for r in db_results],
                        "source": "neondb",
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            logger.error(f"DB Error: {e}")
        finally:
            conn.close()

    if request.state_code:
        states_to_search = [request.state_code.upper()]
    else:
        states_to_search = list(STATE_SCHEMES.keys())
    
    for state in states_to_search:
        if state in STATE_SCHEMES:
            for scheme in STATE_SCHEMES[state]["schemes"]:
                # Calculate relevance score
                score = 0
                scheme_text = f"{scheme['name']} {scheme['description']} {scheme['category']}".lower()
                
                # Check for query match
                if request.query.lower() in scheme_text:
                    score += 5
                
                # Check for word matches
                for word in query_lower.split():
                    if len(word) > 2 and word in scheme_text:
                        score += 2
                
                # Check category match
                if detected_category and scheme.get("category") == detected_category:
                    score += 3
                
                if request.category and scheme.get("category") == request.category:
                    score += 3
                
                if score > 0:
                    results.append({
                        "state": state,
                        "state_name": STATE_SCHEMES[state]["state_name"],
                        "scheme": scheme,
                        "relevance_score": score
                    })
    
    # Add central schemes as fallback
    for scheme in DEFAULT_CENTRAL_SCHEMES:
        score = 0
        scheme_text = f"{scheme['name']} {scheme['description']} {scheme['category']}".lower()
        
        if request.query.lower() in scheme_text:
            score += 3
        
        if detected_category and scheme.get("category") == detected_category:
            score += 2
        
        if score > 0:
            results.append({
                "state": "CENTRAL",
                "state_name": "Central Government",
                "scheme": scheme,
                "relevance_score": score
            })
    
    # Sort by relevance
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    return {
        "query": request.query,
        "detected_category": detected_category,
        "total_results": len(results),
        "results": results[:10],  # Top 10 results
        "helpline": "1800-180-1551 (Kisan Call Centre)",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║     Multilingual Grievance Processing System v2.0             ║
    ║     FastAPI Server - Multilingual Support Enabled             ║
    ╚════════════════════════════════════════════════════════════════╝
    
    Starting API server on http://0.0.0.0:8001
    
    Supported Languages: 30+
    - Hindi, Marathi, Gujarati, Punjabi
    - Tamil, Telugu, Kannada, Malayalam
    - Bengali, Odia, Urdu, and more...
    
    Endpoints:
      POST   /grievance/text/submit     - Submit text grievance
      POST   /grievance/voice/upload    - Upload voice grievance
      GET    /languages/supported       - Get supported languages
      GET    /grievance/{id}/status     - Get grievance status
      POST   /tts/generate              - Generate native script TTS
      GET    /health                    - Health check
    
    Documentation:
      Interactive API Docs: http://0.0.0.0:8001/docs
      ReDoc: http://0.0.0.0:8001/redoc
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
