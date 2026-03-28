#!/usr/bin/env python3
"""
Quick test of simplified grievance system with Sarvam Ritu (TEXT MODE)
"""

import sys
import os
sys.path.insert(0, '/home/parth/Desktop/delhi')

import asyncio
from grievance_simple_ritu import (
    generate_groq_response, GROQ_AVAILABLE, LANGUAGE_CONFIG,
    classify_urgency, detect_service_type, Colors, print_section
)

async def test_text_mode():
    """Test system with text input (no microphone)"""
    
    print_section("TESTING SIMPLIFIED SYSTEM (TEXT MODE)")
    
    test_complaints = [
        ("पानी नहीं आ रहा है। नल खराब हो गया।", "hi", "Water"),
        ("Road की बहुत खराब हालत है। बड़ा गड्ढा है।", "hi", "Road"),
        ("Electricity is off for 2 days!", "en", "Electricity"),
    ]
    
    for complaint, lang, expected_dept in test_complaints:
        print(f"\n📝 Complaint: {complaint}")
        print(f"   Language: {lang}")
        print(f"   Expected: {expected_dept}")
        
        # Step 1: Routing
        urgency, matched_keywords, conf = classify_urgency(complaint)
        service_type, service_keywords, _ = detect_service_type(complaint, matched_keywords)
        
        print(f"   ✓ Detected Dept: {service_type.upper()}")
        print(f"   ✓ Urgency: {urgency.name}")
        
        # Step 2: Generate response
        response = await generate_groq_response(
            complaint, lang, urgency.name, service_type, f"{service_type} Service"
        )
        
        print(f"   ✓ Response ({lang}): {response[:80]}...")
        print()
    
    print_section("✅ TEXT MODE TEST COMPLETE")

if __name__ == "__main__":
    asyncio.run(test_text_mode())
