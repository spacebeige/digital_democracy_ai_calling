#!/usr/bin/env python3
"""
Voice-to-NLP Analysis Integration Script
=========================================

Captures live voice input and automatically sends transcript to post-call analysis API.

Usage:
    python3 voice_to_analysis_integration.py [--mode mic|file] [--input FILE] [--lang LANG]

This script:
1. Records live voice from microphone OR loads audio file
2. Transcribes using awaaz STT pipeline
3. Sends transcript to post-call analyzer API
4. Displays analysis results
"""

import asyncio
import os
import sys
import json
import argparse
import httpx
from datetime import datetime
from uuid import uuid4

# Add awaaz to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'awaaz'))

try:
    from awaaz.src.pipeline.stt import STTProcessor
    AWAAZ_AVAILABLE = True
except ImportError:
    print("❌ awaaz module not available")
    AWAAZ_AVAILABLE = False


# Configuration
API_BASE_URL = "http://127.0.0.1:8000"
API_ENDPOINT = f"{API_BASE_URL}/api/v1/analysis/analyze-call"
HEALTH_CHECK = f"{API_BASE_URL}/api/v1/analysis/health"


async def check_api_health():
    """Check if analysis API is running"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(HEALTH_CHECK)
            if response.status_code == 200:
                print(f"✅ Analysis API is healthy at {API_BASE_URL}")
                return True
    except Exception as e:
        print(f"❌ Analysis API not available: {e}")
        return False


async def transcribe_audio(audio_path: str, language: str = None):
    """Transcribe audio using awaaz STT pipeline"""
    print(f"\n[STT] Transcribing audio: {audio_path}")
    
    try:
        stt = STTProcessor()
        result = await stt.transcribe(
            audio_path,
            language="auto" if not language else language
        )
        
        if result and result.text:
            print(f"✓ Transcription complete")
            print(f"  Language: {result.detected_language or 'auto-detected'}")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Text: {result.text}")
            return result.text
        else:
            print("❌ STT failed to transcribe")
            return None
            
    except Exception as e:
        print(f"❌ STT error: {e}")
        return None


async def send_to_analysis_api(transcript: str, call_duration: float = 180, language: str = None):
    """Send transcript to post-call analysis API"""
    print(f"\n[API] Sending to Analysis Endpoint...")
    
    call_id = f"call_{uuid4().hex[:12]}"
    session_id = f"session_{uuid4().hex[:12]}"
    
    payload = {
        "call_id": call_id,
        "session_id": session_id,
        "transcript": transcript,
        "call_duration_seconds": call_duration,
        "caller_phone": "+919876543210",  # Demo phone
        "detected_language": language
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                API_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Analysis received (ID: {result.get('analysis_id', 'N/A')})")
                return result
            else:
                print(f"❌ API Error ({response.status_code}): {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return None


def print_analysis_results(analysis: dict):
    """Pretty print analysis results"""
    if not analysis:
        return
    
    print("\n" + "=" * 80)
    print("📊 POST-CALL ANALYSIS RESULTS")
    print("=" * 80)
    
    # Status
    print("\n🔍 STATUS")
    print(f"  Analysis ID: {analysis.get('analysis_id', 'N/A')}")
    print(f"  Status: {analysis.get('status', 'N/A')}")
    print(f"  Processing Time: {analysis.get('processing_time_ms', 0):.1f}ms")
    
    # Classification
    if analysis.get('classification'):
        c = analysis['classification']
        print("\n🗣️  CLASSIFICATION")
        print(f"  Language: {c.get('language', 'N/A')}")
        print(f"  Intent: {c.get('intent', 'N/A')}")
        print(f"  Edge Case: {c.get('edge_case', 'N/A')}")
        print(f"  Confidence: {c.get('confidence', 0):.2f}")
    
    # Routing
    if analysis.get('routing'):
        r = analysis['routing']
        print("\n🎯 ROUTING & ACTION")
        print(f"  Department: {r.get('department_name', 'N/A')} ({r.get('department_id', 'N/A')})")
        print(f"  Category: {r.get('issue_category', 'N/A')}")
        print(f"  Priority: {r.get('priority_level', 'N/A')}")
        print(f"  Suggested Action: {r.get('suggested_action', 'N/A')}")
        print(f"  Confidence: {r.get('routing_confidence', 0):.2f}")
    
    # Flags
    print("\n⚠️  FLAGS")
    print(f"  Emergency: {'🔴 YES' if analysis.get('is_emergency') else '🟢 NO'}")
    print(f"  Abuse: {'🔴 YES' if analysis.get('is_abuse') else '🟢 NO'}")
    print(f"  Genuine Complaint: {'✅ YES' if analysis.get('is_genuine_complaint') else '❌ NO'}")
    
    # Metrics
    print("\n📈 METRICS")
    print(f"  Transcript Length: {analysis.get('transcript_length', 0)} chars")
    print(f"  Word Count: {analysis.get('word_count', 0)}")
    
    # Summary
    print("\n📝 SUMMARY")
    print(f"  {analysis.get('summary', 'N/A')}")
    
    print("\n" + "=" * 80 + "\n")


async def main():
    """Main integration flow"""
    print("\n" + "=" * 80)
    print("  🚀 VOICE-TO-NLP ANALYSIS INTEGRATION")
    print("=" * 80)
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Capture voice and analyze with post-call NLP pipeline"
    )
    parser.add_argument(
        "--mode",
        choices=["mic", "file"],
        default="mic",
        help="Input mode: microphone or audio file"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="",
        help="Audio file path (required if --mode file)"
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="",
        help="Language code (hi, en, ta, mr, etc.)"
    )
    parser.add_argument(
        "--api",
        type=str,
        default=API_BASE_URL,
        help="Analysis API base URL"
    )
    args = parser.parse_args()
    
    # Check API availability
    print(f"\n[INIT] Checking API at {args.api}...")
    if not await check_api_health():
        print("\n❌ Analysis API is not running!")
        print(f"\nStart it with:")
        print(f"  cd backend")
        print(f"  python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
        sys.exit(1)
    
    # Get audio input
    if args.mode == "file":
        audio_path = args.input
        if not audio_path:
            print("❌ --input is required with --mode file")
            sys.exit(1)
        if not os.path.exists(audio_path):
            print(f"❌ File not found: {audio_path}")
            sys.exit(1)
        print(f"✓ Using audio file: {audio_path}")
    else:
        # Try to record from microphone
        try:
            from awaaz.awaaz_recorder import Recorder, VADEngine
            print("\n[REC] Recording live audio from microphone...")
            print("🎤 Speak now (10s max, stops on 1.5s silence)...")
            
            vad = VADEngine(aggressiveness=2)
            recorder = Recorder(vad=vad, device_index=None)
            audio = recorder.record(
                max_duration_s=10,
                silence_ms=1500,
                calibration=None
            )
            
            if not audio:
                print("❌ Recording failed")
                sys.exit(1)
            
            # Save temporary file
            import soundfile as sf
            audio_path = "/tmp/voice_input_temp.wav"
            sf.write(audio_path, audio, 16000)
            print(f"✓ Audio recorded ({len(audio)/16000:.1f}s): {audio_path}")
            
        except ImportError:
            print("❌ awaaz_recorder not available")
            print("   Please install or use --mode file to test with audio file")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Recording failed: {e}")
            sys.exit(1)
    
    # Transcribe audio
    if not AWAAZ_AVAILABLE:
        print("❌ awaaz module not available")
        sys.exit(1)
    
    transcript = await transcribe_audio(audio_path, args.lang)
    if not transcript:
        print("❌ Failed to get transcript")
        sys.exit(1)
    
    # Send to analysis API
    analysis = await send_to_analysis_api(
        transcript,
        call_duration=10,
        language=args.lang if args.lang else None
    )
    
    # Display results
    if analysis:
        print_analysis_results(analysis)
        print("✅ Voice-to-NLP analysis complete!")
    else:
        print("❌ Analysis failed")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
