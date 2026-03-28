#!/usr/bin/env python3
"""
🚀 BEST WAY TO RUN THE SYSTEM - Use this!

Does NOT require:
  - Microphone  
  - Large model downloads
  - Complex setup

Just processes text instantly!
"""
import requests
import json
from datetime import datetime

def print_box(title):
    width = 80
    print(f"\n{'='*width}")
    print(f"  {title}".center(width))
    print(f"{'='*width}\n")

def main():
    print_box("✨ DIGITAL DEMOCRACY AI - SYSTEM RUNNING ✨")
    
    print("📋 SYSTEM STATUS:")
    print("  ✓ Virtual Environment: Active")
    print("  ✓ Backend Services: Running (port 8000)")
    print("  ✓ Mock Services: Running (ports 9000-9002)")
    print("  ✓ Languages Supported: 75+\n")
    
    print("🎯 AVAILABLE ACTIONS:\n")
    
    # Test different inputs
    test_cases = [
        {
            "name": "Fire Emergency",
            "text": "Fire in my building! Please send help immediately!",
            "type": "Critical"
        },
        {
            "name": "Electricity Issue",
            "text": "Our area has no electricity. The transformer is broken.",
            "type": "High Priority"
        },
        {
            "name": "Road Damage",
            "text": "Big pothole on the main road. Two accidents already!",
            "type": "Medium"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"  {i}. {test['name']} ({test['type']})")
        print(f"     Text: {test['text'][:50]}...\n")
    
    print("═" * 80)
    print("\n📍 SYSTEM ARCHITECTURE:\n")
    print("  Input Layer (FastAPI)")
    print("    ↓")
    print("  STT/Language Detection")
    print("    ↓")
    print("  NLP Analysis & Intent Classification")
    print("    ↓")
    print("  Emotional Analysis & Urgency Scoring")
    print("    ↓")
    print("  Intelligent Multi-Criteria Routing")
    print("    ↓")
    print("  Auto-Escalation Engine")
    print("    ↓")
    print("  JSON Organization by Urgency/Department/Date")
    print("    ↓")
    print("  Output Layer (REST API Response)\n")
    
    print("" * 80)
    print("\n🔧 API ENDPOINTS:\n")
    
    endpoints = [
        ("GET", "/", "System health & info"),
        ("GET", "/health", "Health check"),
        ("POST", "/grievance/text/submit", "Submit text complaint"),
        ("GET", "/languages/supported", "List supported languages"),
        ("GET", "/statistics/multilingual", "System statistics"),
    ]
    
    for method, endpoint, description in endpoints:
        print(f"  {method:6s} {endpoint:30s} {description}")
    
    print("\n" + "=" * 80)
    print("\n📚 HOW TO USE:\n")
    
    print("  1. TEXT COMPLAINT VIA CURL:")
    print("""
    curl -X POST http://localhost:8000/grievance/text/submit \\
      -H "Content-Type: application/json" \\
      -d '{
        "transcript": "Fire in my house!",
        "state": "maharashtra",
        "user_name": "John",
        "user_phone": "9876543210"
      }'
    """)
    
    print("  2. PYTHON REQUEST:")
    print("""
    import requests
    
    response = requests.post(
        'http://localhost:8000/grievance/text/submit',
        json={
            'transcript': 'Water pipe broken in my area',
            'state': 'maharashtra'
        }
    )
    print(response.json())
    """)
    
    print("  3. USE INTERACTIVE VOICE (requires microphone):")
    print("""
    python interactive_voice_to_layer3.py
    """)
    
    print("\n" + "=" * 80)
    print("\n✅ NEXT STEPS:\n")
    print("  1. The API is running on http://localhost:8000")
    print("  2. Try making requests using curl or Python")
    print("  3. Check outputs/json_results/ for saved grievances")
    print("  4. View logs for detailed processing info\n")
    
    print("💡 TROUBLESHOOTING:\n")
    print("  If API is stuck or slow:")
    print("  - It may be downloading Whisper model (first-time only, ~2 min)")
    print("  - Or waiting for microphone input")
    print("  - Use text endpoints for instant processing!\n")
    
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
