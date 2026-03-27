#!/usr/bin/env python3
"""
Quick Start: Sentence-Level Multilingual Language Detection

This script demonstrates the simplest way to use the new sentence-level
language detection feature for handling multiple languages in different
sentences.

Usage:
  python quickstart_sentence_detection.py

Features demonstrated:
  ✓ Single language text (control)
  ✓ Mixed-language text (code-switching)
  ✓ Per-segment language codes
  ✓ TTS format for synthesis
"""

import asyncio
import sys
import os

sys.path.insert(0, '/Users/ashwinagarkhed/integration1')
sys.path.insert(0, '/Users/ashwinagarkhed/integration1/awaaz')


async def demo_basic_detection():
    """Demo 1: Basic sentence-level detection"""
    print("\n" + "="*80)
    print("DEMO 1: BASIC SENTENCE-LEVEL LANGUAGE DETECTION")
    print("="*80)
    
    from awaaz.src.pipeline.sentence_language_detector import SentenceLevelLanguageDetector
    
    detector = SentenceLevelLanguageDetector()
    
    # Test case 1: Pure Hindi
    print("\n📝 Test Case 1: Pure Hindi")
    text1 = "नमस्ते, मेरा नाम राज है। मुझे पानी की समस्या है।"
    print(f"Input: {text1}")
    
    prediction1 = await detector.detect_multilingual_sentences(text1)
    print(f"\nResults:")
    print(f"  Primary Language: {prediction1.primary_language}")
    print(f"  Code-Switched: {prediction1.is_code_switched}")
    print(f"  Segments: {len(prediction1.segments)}")
    
    for i, seg in enumerate(prediction1.segments, 1):
        print(f"    [{i}] {seg.language_code}: \"{seg.text}\" (conf={seg.confidence:.2f})")
    
    # Test case 2: Mixed Hindi + English
    print("\n📝 Test Case 2: Mixed Hindi + English")
    text2 = "नमस्ते। I need to file a complaint. मुझे बिजली की समस्या है।"
    print(f"Input: {text2}")
    
    prediction2 = await detector.detect_multilingual_sentences(text2)
    print(f"\nResults:")
    print(f"  Primary Language: {prediction2.primary_language}")
    print(f"  Code-Switched: {prediction2.is_code_switched} ⬅️ Multiple languages detected!")
    print(f"  Language Distribution: {prediction2.language_distribution}")
    print(f"  Segments: {len(prediction2.segments)}")
    
    for i, seg in enumerate(prediction2.segments, 1):
        print(f"    [{i}] {seg.language_code}: \"{seg.text}\" (conf={seg.confidence:.2f})")


async def demo_tts_format():
    """Demo 2: Getting TTS-ready format"""
    print("\n" + "="*80)
    print("DEMO 2: TTS-READY FORMAT (For Sarvam Synthesis)")
    print("="*80)
    
    from awaaz.src.pipeline.sentence_language_detector import SentenceLevelLanguageDetector
    
    detector = SentenceLevelLanguageDetector()
    
    text = "नमस्ते, मेरा नाम राज है। I have a water problem। मैं शिकायत दर्ज करना चाहता हूं।"
    print(f"\nInput: {text}")
    
    prediction = await detector.detect_multilingual_sentences(text)
    
    print(f"\n✓ Detected {len(prediction.segments)} segments for TTS synthesis:")
    print(f"  Primary Language: {prediction.primary_language}")
    print(f"  Code-Switched: {prediction.is_code_switched}\n")
    
    # Format for TTS
    tts_format = detector.format_predictions_for_tts(prediction)
    
    for i, segment in enumerate(tts_format, 1):
        print(f"[Segment {i}] → Language: {segment['language']}")
        print(f"  Text: \"{segment['text']}\"")
        print(f"  Confidence: {segment['confidence']:.2f}")
        print(f"  Position: {segment['start_idx']}-{segment['end_idx']}")
        print()
    
    print("💡 Each segment can now be synthesized with its language-specific voice!")


async def demo_predictions_api():
    """Demo 3: Using the Predictions API"""
    print("\n" + "="*80)
    print("DEMO 3: MULTILINGUAL PREDICTIONS API")
    print("="*80)
    
    from awaaz.src.pipeline.multilingual_predictions import get_multilingual_predictions
    
    text = "नमस्ते। I am filing a complaint. मेरे घर में पानी नहीं है।"
    print(f"\nInput: {text}")
    
    # Get predictions using the API
    predictions = await get_multilingual_predictions(text)
    
    print(f"\nPredictions API Results:")
    print(f"  ✓ Primary Language: {predictions['primary_language']}")
    print(f"  ✓ Code-Switched: {predictions['is_code_switched']}")
    print(f"  ✓ Total Segments: {len(predictions['segments'])}")
    print(f"  ✓ Language Distribution: {predictions['language_distribution']}")
    print(f"  ✓ Segmentation Script: {predictions['metadata']['segmentation_script']}")
    
    print(f"\nPer-Segment Breakdown:")
    for i, segment in enumerate(predictions['segments'], 1):
        print(f"  [{i}] {segment['language']:3s} - \"{segment['text'][:40]}...\"")


async def demo_consolidation():
    """Demo 4: Understanding consolidated results"""
    print("\n" + "="*80)
    print("DEMO 4: UNDERSTANDING PREDICTIONS")
    print("="*80)
    
    from awaaz.src.pipeline.sentence_language_detector import SentenceLevelLanguageDetector
    
    detector = SentenceLevelLanguageDetector()
    
    text = "नमस्ते, मेरा नाम राज है। I need help with water supply। मेरे घर में पानी नहीं है।"
    print(f"\nInput: {text}")
    
    prediction = await detector.detect_multilingual_sentences(text)
    
    print(f"\n📊 PREDICTION ANALYSIS:")
    print(f"  General Info:")
    print(f"    • Total Segments: {len(prediction.segments)}")
    print(f"    • Primary Language: {prediction.primary_language}")
    print(f"    • Primary Confidence: {prediction.primary_confidence:.2f}")
    print(f"    • Is Code-Switched: {prediction.is_code_switched}")
    
    print(f"\n  Language Distribution:")
    for lang, pct in prediction.language_distribution.items():
        bar_length = int(pct * 30)
        bar = "█" * bar_length + "░" * (30 - bar_length)
        print(f"    {lang:3s}: {bar} {pct:.1%}")
    
    print(f"\n  Per-Segment Details:")
    for i, seg in enumerate(prediction.segments, 1):
        print(f"    Segment {i}:")
        print(f"      Text: \"{seg.text}\"")
        print(f"      Language: {seg.language_code}")
        print(f"      Confidence: {seg.confidence:.2f}")
        print(f"      Position: [{seg.start_idx}:{seg.end_idx}]")


async def main():
    """Run all demos"""
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + "SENTENCE-LEVEL MULTILINGUAL LANGUAGE DETECTION - QUICKSTART".center(78) + "║")
    print("╚" + "═"*78 + "╝")
    
    print("\n⚙️  Checking configuration...")
    sarvam_key = os.getenv("SARVAM_API_KEY", "").strip()
    if sarvam_key:
        print("  ✅ SARVAM_API_KEY is set")
    else:
        print("  ⚠️  SARVAM_API_KEY not set (will use fallback detection)")
        print("     To enable Sarvam: export SARVAM_API_KEY=\"your-key\"")
    
    try:
        # Run demos
        await demo_basic_detection()
        await demo_tts_format()
        await demo_predictions_api()
        await demo_consolidation()
        
        # Summary
        print("\n" + "="*80)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*80)
        
        print("\n📚 Next Steps:")
        print("  1. Review documentation:")
        print("     - SENTENCE_LEVEL_MULTILINGUAL_DETECTION.md")
        print("     - IMPLEMENTATION_SUMMARY_SENTENCE_LEVEL_DETECTION.md")
        
        print("\n  2. Run full test suite:")
        print("     python test_sentence_multilingual.py")
        
        print("\n  3. Try the API endpoint:")
        print("     python example_multilingual_api.py")
        
        print("\n  4. Integrate into your system:")
        print("     from awaaz.src.pipeline.multilingual_predictions import get_multilingual_predictions")
        print("     predictions = await get_multilingual_predictions(transcript)")
        print("     for segment in predictions['segments']:")
        print("         # Process each segment with its language code")
        
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error running demos: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
