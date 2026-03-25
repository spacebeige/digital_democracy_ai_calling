#!/usr/bin/env python3
"""
INTEGRATED LIVE CALL + LAYER 3 ROUTING FLOW
============================================

Demonstrates the complete pipeline:
1. Simulate a live voice call (Layer 1-2)
2. Get transcription and initial response
3. Run post-call analysis through Layer 3 routing

Run with: python run_integrated_live_flow.py
"""

import asyncio
import json
import sys
import time
import requests
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
STT_API = "http://localhost:9000"
TTS_API = "http://localhost:9001"
LLM_API = "http://localhost:9002"

# Test audio files
AUDIO_FILES = {
    "water": "water_leak_test.wav",
    "emergency": "water_leak_test.wav",  # reuse for demo
    "dummy": "dummy.wav",
}


def check_services():
    """Verify all services are running."""
    print("\n" + "="*80)
    print("SERVICE HEALTH CHECK")
    print("="*80)
    
    services = {
        "Backend": f"{BACKEND_URL}/",
        "STT": f"{STT_API}/",
        "TTS": f"{TTS_API}/",
        "LLM": f"{LLM_API}/",
    }
    
    all_ok = True
    for name, url in services.items():
        try:
            resp = requests.get(url, timeout=2)
            status = "✓ OK" if resp.status_code < 400 else f"✗ Error {resp.status_code}"
            print(f"  {name:15} {status}")
        except Exception as e:
            print(f"  {name:15} ✗ FAILED ({str(e)[:30]})")
            all_ok = False
    
    if not all_ok:
        print("\n⚠️  Some services are not running. Start them with:")
        print("   source venv/bin/activate && python start_all.py")
        return False
    
    return True


def simulate_live_call(call_type: str = "water"):
    """
    Simulate a live voice call to the backend.
    
    Simulates the Layer 1-2 processing:
    - Audio submission
    - STT (Speech-to-Text)
    - LLM processing
    - TTS response generation
    """
    print("\n" + "="*80)
    print(f"LAYER 1-2: LIVE CALL SIMULATION ({call_type.upper()})")
    print("="*80)
    
    call_id = str(uuid4())[:13]
    audio_file = AUDIO_FILES.get(call_type, "water_leak_test.wav")
    audio_path = Path(audio_file)
    
    if not audio_path.exists():
        print(f"⚠️  Audio file not found: {audio_file}")
        print("   Using mock data instead...")
        audio_data = b"dummy_audio"
    else:
        with open(audio_path, "rb") as f:
            audio_data = f.read()
    
    print(f"📞 Simulating call: {call_id}")
    print(f"📁 Audio file: {audio_file}")
    
    try:
        # Submit audio to handle-turn endpoint
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/calls/handle-turn",
            files={"audio_file": ("audio.wav", audio_data)},
            data={"call_id": call_id},
            timeout=10,
        )
        call_duration = (time.time() - start_time) * 1000
        
        if response.status_code != 200:
            print(f"✗ Call failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return None
        
        result = response.json()
        print(f"✓ Call completed in {call_duration:.0f}ms")
        
        print("\n🎤 VOICE DATA:")
        print(f"  Transcript: {result.get('transcript', 'N/A')[:80]}...")
        
        print("\n🤖 AGENT RESPONSE:")
        print(f"  Response: {result.get('agent_text', 'N/A')[:80]}...")
        
        print("\n📊 CLASSIFICATION:")
        print(f"  Department: {result.get('department', 'N/A')}")
        print(f"  Complaint ID: {result.get('complaint_id', 'N/A')}")
        
        return {
            "call_id": call_id,
            "transcript": result.get("transcript", ""),
            "department": result.get("department", "general"),
            "agent_response": result.get("agent_text", ""),
            "complaint_id": result.get("complaint_id"),
        }
    
    except Exception as e:
        print(f"✗ Error during call: {e}")
        return None


def route_call_layer3(call_data: dict):
    """
    Route the call through Layer 3 for post-call analysis.
    
    Sends transcription to the smart router for:
    - Emergency detection
    - Intent classification
    - Department routing
    - Urgency scoring
    """
    print("\n" + "="*80)
    print("LAYER 3: POST-CALL ROUTING ANALYSIS")
    print("="*80)
    
    if not call_data:
        print("⚠️  No call data to route")
        return None
    
    call_id = call_data.get("call_id")
    transcript = call_data.get("transcript", "")
    
    print(f"📍 Routing call: {call_id}")
    print(f"📝 Transcript: {transcript[:100]}...")
    
    try:
        # Send to Layer 3 router
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/v1/router/route-call",
            json={
                "session_id": call_id,
                "transcript": transcript,
            },
            timeout=10,
        )
        routing_duration = (time.time() - start_time) * 1000
        
        if response.status_code != 200:
            print(f"✗ Routing failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return None
        
        result = response.json()
        print(f"✓ Routing completed in {routing_duration:.0f}ms")
        
        print("\n🚨 EMERGENCY CHECK:")
        is_emergency = result.get("is_emergency", False)
        print(f"  {"🔴 EMERGENCY" if is_emergency else "✓ Normal"}")
        
        print("\n🎯 CLASSIFICATION:")
        print(f"  Intent: {result.get('intent', 'N/A')}")
        print(f"  Issue Category: {result.get('issue_category', 'N/A')}")
        print(f"  Language: {result.get('language', 'N/A')}")
        print(f"  Confidence: {result.get('confidence', 'N/A')}")
        
        print("\n📂 ROUTING:")
        routing_data = result.get("routing_data", {})
        print(f"  Department ID: {routing_data.get('dept_id', 'N/A')}")
        print(f"  Priority: {routing_data.get('priority', 'N/A')}/5")
        print(f"  Summary: {routing_data.get('summary', 'N/A')}")
        
        print("\n📋 ACTION:")
        print(f"  Action: {result.get('action', 'N/A')}")
        
        return result
    
    except Exception as e:
        print(f"✗ Error during routing: {e}")
        return None


def print_summary(call_result: dict, routing_result: dict):
    """Print final summary of the integrated flow."""
    print("\n" + "="*80)
    print("INTEGRATED FLOW SUMMARY")
    print("="*80)
    
    if call_result:
        print("\n📞 LIVE CALL PHASE:")
        print(f"  ✓ Call ID: {call_result.get('call_id')}")
        print(f"  ✓ Transcript: {call_result.get('transcript')[:60]}...")
        print(f"  ✓ Department: {call_result.get('department')}")
    
    if routing_result:
        print("\n🧠 LAYER 3 ROUTING PHASE:")
        print(f"  ✓ Intent: {routing_result.get('intent')}")
        print(f"  ✓ Category: {routing_result.get('issue_category')}")
        routing_data = routing_result.get('routing_data', {})
        print(f"  ✓ Department: {routing_data.get('dept_id')}")
        print(f"  ✓ Priority: {routing_data.get('priority')}/5")
        print(f"  ✓ Emergency: {'YES 🔴' if routing_result.get('is_emergency') else 'NO ✓'}")
        print(f"  ✓ Confidence: {routing_result.get('confidence')}")
    
    print("\n" + "="*80)
    print("✅ INTEGRATED PIPELINE COMPLETE")
    print("="*80 + "\n")


def main():
    """Main entry point."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  INTEGRATED LIVE CALL + LAYER 3 ROUTING FLOW".center(78) + "║")
    print("║" + "  Digital Democracy AI Calling System".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    # Step 1: Health check
    if not check_services():
        print("\n💡 Ensure services are running:")
        print("   Terminal 1: cd awaaz && python main.py")
        print("   Terminal 2: python start_all.py")
        sys.exit(1)
    
    print("\n✓ All services healthy!")
    
    # Step 2: Run multiple test cases
    test_cases = [
        ("water", "Water leak complaint"),
        ("emergency", "Emergency scenario"),
        ("dummy", "Generic complaint"),
    ]
    
    all_results = []
    
    for test_type, description in test_cases:
        print(f"\n\n{'='*80}")
        print(f"TEST CASE: {description}")
        print(f"{'='*80}")
        
        # Phase 1: Simulate live call
        call_result = simulate_live_call(test_type)
        
        # Phase 2: Route through Layer 3
        routing_result = None
        if call_result:
            time.sleep(0.5)  # Brief pause
            routing_result = route_call_layer3(call_result)
        
        # Summary
        print_summary(call_result, routing_result)
        
        all_results.append({
            "test_case": description,
            "call": call_result,
            "routing": routing_result,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    # Final report
    print("\n" + "="*80)
    print("FINAL REPORT")
    print("="*80)
    print(f"Total test cases: {len(all_results)}")
    print(f"Completed at: {datetime.utcnow().isoformat()}")
    
    successful_calls = sum(1 for r in all_results if r["call"] is not None)
    successful_routing = sum(1 for r in all_results if r["routing"] is not None)
    
    print(f"\n✓ Successful calls: {successful_calls}/{len(all_results)}")
    print(f"✓ Successful routing: {successful_routing}/{len(all_results)}")
    
    # Save results
    results_file = "integrated_flow_results.json"
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n📁 Results saved to: {results_file}")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
