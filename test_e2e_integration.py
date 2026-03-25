#!/usr/bin/env python3
"""
END-TO-END INTEGRATION TEST
===========================
Tests the complete flow: Voice → Database → SMS Notification

This test verifies:
1. Database connectivity with Neon
2. Language detection accuracy
3. Department routing logic
4. SMS notification sending (dry-run mode)
5. Complete complaint pipeline
"""

import sys
import os
sys.path.insert(0, '/home/parth/Desktop/indiainnovates/digital_democracy_ai_calling')

from dotenv import load_dotenv
load_dotenv('/home/parth/Desktop/indiainnovates/digital_democracy_ai_calling/.env', override=True)

# Set dry-run mode for testing
os.environ["SMS_DRY_RUN"] = "true"

import json
import logging
from datetime import datetime
from uuid import uuid4

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Test data
TEST_COMPLAINTS = [
    {
        "name": "Fire Emergency (Hindi)",
        "transcript": "आग लगी है! आग लगी है! तुरंत मदद करो! बहुत खतरनाक है!",
        "language": "hi",
        "phone": "9876543210",
        "expected_dept": "fire",
        "expected_urgency": "CRITICAL"
    },
    {
        "name": "Police - Robbery (English)",
        "transcript": "There has been a robbery. Thieves broke into my house. Please send police immediately!",
        "language": "en",
        "phone": "8765432109",
        "expected_dept": "police",
        "expected_urgency": "CRITICAL"
    },
    {
        "name": "Health Issue (Tamil)",
        "transcript": "என் உடல் நன்றாக இல்லை. நான் ஆஸ்பத்திரிக்கு செல்ல வேண்டும்.",
        "language": "ta",
        "phone": "7654321098",
        "expected_dept": "health",
        "expected_urgency": "HIGH"
    },
    {
        "name": "Electricity Problem (Hindi)",
        "transcript": "बिजली नहीं है। पूरी सड़क में बिजली गई है। कृपया ठीक करो।",
        "language": "hi",
        "phone": "6543210987",
        "expected_dept": "electricity",
        "expected_urgency": "HIGH"
    },
    {
        "name": "General Complaint (English)",
        "transcript": "I want to report a broken street light on my street.",
        "language": "en",
        "phone": "5432109876",
        "expected_dept": "general",
        "expected_urgency": "LOW"
    }
]

def print_header(text):
    """Print formatted header."""
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")

def print_test(test_num, name):
    """Print test header."""
    print(f"\n{'─'*80}")
    print(f"  TEST {test_num}: {name}")
    print(f"{'─'*80}\n")

def print_result(passed, message):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} - {message}")

def test_database_connection():
    """Test 1: Database connectivity."""
    print_test(1, "Database Connection")
    
    try:
        import psycopg2
        from database_router import get_db_connection
        
        print("  Connecting to Neon Database...")
        conn = get_db_connection()
        
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM complaints")
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            print_result(True, f"Connected successfully. Existing complaints: {count}")
            return True
        else:
            print_result(False, "Connection returned None")
            return False
    
    except Exception as e:
        print_result(False, f"Connection failed: {e}")
        return False

def test_language_detection():
    """Test 2: Language detection accuracy."""
    print_test(2, "Language Detection Accuracy")
    
    try:
        from unified_stt_service import detect_language
        
        test_cases = [
            ("आग लगी है!", "hi", "Hindi"),
            ("There has been a robbery.", "en", "English"),
            ("என் உடல் நன்றாக இல்லை.", "ta", "Tamil"),
            ("తెలుగు ভাষ", "te", "Telugu"),
        ]
        
        all_passed = True
        for text, expected_code, lang_name in test_cases:
            detected_code, detected_name = detect_language(text)
            
            if detected_code == expected_code:
                print_result(True, f"{lang_name} correctly detected: {detected_code} ({detected_name})")
            else:
                print_result(False, f"{lang_name}: Expected {expected_code}, got {detected_code}")
                all_passed = False
        
        return all_passed
    
    except Exception as e:
        print_result(False, f"Language detection failed: {e}")
        return False

def test_department_routing():
    """Test 3: Department routing logic."""
    print_test(3, "Department Routing Logic")
    
    try:
        from database_router import route_complaint
        
        all_passed = True
        for complaint in TEST_COMPLAINTS[:3]:  # Test first 3
            routing = route_complaint(
                transcript=complaint["transcript"],
                urgency=complaint["expected_urgency"],
                keywords=[complaint["transcript"][:20]],
                language=complaint["language"]
            )
            
            dept = routing.get("department", "").lower()
            expected = complaint["expected_dept"].lower()
            
            if dept == expected:
                confidence = routing.get("confidence", 0)
                print_result(True, f"{complaint['name']}: {dept} (confidence: {confidence:.0f}%)")
            else:
                print_result(False, f"{complaint['name']}: Expected {expected}, got {dept}")
                all_passed = False
        
        return all_passed
    
    except Exception as e:
        print_result(False, f"Routing test failed: {e}")
        return False

def test_sms_notifications():
    """Test 4: SMS notification sending (dry-run)."""
    print_test(4, "SMS Notifications (DRY-RUN)")
    
    try:
        from sms_notifier import TwilioSMSNotifier
        
        notifier = TwilioSMSNotifier()
        
        if not notifier.client and not notifier.dry_run:
            print_result(False, "SMS notifier not configured")
            return False
        
        all_passed = True
        
        # Test sending SMS for each complaint type
        for i, complaint in enumerate(TEST_COMPLAINTS[:2]):
            result = notifier.send_complaint_acknowledgment(
                phone_number=complaint["phone"],
                complaint_id=f"TEST-{i:03d}",
                department=complaint["expected_dept"],
                urgency=complaint["expected_urgency"],
                language=complaint["language"]
            )
            
            if result.get("success"):
                print_result(True, f"SMS for {complaint['name']}: {complaint['phone']}")
            else:
                print_result(False, f"SMS failed: {result.get('error')}")
                all_passed = False
        
        return all_passed
    
    except Exception as e:
        print_result(False, f"SMS test failed: {e}")
        return False

def test_complete_pipeline():
    """Test 5: Complete complaint pipeline."""
    print_test(5, "Complete Complaint Pipeline")
    
    try:
        from database_router import route_complaint, save_complaint_to_db
        from sms_notifier import notify_complaint_received
        from unified_stt_service import detect_language
        
        all_passed = True
        
        for i, complaint in enumerate(TEST_COMPLAINTS):
            session_id = f"TEST-{i:03d}-{str(uuid4())[:8]}"
            
            print(f"\n  Processing: {complaint['name']}")
            print(f"    Session ID: {session_id}")
            
            # Step 1: Detect language
            detected_code, detected_name = detect_language(complaint["transcript"])
            print(f"    Language: {detected_name} ({detected_code})")
            
            # Step 2: Route complaint
            routing = route_complaint(
                transcript=complaint["transcript"],
                urgency=complaint["expected_urgency"],
                keywords=[complaint["transcript"][:20]],
                language=detected_code
            )
            print(f"    Department: {routing['department']} (confidence: {routing['confidence']:.0f}%)")
            
            # Step 3: Save to database
            db_saved = save_complaint_to_db(
                session_id=session_id,
                transcript=complaint["transcript"],
                language_code=detected_code,
                urgency_level=complaint["expected_urgency"],
                keywords=[complaint["transcript"][:20]],
                routing_info=routing
            )
            
            if db_saved:
                print(f"    ✅ Saved to database")
            else:
                print(f"    ⚠️ Database save failed")
            
            # Step 4: Send SMS
            complaint_data = {
                "session_id": session_id,
                "department_assigned": routing['department'],
                "urgency_level": complaint["expected_urgency"],
                "transcript": complaint["transcript"][:50]
            }
            
            sms_result = notify_complaint_received(
                complaint_data=complaint_data,
                phone_number=complaint["phone"],
                language=detected_code
            )
            
            if sms_result.get("success"):
                if sms_result.get("dry_run"):
                    print(f"    ✅ SMS (dry-run) ready for {sms_result['phone']}")
                else:
                    print(f"    ✅ SMS sent to {sms_result['phone']}")
            else:
                print(f"    ⚠️ SMS failed: {sms_result.get('error')}")
        
        return True
    
    except Exception as e:
        print_result(False, f"Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests."""
    print_header("🔧 END-TO-END INTEGRATION TEST SUITE")
    
    print("Configuration:")
    print(f"  Database: {os.getenv('DATABASE_URL', 'NOT SET')[:60]}...")
    print(f"  SMS Mode: {'DRY-RUN' if os.getenv('SMS_DRY_RUN', 'false').lower() == 'true' else 'PRODUCTION'}")
    print(f"  Twilio Account: {os.getenv('TWILIO_ACCOUNT_SID', 'NOT SET')[:20]}...")
    
    results = {}
    
    # Run tests
    results["Database"] = test_database_connection()
    results["Language Detection"] = test_language_detection()
    results["Department Routing"] = test_department_routing()
    results["SMS Notifications"] = test_sms_notifications()
    results["Complete Pipeline"] = test_complete_pipeline()
    
    # Summary
    print_header("📊 TEST SUMMARY")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status:12} - {test_name}")
    
    total_passed = sum(1 for v in results.values() if v)
    total_tests = len(results)
    
    print(f"\n  Overall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n  🎉 ALL TESTS PASSED!\n")
        return 0
    else:
        print(f"\n  ⚠️  {total_tests - total_passed} test(s) failed\n")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
