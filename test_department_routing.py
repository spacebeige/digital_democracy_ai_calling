#!/usr/bin/env python3
"""
Test script to verify department routing is working correctly.
"""

import sys
import os
sys.path.insert(0, '/home/parth/Desktop/delhi')

from external_services.gov_services_map import detect_service_type, SERVICE_KEYWORDS
from core.nlp_routing import classify_urgency, classify_intent
from models.grievance_models import UrgencyLevel

# Test cases covering different departments
test_cases = [
    # Water complaints
    ("पानी नहीं आ रहा है", "water", "No water coming from tap"),
    ("नल टूट गया है पानी निकल रहा है", "water", "Tap is broken, water leaking"),
    ("Water leak in my kitchen", "water", "English water complaint"),
    
    # Road/Municipal complaints
    ("सड़क पर बहुत बड़ा गड्ढा है", "municipal", "Large pothole in road"),
    ("Road की बहुत खराब हालत है", "municipal", "Road is in bad condition"),
    ("Pothole on main street needs repair", "municipal", "Pothole in English"),
    
    # Electricity complaints
    ("बिजली चली गई है", "electricity", "Electricity is off"),
    ("मीटर खराब है", "electricity", "Meter is broken"),
    ("Power cut for 3 days", "electricity", "Power cut in English"),
    
    # Sanitation complaints
    ("गली में कचरा बिखरा हुआ है", "municipal", "Garbage scattered in alley"),
    ("कूड़े की सफाई नहीं हुई", "municipal", "Garbage not cleaned"),
    ("Trash collection not done", "municipal", "Garbage in English"),
    
    # Fire/Emergency
    ("आग लगी है!", "fire", "Fire emergency"),
    ("Fire in building!", "fire", "Fire in English"),
    
    # Police/Crime
    ("चोरी हो गई है", "police", "Theft occurred"),
    ("Robbery in my area", "police", "Crime in English"),
]

print("\n" + "=" * 80)
print("DEPARTMENT ROUTING VERIFICATION TEST")
print("=" * 80 + "\n")

passed = 0
failed = 0

for complaint, expected_dept, description in test_cases:
    # Step 1: Classify urgency (which populates matched_keywords)
    urgency, matched_keywords, confidence = classify_urgency(complaint)
    
    # Step 2: Detect service type
    service_type, service_keywords, may_escalate = detect_service_type(complaint, matched_keywords)
    
    # Check if routing matched expected department
    status = "✅ PASS" if service_type == expected_dept else "❌ FAIL"
    if service_type == expected_dept:
        passed += 1
    else:
        failed += 1
    
    print(f"{status} | {description}")
    print(f"  Input: \"{complaint}\"")
    print(f"  Expected: {expected_dept.upper()} | Got: {service_type.upper()}")
    if matched_keywords:
        print(f"  Keywords matched: {', '.join(matched_keywords[:3])}")
    if service_type != expected_dept:
        print(f"  ❌ MISMATCH - This should route to {expected_dept}, not {service_type}")
    print()

print("=" * 80)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print("=" * 80 + "\n")

if failed > 0:
    print("⚠️ Some tests failed! The routing logic needs adjustment.")
    sys.exit(1)
else:
    print("✅ All tests passed! Department routing is working correctly.")
    sys.exit(0)
