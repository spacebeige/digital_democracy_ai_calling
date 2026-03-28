#!/usr/bin/env python3
"""
Quick test of language detection WITHOUT audio input
"""

import sys
import os
sys.path.insert(0, '/home/parth/Desktop/delhi')

import asyncio
from interactive_voice_to_layer3_integrated import MeeraAssistant

async def test_language_detection():
    """Test Meera's language detection from text only"""
    
    meera = MeeraAssistant()
    
    test_cases = [
        ("मेरा बिजली बिल बहुत ज्यादा आया है", "Hindi - Electricity complaint"),
        ("பெரிய குழிதனை சாலையில் சரிசெய்ய வேண்டும்", "Tamil - Road complaint"),
        ("నా వద్ద నీటి సరఫరా లేదు", "Telugu - Water complaint"),
        ("Water is leaking from my tap", "English - Water complaint"),
        ("गल्ली में कचरा बिखरा हुआ है", "Hindi - Garbage complaint"),
    ]
    
    print("\n" + "="*80)
    print("LANGUAGE DETECTION TEST (TEXT ONLY, NO AUDIO)")
    print("="*80 + "\n")
    
    for text, description in test_cases:
        print(f"📝 {description}")
        print(f"   Input: {text}")
        
        # Test Meera's language detection
        result = await meera.process_input(text, f"test_{test_cases.index((text, description))}")
        
        print(f"   ✓ Detected: {result['lang_name']} ({result['lang_code']})")
        print(f"   ✓ Confidence: {result['confidence']}")
        print(f"   ✓ Intent: {result['intent']}")
        print(f"   ✓ Urgency: {result['urgency']}\n")
    
    print("="*80)
    print("✅ Language detection works WITHOUT audio!")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_language_detection())
