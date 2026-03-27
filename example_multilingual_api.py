#!/usr/bin/env python3
"""
Integration Example: Sentence-Level Multilingual API Endpoint
==============================================================

Shows how to integrate the new sentence-level language detection
into the FastAPI grievance processing system.

Complete flow:
  1. Receive transcript (voice or text)
  2. Detect language at sentence level using Sarvam
  3. Route each sentence independently
  4. Synthesize TTS per-sentence with correct language
  5. Return comprehensive multilingual response
"""

import sys
import os
from typing import Optional, Dict, List
from datetime import datetime
import asyncio

sys.path.insert(0, '/Users/ashwinagarkhed/integration1')
sys.path.insert(0, '/Users/ashwinagarkhed/integration1/awaaz')

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import uuid4

# Import multilingual system
try:
    from awaaz.src.pipeline.stt import STTProcessor
    from awaaz.src.pipeline.multilingual_predictions import (
        get_multilingual_predictions,
        apply_per_sentence_routing,
        consolidate_predictions,
        format_for_response
    )
    from analytics.analytical_model import create_processor
    from models.grievance_models import create_session_id
except ImportError as e:
    print(f"Import error: {e}")

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────────────

class MultilingualGrievanceRequest(BaseModel):
    """Request for multilingual grievance processing."""
    transcript: str
    language: Optional[str] = "auto"  # Will detect via sentence-level
    state: str = "maharashtra"
    user_id: Optional[str] = None
    user_phone: Optional[str] = None
    auto_detect_per_sentence: bool = True  # NEW: Enable sentence-level detection


class SegmentAnalysis(BaseModel):
    """Analysis for a single text segment."""
    segment_text: str
    language: str
    confidence: float
    intent: str
    urgency: str
    department: Optional[str]


class MultilingualGrievanceResponse(BaseModel):
    """Response for multilingual grievance processing."""
    session_id: str
    status: str
    multilingual_info: Dict  # Sentence-level language info
    segments: List[SegmentAnalysis]  # Per-segment analysis
    consolidated: Dict  # Unified analysis
    is_code_switched: bool
    languages_involved: List[str]
    timestamp: str


# ─────────────────────────────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────────────────────────────

# Initialize processors
processor = None
stt_processor = None

async def init_processors():
    """Initialize processors on startup."""
    global processor, stt_processor
    logger.info("Initializing processors...")
    
    try:
        processor = create_processor(use_groq=False)
        logger.info("✓ Grievance processor initialized")
    except Exception as e:
        logger.error(f"Grievance processor init failed: {e}")
    
    try:
        stt_processor = STTProcessor(preferred_provider="groq_whisper")
        await stt_processor.load()
        logger.info("✓ STT processor initialized")
    except Exception as e:
        logger.error(f"STT processor init failed: {e}")


app = FastAPI(
    title="Multilingual Grievance System with Sentence-Level Detection",
    description="Process grievances in multiple languages with per-sentence language codes",
    version="3.0.0"
)


@app.on_event("startup")
async def startup():
    """Initialize on startup."""
    await init_processors()


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "sentence_level_detection": True,
            "code_switching_support": True,
            "per_segment_routing": True,
            "sarvam_integration": True,
        }
    }


@app.post("/grievance/multilingual/process")
async def process_multilingual_grievance(
    request: MultilingualGrievanceRequest
) -> MultilingualGrievanceResponse:
    """
    Process grievance with sentence-level multilingual language detection.
    
    Features:
      • Detects language per sentence using Sarvam
      • Handles code-switching automatically
      • Routes each segment independently
      • Returns per-segment and consolidated analysis
    
    Example Request:
      {
        "transcript": "नमस्ते। I need help with water. मुझे बिजली का बिल भी जमा करना है।",
        "state": "maharashtra",
        "auto_detect_per_sentence": true
      }
    
    Example Response:
      {
        "session_id": "session-123",
        "is_code_switched": true,
        "languages_involved": ["hi", "en"],
        "segments": [
          {
            "segment_text": "नमस्ते",
            "language": "hi",
            "confidence": 0.92,
            "intent": "greeting",
            "urgency": "LOW"
          },
          ...
        ],
        "consolidated": {
          "primary_intent": "grievance_filing",
          "primary_urgency": "MEDIUM"
        }
      }
    """
    try:
        session_id = create_session_id()
        logger.info(f"[{session_id}] Processing multilingual grievance")
        
        # ─────────────────────────────────────────────────────────────
        # STEP 1: Get sentence-level language predictions
        # ─────────────────────────────────────────────────────────────
        logger.info(f"[{session_id}] Step 1: Getting per-sentence language predictions")
        
        predictions = await get_multilingual_predictions(
            transcript=request.transcript,
            stt_processor=stt_processor,
            fallback_language="hi"
        )
        
        if 'error' in predictions:
            logger.warning(f"[{session_id}] Prediction error: {predictions['error']}")
        
        logger.info(
            f"[{session_id}] ✓ Detected {len(predictions['segments'])} segments, "
            f"primary={predictions['primary_language']}, "
            f"code_switched={predictions['is_code_switched']}"
        )
        
        # ─────────────────────────────────────────────────────────────
        # STEP 2: Route and analyze each segment
        # ─────────────────────────────────────────────────────────────
        logger.info(f"[{session_id}] Step 2: Routing per-segment analysis")
        
        if not processor:
            raise HTTPException(
                status_code=500,
                detail="Grievance processor not initialized"
            )
        
        routing_results = await apply_per_sentence_routing(
            predictions,
            processor,
            state=request.state
        )
        
        logger.info(
            f"[{session_id}] ✓ Analyzed {len(routing_results)} segments"
        )
        
        # ─────────────────────────────────────────────────────────────
        # STEP 3: Consolidate findings
        # ─────────────────────────────────────────────────────────────
        logger.info(f"[{session_id}] Step 3: Consolidating analysis")
        
        consolidated = consolidate_predictions(
            routing_results,
            primary_language=predictions['primary_language']
        )
        
        logger.info(
            f"[{session_id}] ✓ Consolidated intent={consolidated['consolidated_intent']}, "
            f"urgency={consolidated['consolidated_urgency']}"
        )
        
        # ─────────────────────────────────────────────────────────────
        # STEP 4: Format segments for response
        # ─────────────────────────────────────────────────────────────
        segments_response = []
        for routing_result in routing_results:
            segment_analysis = SegmentAnalysis(
                segment_text=routing_result.get('segment', ''),
                language=routing_result.get('language', 'unknown'),
                confidence=routing_result.get('confidence', 0.0),
                intent=routing_result.get('intent', 'unknown'),
                urgency=routing_result.get('urgency', 'MEDIUM'),
                department=routing_result.get('routing', {}).get('department')
            )
            segments_response.append(segment_analysis)
        
        # ─────────────────────────────────────────────────────────────
        # STEP 5: Build response
        # ─────────────────────────────────────────────────────────────
        response = MultilingualGrievanceResponse(
            session_id=session_id,
            status="completed",
            multilingual_info={
                "segments": predictions['segments'],
                "primary_language": predictions['primary_language'],
                "primary_confidence": predictions.get('primary_confidence', 0.0),
                "language_distribution": predictions['language_distribution'],
            },
            segments=segments_response,
            consolidated={
                "primary_intent": consolidated['consolidated_intent'],
                "primary_urgency": consolidated['consolidated_urgency'],
                "languages_involved": list(consolidated['language_intent_distribution'].keys()),
                "intents_detected": list(consolidated['all_intents']),
            },
            is_code_switched=predictions['is_code_switched'],
            languages_involved=list(predictions['language_distribution'].keys()),
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(
            f"[{session_id}] ✓ COMPLETE: "
            f"intent={response.consolidated['primary_intent']}, "
            f"languages={response.languages_involved}"
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing multilingual grievance: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )


@app.get("/languages/distribution")
async def get_language_distribution(
    transcript: str
) -> Dict:
    """
    Get language distribution in a transcript without full processing.
    
    Useful for:
      • Understanding which languages are in the transcript
      • Checking if code-switching is present
      • Previewing segmentation before full analysis
    """
    try:
        predictions = await get_multilingual_predictions(transcript)
        
        return {
            "primary_language": predictions['primary_language'],
            "is_code_switched": predictions['is_code_switched'],
            "language_distribution": predictions['language_distribution'],
            "segment_count": len(predictions['segments']),
            "segments_preview": [
                {
                    "text": seg['text'][:50] + ("..." if len(seg['text']) > 50 else ""),
                    "language": seg['language'],
                    "confidence": seg['confidence']
                }
                for seg in predictions['segments'][:10]  # First 10 segments
            ]
        }
    
    except Exception as e:
        logger.error(f"Error getting language distribution: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/analyze/per-segment")
async def analyze_per_segment(
    request: MultilingualGrievanceRequest
) -> Dict:
    """
    Detailed per-segment analysis without consolidation.
    
    Returns:
      List of analyses, one per segment, with full details.
    """
    try:
        predictions = await get_multilingual_predictions(request.transcript)
        routing_results = await apply_per_sentence_routing(
            predictions,
            processor,
            state=request.state
        )
        
        return {
            "session_id": create_session_id(),
            "total_segments": len(routing_results),
            "segments": routing_results,
            "languages": list(predictions['language_distribution'].keys()),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in per-segment analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ─────────────────────────────────────────────────────────────────────
# Demo/Testing
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    # Example usage
    logger.info("Starting Multilingual Grievance Processing Server...")
    logger.info("Features enabled:")
    logger.info("  ✓ Sentence-level language detection (Sarvam)")
    logger.info("  ✓ Code-switching support")
    logger.info("  ✓ Per-segment routing and analysis")
    logger.info("  ✓ Consolidated multilingual response")
    logger.info("")
    logger.info("Test endpoint:")
    logger.info("  POST http://localhost:8000/grievance/multilingual/process")
    logger.info("")
    logger.info("Example request:")
    logger.info("""{
  "transcript": "नमस्ते। I have a water problem. मुझे बिजली का बिल जमा करना है।",
  "state": "maharashtra",
  "auto_detect_per_sentence": true
}""")
    logger.info("")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
