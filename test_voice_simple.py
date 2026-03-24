#!/usr/bin/env python3
"""
Simple synchronous voice analysis test
"""
import json
import sys
import requests
from uuid import uuid4

API_ENDPOINT = "http://127.0.0.1:8000/api/v1/analysis/analyze-call"

SCENARIOS = {
    1: ("Water Leak", "Hello, there is water leaking from the pipe near my house in Sector 5 for two days. Please send someone to fix it."),
    2: ("Fire Emergency", "FIRE! There is fire in my building! Please help immediately! Emergency services needed now!"),
    3: ("Electricity", "The electricity in my area has been cut off since morning. No power in my house. Can you check?"),
    4: ("Road Damage", "The road near my locality has a big pothole. It's dangerous. A motorcycle got stuck. Please repair it!"),
}

def print_header():
    print("\n" + "=" * 80)
    print("  🎤 VOICE-TO-ANALYSIS TEST")
    print("=" * 80)

def print_results(data):
    """Pretty print analysis results"""
    if not data or not data.get('success'):
        print(f"\n❌ Analysis failed: {data.get('detail', 'Unknown error')}")
        return
    
    print("\n" + "=" * 80)
    print("📊 ANALYSIS RESULTS")
    print("=" * 80)
    
    print(f"\n✅ Analysis ID: {data['analysis_id']}")
    print(f"⚡ Speed: {data['processing_time_ms']:.1f}ms")
    
    if data.get('classification'):
        c = data['classification']
        print(f"\n🗣️  Language: {c['language']}")
        print(f"   Intent: {c['intent']}")
        print(f"   Confidence: {c['confidence']*100:.0f}%")
    
    if data.get('routing'):
        r = data['routing']
        print(f"\n🎯 Department: {r['department_name']} ({r['department_id']})")
        print(f"   Priority: {r['priority_level']}")
        if r.get('action_type'):
            print(f"   Action: {r['action_type']}")
    
    flags = []
    if data.get('is_emergency'):
        flags.append("🔴 EMERGENCY")
    if data.get('is_abuse'):
        flags.append("🔴 ABUSE")
    if data.get('is_genuine_complaint'):
        flags.append("✅ GENUINE")
    
    if flags:
        print(f"\n⚠️  Flags: {', '.join(flags)}")
    
    print("\n" + "=" * 80 + "\n")

def main():
    print_header()
    
    if len(sys.argv) < 2:
        print("\n📚 USAGE:\n")
        print("  Test scenario:    python3 test_voice_simple.py --scenario 1")
        print("  Custom text:      python3 test_voice_simple.py \"Your message here\"\n")
        print("SCENARIOS:")
        for num, (name, _) in SCENARIOS.items():
            print(f"  {num}. {name}")
        sys.exit(1)
    
    # Parse input
    if sys.argv[1] == "--scenario":
        if len(sys.argv) < 3:
            print("❌ Missing scenario number")
            sys.exit(1)
        try:
            scenario_num = int(sys.argv[2])
            if scenario_num not in SCENARIOS:
                print(f"❌ Scenario {scenario_num} not found")
                sys.exit(1)
            name, transcript = SCENARIOS[scenario_num]
        except ValueError:
            print("❌ Invalid scenario number")
            sys.exit(1)
    else:
        transcript = " ".join(sys.argv[1:])
        name = "Custom"
    
    print(f"📝 Scenario: {name}")
    print(f"   Input: \"{transcript[:70]}{'...' if len(transcript) > 70 else ''}\"")
    
    call_id = f"call_{uuid4().hex[:10]}"
    
    try:
        print(f"\n⏳ Sending to API at {API_ENDPOINT}...")
        
        response = requests.post(
            API_ENDPOINT,
            json={
                "call_id": call_id,
                "session_id": f"session_{uuid4().hex[:10]}",
                "transcript": transcript,
                "call_duration_seconds": 180,
                "caller_phone": "+919876543210"
            },
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        print_results(result)
        print("✅ Analysis complete!")
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API at {API_ENDPOINT}")
        print("   Make sure the backend is running:")
        print("   cd backend && python3 -m uvicorn app.main:app --port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
