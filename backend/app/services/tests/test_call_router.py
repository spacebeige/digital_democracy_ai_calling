"""
Integration Tests and Examples for Layer 3 Call Router

This file demonstrates how to use the call router in various scenarios.
"""

import json
import pytest
from app.services.call_router import (
    CallRouter,
    RouterInput,
    RouterOutput,
    IntentType,
    UrgencyLevel,
    MockSarvamAPIClient,
    RealSarvamAPIClient,
    route_call,
    DEPARTMENT_REGISTRY,
)


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def mock_router():
    """Create a router with mock LLM client."""
    return CallRouter(use_mock=True)


@pytest.fixture
def sample_inputs():
    """Collection of test inputs."""
    return {
        "emergency": RouterInput(
            session_id="call_001",
            transcription_text="There is a fire in my building, emergency!",
            language_code="en",
        ),
        "water_complaint": RouterInput(
            session_id="call_002",
            transcription_text="Mere ghar se pani leak ho raha hai. Takarav se pani bahar aa raha hai.",
            language_code="hi",
        ),
        "road_complaint": RouterInput(
            session_id="call_003",
            transcription_text="Road mein bohot bade pothole hain, bahut khatarnak hai",
            language_code="hi",
        ),
        "inquiry": RouterInput(
            session_id="call_004",
            transcription_text="When will you fix the street lights on Main Street?",
            language_code="en",
        ),
        "noise": RouterInput(
            session_id="call_005",
            transcription_text="uh hello um okay",
            language_code="en",
        ),
        "vague": RouterInput(
            session_id="call_006",
            transcription_text="hi",
            language_code="en",
        ),
    }


# ============================================================================
# BASIC ROUTING TESTS
# ============================================================================


def test_emergency_detection(mock_router: CallRouter, sample_inputs):
    """Test emergency keyword detection."""
    result = mock_router.process_call(sample_inputs["emergency"])
    
    assert result.is_emergency is True
    assert result.urgency == UrgencyLevel.EMERGENCY
    assert result.dept_id == "DEPT_EMERGENCY_911"
    assert result.confidence_score == 1.0


def test_water_complaint_routing(mock_router: CallRouter, sample_inputs):
    """Test Hindi water complaint routing."""
    result = mock_router.process_call(sample_inputs["water_complaint"])
    
    assert result.is_emergency is False
    assert result.intent == IntentType.COMPLAINT
    assert result.dept_id == "DEPT_WATER_001"
    assert result.confidence_score > 0.5
    assert "water" in result.summary.lower() or "pani" in result.raw_transcript.lower()


def test_road_complaint_routing(mock_router: CallRouter, sample_inputs):
    """Test Hindi road complaint routing."""
    result = mock_router.process_call(sample_inputs["road_complaint"])
    
    assert result.is_emergency is False
    assert result.intent == IntentType.COMPLAINT
    assert result.dept_id == "DEPT_ROADS_001"


def test_inquiry_detection(mock_router: CallRouter, sample_inputs):
    """Test inquiry (non-complaint) detection."""
    result = mock_router.process_call(sample_inputs["inquiry"])
    
    # Could be inquiry or complaint depending on LLM
    assert result.intent in [IntentType.INQUIRY, IntentType.COMPLAINT]
    assert result.is_emergency is False


def test_noise_detection(mock_router: CallRouter, sample_inputs):
    """Test noise/filler detection."""
    result = mock_router.process_call(sample_inputs["noise"])
    
    assert result.intent in [IntentType.NOISE, IntentType.VAGUE]
    assert result.confidence_score == 0.0
    assert "re-prompt" in result.department_name.lower()


def test_vague_detection(mock_router: CallRouter, sample_inputs):
    """Test vague/too-short input detection."""
    result = mock_router.process_call(sample_inputs["vague"])
    
    assert result.intent == IntentType.VAGUE
    assert result.confidence_score == 0.0


# ============================================================================
# ROUTING ACCURACY TESTS
# ============================================================================


def test_department_registry_consistency():
    """Verify department registry structure."""
    for dept_id, dept_info in DEPARTMENT_REGISTRY.items():
        assert "name" in dept_info
        assert "keywords" in dept_info
        assert "aliases" in dept_info
        assert isinstance(dept_info["keywords"], list)
        assert isinstance(dept_info["aliases"], list)


def test_entity_extraction(mock_router: CallRouter):
    """Test entity extraction."""
    router_input = RouterInput(
        session_id="call_007",
        transcription_text="The water pipe near the main gate is leaking.",
        language_code="en",
    )
    result = mock_router.process_call(router_input)
    
    # Mock client should extract entities
    assert result.entities is not None
    assert result.summary is not None


def test_confidence_score_bounds(mock_router: CallRouter):
    """Verify confidence scores are always valid (0-1)."""
    test_texts = [
        "Fire emergency outside!",
        "Mera ghar ke paas water leak ho gaya",
        "Hello um uh",
        "This is a complaint about roads",
    ]
    
    for text in test_texts:
        router_input = RouterInput(
            session_id=f"call_{text[:10]}",
            transcription_text=text,
            language_code="en",
        )
        result = mock_router.process_call(router_input)
        
        assert 0.0 <= result.confidence_score <= 1.0


# ============================================================================
# PERFORMANCE & TIMEOUT TESTS
# ============================================================================


def test_processing_time_tracked(mock_router: CallRouter):
    """Verify processing time is tracked."""
    router_input = RouterInput(
        session_id="call_perf",
        transcription_text="Water leak in my house",
        language_code="en",
    )
    result = mock_router.process_call(router_input)
    
    assert result.processing_time_ms > 0
    assert result.processing_time_ms < 5000  # Should be fast for mock


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================


def test_route_call_convenience_function():
    """Test the convenience wrapper function."""
    result = route_call(
        session_id="conv_001",
        text="There is a pothole on the main road",
        language_code="en",
    )
    
    assert isinstance(result, RouterOutput)
    assert result.session_id == "conv_001"
    assert result.dept_id == "DEPT_ROADS_001"


# ============================================================================
# EDGE CASES
# ============================================================================


def test_empty_string_validation():
    """Test that empty strings are rejected."""
    with pytest.raises(ValueError):
        RouterInput(
            session_id="call_empty",
            transcription_text="   ",  # Only whitespace
            language_code="en",
        )


def test_very_long_transcription(mock_router: CallRouter):
    """Test handling of very long transcriptions."""
    long_text = "water leak " * 500  # Create a long string
    router_input = RouterInput(
        session_id="call_long",
        transcription_text=long_text,
        language_code="en",
    )
    result = mock_router.process_call(router_input)
    
    assert result.dept_id == "DEPT_WATER_001"


def test_multilingual_support(mock_router: CallRouter):
    """Test multilingual handling."""
    hindi_input = RouterInput(
        session_id="call_hi",
        transcription_text="Mera ghar ke paas sadak mein gaddha hai",
        language_code="hi",
    )
    
    english_input = RouterInput(
        session_id="call_en",
        transcription_text="There is a pothole near my house",
        language_code="en",
    )
    
    hi_result = mock_router.process_call(hindi_input)
    en_result = mock_router.process_call(english_input)
    
    # Both should be routed to roads department
    assert hi_result.dept_id == "DEPT_ROADS_001"
    assert en_result.dept_id == "DEPT_ROADS_001"


# ============================================================================
# MOCK SARVAM CLIENT TESTS
# ============================================================================


def test_mock_sarvam_client():
    """Test mock Sarvam client directly."""
    client = MockSarvamAPIClient()
    
    result = client.classify_intent(
        "Water is leaking from the tap continuously",
        "en"
    )
    
    assert "intent" in result
    assert "entities" in result
    assert "confidence" in result
    assert result["confidence"] > 0.0


# ============================================================================
# REAL SARVAM CLIENT TESTS (Conditional - requires API key)
# ============================================================================


@pytest.mark.skip(reason="Requires real API key")
def test_real_sarvam_client():
    """Test real Sarvam API client."""
    import os
    api_key = os.getenv("SARVAM_API_KEY")
    
    if not api_key:
        pytest.skip("SARVAM_API_KEY not set")
    
    client = RealSarvamAPIClient(api_key=api_key)
    router = CallRouter(llm_client=client)
    
    result = router.process_call(RouterInput(
        session_id="real_test",
        transcription_text="Mera ghar ke paas water leak ho gaya",
        language_code="hi",
    ))
    
    assert result.dept_id == "DEPT_WATER_001"


# ============================================================================
# EXAMPLE USAGE SCENARIOS
# ============================================================================


def example_basic_usage():
    """Example 1: Basic usage with mock client."""
    router = CallRouter(use_mock=True)
    
    result = router.process_call(RouterInput(
        session_id="example_001",
        transcription_text="The water pipe in front of my building is leaking",
        language_code="en",
    ))
    
    print("Basic Usage Example:")
    print(json.dumps(result.dict(), indent=2))
    print()


def example_emergency_routing():
    """Example 2: Emergency call routing."""
    router = CallRouter(use_mock=True)
    
    result = router.process_call(RouterInput(
        session_id="example_002",
        transcription_text="Fire! There's a gas leak and it caught fire!",
        language_code="en",
    ))
    
    print("Emergency Routing Example:")
    print(f"Is Emergency: {result.is_emergency}")
    print(f"Urgency: {result.urgency}")
    print(f"Department: {result.department_name}")
    print()


def example_multilingual_complaint():
    """Example 3: Multilingual complaint."""
    router = CallRouter(use_mock=True)
    
    result = router.process_call(RouterInput(
        session_id="example_003",
        transcription_text="Namaskar, mere ghar ke samne sadak mein bahut bade gaddhe hain. Gaadi chalate samay bahut problem hota hai.",
        language_code="hi",
    ))
    
    print("Multilingual Complaint Example (Hindi):")
    print(f"Detected Intent: {result.intent}")
    print(f"Routed to: {result.department_name}")
    print(f"Summary: {result.summary}")
    print(f"Confidence: {result.confidence_score:.2%}")
    print()


def example_noise_handling():
    """Example 4: Noise and vague input handling."""
    router = CallRouter(use_mock=True)
    
    result = router.process_call(RouterInput(
        session_id="example_004",
        transcription_text="uh um hello okay yeah",
        language_code="en",
    ))
    
    print("Noise Handling Example:")
    print(f"Intent: {result.intent}")
    print(f"Confidence: {result.confidence_score}")
    print(f"Action: {result.summary}")
    print()


if __name__ == "__main__":
    # Run examples
    print("="*70)
    print("LAYER 3 CALL ROUTER - USAGE EXAMPLES")
    print("="*70)
    print()
    
    example_basic_usage()
    example_emergency_routing()
    example_multilingual_complaint()
    example_noise_handling()
    
    print("="*70)
    print("To run pytest tests:")
    print("  pytest backend/app/services/tests/test_call_router.py -v")
    print("="*70)
