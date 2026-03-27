"""
Enhanced Grievance API with Vulgarity Detection, State Schemes, and Better AI Summaries
FastAPI endpoints integrating all enhanced services.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.services.enhanced_summary_service import (
    EnhancedAISummaryService,
    EnhancedSummary,
    SummaryStyle,
    UrgencyLevel,
)
from backend.app.services.state_schemes_service import (
    SchemeCategory,
    StateSchemesService,
)
from backend.app.services.vulgarity_handler import VulgarityHandler, VulgarityResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/enhanced", tags=["Enhanced Grievance"])

# Initialize services
vulgarity_handler = VulgarityHandler()
summary_service = EnhancedAISummaryService(enable_cache=True)
schemes_service = StateSchemesService(enable_grok=False)  # Set to True to enable Grok


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════


class ComplaintRequest(BaseModel):
    """Enhanced complaint request with all features."""
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    transcript: str = Field(..., description="Complaint text from STT")
    language: str = Field(default="en", description="Detected language code")
    category: Optional[str] = Field(default="General", description="Complaint category")


class ComplaintResponse(BaseModel):
    """Enhanced complaint response."""
    session_id: str
    vulgarity_check: VulgarityResponse
    summary: EnhancedSummary
    state_schemes: Optional[List[Dict]] = None
    should_continue: bool = Field(..., description="Whether to continue conversation")
    response_message: Dict[str, str] = Field(..., description="Language-specific response")
    warning_count: int = 0


class SchemeQueryRequest(BaseModel):
    """Request for state-specific schemes."""
    state_identifier: str = Field(..., description="State name or code (e.g., 'Maharashtra', 'MH')")
    category: Optional[SchemeCategory] = None
    language: str = Field(default="en")


class SchemeQueryResponse(BaseModel):
    """Response with state schemes."""
    state_code: str
    state_name: str
    schemes: List[Dict]
    formatted_response: str
    total_schemes: int


class VulgarityCheckRequest(BaseModel):
    """Request for vulgarity check only."""
    text: str
    language: str = Field(default="en")
    session_id: Optional[str] = None


class SummaryRequest(BaseModel):
    """Request for AI summary generation."""
    text: str
    category: str = Field(default="General")
    language: str = Field(default="en")
    style: SummaryStyle = Field(default=SummaryStyle.CONCISE)


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/process-complaint", response_model=ComplaintResponse)
async def process_complaint(request: ComplaintRequest):
    """
    Process complaint with vulgarity detection, AI summary, and state schemes.
    
    This is the main endpoint that integrates all enhanced features:
    - Vulgarity detection with progressive warnings
    - Enhanced AI summarization with urgency detection
    - State-wise scheme recommendations (if state detected)
    
    Flow:
    1. Check for vulgarity -> warn/terminate if detected
    2. Generate enhanced AI summary with urgency
    3. Detect state and provide relevant schemes
    4. Return integrated response
    """
    try:
        # Step 1: Vulgarity Check
        vulgarity_check = vulgarity_handler.detect_vulgarity(
            text=request.transcript,
            language=request.language,
            session_id=request.session_id
        )
        
        # If service should terminate, return immediately
        if vulgarity_check.should_terminate:
            logger.warning(f"Session {request.session_id} terminated due to vulgarity")
            return ComplaintResponse(
                session_id=request.session_id,
                vulgarity_check=vulgarity_check,
                summary=EnhancedSummary(
                    original_text=request.transcript,
                    summary="Service terminated",
                    urgency=UrgencyLevel.INFORMATIONAL,
                    urgency_score=0.0,
                    category="Terminated",
                    requires_immediate_action=False,
                    suggested_response_time="N/A"
                ),
                state_schemes=None,
                should_continue=False,
                response_message=vulgarity_check.response_message,
                warning_count=vulgarity_check.warning_count
            )
        
        # Step 2: Generate Enhanced Summary (only if not vulgar or first warning)
        summary = summary_service.generate_summary(
            text=request.transcript,
            category=request.category,
            language=request.language,
            style=SummaryStyle.CONCISE
        )
        
        # Step 3: Detect State and Get Schemes
        state_schemes = None
        detected_state = schemes_service.detect_state_from_text(request.transcript)
        
        if detected_state:
            logger.info(f"Detected state: {detected_state} for session {request.session_id}")
            try:
                # Get category-specific schemes
                category_map = {
                    "Water": SchemeCategory.WATER,
                    "Electricity": SchemeCategory.ELECTRICITY,
                    "Road": SchemeCategory.ROAD,
                    "Sanitation": SchemeCategory.SANITATION,
                    "Health": SchemeCategory.HEALTH,
                    "Education": SchemeCategory.EDUCATION
                }
                
                scheme_category = category_map.get(request.category)
                schemes = await schemes_service.get_schemes_for_state(
                    state_code=detected_state,
                    category=scheme_category
                )
                
                state_schemes = [
                    {
                        "name": s.name,
                        "name_local": s.name_local,
                        "category": s.category.value,
                        "description": s.description,
                        "contact_number": s.contact_number,
                        "website": s.website
                    }
                    for s in schemes[:3]  # Limit to top 3 schemes
                ]
            except Exception as e:
                logger.error(f"Error fetching schemes: {e}")
        
        # Step 4: Generate Response Message
        response_message = _generate_response_message(
            vulgarity_detected=vulgarity_check.detected,
            vulgarity_response=vulgarity_check.response_message,
            summary=summary,
            has_schemes=state_schemes is not None and len(state_schemes) > 0,
            language=request.language
        )
        
        return ComplaintResponse(
            session_id=request.session_id,
            vulgarity_check=vulgarity_check,
            summary=summary,
            state_schemes=state_schemes,
            should_continue=not vulgarity_check.should_terminate,
            response_message=response_message,
            warning_count=vulgarity_check.warning_count
        )
    
    except Exception as e:
        logger.error(f"Error processing complaint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing complaint: {str(e)}")


@router.post("/check-vulgarity", response_model=VulgarityResponse)
async def check_vulgarity(request: VulgarityCheckRequest):
    """
    Check text for vulgarity and get warning status.
    
    Standalone endpoint for vulgarity detection without full complaint processing.
    """
    try:
        result = vulgarity_handler.detect_vulgarity(
            text=request.text,
            language=request.language,
            session_id=request.session_id
        )
        return result
    except Exception as e:
        logger.error(f"Error checking vulgarity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-summary", response_model=EnhancedSummary)
async def generate_summary(request: SummaryRequest):
    """
    Generate enhanced AI summary with urgency detection.
    
    Standalone endpoint for summary generation.
    """
    try:
        summary = summary_service.generate_summary(
            text=request.text,
            category=request.category,
            language=request.language,
            style=request.style
        )
        return summary
    except Exception as e:
        logger.error(f"Error generating summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get-state-schemes", response_model=SchemeQueryResponse)
async def get_state_schemes(request: SchemeQueryRequest):
    """
    Get government schemes for a specific state.
    
    Supports:
    - State code (e.g., "MH", "DL")
    - State name (e.g., "Maharashtra", "Delhi")
    - State name in local language (e.g., "महाराष्ट्र")
    - Optional category filtering
    """
    try:
        # Detect state code from identifier
        state_code = schemes_service.detect_state_from_text(request.state_identifier)
        
        if not state_code:
            # Try direct state code
            state_code = request.state_identifier.upper()
            if state_code not in [s.value for s in schemes_service.state_name_mappings.keys()]:
                raise HTTPException(
                    status_code=404,
                    detail=f"Could not identify state from: {request.state_identifier}"
                )
        
        # Get schemes
        schemes = await schemes_service.get_schemes_for_state(
            state_code=state_code,
            category=request.category
        )
        
        # Format response
        formatted_response = schemes_service.format_schemes_for_response(
            schemes=schemes,
            language=request.language,
            max_schemes=5
        )
        
        return SchemeQueryResponse(
            state_code=state_code,
            state_name=state_code,  # Could be enhanced with full name mapping
            schemes=[
                {
                    "name": s.name,
                    "name_local": s.name_local,
                    "category": s.category.value,
                    "description": s.description,
                    "eligibility": s.eligibility,
                    "contact_number": s.contact_number,
                    "website": s.website
                }
                for s in schemes
            ],
            formatted_response=formatted_response,
            total_schemes=len(schemes)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting state schemes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session-status/{session_id}")
async def get_session_status(session_id: str):
    """
    Get current warning status for a session.
    
    Returns warning count, warnings remaining, and termination status.
    """
    try:
        status = vulgarity_handler.get_session_status(session_id)
        return status
    except Exception as e:
        logger.error(f"Error getting session status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-warnings/{session_id}")
async def reset_session_warnings(session_id: str):
    """
    Reset warning count for a session.
    
    Use this when a complaint is successfully resolved and user has been cooperative.
    """
    try:
        vulgarity_handler.reset_session_warnings(session_id)
        return {"message": f"Warnings reset for session {session_id}", "session_id": session_id}
    except Exception as e:
        logger.error(f"Error resetting warnings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Enhanced Grievance API",
        "features": [
            "vulgarity_detection",
            "ai_summary",
            "state_schemes",
            "urgency_detection",
            "multilingual_support"
        ],
        "timestamp": datetime.now().isoformat()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


def _generate_response_message(
    vulgarity_detected: bool,
    vulgarity_response: Dict[str, str],
    summary: EnhancedSummary,
    has_schemes: bool,
    language: str
) -> Dict[str, str]:
    """Generate appropriate response message based on analysis."""
    
    if vulgarity_detected:
        # Return vulgarity warning message
        return vulgarity_response
    
    # Generate normal response based on summary
    if language == "hi":
        base_msg = f"आपकी शिकायत दर्ज की गई है। {summary.summary}। "
        
        if summary.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
            base_msg += "यह उच्च प्राथमिकता का मामला है और जल्द ही संबोधित किया जाएगा। "
        
        if has_schemes:
            base_msg += "आपके क्षेत्र के लिए सरकारी योजनाएं उपलब्ध हैं। "
        
        return {
            "hi": base_msg,
            "en": f"Your complaint has been registered. {summary.summary}."
        }
    else:
        base_msg = f"Your complaint has been registered. {summary.summary}. "
        
        if summary.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
            base_msg += "This is a high priority matter and will be addressed soon. "
        
        if has_schemes:
            base_msg += "Relevant government schemes are available for your area. "
        
        return {
            "en": base_msg,
            "hi": f"आपकी शिकायत दर्ज की गई है। {summary.summary}।"
        }
