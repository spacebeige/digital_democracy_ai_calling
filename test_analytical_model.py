#!/usr/bin/env python3
"""
Grievance System v2.0 - Direct Processing Example
==================================================
Demonstrates using the analytical model processor directly
without the REST API, useful for testing and batch processing.

Usage:
    python test_analytical_model.py
    python test_analytical_model.py --text "There is no electricity"
    python test_analytical_model.py --audio complaint.wav
"""

import sys
import json
import argparse
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/Users/ashwinagarkhed/integration1')

from models.grievance_models import create_session_id
from analytics.analytical_model import create_processor
from core.nlp_routing import classify_urgency, classify_intent


def example_text_grievance():
    """Process a text grievance."""
    print("\n" + "="*80)
    print("  EXAMPLE 1: TEXT-BASED GRIEVANCE (English)")
    print("="*80 + "\n")
    
    # Initialize processor
    processor = create_processor(use_groq=False)  # Set to True to use Groq
    
    # Grievance data
    session_id = create_session_id()
    transcript = "There has been no electricity for the past 24 hours. My whole neighborhood is affected. Please help urgently."
    audio_data = np.zeros(16000)  # Dummy audio (1 second silence)
    sample_rate = 16000
    
    print(f"Processing: {transcript}\n")
    
    # Process
    analytical_model = processor.process_grievance(
        session_id=session_id,
        transcript=transcript,
        audio_data=audio_data,
        sample_rate=sample_rate,
        detected_language="en",
        state="maharashtra",
    )
    
    # Display results
    print(f"Session ID: {session_id}")
    print(f"Timestamp: {analytical_model.timestamp.isoformat()}")
    print(f"\n📊 ANALYSIS RESULTS:")
    print(f"  Intent: {analytical_model.intent.primary_intent}")
    print(f"  Urgency: {analytical_model.intent.urgency_level.value} (Score: {analytical_model.intent.urgency_score}/4)")
    print(f"  Confidence: {analytical_model.intent.confidence}/4 ({analytical_model.intent.confidence_reason})")
    print(f"  Keywords: {', '.join(analytical_model.intent.matched_keywords)}")
    
    print(f"\n🎯 ROUTING:")
    print(f"  Department: {analytical_model.routing.primary_department}")
    if analytical_model.routing.mapped_service:
        svc = analytical_model.routing.mapped_service
        print(f"  Service: {svc.service_name}")
        print(f"  Contact: {svc.contact_info}")
        print(f"  SLA: {svc.sla_minutes} minutes")
    
    print(f"\n🤖 AI SUMMARY:")
    print(f"  {analytical_model.ai_summary}")
    
    print(f"\n⚠️  EMOTION ANALYSIS:")
    emotion = analytical_model.emotion
    print(f"  Detected: {emotion.detected_emotion.value}")
    print(f"  Anger: {emotion.anger_score:.1%}")
    print(f"  Stress: {emotion.stress_level:.1%}")
    print(f"  Reasoning: {emotion.reasoning}")
    
    if analytical_model.severity_flags:
        print(f"\n🚨 SEVERITY FLAGS:")
        for flag in analytical_model.severity_flags:
            print(f"  - {flag}")
    
    print(f"\n✅ Follow-up Needed: {analytical_model.follow_up_needed}")
    
    # Save JSON
    json_dict = analytical_model.to_dict()
    print(f"\n💾 JSON Output Saved (sample):")
    print(json.dumps(json_dict, indent=2)[:500] + "...\n")
    
    return analytical_model


def example_hindi_grievance():
    """Process a Hindi grievance."""
    print("\n" + "="*80)
    print("  EXAMPLE 2: HINDI GRIEVANCE - WATER SHORTAGE")
    print("="*80 + "\n")
    
    processor = create_processor(use_groq=False)
    
    session_id = create_session_id()
    transcript = "कल से नल से पानी नहीं आ रहा है। पूरे मोहल्ले में यही समस्या है। क्या तुम हमारी मदद कर सकते हो?"
    audio_data = np.zeros(16000)
    
    print(f"Processing: {transcript}\n")
    
    analytical_model = processor.process_grievance(
        session_id=session_id,
        transcript=transcript,
        audio_data=audio_data,
        sample_rate=16000,
        detected_language="hi",
        state="maharashtra",
    )
    
    print(f"Session ID: {session_id}")
    print(f"Intent: {analytical_model.intent.primary_intent}")
    print(f"Urgency: {analytical_model.intent.urgency_level.value}")
    print(f"Keywords: {', '.join(analytical_model.intent.matched_keywords)}")
    print(f"Department: {analytical_model.routing.primary_department}")
    if analytical_model.routing.mapped_service:
        print(f"Contact: {analytical_model.routing.mapped_service.contact_info}")
    print(f"\nSummary: {analytical_model.ai_summary}\n")


def example_critical_emergency():
    """Process a critical emergency."""
    print("\n" + "="*80)
    print("  EXAMPLE 3: CRITICAL EMERGENCY - FIRE")
    print("="*80 + "\n")
    
    processor = create_processor(use_groq=False)
    
    session_id = create_session_id()
    transcript = "आग! आग लगी! मेरे घर में आग है! जल्दी मदद करो! तुरंत बचाओ!"
    audio_data = np.random.normal(0, 0.1, 16000)  # Simulated stressed speech
    
    print(f"Processing: {transcript}\n")
    
    analytical_model = processor.process_grievance(
        session_id=session_id,
        transcript=transcript,
        audio_data=audio_data,
        sample_rate=16000,
        detected_language="hi",
        state="maharashtra",
    )
    
    print(f"Session ID: {session_id}")
    print(f"🚨 URGENCY: {analytical_model.intent.urgency_level.value}")
    print(f"Department: {analytical_model.routing.primary_department}")
    print(f"Priority: {analytical_model.routing.priority_level}/5  (1=HIGHEST)")
    print(f"Contact: {analytical_model.routing.mapped_service.contact_info if analytical_model.routing.mapped_service else 'Emergency: 101'}")
    print(f"\nEmotion Analysis:")
    print(f"  Anger: {analytical_model.emotion.anger_score:.0%}")
    print(f"  Stress: {analytical_model.emotion.stress_level:.0%}")
    print(f"\nSeverity: {', '.join(analytical_model.severity_flags)}\n")


def example_audio_grievance():
    """Example showing how to process audio files."""
    print("\n" + "="*80)
    print("  EXAMPLE 4: AUDIO PROCESSING")
    print("="*80 + "\n")
    
    try:
        import soundfile as sf
        
        # Try to load an existing test audio file
        audio_files = [
            "/Users/ashwinagarkhed/integration1/awaaz/final_test.wav",
            "/Users/ashwinagarkhed/integration1/awaaz/multilang_test_en.wav",
        ]
        
        for audio_file in audio_files:
            try:
                audio_data, sample_rate = sf.read(audio_file)
                
                # Convert stereo to mono if needed
                if len(audio_data.shape) > 1:
                    audio_data = np.mean(audio_data, axis=1)
                
                print(f"Loaded: {audio_file}")
                print(f"  Sample Rate: {sample_rate} Hz")
                print(f"  Duration: {len(audio_data) / sample_rate:.1f} seconds\n")
                
                # In production, use STT service to transcribe
                # For demo, use mock transcript
                processor = create_processor(use_groq=False)
                speaker_id = create_session_id()
                
                analytical_model = processor.process_grievance(
                    session_id=speaker_id,
                    transcript="[Mock transcription from audio file]",
                    audio_data=audio_data,
                    sample_rate=sample_rate,
                    detected_language="en",
                    state="maharashtra",
                )
                
                print(f"✓ Audio analysis complete")
                print(f"  Emotion: {analytical_model.emotion.detected_emotion.value}")
                print(f"  Speech Duration: {analytical_model.vad_analysis.total_speech_duration:.1f}s")
                print(f"  Pause Pattern: {analytical_model.vad_analysis.pause_patterns}\n")
                
                break  # Process first available file
            
            except FileNotFoundError:
                continue
    
    except ImportError:
        print("Note: soundfile not installed. Skipping audio examples.\n")


def main():
    """Run examples."""
    parser = argparse.ArgumentParser(description="Test Grievance System v2.0")
    parser.add_argument("--text", help="Process text grievance")
    parser.add_argument("--audio", help="Process audio file")
    parser.add_argument("--all", action="store_true", help="Run all examples")
    
    args = parser.parse_args()
    
    if args.text:
        # Custom text
        processor = create_processor(use_groq=False)
        session_id = create_session_id()
        
        analytical_model = processor.process_grievance(
            session_id=session_id,
            transcript=args.text,
            audio_data=np.zeros(16000),
            sample_rate=16000,
            detected_language="en",
            state="maharashtra",
        )
        
        print(f"\n📊 Analysis of: {args.text}")
        print(f"Urgency: {analytical_model.intent.urgency_level.value}")
        print(f"Department: {analytical_model.routing.primary_department}")
        print(f"Summary: {analytical_model.ai_summary}\n")
    
    elif args.audio:
        try:
            import soundfile as sf
            audio_data, sample_rate = sf.read(args.audio)
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            processor = create_processor(use_groq=False)
            analytical_model = processor.process_grievance(
                session_id=create_session_id(),
                transcript="[Audio processed - mock transcript]",
                audio_data=audio_data,
                sample_rate=sample_rate,
                detected_language="en",
                state="maharashtra",
            )
            
            print(f"\n🎵 Audio Analysis: {args.audio}")
            print(f"Emotion: {analytical_model.emotion.detected_emotion.value}")
            print(f"Stress: {analytical_model.emotion.stress_level:.0%}\n")
        
        except ImportError:
            print("Error: soundfile not installed")
        except FileNotFoundError:
            print(f"Error: Audio file not found: {args.audio}")
    
    elif args.all:
        # Run all examples
        example_text_grievance()
        example_hindi_grievance()
        example_critical_emergency()
        example_audio_grievance()
    
    else:
        # Default: Run primary examples
        example_text_grievance()
        example_hindi_grievance()
        example_critical_emergency()
        
        print("\n" + "="*80)
        print("  USAGE OPTIONS")
        print("="*80)
        print("""
python test_analytical_model.py --text "Your grievance text"
python test_analytical_model.py --audio audio_file.wav
python test_analytical_model.py --all
        """)


if __name__ == "__main__":
    main()
