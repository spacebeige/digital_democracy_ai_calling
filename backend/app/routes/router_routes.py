"""
FastAPI Integration for SmartRouter — Layer 3 API Endpoints

Endpoints:
    POST /v1/router/route-call       — Route a single voice input
    POST /v1/router/route-call/batch — Batch route (max 100)
    GET  /v1/router/health           — Health check
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
import logging

from app.services.smart_router import (
    SmartRouter,
    VoiceInput,
    RoutingResult,
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


@router.post("/route-call", response_model=RoutingResult)
async def route_call(
    voice_input: VoiceInput,
    smart_router: SmartRouter = Depends(get_router),
) -> RoutingResult:
    """
    Route an incoming voice call through the 3-stage pipeline.

    Accepts the raw STT output and returns structured routing intelligence.
    """
    try:
        return await smart_router.process(voice_input)

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
        "mode": "mock" if smart_router._use_mock else "real",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
