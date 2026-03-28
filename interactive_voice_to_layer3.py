#!/usr/bin/env python3
"""
INTERACTIVE VOICE → TRANSCRIPTION → LAYER 3 ROUTING
====================================================

Workflow:
1. Capture real voice input from microphone
2. Transcribe using STT
3. Send transcription to Layer 3 for intelligent routing
4. Show routing decision

Run with: python interactive_voice_to_layer3.py
"""

import sys
import os
import time
import requests
import json
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Audio libraries for microphone capture
try:
    import sounddevice as sd
    import soundfile as sf
    MICROPHONE_AVAILABLE = True
    SAMPLE_RATE = 16000
except ImportError:
    print("⚠️  sounddevice/soundfile not available - microphone disabled")
    MICROPHONE_AVAILABLE = False
    SAMPLE_RATE = 16000

# Configuration
STT_API = "http://localhost:9000"
BACKEND_API = "http://localhost:8000"

# Color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}\n")


def print_section(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'─'*80}{Colors.END}")
    print(f"{Colors.CYAN}  {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'─'*80}{Colors.END}\n")


def check_services():
    """Verify services are running."""
    services = {
        "STT Service": STT_API,
        "Backend API": BACKEND_API,
    }
    
    for name, url in services.items():
        try:
            resp = requests.get(f"{url}/", timeout=2)
            print(f"  {Colors.GREEN}✓{Colors.END} {name:20} OK")
        except:
            print(f"  {Colors.RED}✗{Colors.END} {name:20} FAILED")
            return False
    
    return True


def capture_microphone_audio(duration_seconds=10) -> str:
    """
    Capture audio from microphone using sounddevice.
    Returns path to WAV file.
    """
    if not MICROPHONE_AVAILABLE:
        print(f"{Colors.RED}✗{Colors.END} Microphone recording not available")
        return None
    
    try:
        print(f"\n{Colors.YELLOW}🎤 Initializing microphone...{Colors.END}")
        print(f"   Sample Rate: {SAMPLE_RATE} Hz")
        print(f"   Max Duration: {duration_seconds}s")
        
        print(f"\n{Colors.GREEN}🔴 RECORDING NOW - Speak your complaint!{Colors.END}")
        print(f"{Colors.YELLOW}   (Press Ctrl+C to stop, or wait {duration_seconds}s){Colors.END}\n")
        
        # Record audio from microphone
        audio_data = sd.rec(int(SAMPLE_RATE * duration_seconds), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
        sd.wait()  # Wait for recording to complete
        
        if audio_data is None or len(audio_data) == 0:
            print(f"{Colors.RED}✗ No audio captured{Colors.END}")
            return None
        
        # Save to file
        output_file = f"/tmp/voice_input_{uuid4().hex[:8]}.wav"
        sf.write(output_file, audio_data, SAMPLE_RATE)
        
        print(f"\n{Colors.GREEN}✓ Recording complete!{Colors.END}")
        print(f"   Duration: {len(audio_data) / SAMPLE_RATE:.1f}s")
        print(f"   Saved: {output_file}{Colors.END}")
        return output_file
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⏹️  Recording stopped by user{Colors.END}")
        return None
    except Exception as e:
        print(f"{Colors.RED}✗ Recording failed: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        return None


def record_sample_audio_file(filename: str) -> str:
    """
    Use existing audio file (for testing without mic).
    """
    if not os.path.exists(filename):
        print(f"{Colors.RED}✗ File not found: {filename}{Colors.END}")
        return None
    
    return filename


def transcribe_audio(audio_file: str) -> str:
    """
    Send audio to STT service for transcription.
    Returns transcription text.
    """
    print_section("🎤 STEP 1: SPEECH-TO-TEXT PROCESSING")
    
    print(f"  Sending audio to STT service...")
    print(f"  File: {audio_file}")
    
    try:
        with open(audio_file, "rb") as f:
            audio_data = f.read()
        
        response = requests.post(
            f"{STT_API}/transcribe",
            files={"file": ("audio.wav", audio_data)},
            timeout=30,
        )
        
        if response.status_code != 200:
            print(f"  {Colors.RED}✗ Error: {response.status_code}{Colors.END}")
            return None
        
        result = response.json()
        transcript = result.get("text", "").strip()
        
        if not transcript:
            print(f"  {Colors.RED}✗ No transcription returned{Colors.END}")
            return None
        
        print(f"\n  {Colors.GREEN}✓ Transcription:({Colors.END}")
        print(f"     {Colors.YELLOW}{transcript}{Colors.END}")
        
        return transcript
    
    except Exception as e:
        print(f"  {Colors.RED}✗ Error: {e}{Colors.END}")
        return None


def route_to_layer3(transcript: str) -> dict:
    """
    Send transcription to Layer 3 for intelligent routing.
    Returns routing decision.
    """
    print_section("🧠 STEP 2: LAYER 3 INTELLIGENT ROUTING")
    
    session_id = str(uuid4())[:13]
    
    print(f"  Sending transcript to Layer 3 router...")
    print(f"  Session ID: {Colors.CYAN}{session_id}{Colors.END}")
    
    try:
        response = requests.post(
            f"{BACKEND_API}/grievance/text/submit",
            json={
                "complaint_text": transcript,
                "user_name": "Voice User",
                "user_phone": "0000000000",
                "user_location": "Unknown",
            },
            timeout=30,
        )
        
        if response.status_code != 200:
            print(f"  {Colors.RED}✗ Routing failed: {response.status_code}{Colors.END}")
            print(f"     {response.text[:100]}")
            return None
        
        result = response.json()
        
        print(f"\n  {Colors.GREEN}✓ Routing Complete!{Colors.END}\n")
        
        return result
    
    except Exception as e:
        print(f"  {Colors.RED}✗ Error: {e}{Colors.END}")
        return None


def display_routing_decision(routing: dict):
    """Display the routing decision from Layer 3."""
    print_section("📊 ROUTING DECISION")
    
    if not routing:
        print(f"  {Colors.RED}No routing data available{Colors.END}")
        return
    
    # Emergency check
    is_emergency = routing.get("is_emergency", False)
    if is_emergency:
        print(f"  {Colors.RED}{Colors.BOLD}🚨 EMERGENCY DETECTED!{Colors.END}")
    else:
        print(f"  {Colors.GREEN}✓ Normal Complaint{Colors.END}")
    
    # Language & Intent
    print(f"\n  {Colors.BOLD}CLASSIFICATION:{Colors.END}")
    print(f"    • Language: {Colors.YELLOW}{routing.get('language', 'N/A')}{Colors.END}")
    print(f"    • Intent: {Colors.YELLOW}{routing.get('intent', 'N/A')}{Colors.END}")
    print(f"    • Category: {Colors.YELLOW}{routing.get('issue_category', 'N/A')}{Colors.END}")
    print(f"    • Confidence: {Colors.YELLOW}{routing.get('confidence', 0)*100:.0f}%{Colors.END}")
    
    # Routing info
    routing_data = routing.get("routing_data", {})
    if routing_data:
        print(f"\n  {Colors.BOLD}ROUTING ASSIGNMENT:{Colors.END}")
        print(f"    • Department: {Colors.CYAN}{routing_data.get('dept_id', 'N/A')}{Colors.END}")
        print(f"    • Priority: {Colors.CYAN}{routing_data.get('priority', 'N/A')}/5{Colors.END}")
        print(f"    • Summary: {Colors.CYAN}{routing_data.get('summary', 'N/A')[:80]}{Colors.END}")
    
    # Action
    print(f"\n  {Colors.BOLD}ACTION:{Colors.END}")
    print(f"    • Recommended: {Colors.GREEN}{routing.get('action', 'N/A')}{Colors.END}")
    
    # Audit trail
    if routing.get("audit_log"):
        print(f"\n  {Colors.BOLD}PROCESSING TRACE:{Colors.END}")
        for i, log in enumerate(routing.get("audit_log", []), 1):
            print(f"    {i}. {log}")


def save_results(transcript: str, routing: dict):
    """Save results to JSON file."""
    filename = f"voice_to_layer3_result_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    
    data = {
        "timestamp": datetime.utcnow().isoformat(),
        "transcript": transcript,
        "routing": routing,
    }
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"\n  📁 Results saved: {Colors.CYAN}{filename}{Colors.END}")


def main():
    """Main entry point."""
    print_header("🎬 INTERACTIVE VOICE → TRANSCRIPTION → LAYER 3 ROUTING")
    
    # Check services
    print(f"{Colors.BOLD}Checking services...{Colors.END}")
    if not check_services():
        print(f"\n{Colors.RED}✗ Required services are not running!{Colors.END}")
        print(f"   Start them with:")
        print(f"     Terminal 1: {Colors.YELLOW}python start_all.py{Colors.END}")
        print(f"     Terminal 2: {Colors.YELLOW}cd backend && uvicorn app.main:app --reload{Colors.END}")
        sys.exit(1)
    
    print(f"\n{Colors.GREEN}✓ All services ready!{Colors.END}")
    
    # Choose input method
    print_section("INPUT METHOD")
    print("  1. Capture from microphone")
    print("  2. Use existing audio file")
    print("  3. Exit")
    
    choice = input("\n  Select option (1-3): ").strip()
    
    audio_file = None
    
    if choice == "1":
        if not MICROPHONE_AVAILABLE:
            print(f"\n{Colors.YELLOW}⚠️  Microphone not available. Try option 2 with a WAV file.{Colors.END}")
            return
        audio_file = capture_microphone_audio()
    
    elif choice == "2":
        file_path = input("  Enter audio file path: ").strip()
        audio_file = record_sample_audio_file(file_path)
    
    else:
        print(f"  {Colors.YELLOW}Exiting...{Colors.END}")
        return
    
    if not audio_file:
        print(f"  {Colors.RED}✗ No audio file available{Colors.END}")
        return
    
    # Process the audio
    print(f"\n{Colors.GREEN}Starting voice processing pipeline...{Colors.END}")
    
    # Step 1: Transcribe
    transcript = transcribe_audio(audio_file)
    if not transcript:
        print(f"{Colors.RED}✗ Transcription failed{Colors.END}")
        return
    
    # Step 2: Route to Layer 3
    routing = route_to_layer3(transcript)
    if not routing:
        print(f"{Colors.RED}✗ Routing failed{Colors.END}")
        return
    
    # Display results
    display_routing_decision(routing)
    
    # Save results
    save_results(transcript, routing)
    
    # Summary
    print_header(f"{Colors.GREEN}✅ COMPLETE{Colors.END}")
    print(f"  Your complaint was processed and routed to the appropriate department.")
    print(f"  Department: {Colors.CYAN}{routing.get('routing_data', {}).get('dept_id', 'N/A')}{Colors.END}")
    print(f"  Priority: {Colors.CYAN}Level {routing.get('routing_data', {}).get('priority', 'N/A')}/5{Colors.END}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⏹️  Interrupted by user{Colors.END}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}✗ Error: {e}{Colors.END}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
