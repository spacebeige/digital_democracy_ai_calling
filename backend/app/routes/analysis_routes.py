"""
Post-Call Analysis Routes
=========================

API endpoints for post-call analysis and results retrieval.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.post_call_analyzer import (
    PostCallAnalyzer,
    PostCallAnalysisInput,
    CallMetadata,
    TranscriptSegment,
    PostCallAnalysisOutput,
    ActionRequired,
)

router = APIRouter(prefix="/api/v1/analysis", tags=["post_call_analysis"])

# Initialize analyzer
analyzer = PostCallAnalyzer()


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════


class AnalyzeCallRequest(BaseModel):
    """Request schema for post-call analysis."""
    call_id: str = Field(..., description="Unique call identifier")
    session_id: str = Field(..., description="Session ID")
    transcript: str = Field(..., description="Full call transcript")
    call_duration_seconds: float = Field(..., description="Call duration")
    caller_phone: Optional[str] = Field(None, description="Caller's phone")
    detected_language: Optional[str] = Field(None, description="Pre-detected language")


class AnalyzeCallResponse(BaseModel):
    """Response schema for post-call analysis."""
    success: bool
    analysis_id: str
    status: str
    classification: dict
    routing: dict
    summary: str
    is_emergency: bool
    is_abuse: bool
    is_genuine_complaint: bool
    suggested_action: str
    processing_time_ms: float


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/analyze-call", response_model=AnalyzeCallResponse)
async def analyze_call(request: AnalyzeCallRequest):
    """
    Analyze a completed call.
    
    Flow:
    1. Takes the full transcript
    2. Detects language and intent
    3. Routes to appropriate department
    4. Determines required action
    
    Returns structured analysis for storage/action.
    """
    try:
        # Build metadata
        call_metadata = CallMetadata(
            call_id=request.call_id,
            session_id=request.session_id,
            caller_phone=request.caller_phone,
            call_start_time=datetime.utcnow(),  # Would come from actual call data
            call_end_time=datetime.utcnow(),
            call_duration_seconds=request.call_duration_seconds,
        )

        # Build analysis input
        analysis_input = PostCallAnalysisInput(
            call_metadata=call_metadata,
            full_transcript=request.transcript,
            detected_language=request.detected_language,
        )

        # Run analysis
        result = await analyzer.analyze(analysis_input)

        # Format response
        return AnalyzeCallResponse(
            success=True,
            analysis_id=result.analysis_id,
            status=result.status.value,
            classification={
                "language": result.classification.language,
                "intent": result.classification.intent,
                "edge_case": result.classification.edge_case,
                "confidence": result.classification.confidence,
            },
            routing={
                "department_id": result.routing.department_id,
                "department_name": result.routing.department_name,
                "issue_category": result.routing.issue_category,
                "priority_level": result.routing.priority_level,
            },
            summary=result.summary,
            is_emergency=result.is_emergency,
            is_abuse=result.is_abuse,
            is_genuine_complaint=result.is_genuine_complaint,
            suggested_action=result.routing.suggested_action.value,
            processing_time_ms=result.processing_time_ms,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.post("/batch-analyze")
async def batch_analyze_calls(requests: list[AnalyzeCallRequest]):
    """
    Analyze multiple calls in batch.
    
    Returns list of analysis results.
    """
    results = []
    for request in requests:
        try:
            result = await analyze_call(request)
            results.append(result)
        except HTTPException as e:
            results.append({
                "success": False,
                "call_id": request.call_id,
                "error": e.detail,
            })
    
    return {"successful": len([r for r in results if r.get("success", False)]),"results": results}


@router.get("/health")
async def health_check():
    """Health check for analysis service."""
    return {
        "status": "healthy",
        "service": "post-call-analyzer",
        "version": "1.0.0",
    }
