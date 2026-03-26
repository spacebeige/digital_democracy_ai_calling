"""
FastAPI Integration for SmartRouter — Layer 3 API Endpoints

Endpoints:
    POST /v1/router/route-call       — Route a single voice input (simplified)
    POST /v1/router/route-call/batch — Batch route (max 100)
    GET  /v1/router/health           — Health check
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
import logging

from app.services.smart_router import (
    SmartRouter,
    VoiceInput,
    RoutingResult,
    DEPT_MAPPING,
)
from app.schemas import (
    SimpleRouterRequest,
    SimpleRouterResponse,
    DepartmentRoutingInfo,
)
from app.config import SARVAM_API_KEY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/router", tags=["smart_router"])

# Lazy singleton
_router_instance: Optional[SmartRouter] = None


def get_router() -> SmartRouter:
    """Dependency injection for SmartRouter."""
    global _router_instance
    if _router_instance is None:
        _router_instance = SmartRouter(
            sarvam_api_key=SARVAM_API_KEY,
            use_mock=(SARVAM_API_KEY is None),
        )
        logger.info(
            "SmartRouter initialised (mock=%s)", SARVAM_API_KEY is None
        )
    return _router_instance


def _routing_result_to_simple_response(
    result: RoutingResult,
    transcript: str,
    language: str,
    intent: str,
    issue_category: str,
) -> SimpleRouterResponse:
    """Convert RoutingResult to user-friendly SimpleRouterResponse."""
    dept_info = DEPT_MAPPING.get(result.routing_data.dept_id, {})
    dept_name = dept_info.get("name", "Unknown Department")
    
    return SimpleRouterResponse(
        session_id=str(result.session_id),
        transcript=transcript,
        language=language,
        intent=intent,
        issue_category=issue_category,
        department=DepartmentRoutingInfo(
            dept_id=result.routing_data.dept_id,
            dept_name=dept_name,
            priority=result.routing_data.priority,
        ),
        urgency=result.routing_data.priority,
        is_emergency=result.is_emergency,
        action=result.action.value,
        summary=result.routing_data.summary,
        confidence=result.confidence,
        processing_time_ms=result.processing_time_ms,
    )


@router.post("/route-call", response_model=SimpleRouterResponse)
async def route_call(
    request: SimpleRouterRequest,
    smart_router: SmartRouter = Depends(get_router),
) -> SimpleRouterResponse:
    """
    Route an incoming voice call through the intelligent NLP + routing pipeline.
    
    **What you provide:**
    - `session_id`: Unique identifier for this call (optional, auto-generated if not provided)
    - `transcript`: User's complaint or query (the only manual input)
    
    **What the system auto-detects:**
    - Language (Hindi, English, Hinglish, Tamil, etc.)
    - Intent (NEW_COMPLAINT, STATUS_QUERY, FEEDBACK, etc.)
    - Issue category (Water, Electricity, Road, Waste, Health, Education)
    - Department routing (PWD, Water Board, Health Ministry, etc.)
    - Urgency level (1-5)
    - Emergency detection
    
    **Returns:**
    - Detected language and intent
    - Automatically routed department
    - Action to take (CREATE_TICKET, TRANSFER_HUMAN, etc.)
    - Processing summary
    """
    try:
        # Generate session_id if not provided
        session_id = request.session_id if request.session_id != "auto" else str(uuid4())
        
        # Convert to VoiceInput (internally only has session_id and transcript)
        voice_input = VoiceInput(
            session_id=session_id,  # Can be string or UUID
            transcript=request.transcript,
        )
        
        # Process through NLP + routing
        routing_result = await smart_router.process(voice_input)
        
        # All auto-detected information is now in routing_result
        language = routing_result.language
        intent = routing_result.intent
        issue_category = routing_result.issue_category
        
        # Convert to SimpleRouterResponse
        return _routing_result_to_simple_response(
            routing_result,
            request.transcript,
            language,
            intent,
            issue_category,
        )

    except ValueError as exc:
        logger.warning("Validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {exc}",
        )
    except RuntimeError as exc:
        logger.error("LLM processing error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service unavailable. Please retry.",
        )
    except Exception as exc:
        logger.error("Unexpected error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error.",
        )


@router.post("/route-call/batch")
async def batch_route_calls(
    inputs: list[VoiceInput],
    smart_router: SmartRouter = Depends(get_router),
) -> dict:
    """Batch-route up to 100 voice inputs."""
    if len(inputs) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size cannot exceed 100",
        )

    results, failures = [], []
    for vi in inputs:
        try:
            r = await smart_router.process(vi)
            results.append(r.model_dump(mode="json"))
        except Exception as exc:
            logger.error("Batch item %s failed: %s", vi.session_id, exc)
            failures.append({"session_id": str(vi.session_id), "error": str(exc)})

    return {
        "processed": len(inputs),
        "succeeded": len(results),
        "failed": len(failures),
        "results": results,
        "failed_sessions": failures,
    }


@router.get("/health")
async def health_check(
    smart_router: SmartRouter = Depends(get_router),
) -> dict:
    """Health-check for the SmartRouter service."""
    return {
        "status": "healthy",
        "service": "smart_router",
        "mode": "mock" if SARVAM_API_KEY is None else "real",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
