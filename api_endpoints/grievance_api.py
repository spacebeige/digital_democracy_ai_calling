"""
API Endpoints - FastAPI handlers for grievance processing
=========================================================
Provides endpoints for:
- POST /grievance/text - Text-based grievance
- POST /grievance/audio - Audio file upload and processing
- GET /grievance/{session_id} - Retrieve result
- GET /status - System health check
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import json
import numpy as np
import asyncio
from datetime import datetime
import uuid

# Import audio processing
try:
    import soundfile as sf
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# Import our modules
from models.grievance_models import (
    UrgencyLevel,
    EmotionState,
    GrievanceResponse,
    create_session_id,
)
from analytics.analytical_model import create_processor
from core.nlp_routing import classify_urgency, classify_intent
from external_services.gov_services_map import get_service_mapping
from core.policies import (
    ESCALATION_POLICIES, SLA_POLICIES, RESPONSE_TEMPLATES,
    DEPARTMENT_GUIDELINES, GRIEVANCE_HANDLING_PROCEDURE,
    get_escalation_policy, get_sla_policy, get_response_template,
    get_department_guideline, PolicyType
)

# Initialize FastAPI app
app = FastAPI(title="Grievance Processing AI", version="2.0")

# Initialize processor
analytical_processor = create_processor(use_groq=True)


# ─────────────────────────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────────────────────────

class TextGrievanceRequest(BaseModel):
    """Request model for text-based grievance."""
    transcript: str
    language: str = "en"
    state: str = "maharashtra"
    phone_number: Optional[str] = None
    email: Optional[str] = None


class GrievanceResponseModel(BaseModel):
    """Response model for grievance processing."""
    session_id: str
    status: str  # "success", "error"
    message: str
    data: Optional[dict] = None
    timestamp: str


# ─────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Grievance Processing AI v2.0",
        "status": "operational",
        "endpoints": {
            "POST /grievance/text": "Process text complaint",
            "POST /grievance/audio": "Process audio complaint",
            "GET /grievance/{session_id}": "Retrieve result",
            "GET /status": "System status",
        }
    }


@app.get("/status")
async def get_status():
    """Get system status and available services."""
    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "audio_processing": AUDIO_AVAILABLE,
            "nlp_routing": True,
            "emotion_detection": True,
            "gov_service_mapping": True,
            "groq_ai": analytical_processor.groq_client is not None,
        },
        "output_directories": {
            "json_results": "outputs/json_results",
            "audio_responses": "outputs/audio_responses",
        }
    }


@app.post("/grievance/text")
async def process_text_grievance(request: TextGrievanceRequest):
    """
    Process text-based grievance.
    
    Example request:
    ```json
    {
        "transcript": "There has been no electricity since yesterday morning",
        "language": "en",
        "state": "maharashtra"
    }
    ```
    """
    try:
        session_id = create_session_id()
        
        # Classify urgency
        urgency_level, matched_keywords, confidence = classify_urgency(
            request.transcript,
            emotion_score=0.0,  # No voice emotion for text
        )
        
        # Classify intent
        intent = classify_intent(
            request.transcript,
            urgency_level,
            matched_keywords,
            request.language,
        )
        
        # Create dummy audio data for analytical model
        dummy_audio = np.zeros(16000)  # 1 second of silence
        
        # Process with analytical model
        analytical_model = analytical_processor.process_grievance(
            session_id=session_id,
            transcript=request.transcript,
            audio_data=dummy_audio,
            sample_rate=16000,
            detected_language=request.language,
            state=request.state,
        )
        
        # ✨ APPLY INTELLIGENT ROUTING & ESCALATION
        analytical_model, escalation_info = analytical_processor.apply_routing_and_escalation(
            analytical_model,
            time_since_filing_minutes=0,
            num_previous_calls=0,
        )
        
        # Create response
        grievance_response = GrievanceResponse(
            session_id=session_id,
            timestamp=datetime.utcnow(),
            original_transcript=request.transcript,
            language=request.language,
            duration_seconds=0.0,
            analytical_model=analytical_model,
            response_text=generate_response_text(analytical_model),
            action_taken="Grievance logged and routed",
            processing_time_ms=100.0,
            quality_score=0.85,
        )
        
        # 📁 SAVE TO ORGANIZED FOLDERS (by_urgency, by_department, by_date)
        saved_paths = analytical_processor.save_result_organized(
            analytical_model,
            escalation_info=escalation_info,
        )
        
        response_data = grievance_response.to_json_dict()
        response_data["saved_paths"] = saved_paths
        response_data["routing_department"] = analytical_model.routing.primary_department
        response_data["escalation"] = escalation_info
        
        return GrievanceResponseModel(
            session_id=session_id,
            status="success",
            message="Grievance processed successfully",
            data=response_data,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/grievance/audio")
async def process_audio_grievance(
    file: UploadFile = File(...),
    language: str = "en",
    state: str = "maharashtra",
):
    """
    Process audio-based grievance.
    
    Accepts WAV files and processes through complete pipeline.
    """
    if not AUDIO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Audio processing not available")
    
    try:
        session_id = create_session_id()
        
        # Read audio file
        contents = await file.read()
        temp_path = f"/tmp/grievance_{session_id}.wav"
        
        with open(temp_path, 'wb') as f:
            f.write(contents)
        
        # Load audio
        audio_data, sample_rate = sf.read(temp_path)
        if len(audio_data.shape) > 1:  # Stereo to mono
            audio_data = np.mean(audio_data, axis=1)
        
        # For now, use mock transcription (in production, use STT service)
        transcript = "[Mock transcription from audio]"  # Replace with actual STT
        
        # Process with analytical model
        analytical_model = analytical_processor.process_grievance(
            session_id=session_id,
            transcript=transcript,
            audio_data=audio_data,
            sample_rate=sample_rate,
            detected_language=language,
            state=state,
        )
        
        # ✨ APPLY INTELLIGENT ROUTING & ESCALATION
        analytical_model, escalation_info = analytical_processor.apply_routing_and_escalation(
            analytical_model,
            time_since_filing_minutes=0,
            num_previous_calls=0,
        )
        
        # Create response
        grievance_response = GrievanceResponse(
            session_id=session_id,
            timestamp=datetime.utcnow(),
            original_transcript=transcript,
            language=language,
            duration_seconds=len(audio_data) / sample_rate,
            analytical_model=analytical_model,
            response_text=generate_response_text(analytical_model),
            response_audio_file=None,  # Can generate TTS response
            action_taken="Audio grievance logged and analyzed",
            processing_time_ms=1000.0,
            quality_score=0.8,
        )
        
        # 📁 SAVE TO ORGANIZED FOLDERS (by_urgency, by_department, by_date)
        saved_paths = analytical_processor.save_result_organized(
            analytical_model,
            escalation_info=escalation_info,
        )
        
        # Clean up temp file
        os.remove(temp_path)
        
        response_data = grievance_response.to_json_dict()
        response_data["saved_paths"] = saved_paths
        response_data["routing_department"] = analytical_model.routing.primary_department
        response_data["escalation"] = escalation_info
        
        return GrievanceResponseModel(
            session_id=session_id,
            status="success",
            message="Audio grievance processed successfully",
            data=response_data,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/grievance/{session_id}")
async def get_grievance_result(session_id: str):
    """
    Retrieve processed grievance result by session ID.
    
    Searches organized storage (by_urgency, by_department, by_date).
    """
    try:
        # Use JSON storage manager to find result
        result = analytical_processor.json_storage.get_result_by_session(session_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"No result found for session {session_id}")
        
        return GrievanceResponseModel(
            session_id=session_id,
            status="success",
            message="Result retrieved successfully",
            data=result,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/grievance/{session_id}/download")
async def download_grievance_result(session_id: str):
    """Download grievance result as JSON file from organized storage."""
    try:
        # Search in all urgency levels
        for urgency in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            urgency_dir = f"outputs/json_results/by_urgency/{urgency}"
            if os.path.exists(urgency_dir):
                for filename in os.listdir(urgency_dir):
                    if session_id in filename and filename.endswith('.json'):
                        json_path = os.path.join(urgency_dir, filename)
                        return FileResponse(
                            json_path,
                            filename=filename,
                            media_type="application/json"
                        )
        
        raise HTTPException(status_code=404, detail=f"File not found for session {session_id}")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────

def generate_response_text(analytical_model) -> str:
    """Generate user-friendly response text."""
    urgency_text = {
        UrgencyLevel.CRITICAL: "🚨 CRITICAL: This is an emergency. Emergency services are being alerted.",
        UrgencyLevel.HIGH: "⚠️  URGENT: This issue requires immediate attention. Routing to specialized team.",
        UrgencyLevel.MEDIUM: "📋 Your complaint has been received and will be addressed soon.",
        UrgencyLevel.LOW: "ℹ️  Thank you for your feedback. We will review and respond within standard timeframe.",
    }.get(analytical_model.intent.urgency_level, "Thank you for submitting your grievance.")
    
    routing_text = ""
    if analytical_model.routing.mapped_service:
        routing_text = f"\nRouting to: {analytical_model.routing.mapped_service.service_name} ({analytical_model.routing.mapped_service.contact_info})"
    
    summary_text = f"\nSummary: {analytical_model.ai_summary[:200]}..."
    
    return urgency_text + routing_text + summary_text


# ─────────────────────────────────────────────────────────────────
# POLICY ENDPOINTS - FOR LIVE FEED INTEGRATION
# ─────────────────────────────────────────────────────────────────

@app.get("/policies/escalation")
async def get_escalation_policies():
    """Get all escalation policies for live feed display."""
    return {
        "status": "success",
        "policy_type": "escalation",
        "total_policies": len(ESCALATION_POLICIES),
        "policies": [policy.to_dict() for policy in ESCALATION_POLICIES],
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/policies/sla")
async def get_sla_policies():
    """Get all SLA policies for live feed display."""
    return {
        "status": "success",
        "policy_type": "service_level_agreement",
        "total_policies": len(SLA_POLICIES),
        "policies": [policy.to_dict() for policy in SLA_POLICIES],
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/policies/sla/{department}")
async def get_sla_by_department(department: str):
    """Get SLA policies for specific department."""
    dept_policies = [p for p in SLA_POLICIES if p.department == department]
    
    if not dept_policies:
        raise HTTPException(status_code=404, detail=f"No SLA policies found for department: {department}")
    
    return {
        "status": "success",
        "department": department,
        "policies": [policy.to_dict() for policy in dept_policies],
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/policies/response-templates")
async def get_response_templates():
    """Get all response templates for live feed display."""
    return {
        "status": "success",
        "policy_type": "response_templates",
        "total_templates": len(RESPONSE_TEMPLATES),
        "templates": [template.to_dict() for template in RESPONSE_TEMPLATES],
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/policies/response-templates/{scenario}")
async def get_template_by_scenario(scenario: str, language: str = "en"):
    """Get response template for specific scenario and language."""
    template = get_response_template(scenario, language)
    
    if not template:
        raise HTTPException(status_code=404, detail=f"No template found for scenario: {scenario} in language: {language}")
    
    return {
        "status": "success",
        "scenario": scenario,
        "language": language,
        "template": template.to_dict(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/policies/department-guidelines")
async def get_department_guidelines():
    """Get all department guidelines for live feed display."""
    return {
        "status": "success",
        "policy_type": "department_guidelines",
        "total_departments": len(DEPARTMENT_GUIDELINES),
        "guidelines": [guideline.to_dict() for guideline in DEPARTMENT_GUIDELINES],
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/policies/department-guidelines/{department}")
async def get_guideline_by_department(department: str):
    """Get guidelines for specific department."""
    guideline = get_department_guideline(department)
    
    if not guideline:
        raise HTTPException(status_code=404, detail=f"No guidelines found for department: {department}")
    
    return {
        "status": "success",
        "department": department,
        "guideline": guideline.to_dict(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/policies/grievance-handling-procedure")
async def get_grievance_procedure():
    """Get complete grievance handling procedure for live feed display."""
    return {
        "status": "success",
        "policy_type": "grievance_handling",
        "procedure": GRIEVANCE_HANDLING_PROCEDURE,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/policies/summary")
async def get_policies_summary():
    """Get summary of all available policies."""
    return {
        "status": "success",
        "summary": {
            "escalation_policies": len(ESCALATION_POLICIES),
            "sla_policies": len(SLA_POLICIES),
            "response_templates": len(RESPONSE_TEMPLATES),
            "department_guidelines": len(DEPARTMENT_GUIDELINES),
            "available_departments": [g.department for g in DEPARTMENT_GUIDELINES],
            "available_scenarios": list(set([t.scenario for t in RESPONSE_TEMPLATES])),
        },
        "endpoints": [
            "/policies/escalation",
            "/policies/sla",
            "/policies/sla/{department}",
            "/policies/response-templates",
            "/policies/response-templates/{scenario}",
            "/policies/department-guidelines",
            "/policies/department-guidelines/{department}",
            "/policies/grievance-handling-procedure",
            "/policies/summary",
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
