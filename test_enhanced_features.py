#!/usr/bin/env python3
"""
Quick Test Script for Enhanced Features
Tests vulgarity detection, state schemes, and AI summary
"""

import asyncio
import httpx
import json
from datetime import datetime


BASE_URL = "http://localhost:8000"


async def test_vulgarity_detection():
    """Test vulgarity detection with progressive warnings."""
    print("\n" + "="*60)
    print("TEST 1: VULGARITY DETECTION")
    print("="*60)
    
    session_id = f"test-{datetime.now().timestamp()}"
    
    test_cases = [
        ("Clean text", "मुझे पानी की समस्या है", False),
        ("Mild profanity", "यह सेवा बकवास है", True),
        ("Moderate profanity", "आप लोग कुत्ते हो", True),
        ("Severe profanity", "madarchod सब", True),
    ]
    
    async with httpx.AsyncClient() as client:
        for i, (description, text, should_detect) in enumerate(test_cases, 1):
            print(f"\n{i}. {description}")
            print(f"   Text: {text}")
            
            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/enhanced/check-vulgarity",
                    json={
                        "text": text,
                        "language": "hi",
                        "session_id": session_id
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✓ Detected: {result['detected']}")
                    print(f"   ✓ Level: {result['level']}")
                    print(f"   ✓ Warning Count: {result['warning_count']}")
                    print(f"   ✓ Should Terminate: {result['should_terminate']}")
                    
                    if result['detected']:
                        print(f"   ✓ Warning: {result['response_message']['hi'][:100]}...")
                else:
                    print(f"   ✗ Error: {response.status_code}")
            except Exception as e:
                print(f"   ✗ Exception: {e}")


async def test_ai_summary():
    """Test enhanced AI summary generation."""
    print("\n" + "="*60)
    print("TEST 2: AI SUMMARY GENERATION")
    print("="*60)
    
    test_cases = [
        {
            "text": "There is no water in our area for the past 3 days. Around 50 families are affected in ward 5.",
            "category": "Water",
            "language": "en",
            "expected_urgency": "HIGH"
        },
        {
            "text": "आग लगी है! मदद चाहिए तुरंत!",
            "category": "Emergency",
            "language": "hi",
            "expected_urgency": "CRITICAL"
        },
        {
            "text": "Road needs repair near school",
            "category": "Road",
            "language": "en",
            "expected_urgency": "MEDIUM"
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['text'][:50]}...")
            
            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/enhanced/generate-summary",
                    json={
                        "text": test_case["text"],
                        "category": test_case["category"],
                        "language": test_case["language"],
                        "style": "CONCISE"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✓ Summary: {result['summary']}")
                    print(f"   ✓ Urgency: {result['urgency']} (expected: {test_case['expected_urgency']})")
                    print(f"   ✓ Urgency Score: {result['urgency_score']:.2f}")
                    print(f"   ✓ Emotion: {result['citizen_emotion']}")
                    print(f"   ✓ Response Time: {result['suggested_response_time']}")
                    
                    if result['key_points']:
                        print(f"   ✓ Key Points: {', '.join(result['key_points'][:3])}")
                else:
                    print(f"   ✗ Error: {response.status_code}")
            except Exception as e:
                print(f"   ✗ Exception: {e}")


async def test_state_schemes():
    """Test state-wise government schemes."""
    print("\n" + "="*60)
    print("TEST 3: STATE SCHEMES")
    print("="*60)
    
    test_states = [
        ("Maharashtra", "hi"),
        ("Delhi", "en"),
        ("Tamil Nadu", "en"),
        ("मुंबई", "hi"),  # Should detect Maharashtra
    ]
    
    async with httpx.AsyncClient() as client:
        for i, (state, language) in enumerate(test_states, 1):
            print(f"\n{i}. State: {state}, Language: {language}")
            
            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/enhanced/get-state-schemes",
                    json={
                        "state_identifier": state,
                        "language": language
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✓ State Code: {result['state_code']}")
                    print(f"   ✓ Total Schemes: {result['total_schemes']}")
                    
                    if result['schemes']:
                        print(f"   ✓ Sample Scheme: {result['schemes'][0]['name']}")
                        print(f"   ✓ Contact: {result['schemes'][0].get('contact_number', 'N/A')}")
                else:
                    print(f"   ✗ Error: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"   ✗ Exception: {e}")


async def test_complete_flow():
    """Test complete complaint processing flow."""
    print("\n" + "="*60)
    print("TEST 4: COMPLETE COMPLAINT PROCESSING")
    print("="*60)
    
    test_complaints = [
        {
            "transcript": "मुंबई में पानी नहीं आ रहा है 2 दिन से, बहुत परेशानी है",
            "language": "hi",
            "category": "Water"
        },
        {
            "transcript": "No electricity in Delhi ward 5 for 3 days",
            "language": "en",
            "category": "Electricity"
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for i, complaint in enumerate(test_complaints, 1):
            print(f"\n{i}. Complaint: {complaint['transcript'][:50]}...")
            
            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/enhanced/process-complaint",
                    json=complaint,
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    print(f"   ✓ Session ID: {result['session_id']}")
                    print(f"   ✓ Vulgarity Detected: {result['vulgarity_check']['detected']}")
                    print(f"   ✓ Summary: {result['summary']['summary']}")
                    print(f"   ✓ Urgency: {result['summary']['urgency']}")
                    print(f"   ✓ Should Continue: {result['should_continue']}")
                    
                    if result.get('state_schemes'):
                        print(f"   ✓ Schemes Found: {len(result['state_schemes'])}")
                        print(f"   ✓ First Scheme: {result['state_schemes'][0]['name']}")
                    
                    print(f"   ✓ Response: {result['response_message'][complaint['language']][:100]}...")
                else:
                    print(f"   ✗ Error: {response.status_code}")
            except Exception as e:
                print(f"   ✗ Exception: {e}")


async def test_health_check():
    """Test health endpoint."""
    print("\n" + "="*60)
    print("TEST 0: HEALTH CHECK")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/v1/enhanced/health", timeout=5.0)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Status: {result['status']}")
                print(f"✓ Service: {result['service']}")
                print(f"✓ Features: {', '.join(result['features'])}")
            else:
                print(f"✗ Error: {response.status_code}")
        except Exception as e:
            print(f"✗ Server not running or not accessible: {e}")
            print("\nPlease start the server first:")
            print("  cd /Users/ashwinagarkhed/integration1")
            print("  python -m uvicorn backend.app.main:app --reload --port 8000")
            return False
    
    return True


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ENHANCED FEATURES TEST SUITE")
    print("="*60)
    
    # Check if server is running
    server_running = await test_health_check()
    
    if not server_running:
        return
    
    # Run all tests
    await test_vulgarity_detection()
    await test_ai_summary()
    await test_state_schemes()
    await test_complete_flow()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
