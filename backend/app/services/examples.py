#!/usr/bin/env python3
"""
Layer 3 Call Router - Quick Reference & Examples

This script demonstrates all major features of the call router.
Run with: python backend/app/services/examples.py
"""

import json
from app.services.call_router import (
    CallRouter,
    RouterInput,
    MockSarvamAPIClient,
    route_call,
    IntentType,
    UrgencyLevel,
)


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_result(result):
    """Pretty print routing result."""
    print(f"  Session ID:    {result.session_id}")
    print(f"  Is Emergency:  {result.is_emergency}")
    print(f"  Intent:        {result.intent.value}")
    print(f"  Urgency:       {result.urgency.value}")
    print(f"  Department:    {result.department_name}")
    print(f"  Confidence:    {result.confidence_score:.1%}")
    print(f"  Summary:       {result.summary}")
    print(f"  Problem:       {result.entities.problem}")
    print(f"  Location:      {result.entities.location}")
    print(f"  Latency:       {result.processing_time_ms}ms")


# ============================================================================
# EXAMPLE 1: Basic Water Complaint
# ============================================================================

def example_1_basic_water_complaint():
    """Simplest use case: English complaint about water."""
    print_section("EXAMPLE 1: Basic Water Complaint")
    
    result = route_call(
        session_id="example_001",
        text="Water is leaking from the tap in my kitchen",
        language_code="en"
    )
    
    print_result(result)


# ============================================================================
# EXAMPLE 2: Hindi Complaint (Multilingual)
# ============================================================================

def example_2_hindi_complaint():
    """Multilingual support: Hindi complaint."""
    print_section("EXAMPLE 2: Hindi Complaint (Multilingual)")
    
    result = route_call(
        session_id="example_002",
        text="Mere ghar ke samne sadak mein bahut bade gaddhe hain",
        language_code="hi"
    )
    
    print_result(result)


# ============================================================================
# EXAMPLE 3: Emergency Detection
# ============================================================================

def example_3_emergency():
    """Fast emergency detection (bypasses LLM)."""
    print_section("EXAMPLE 3: Emergency Detection (Fast-Path)")
    
    result = route_call(
        session_id="example_003",
        text="Fire! There's a fire in my building!",
        language_code="en"
    )
    
    print_result(result)
    print(f"\n  ⚠️  EMERGENCY: Routed to {result.dept_id}")


# ============================================================================
# EXAMPLE 4: Noise/Vague Detection
# ============================================================================

def example_4_noise_detection():
    """Detect noise and vague inputs."""
    print_section("EXAMPLE 4: Noise Detection")
    
    result = route_call(
        session_id="example_004",
        text="uh hello um okay",
        language_code="en"
    )
    
    print_result(result)
    print(f"\n  ℹ️  Detected as NOISE - system will re-prompt user")


# ============================================================================
# EXAMPLE 5: Short/Vague Input
# ============================================================================

def example_5_vague_input():
    """Detect vague/insufficient input."""
    print_section("EXAMPLE 5: Vague (Too Short) Input")
    
    result = route_call(
        session_id="example_005",
        text="hello",
        language_code="en"
    )
    
    print_result(result)
    print(f"\n  ℹ️  Input too short (<3 words) - flagged for re-prompt")


# ============================================================================
# EXAMPLE 6: Multiple Department Routing
# ============================================================================

def example_6_multiple_departments():
    """Show routing to different departments."""
    print_section("EXAMPLE 6: Multiple Department Routing")
    
    test_cases = [
        ("example_06a", "Power outage in my area", "en", "ELECTRICITY"),
        ("example_06b", "Garbage pile on the street", "en", "SANITATION"),
        ("example_06c", "Hospital mein jain ke liye registration", "hi", "HEALTH"),
        ("example_06d", "School fees mein samasya hai", "hi", "EDUCATION"),
    ]
    
    for session_id, text, lang, expected_dept in test_cases:
        result = route_call(session_id, text, lang)
        match = "✓" if expected_dept.lower() in result.dept_id.lower() else "✗"
        print(f"\n  {match} Input: {text[:40]}")
        print(f"    → Routed to: {result.department_name}")


# ============================================================================
# EXAMPLE 7: Direct Router Usage (Advanced)
# ============================================================================

def example_7_direct_router_usage():
    """Use CallRouter directly with mock client."""
    print_section("EXAMPLE 7: Direct Router Usage with Error Handling")
    
    # Create router instance
    router = CallRouter(use_mock=True)
    
    try:
        result = router.process_call(RouterInput(
            session_id="example_007",
            transcription_text="Electricity bill mein error hai",
            language_code="hi",
        ))
        
        print_result(result)
        
    except ValueError as e:
        print(f"  ✗ Input validation error: {e}")
    except RuntimeError as e:
        print(f"  ✗ LLM processing error: {e}")


# ============================================================================
# EXAMPLE 8: Batch Processing (for analytics)
# ============================================================================

def example_8_batch_processing():
    """Process multiple calls at once."""
    print_section("EXAMPLE 8: Batch Processing")
    
    router = CallRouter(use_mock=True)
    
    batch_input = [
        RouterInput(
            session_id=f"batch_00{i}",
            transcription_text=text,
            language_code=lang,
        )
        for i, (text, lang) in enumerate([
            ("Water leak", "en"),
            ("Sadak mein pothole", "hi"),
            ("Garbage collection", "en"),
            ("uh um hello", "en"),
        ])
    ]
    
    results = [router.process_call(inp) for inp in batch_input]
    
    print(f"\n  Processed {len(results)} calls:")
    for result in results:
        status = "✓" if result.confidence_score > 0.5 else "⚠"
        print(f"    {status} {result.session_id}: {result.department_name} "
              f"(confidence: {result.confidence_score:.0%})")


# ============================================================================
# EXAMPLE 9: Confidence Scoring
# ============================================================================

def example_9_confidence_scoring():
    """Show how confidence varies by input clarity."""
    print_section("EXAMPLE 9: Confidence Scoring by Input Clarity")
    
    router = CallRouter(use_mock=True)
    
    test_cases = [
        ("Clear", "The water pipe is leaking"),
        ("Somewhat Clear", "water problem"),
        ("Vague", "There's something"),
        ("Noise", "uh um hello"),
    ]
    
    for clarity, text in test_cases:
        result = router.process_call(RouterInput(
            session_id=f"conf_{clarity}",
            transcription_text=text,
            language_code="en",
        ))
        
        confidence_bar = "█" * int(result.confidence_score * 10) + "░" * (10 - int(result.confidence_score * 10))
        print(f"\n  {clarity:15} | {confidence_bar} | {result.confidence_score:.0%}")
        print(f"  {' ' * 15} | '{text}'")


# ============================================================================
# EXAMPLE 10: Integration with Response Generation
# ============================================================================

def example_10_response_generation():
    """Show how to use routing result to generate TTS response."""
    print_section("EXAMPLE 10: Generate TTS Response Based on Routing")
    
    result = route_call(
        session_id="example_010",
        text="Electricity meter mein problem hai",
        language_code="hi"
    )
    
    # Generate response based on routing result
    if result.is_emergency:
        response = "आपातकाल सेवाएं जुटाई जा रही हैं।"
    elif result.intent == IntentType.COMPLAINT:
        response = (f"आपकी {result.entities.problem or 'समस्या'} की शिकायत "
                   f"{result.department_name} को भेजी जा रही है।")
    elif result.intent == IntentType.NOISE:
        response = "कृपया विस्तार से बताएं कि समस्या क्या है।"
    else:
        response = "आपकी पूछताछ के लिए धन्यवाद। ऐसे समय में जवाब मिलेगा।"
    
    print(f"\n  Routing Result:")
    print(f"    Department: {result.department_name}")
    print(f"    Urgency: {result.urgency.value}")
    print(f"\n  Generated Response (would be converted to speech):")
    print(f"    \"{response}\"")


# ============================================================================
# EXAMPLE 11: Performance Comparison
# ============================================================================

def example_11_performance_comparison():
    """Compare performance across different scenarios."""
    print_section("EXAMPLE 11: Performance Comparison")
    
    router = CallRouter(use_mock=True)
    
    scenarios = [
        ("Emergency (Fast-path)", "Fire emergency!"),
        ("Noise Detection (Fast)", "uh um hello"),
        ("Normal Complaint", "Water is leaking from the tap"),
        ("Long Transcript", "Water is leaking from the tap in my kitchen and I cannot stop it"),
    ]
    
    print("\n  Scenario vs Latency:")
    for scenario_name, text in scenarios:
        result = router.process_call(RouterInput(
            session_id=f"perf_{scenario_name}",
            transcription_text=text,
            language_code="en",
        ))
        
        latency_bar = "█" * min(int(result.processing_time_ms / 10), 10)
        print(f"  {scenario_name:30} | {latency_bar} | {result.processing_time_ms:6.1f}ms")


# ============================================================================
# EXAMPLE 12: Error Handling
# ============================================================================

def example_12_error_handling():
    """Show error handling patterns."""
    print_section("EXAMPLE 12: Error Handling Patterns")
    
    router = CallRouter(use_mock=True)
    
    # Test 1: Empty input
    print("\n  Test 1: Empty input")
    try:
        result = router.process_call(RouterInput(
            session_id="error_001",
            transcription_text="   ",  # Only whitespace
            language_code="en",
        ))
    except ValueError as e:
        print(f"    ✓ Caught validation error: {str(e)[:50]}...")
    
    # Test 2: Invalid language code
    print("\n  Test 2: Invalid input (should be handled gracefully)")
    try:
        result = router.process_call(RouterInput(
            session_id="error_002",
            transcription_text="test",
            language_code="en",  # Valid input now
        ))
        print(f"    ✓ Processed successfully: {result.dept_id}")
    except Exception as e:
        print(f"    ✗ Error: {e}")


# ============================================================================
# EXAMPLE 13: Department Registry Inspection
# ============================================================================

def example_13_department_registry():
    """Inspect available departments and keywords."""
    print_section("EXAMPLE 13: Department Registry")
    
    from app.services.call_router import DEPARTMENT_REGISTRY
    
    print("\n  Available Departments:\n")
    for dept_id, dept_info in DEPARTMENT_REGISTRY.items():
        print(f"  {dept_id}")
        print(f"    Name: {dept_info['name']}")
        print(f"    Keywords: {', '.join(dept_info['keywords'][:5])}")
        if len(dept_info['keywords']) > 5:
            print(f"              ... and {len(dept_info['keywords']) - 5} more")
        print()


# ============================================================================
# EXAMPLE 14: Multilingual Support
# ============================================================================

def example_14_multilingual():
    """Show multilingual support across different languages."""
    print_section("EXAMPLE 14: Multilingual Support")
    
    router = CallRouter(use_mock=True)
    
    test_cases = [
        ("hi", "Mere ghar ke paas sadak mein gaddha hai", "Hindi"),
        ("en", "There is a pothole on the street", "English"),
        ("ta", "Enakku water leak irukku", "Tamil"),
        ("te", "Naa houses chala garbage irundhi", "Telugu"),
    ]
    
    print("\n  Language Support Test:\n")
    for lang_code, text, lang_name in test_cases:
        result = route_call(
            session_id=f"multi_{lang_code}",
            text=text,
            language_code=lang_code
        )
        
        print(f"  {lang_name:10} ({lang_code}): → {result.department_name}")


# ============================================================================
# EXAMPLE 15: JSON Output (for API Response)
# ============================================================================

def example_15_json_output():
    """Show JSON serialization for API responses."""
    print_section("EXAMPLE 15: JSON Output (API Response)")
    
    result = route_call(
        session_id="json_001",
        text="Water is leaking from the main pipeline",
        language_code="en"
    )
    
    print("\n  JSON Response:")
    print(json.dumps(result.model_dump(), indent=2, default=str))


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run all examples."""
    print("""
    ┌─────────────────────────────────────────────────────────┐
    │  Layer 3: The Brain - Call Router Examples              │
    │  Production-Ready Call Routing for Automated Helpline   │
    └─────────────────────────────────────────────────────────┘
    """)
    
    examples = [
        ("Basic Water Complaint", example_1_basic_water_complaint),
        ("Hindi Complaint (Multilingual)", example_2_hindi_complaint),
        ("Emergency Detection", example_3_emergency),
        ("Noise Detection", example_4_noise_detection),
        ("Vague Input", example_5_vague_input),
        ("Multiple Departments", example_6_multiple_departments),
        ("Direct Router Usage", example_7_direct_router_usage),
        ("Batch Processing", example_8_batch_processing),
        ("Confidence Scoring", example_9_confidence_scoring),
        ("Response Generation", example_10_response_generation),
        ("Performance Comparison", example_11_performance_comparison),
        ("Error Handling", example_12_error_handling),
        ("Department Registry", example_13_department_registry),
        ("Multilingual Support", example_14_multilingual),
        ("JSON Output", example_15_json_output),
    ]
    
    print("\n  Available Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"    {i:2}. {name}")
    
    # Run all examples
    print("\n" + "=" * 70)
    print(" Running All Examples")
    print("=" * 70)
    
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n  ✗ Error in {name}: {e}")
    
    print("\n" + "=" * 70)
    print(" Examples Complete!")
    print("=" * 70)
    print("\n  For more information, see:")
    print("    - backend/app/services/LAYER3_README.md")
    print("    - backend/INTEGRATION_GUIDE.py")
    print("    - backend/app/services/tests/test_call_router.py")
    print()


if __name__ == "__main__":
    main()
