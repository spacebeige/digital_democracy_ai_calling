"""
Tests for Layer 3: SmartRouter — NLP + Smart Routing Pipeline

Required test cases:
  1. Broken Water Pipe in Hindi
  2. Silent / Prank call
Plus additional coverage for emergencies, malformed LLM JSON, etc.

Uses asyncio.run() wrappers for maximum pytest compatibility.
"""

import asyncio
import uuid

import pytest

from app.services.smart_router import (
    ActionType,
    IntentType,
    IssueCategory,
    MockSarvamClient,
    RoutingResult,
    SmartRouter,
    SarvamLLMResponse,
    VoiceInput,
    _parse_llm_json,
)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def _router() -> SmartRouter:
    return SmartRouter(use_mock=True)


def _sid() -> uuid.UUID:
    return uuid.uuid4()


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ═══════════════════════════════════════════════════════════════════════════════
# REQUIRED TEST CASE 1: Broken Water Pipe in Hindi
# ═══════════════════════════════════════════════════════════════════════════════


def test_broken_water_pipe_hindi():
    """
    A citizen calls in Hindi about a broken water pipe.
    Expected: routed to Water dept, CREATE_TICKET action, non-emergency.
    """
    router = _router()
    voice_input = VoiceInput(
        session_id=_sid(),
        caller_metadata={"phone": "+919876543210", "location": "Jaipur"},
        transcript="Mere ghar ke saamne pani ki pipeline tut gayi hai, bahut pani beh raha hai",
        language_code="hi-IN",
        stt_confidence=0.87,
    )

    result: RoutingResult = _run(router.process(voice_input))

    assert result.is_emergency is False
    assert result.action == ActionType.CREATE_TICKET
    assert result.routing_data.dept_id == "DEPT_WATER_001"
    assert result.routing_data.priority >= 3
    assert len(result.audit_log) >= 3
    assert any("STAGE_A" in entry for entry in result.audit_log)
    assert any("STAGE_B" in entry for entry in result.audit_log)
    assert any("STAGE_C" in entry for entry in result.audit_log)
    assert result.processing_time_ms > 0


# ═══════════════════════════════════════════════════════════════════════════════
# REQUIRED TEST CASE 2: Silent / Prank Call
# ═══════════════════════════════════════════════════════════════════════════════


def test_silent_prank_call_filler():
    """
    Caller says only filler words → INVALID_INPUT → DISCONNECT.
    """
    router = _router()
    voice_input = VoiceInput(
        session_id=_sid(),
        caller_metadata={"phone": "+910000000000", "location": "Unknown"},
        transcript="hello ji umm hello hi",
        language_code="hi-IN",
        stt_confidence=0.30,
    )

    result: RoutingResult = _run(router.process(voice_input))

    assert result.is_emergency is False
    assert result.action == ActionType.DISCONNECT
    assert any("STAGE_A" in entry for entry in result.audit_log)
    assert any("INVALID_INPUT" in entry or "filler" in entry for entry in result.audit_log)


def test_silent_prank_call_too_short():
    """
    Caller says < 3 words → INVALID_INPUT → DISCONNECT.
    """
    router = _router()
    voice_input = VoiceInput(
        session_id=_sid(),
        caller_metadata={"phone": "+910000000000", "location": "Unknown"},
        transcript="hi ok",
        language_code="hi-IN",
        stt_confidence=0.10,
    )

    result: RoutingResult = _run(router.process(voice_input))

    assert result.is_emergency is False
    assert result.action == ActionType.DISCONNECT
    assert any("STAGE_A" in entry for entry in result.audit_log)


# ═══════════════════════════════════════════════════════════════════════════════
# EMERGENCY BYPASS
# ═══════════════════════════════════════════════════════════════════════════════


def test_emergency_fire_bypass():
    """
    Life-threatening emergency (fire) → bypass LLM → TRANSFER_HUMAN.
    """
    router = _router()
    voice_input = VoiceInput(
        session_id=_sid(),
        caller_metadata={"phone": "+919876543210", "location": "Delhi"},
        transcript="Mere building mein fire lag gayi hai, please help! Emergency!",
        language_code="hi-IN",
        stt_confidence=0.92,
    )

    result: RoutingResult = _run(router.process(voice_input))

    assert result.is_emergency is True
    assert result.action == ActionType.TRANSFER_HUMAN
    assert result.routing_data.dept_id == "DEPT_EMERGENCY_911"
    assert result.routing_data.priority == 5
    assert any("STAGE_A" in entry and "Emergency" in entry for entry in result.audit_log)
    # Audit log should NOT contain STAGE_B (LLM was bypassed)
    assert not any("STAGE_B" in entry for entry in result.audit_log)


def test_emergency_medical():
    """Medical emergency → bypass LLM."""
    router = _router()
    voice_input = VoiceInput(
        session_id=_sid(),
        caller_metadata={"phone": "+919876543210", "location": "Mumbai"},
        transcript="Please send ambulance quickly, someone had an accident",
        language_code="en-IN",
        stt_confidence=0.95,
    )

    result = _run(router.process(voice_input))

    assert result.is_emergency is True
    assert result.action == ActionType.TRANSFER_HUMAN


# ═══════════════════════════════════════════════════════════════════════════════
# MALFORMED LLM JSON HANDLING
# ═══════════════════════════════════════════════════════════════════════════════


def test_parse_malformed_llm_json_with_markdown():
    """LLM wraps JSON in markdown code fence."""
    raw = '```json\n{"intent": "NEW_COMPLAINT", "issue_category": "Water", "summary": "Broken pipe leaking", "urgency": 4}\n```'
    result = _parse_llm_json(raw)

    assert result.intent == IntentType.NEW_COMPLAINT
    assert result.issue_category == IssueCategory.WATER
    assert result.urgency == 4


def test_parse_malformed_llm_json_with_extra_text():
    """LLM returns text mixed with partial JSON fields."""
    raw = 'Here is the classification: "intent": "PRANK", "issue_category": "General", "summary": "Prank detected", "urgency": 1'
    result = _parse_llm_json(raw)

    assert result.intent == IntentType.PRANK
    assert result.urgency == 1


def test_parse_completely_broken_llm_output():
    """LLM returns total garbage → fallback defaults."""
    raw = "I cannot process this request right now."
    result = _parse_llm_json(raw)

    assert result.intent == IntentType.NEW_COMPLAINT  # safe default
    assert result.issue_category == IssueCategory.GENERAL


# ═══════════════════════════════════════════════════════════════════════════════
# DEPARTMENT ROUTING
# ═══════════════════════════════════════════════════════════════════════════════


def test_electricity_complaint_routing():
    """Electricity-related complaint routes to power dept."""
    router = _router()
    voice_input = VoiceInput(
        session_id=_sid(),
        caller_metadata={"phone": "+919876543210", "location": "Pune"},
        transcript="Hamaare mohalle mein bijli nahi aa rahi hai, transformer kharab hai",
        language_code="hi-IN",
        stt_confidence=0.88,
    )

    result = _run(router.process(voice_input))

    assert result.routing_data.dept_id == "DEPT_ELECTRICITY_001"
    assert result.action == ActionType.CREATE_TICKET


def test_road_complaint_routing():
    """Pothole complaint → Roads department."""
    router = _router()
    voice_input = VoiceInput(
        session_id=_sid(),
        caller_metadata={"phone": "+919876543210", "location": "Bengaluru"},
        transcript="Main road pe bahut bada pothole hai, do accidents ho chuke hain",
        language_code="hi-IN",
        stt_confidence=0.90,
    )

    result = _run(router.process(voice_input))

    assert result.routing_data.dept_id == "DEPT_ROADS_001"


def test_unknown_category_fallback():
    """Unknown topic → GENERAL_ADMIN fallback."""
    router = _router()
    voice_input = VoiceInput(
        session_id=_sid(),
        caller_metadata={"phone": "+919876543210", "location": "Chennai"},
        transcript="Ration card mein galat naam likha hua hai, correction chahiye",
        language_code="hi-IN",
        stt_confidence=0.85,
    )

    result = _run(router.process(voice_input))

    assert result.routing_data.dept_id == "DEPT_GENERAL_ADMIN"


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════


def test_voice_input_rejects_empty_transcript():
    """Empty transcript must raise ValidationError."""
    with pytest.raises(Exception):
        VoiceInput(
            session_id=uuid.uuid4(),
            transcript="   ",
            language_code="en-IN",
        )


def test_voice_input_accepts_valid_data():
    """Standard valid input."""
    vi = VoiceInput(
        session_id=uuid.uuid4(),
        caller_metadata={"phone": "+91123", "location": "Delhi"},
        transcript="Water pipe broken in my area",
        language_code="en-IN",
        stt_confidence=0.9,
    )
    assert vi.transcript == "Water pipe broken in my area"


# ═══════════════════════════════════════════════════════════════════════════════
# MOCK CLIENT UNIT TESTS
# ═══════════════════════════════════════════════════════════════════════════════


def test_mock_client_detects_prank():
    client = MockSarvamClient()
    resp = _run(client.classify("bakwas kar raha hai lol", "hi-IN"))
    assert resp.intent == IntentType.PRANK


def test_mock_client_detects_status_query():
    client = MockSarvamClient()
    resp = _run(client.classify("Meri complaint ka status kya hai?", "hi-IN"))
    assert resp.intent == IntentType.STATUS_QUERY


def test_mock_client_detects_feedback():
    client = MockSarvamClient()
    resp = _run(client.classify("Dhanyavad, aapne bahut accha kaam kiya", "hi-IN"))
    assert resp.intent == IntentType.FEEDBACK


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT LOG TRACE
# ═══════════════════════════════════════════════════════════════════════════════


def test_audit_log_contains_full_trace():
    """Normal complaint flow should have stage A, B, C, and ACTION entries."""
    router = _router()
    voice_input = VoiceInput(
        session_id=_sid(),
        caller_metadata={"phone": "+919876543210", "location": "Hyderabad"},
        transcript="Ghar ke saamne kachra bahut zyada jamaa ho gaya hai",
        language_code="hi-IN",
        stt_confidence=0.85,
    )

    result = _run(router.process(voice_input))

    log_text = " ".join(result.audit_log)
    assert "STAGE_A" in log_text
    assert "STAGE_B" in log_text
    assert "STAGE_C" in log_text
    assert "ACTION" in log_text
