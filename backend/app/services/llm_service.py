import asyncio
import logging
import requests
import time
from uuid import uuid4
from app.config import LLM_API, SARVAM_API_KEY
from app.services.smart_router import SmartRouter, VoiceInput

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 20
MAX_RETRIES = 2

# Initialise a local SmartRouter for "The Brain" logic
_local_router = SmartRouter(
    sarvam_api_key=SARVAM_API_KEY,
    use_mock=(SARVAM_API_KEY is None),
)

def _post_with_retry(url: str, payload: dict) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt == MAX_RETRIES:
                break
            time.sleep(0.4 * (attempt + 1))

    raise RuntimeError(f"LLM request failed after retries: {last_error}")

def process_query(query: str):
    """
    Process a citizen query using "The Brain" (Layer 3).
    
    First tries the external LLM API (if reachable), otherwise falls back
    to the new Layer 3 SmartRouter logic.
    """
    # 1. Try external API
    try:
        payload = {"query": query}
        response = _post_with_retry(f"{LLM_API}/generate", payload)
        return response.json()
    except Exception as exc:
        logger.warning("External LLM API (port 9002) is offline or failed: %s. Falling back to Layer 3 SmartRouter.", exc)

    # 2. Fallback to Layer 3: SmartRouter ("The Brain")
    voice_input = VoiceInput(
        session_id=uuid4(),
        transcript=query,
        language_code="hi-IN",
        stt_confidence=1.0,
    )
    
    # Run the async router logic in a sync-compatible way
    try:
        # Check if an event loop is already running
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We are in an async context (e.g. called from an 'async def')
                # Since process_query is sync, we can't easily await here without blocking
                # but in FastAPI sync routes run in threads, so a new loop is fine.
                pass
        except Exception:
            pass
            
        result = asyncio.run(_local_router.process(voice_input))
    except Exception as exc:
        logger.error("SmartRouter fallback failed: %s", exc)
        # Final emergency fallback to a very simple response
        return {
            "response_text": f"Grievance recorded: {query}",
            "department": "general",
            "status": "partial_success"
        }

    # Map SmartRouter output to the schema expected by call_routes.py and complaint_routes.py
    return {
        "response_text": result.routing_data.summary,
        "department": result.routing_data.dept_id,
        "action": result.action.value,
        "is_emergency": result.is_emergency,
        "audit_log": result.audit_log,
        "status": "processed"
    }