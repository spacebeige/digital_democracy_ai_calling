"""
Layer 3 Call Router - Integration & Deployment Guide

This document provides step-by-step instructions to integrate
the call router into your existing backend.
"""

# =============================================================================
# INTEGRATION STEPS
# =============================================================================

"""
STEP 1: Update Dependencies
============================

File: backend/requirements.txt

Add these lines (if not already present):
    requests>=2.28.0
    pydantic>=2.0.0
    python-dotenv>=0.21.0

Then run:
    cd backend
    pip install -r requirements.txt
"""

# =============================================================================

"""
STEP 2: Environment Configuration
==================================

File: backend/.env (create if not exists)

Add configuration:

    # Layer 3: Call Router
    SARVAM_API_KEY=your_api_key_from_sarvam_ai
    SARVAM_API_ENDPOINT=https://api.sarvam.ai/classify
    SARVAM_TIMEOUT=10
    SARVAM_MAX_RETRIES=3

For development, you can leave SARVAM_API_KEY empty to use mock client.
"""

# =============================================================================

"""
STEP 3: Update Main Application
================================

File: backend/app/main.py

The main.py has already been updated to include router routes.
Verify it contains:

    from app.routes.router_routes import router as router_router
    ...
    app.include_router(router_router)
"""

# =============================================================================

"""
STEP 4: Integration in Your Workflow
=====================================

A. Direct Python Usage (within backend services):

    from app.services.call_router import CallRouter, RouterInput
    
    def handle_stt_output(session_id: str, transcript: str, language: str):
        '''Called after STT converts audio to text'''
        
        router = CallRouter(use_mock=False)
        
        routing_decision = router.process_call(RouterInput(
            session_id=session_id,
            transcription_text=transcript,
            language_code=language,
        ))
        
        # Use routing decision to:
        # 1. Store in database with complaint
        # 2. Trigger department-specific response
        # 3. Set priority in queue
        # 4. Select appropriate response template
        
        return routing_decision


B. Via FastAPI (HTTP calls):

    Call the /v1/router/route-call endpoint from your frontend or 
    other services:
    
    POST /v1/router/route-call
    {
        "session_id": "call_12345",
        "transcription_text": "Water leak in my building",
        "language_code": "en"
    }
    
    Returns routing decision as JSON.


C. Batch Processing (for analytics):

    POST /v1/router/route-call/batch
    [
        {"session_id": "call_1", "transcription_text": "...", "language_code": "en"},
        {"session_id": "call_2", "transcription_text": "...", "language_code": "hi"},
        ...
    ]
"""

# =============================================================================

"""
STEP 5: Connect to Existing Systems
====================================

A. Store Routing Decisions in Database:

    from app.models import Complaint
    from app.services.call_router import CallRouter, RouterInput
    from app.database import SessionLocal
    
    def process_call_with_db(session_id, transcript, language):
        router = CallRouter(use_mock=False)
        
        routing_result = router.process_call(RouterInput(
            session_id=session_id,
            transcription_text=transcript,
            language_code=language,
        ))
        
        # Store in database
        db = SessionLocal()
        complaint = Complaint(
            phone_number="...",  # from session
            issue=routing_result.summary,
            department=routing_result.department_name,
            status="pending" if routing_result.urgency != "EMERGENCY" else "urgent",
        )
        db.add(complaint)
        db.commit()
        
        return routing_result


B. Trigger TTS Response:

    from app.services.router import route_call
    from app.services.tts_service import synthesis_speech
    
    async def handle_call(transcript: str):
        # Route the call
        routing_decision = route_call("call_123", transcript, "hi")
        
        # Generate appropriate response based on result
        if routing_decision.is_emergency:
            response_text = "Immediate assistance being provided."
        elif routing_decision.intent == IntentType.COMPLAINT:
            response_text = f"Your complaint about {routing_decision.entities.problem} "
                           f"has been registered with {routing_decision.department_name}."
        else:
            response_text = "Please provide more details."
        
        # Convert to speech
        audio_response = synthesis_speech(response_text)
        return audio_response


C. Log to Analytics:

    from app.services.call_router import route_call
    import logging
    
    logger = logging.getLogger(__name__)
    
    def track_routing_decision(routing_result):
        logger.info({
            "event": "call_routed",
            "session_id": routing_result.session_id,
            "department": routing_result.dept_id,
            "intent": routing_result.intent,
            "urgency": routing_result.urgency,
            "confidence": routing_result.confidence_score,
            "processing_time_ms": routing_result.processing_time_ms,
            "is_emergency": routing_result.is_emergency,
        })
"""

# =============================================================================

"""
STEP 6: Testing Your Integration
=================================

A. Unit Tests:

    cd backend
    pytest app/services/tests/test_call_router.py -v


B. Manual Testing:

    # Start the backend
    cd backend
    uvicorn app.main:app --reload
    
    # In another terminal, test the endpoint
    curl -X POST http://localhost:8000/v1/router/route-call \
      -H "Content-Type: application/json" \
      -d '{
        "session_id": "test_001",
        "transcription_text": "There is a water leak in my apartment",
        "language_code": "en"
      }'
    
    # Or test with mock in Python
    from app.services.call_router import route_call
    
    result = route_call(
        session_id="test_001",
        text="Where is the nearest health clinic?",
        language_code="en"
    )
    print(result.dict())
"""

# =============================================================================

"""
STEP 7: Production Configuration
=================================

Before deploying to production:

1. Set SARVAM_API_KEY in production environment:
   docker run -e SARVAM_API_KEY=your_key ...
   
   OR on cloud platform (AWS, GCP, etc.):
   - Set environment variable in deployment config
   - Use secrets manager for security

2. Configure logging:
   backend/app/config.py or via environment

3. Set up monitoring:
   - Monitor /v1/router/health endpoint
   - Track routing accuracy metrics
   - Alert on LLM failures

4. Load testing:
   ab -n 1000 -c 10 http://your-backend/v1/router/health
   
   Or use locust for more realistic testing:
   locust -f locustfile.py --host=http://localhost:8000

5. Documentation:
   - Document department mappings for your region
   - List supported languages
   - Document SLAs for routing
"""

# =============================================================================

"""
STEP 8: Monitoring & Debugging
===============================

Monitor these metrics:

1. Confidence Scores:
   - Track avg confidence by department
   - Alert if avg < 0.6
   
2. Processing Time:
   - Track p50, p95, p99 latencies
   - Alert if p95 > 1000ms
   
3. Error Rates:
   - LLM failures (503 errors)
   - Validation errors (400)
   - Timeouts
   
4. Department Distribution:
   - Track calls routed to each dept
   - Detect anomalies in distribution

Debug by:

1. Enable debug logging:
   import logging
   logging.basicConfig(level=logging.DEBUG)

2. Check raw transcripts:
   result.raw_transcript

3. Inspect entities:
   result.entities.dict()

4. Test with mock client:
   router = CallRouter(use_mock=True)
"""

# =============================================================================

"""
STEP 9: Customization Examples
===============================

A. Add custom department:

    from app.services.call_router import DEPARTMENT_REGISTRY
    
    DEPARTMENT_REGISTRY["DEPT_CIVIC_001"] = {
        "name": "Civic Infrastructure",
        "keywords": ["bridge", "tunnel", "sidewalk", "पुल"],
        "aliases": ["CIVIC", "INFRASTRUCTURE"],
    }


B. Add custom emergency keywords:

    from app.services.call_router import EMERGENCY_KEYWORDS_PATTERN
    import re
    
    # Extend pattern
    custom_pattern = re.compile(
        r'\b(fire|emergency|ambulance|police|'
        r'flood|earthquake|tsunami|चिंता)\b',
        re.IGNORECASE
    )


C. Custom confidence scoring:

    class CustomCallRouter(CallRouter):
        def _route_to_department(self, text, entities, intent):
            # Your custom logic
            pass
"""

# =============================================================================

"""
STEP 10: Deployment
===================

Docker Deployment Example:

Dockerfile:
    FROM python:3.10-slim
    WORKDIR /app
    COPY backend/requirements.txt .
    RUN pip install -r requirements.txt
    COPY backend/app app
    ENV SARVAM_API_KEY=${SARVAM_API_KEY}
    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]

docker-compose.yml:
    services:
      backend:
        build: .
        ports:
          - "8000:8000"
        environment:
          - SARVAM_API_KEY=${SARVAM_API_KEY}
          - SARVAM_TIMEOUT=10
        depends_on:
          - redis

    volumes:
      - ./backend:/app

Run:
    SARVAM_API_KEY=your_key docker-compose up
"""

# =============================================================================

# CODE INTEGRATION EXAMPLES

# Example 1: Direct Usage in Existing Service
def example_direct_usage():
    """Integrate router directly in your LLM service."""
    from app.services.call_router import CallRouter, RouterInput
    
    router = CallRouter(use_mock=False)
    
    def process_call(session_id: str, transcript: str, language: str):
        result = router.process_call(RouterInput(
            session_id=session_id,
            transcription_text=transcript,
            language_code=language,
        ))
        
        return {
            "session_id": result.session_id,
            "department": result.department_name,
            "urgency": result.urgency.value,
            "summary": result.summary,
        }
    
    return process_call


# Example 2: FastAPI Integration
def example_fastapi_integration():
    """Show how it's integrated in FastAPI."""
    from fastapi import FastAPI, Depends
    from app.routes.router_routes import router as router_router
    
    app = FastAPI()
    app.include_router(router_router)
    
    # Now available at /v1/router/route-call
    return app


# Example 3: Error Handling
def example_error_handling():
    """Show proper error handling."""
    from app.services.call_router import CallRouter, RouterInput
    
    router = CallRouter(use_mock=False)
    
    def safe_process_call(session_id: str, transcript: str):
        try:
            result = router.process_call(RouterInput(
                session_id=session_id,
                transcription_text=transcript,
                language_code="en",
            ))
            return {"success": True, "result": result.dict()}
        
        except ValueError as e:
            # Input validation failed
            return {"success": False, "error": "invalid_input", "details": str(e)}
        
        except RuntimeError as e:
            # LLM processing failed
            return {"success": False, "error": "llm_failed", "details": str(e)}
        
        except Exception as e:
            # Unexpected error
            return {"success": False, "error": "internal_error", "details": str(e)}
    
    return safe_process_call


# Example 4: Logging & Metrics
def example_logging_metrics():
    """Show logging and metrics collection."""
    from app.services.call_router import route_call
    import logging
    import time
    
    logger = logging.getLogger(__name__)
    metrics = {
        "total_calls": 0,
        "emergency_calls": 0,
        "avg_confidence": 0.0,
        "avg_latency_ms": 0.0,
    }
    
    def process_with_metrics(session_id: str, transcript: str):
        start_time = time.time()
        
        result = route_call(session_id, transcript)
        
        latency = (time.time() - start_time) * 1000
        
        # Update metrics
        metrics["total_calls"] += 1
        if result.is_emergency:
            metrics["emergency_calls"] += 1
        
        # Log routing decision
        logger.info({
            "event": "call_routed",
            "session_id": session_id,
            "department": result.dept_id,
            "urgency": result.urgency.value,
            "confidence": result.confidence_score,
            "latency_ms": latency,
        })
        
        return result
    
    return process_with_metrics


if __name__ == "__main__":
    print("""
    Layer 3 Call Router - Integration Guide
    =======================================
    
    Files created:
    - backend/app/services/call_router.py          (Main module)
    - backend/app/services/tests/test_call_router.py   (Tests)
    - backend/app/routes/router_routes.py          (FastAPI routes)
    - backend/app/services/LAYER3_README.md        (Documentation)
    
    Quick Start:
    1. Update backend/requirements.txt
    2. Set SARVAM_API_KEY in .env
    3. Run: pytest app/services/tests/test_call_router.py
    4. Start backend: uvicorn app.main:app
    5. Test: curl http://localhost:8000/v1/router/health
    """)
