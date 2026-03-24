#!/usr/bin/env python3
"""
Direct Voice Analysis Test
===========================

Simple tool to test the post-call analyzer with sample transcripts
without needing recording dependencies.
"""

import asyncio
import json
import httpx
from datetime import datetime
from uuid import uuid4


API_ENDPOINT = "http://127.0.0.1:8000/api/v1/analysis/analyze-call"


def print_results(analysis: dict):
    """Pretty print analysis results"""
    if not analysis or not analysis.get('success'):
        print(f"❌ Analysis failed: {analysis}")
        return
    
    print("\n" + "=" * 80)
    print("📊 POST-CALL ANALYSIS RESULTS")
    print("=" * 80)
    
    print("\n🔍 STATUS")
    print(f"  Analysis ID: {analysis['analysis_id']}")
    print(f"  Status: {analysis['status']}")
    print(f"  Processing Time: {analysis['processing_time_ms']:.1f}ms ⚡")
    
    if analysis.get('classification'):
        c = analysis['classification']
        print("\n🗣️  CLASSIFICATION")
        print(f"  Language: {c['language']}")
        print(f"  Intent: {c['intent']}")
        print(f"  Edge Case: {c['edge_case']}")
        print(f"  Confidence: {c['confidence']:.2f}")
    
    if analysis.get('routing'):
        r = analysis['routing']
        print("\n🎯 ROUTING & ACTION")
        print(f"  Department: {r['department_name']} ({r['department_id']})")
        print(f"  Category: {r.get('issue_category', 'N/A')}")
        print(f"  Priority: {r['priority_level']}")
        print(f"  Action: {r['suggested_action']}")
        print(f"  Confidence: {r['routing_confidence']:.2f}")
    
    print("\n⚠️  FLAGS")
    print(f"  Emergency: {'🔴 YES' if analysis['is_emergency'] else '🟢 NO'}")
    print(f"  Abuse: {'🔴 YES' if analysis['is_abuse'] else '🟢 NO'}")
    print(f"  Genuine: {'✅ YES' if analysis['is_genuine_complaint'] else '❌ NO'}")
    
    print("\n📈 METRICS")
    print(f"  Transcript Length: {analysis['transcript_length']} chars")
    print(f"  Word Count: {analysis['word_count']}")
    
    print("\n" + "=" * 80 + "\n")


async def analyze_transcript(transcript: str, scenario: str = ""):
    """Send transcript to analysis API"""
    
    print(f"\n📝 Analyzing: {scenario}")
    print(f"   Input: \"{transcript[:60]}...\"" if len(transcript) > 60 else f"   Input: \"{transcript}\"")
    
    call_id = f"call_{uuid4().hex[:10]}"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                API_ENDPOINT,
                json={
                    "call_id": call_id,
                    "session_id": f"session_{uuid4().hex[:10]}",
                    "transcript": transcript,
                    "call_duration_seconds": 180,
                    "caller_phone": "+919876543210"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ API Error: {response.status_code}")
                return None
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None


async def main():
    print("\n" + "=" * 80)
    print("  🎤 VOICE-TO-ANALYSIS LIVE TEST")
    print("  (Using sample transcripts)")
    print("=" * 80)
    
    # Test scenarios
    scenarios = [
        {
            "name": "Water Leak Complaint",
            "transcript": "Hello, there is water leaking from the pipe near my house in Sector 5. It has been happening for two days now. Please send someone to fix it."
        },
        {
            "name": "Emergency Fire Call",
            "transcript": "FIRE! There is fire in my building! Please help immediately! Emergency services needed now!"
        },
        {
            "name": "Electricity Issue",
            "transcript": "Hi, the electricity in my area has been cut off since morning. No power in my house. Can you check the transformer?"
        },
        {
            "name": "Road Complaint",
            "transcript": "The road near my locality has a big pothole. It's dangerous. A motorcycle got stuck yesterday. Please repair it urgently."
        }
    ]
    
    print("\n🎯 TEST SCENARIOS:")
    for i, scenario in enumerate(scenarios, 1):
        print(f"  {i}. {scenario['name']}")
    print(f"  {len(scenarios) + 1}. Custom input")
    print(f"  0. Exit")
    
    while True:
        try:
            choice = input("\n▶ Select scenario (0-5): ").strip()
            
            if choice == "0":
                print("\n👋 Exiting\n")
                break
            
            choice_num = int(choice)
            
            if choice_num < 1 or choice_num > len(scenarios) + 1:
                print("❌ Invalid choice")
                continue
            
            if choice_num <= len(scenarios):
                scenario = scenarios[choice_num - 1]
                transcript = scenario["transcript"]
                name = scenario["name"]
            else:
                transcript = input("\n💬 Enter your transcript: ").strip()
                if not transcript:
                    print("❌ Transcript cannot be empty")
                    continue
                name = "Custom Input"
            
            # Analyze
            print("\n⏳ Sending to analysis API...")
            result = await analyze_transcript(transcript, name)
            
            if result:
                print_results(result)
                
                # Ask if they want to continue
                cont = input("▶ Test another? (y/n): ").strip().lower()
                if cont != 'y':
                    break
            
        except ValueError:
            print("❌ Invalid input")
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Exiting\n")
