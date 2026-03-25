#!/usr/bin/env python3
"""
ENHANCED INTERACTIVE VOICE → TRANSCRIPTION → LAYER 3 ROUTING
===========================================================

Features:
✓ Real-time voice level meter during recording
✓ Countdown timer while speaking
✓ Live transcription display
✓ NLP urgency analysis with keyword tracking
✓ Emergency keyword detection
✓ Simplified, focused output

Run with: python interactive_voice_to_layer3_enhanced.py
"""

import sys
import os
import time
import requests
import json
import re
import logging
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from collections import defaultdict

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Audio libraries for microphone capture
try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    MICROPHONE_AVAILABLE = True
    SAMPLE_RATE = 16000
except ImportError:
    print("⚠️  sounddevice/soundfile not available")
    MICROPHONE_AVAILABLE = False
    SAMPLE_RATE = 16000

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configuration
STT_API = "http://localhost:9000"
BACKEND_API = "http://localhost:8000"

# URGENCY KEYWORD DATABASE (Built from real complaints)
URGENCY_KEYWORDS = {
    "CRITICAL": {
        "hindi": ["आग", "आग लगी", "fire", "emergency", "तुरंत", "जल्दी", "तुरंत ही", "बहुत खतरनाक", 
                  "मेरी जान", "जान का खतरा", "घायल", "खून", "गंभीर", "accident", "दुर्घटना",
                  "collision", "टकराव", "ज्यादा चोट", "serious", "madad", "मदद", "मदद करो", "मदद करौ",
                  "बचाओ", "bachao", "बचा लो", "ट्रैप", "फंस", "help", "rescue", "save", "aag", "blaze"],
        "english": ["fire", "emergency", "urgent", "critical", "critical level", "danger", "help", "911", "dying", 
                    "severe", "accident", "bleeding", "unconscious", "dead", "police", "attack", "shot", 
                    "madad", "save me", "rescue", "help immediately", "call police"]
    },
    "HIGH": {
        "hindi": ["बिजली", "बिजली नहीं", "बिजली गई", "बिजली खत्म", "कोई आ रहा है", "चोर", "डाका", "गायब", "खो गया", 
                  "अस्पताल", "बीमार", "बहुत बीमार", "दर्द", "बहुत दर्द", "तकलीफ", "पानी समस्या", "पानी नहीं"],
        "english": ["electricity", "power", "no power", "cut off", "theft", "robbery", "missing", "lost", 
                    "hospital", "sick", "illness", "pain", "suffer", "medical", "urgent care"]
    },
    "MEDIUM": {
        "hindi": ["तोड़ा", "तोड़", "खराब", "नहीं काम", "काम नहीं", "समस्या", "issue", "गड्ढा", "गड्ढे", "पानी", 
                  "सड़क", "गली", "स्कूल", "पार्क", "बस", "ट्रेन", "कूड़ा", "कचरा", "साफ सफाई"],
        "english": ["broken", "damage", "damaged", "not working", "not working", "problem", "issue", "pothole", 
                    "water", "drain", "road", "street", "school", "park", "bus", "train", "garbage", "trash"]
    },
    "LOW": {
        "hindi": ["सुझाव", "शिकायत", "पूछना", "जानकारी", "आवेदन", "स्थिति", "कब", "कहाँ", "क्या"],
        "english": ["suggestion", "complaint", "question", "information", "application", "status", "when", "where", "what"]
    }
}

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
    DIM = '\033[2m'


# Session tracking for keyword analysis
SESSION_KEYWORDS = defaultdict(lambda: {"keywords": [], "urgency_levels": []})


def print_meter(level, width=40):
    """Draw a visual audio level meter."""
    filled = int(width * level)
    bar = "█" * filled + "░" * (width - filled)
    
    if level > 0.8:
        color = Colors.RED
    elif level > 0.6:
        color = Colors.YELLOW
    else:
        color = Colors.GREEN
    
    return f"{color}[{bar}]{Colors.END}"


def record_with_visualization(duration_seconds=10):
    """Record audio with real-time visualization."""
    print(f"\n{Colors.GREEN}🔴 RECORDING...{Colors.END}")
    print(f"{Colors.YELLOW}Speak your complaint now! (Press Ctrl+C to stop){Colors.END}\n")
    
    frames = []
    max_level = 0
    
    try:
        # Calculate how often to update the display
        update_interval = 0.1  # Update every 100ms
        samples_per_update = int(SAMPLE_RATE * update_interval)
        
        # Record in chunks to show live visualization
        stream = sd.InputStream(channels=1, samplerate=SAMPLE_RATE, dtype='float32')
        stream.start()
        
        remaining_time = duration_seconds
        last_display = time.time()
        
        while remaining_time > 0:
            chunk = stream.read(samples_per_update)[0].flatten()
            frames.append(chunk)
            
            # Calculate level
            level = np.sqrt(np.mean(chunk ** 2))
            max_level = max(max_level, level)
            
            # Normalize to 0-1
            norm_level = min(level / 0.1, 1.0)  # Normalize to typical speech level
            
            # Update display
            now = time.time()
            if now - last_display >= update_interval:
                elapsed = duration_seconds - remaining_time
                timer = f"{int(elapsed):02d}s"
                meter = print_meter(norm_level)
                sys.stdout.write(f"\r  {timer} {meter}")
                sys.stdout.flush()
                last_display = now
            
            remaining_time -= update_interval
        
        stream.stop()
        stream.close()
        
        # Combine all frames
        audio_data = np.concatenate(frames)
        
        print(f"\n\n{Colors.GREEN}✓ Recording complete!{Colors.END}")
        print(f"   Duration: {duration_seconds:.1f}s | Max level: {max_level:.2f}")
        
        return audio_data
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⏹️  Recording stopped by user{Colors.END}")
        return None
    except Exception as e:
        print(f"\n{Colors.RED}✗ Recording error: {e}{Colors.END}")
        return None


def capture_microphone_audio(duration_seconds=10):
    """Capture audio from microphone with visualization."""
    if not MICROPHONE_AVAILABLE:
        print(f"{Colors.RED}✗{Colors.END} Microphone not available")
        return None
    
    try:
        print(f"\n{Colors.YELLOW}🎤 Initializing microphone...{Colors.END}")
        
        # Record with visualization
        audio_data = record_with_visualization(duration_seconds)
        
        if audio_data is None or len(audio_data) == 0:
            print(f"{Colors.RED}✗ No audio captured{Colors.END}")
            return None
        
        # Save to file
        output_file = f"/tmp/voice_input_{uuid4().hex[:8]}.wav"
        sf.write(output_file, audio_data, SAMPLE_RATE)
        
        print(f"   Saved: {output_file}")
        return output_file
    
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.END}")
        return None


def analyze_urgency(text, transcript_session_id):
    """Analyze text for urgency level and extract keywords."""
    text_lower = text.lower()
    found_keywords = []
    max_urgency = "LOW"
    urgency_levels = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    max_urgency_score = 0
    
    # Check against all urgency levels
    for urgency, keywords_dict in URGENCY_KEYWORDS.items():
        all_keywords = keywords_dict.get("hindi", []) + keywords_dict.get("english", [])
        
        for keyword in all_keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
                urgency_score = urgency_levels.get(urgency, 0)
                
                if urgency_score > max_urgency_score:
                    max_urgency_score = urgency_score
                    max_urgency = urgency
    
    # Track keywords for this session
    SESSION_KEYWORDS[transcript_session_id]["keywords"].extend(found_keywords)
    SESSION_KEYWORDS[transcript_session_id]["urgency_levels"].append(max_urgency)
    
    return max_urgency, found_keywords, max_urgency_score


def transcribe_audio_with_feedback(audio_file):
    """Transcribe with live feedback - uses Whisper > Google Cloud > Mock.
    
    Returns:
        Tuple of (transcript, language_detected) or (None, None)
    """
    print_section("🎤 STEP 1: TRANSCRIPTION")
    
    try:
        # Try unified STT service first (Whisper)
        print(f"  Attempting real STT transcription...\n")
        
        from unified_stt_service import transcribe, get_status
        
        sys.stdout.write("  ")
        for i in range(3):
            time.sleep(0.2)
            sys.stdout.write(".")
            sys.stdout.flush()
        sys.stdout.write("\n")
        
        transcript, engine_used, language_detected = transcribe(audio_file, engine="auto")
        
        # CONSTRAIN language detection to 22 official Indian languages
        from language_constraint import constrain_detected_language
        language_detected = constrain_detected_language(language_detected, fallback="en")
        
        if not transcript:
            print(f"  {Colors.RED}✗ No transcription returned{Colors.END}")
            return None, None
        
        # Display transcription with engine and language info
        print(f"\n  {Colors.BOLD}YOU SAID:{Colors.END}")
        print(f"  {Colors.CYAN}\"{transcript}\"{Colors.END}")
        print(f"  {Colors.DIM}(Transcribed using: {engine_used} | Language: {language_detected}){Colors.END}\n")
        
        return transcript, language_detected
    
    except ImportError:
        # Fallback to HTTP mock service if unified_stt_service not available
        print(f"  Using mock STT service (HTTP)...\n")
        
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
                return None, None
            
            result = response.json()
            transcript = result.get("text", "").strip()
            
            if not transcript:
                print(f"  {Colors.RED}✗ No transcription returned{Colors.END}")
                return None, None
            
            # Default to Hindi for mock service (since we don't have language detection)
            language = "hi"
            
            print(f"\n  {Colors.BOLD}YOU SAID:{Colors.END}")
            print(f"  {Colors.CYAN}\"{transcript}\"{Colors.END}")
            print(f"  {Colors.DIM}(Transcribed using: Mock Service | Language: {language}){Colors.END}\n")
            
            return transcript, language
        
        except Exception as e:
            print(f"  {Colors.RED}✗ Error: {e}{Colors.END}")
            return None, None
    
    except Exception as e:
        print(f"  {Colors.RED}✗ Error: {e}{Colors.END}")
        return None, None


def route_and_analyze(transcript, session_id, language_detected="en", phone_number=None):
    """Route to appropriate department and show urgency analysis."""
    print_section("🧠 STEP 2: INTELLIGENT ANALYSIS & DEPARTMENT ROUTING")
    
    # Analyze urgency immediately from transcript
    urgency, keywords, score = analyze_urgency(transcript, session_id)
    
    print(f"  {Colors.BOLD}URGENCY ASSESSMENT:{Colors.END}")
    
    # Color-code urgency
    if urgency == "CRITICAL":
        color = Colors.RED
        icon = "🚨"
    elif urgency == "HIGH":
        color = Colors.YELLOW
        icon = "⚠️"
    elif urgency == "MEDIUM":
        color = Colors.BLUE
        icon = "⏱️"
    else:
        color = Colors.GREEN
        icon = "ℹ️"
    
    print(f"  {color}{icon} LEVEL: {urgency}{Colors.END}")
    print(f"  {Colors.DIM}Confidence: {score}/4{Colors.END}")
    
    # Initialize unique_keywords (ALWAYS define it, even if empty)
    unique_keywords = []
    
    # Show identified keywords
    if keywords:
        print(f"\n  {Colors.BOLD}KEY TERMS DETECTED:{Colors.END}")
        unique_keywords = list(set(keywords))[:5]  # Show top 5 unique
        for kw in unique_keywords:
            print(f"    • {Colors.YELLOW}{kw}{Colors.END}")
    else:
        unique_keywords = []
    
    # STEP 2A: Database routing (using DATABASE_ROUTER)
    print(f"\n  {Colors.BOLD}🗄️  DEPARTMENT ROUTING:{Colors.END}")
    
    try:
        from database_router import route_complaint, save_complaint_to_db, get_db_status
        
        # Get database status first
        db_status = get_db_status()
        if db_status.get("status") == "connected":
            # Route using database logic
            routing_info = route_complaint(
                transcript=transcript,
                urgency=urgency,
                keywords=unique_keywords,
                language=language_detected
            )
            
            print(f"    Department: {Colors.CYAN}{routing_info['department'].upper()}{Colors.END}")
            print(f"    Priority: {Colors.CYAN}{routing_info['priority']}/5{Colors.END}")
            print(f"    Confidence: {Colors.CYAN}{routing_info['confidence']:.1f}%{Colors.END}")
            
            # Save to database
            db_saved = save_complaint_to_db(
                session_id=session_id,
                transcript=transcript,
                language_code=language_detected,
                urgency_level=urgency,
                keywords=unique_keywords,
                routing_info=routing_info
            )
            
            if db_saved:
                print(f"    {Colors.GREEN}✓ Saved to database{Colors.END}")
                
                # Send SMS notification if phone number provided
                if phone_number:
                    try:
                        from sms_notifier import notify_complaint_received
                        
                        complaint_data = {
                            "session_id": session_id,
                            "department_assigned": routing_info['department'],
                            "urgency_level": urgency,
                            "transcript": transcript[:50]  # First 50 chars
                        }
                        
                        sms_result = notify_complaint_received(
                            complaint_data=complaint_data,
                            phone_number=phone_number,
                            language=language_detected
                        )
                        
                        if sms_result.get("success"):
                            if sms_result.get("dry_run"):
                                print(f"    {Colors.BLUE}📱 [DRY-RUN] SMS would be sent: {sms_result.get('phone')}{Colors.END}")
                            else:
                                print(f"    {Colors.GREEN}✓ SMS sent to {sms_result.get('phone')}{Colors.END}")
                        else:
                            print(f"    {Colors.YELLOW}⚠️  SMS failed: {sms_result.get('error')}{Colors.END}")
                    
                    except Exception as sms_error:
                        logger.warning(f"SMS notification failed: {sms_error}")
                        print(f"    {Colors.YELLOW}⚠️  SMS error: {str(sms_error)[:50]}{Colors.END}")
            else:
                print(f"    {Colors.YELLOW}⚠️  Database save failed{Colors.END}")
            
            print()
            return routing_info
        else:
            logger.warning(f"Database status: {db_status}")
            raise Exception("Database not connected")
    
    except ModuleNotFoundError:
        logger.warning("database_router module not found, using fallback routing")
    except Exception as e:
        logger.warning(f"Database routing failed: {e}, using fallback")
    
    # FALLBACK: Use local routing logic (no database)
    print(f"    {Colors.DIM}Using local routing (offline mode){Colors.END}")
    
    # Simple local routing based on urgency and keywords
    if urgency == "CRITICAL":
        if unique_keywords and any(kw.lower() in ["aag", "fire", "आग"] for kw in unique_keywords):
            dept = "fire"
        elif unique_keywords and any(kw.lower() in ["police", "चोरी", "डाका"] for kw in unique_keywords):
            dept = "police"
        else:
            dept = "emergency"
    elif urgency == "HIGH":
        dept = "police"
    elif urgency == "MEDIUM":
        dept = "health"
    else:
        dept = "general"
    
    routing_info = {
        "department": dept,
        "priority": {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}.get(urgency, 5),
        "confidence": 50,  # Lower confidence for local routing
        "matched_keywords": unique_keywords[:3] if unique_keywords else [],
        "status": "local_mode"
    }
    
    print(f"    Department: {Colors.CYAN}{dept.upper()}{Colors.END}")
    print(f"    Priority: {Colors.CYAN}{routing_info['priority']}/5{Colors.END}")
    print()
    
    return routing_info


def display_final_action(routing, urgency, keywords):
    """Display final action and routing."""
    print_section("📋 FINAL ACTION")
    
    routing_data = routing.get("routing_data", {})
    
    if urgency == "CRITICAL":
        print(f"  {Colors.RED}{Colors.BOLD}🚨 ESCALATION: CRITICAL LEVEL{Colors.END}")
        print(f"  {Colors.RED}Priority Action: IMMEDIATE DISPATCH{Colors.END}\n")
    elif urgency == "HIGH":
        print(f"  {Colors.YELLOW}{Colors.BOLD}⚠️  HIGH PRIORITY COMPLAINT{Colors.END}")
        print(f"  {Colors.YELLOW}Priority Action: URGENT ASSIGNMENT{Colors.END}\n")
    else:
        print(f"  {Colors.GREEN}Standard complaint processing{Colors.END}\n")
    
    if routing_data:
        dept = routing_data.get("dept_id", "GENERAL")
        priority = routing_data.get("priority", "3")
        print(f"  {Colors.BOLD}ASSIGNMENT:{Colors.END}")
        print(f"    Department: {Colors.CYAN}{dept}{Colors.END}")
        print(f"    Priority: {Colors.CYAN}{priority}/5{Colors.END}")
    
    print(f"\n  {Colors.GREEN}✓ Complaint recorded and routed{Colors.END}")
    print(f"  {Colors.DIM}(Results saved to JSON report){Colors.END}")


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}\n")


def print_section(text):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'─'*80}{Colors.END}")
    print(f"{Colors.CYAN}  {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'─'*80}{Colors.END}\n")


def check_services():
    """Verify services are available (local Python modules or HTTP APIs)."""
    modules_to_check = [
        ("STT (Whisper)", "unified_stt_service"),
        ("Language Detection", "unified_stt_service"),
        ("TTS (gTTS)", "unified_tts_service"),
        ("Urgency Analysis", "interactive_voice_to_layer3_enhanced"),
    ]
    
    all_ok = True
    for name, module in modules_to_check:
        try:
            __import__(module)
            print(f"  {Colors.GREEN}✓{Colors.END} {name:25} Ready")
        except ImportError as e:
            print(f"  {Colors.RED}✗{Colors.END} {name:25} FAILED: {e}")
            all_ok = False
    
    return all_ok


def save_results(transcript, urgency, keywords, routing, session_id):
    """Save results to JSON."""
    filename = f"complaint_analysis_{session_id}.json"
    
    data = {
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "transcript": transcript,
        "urgency_level": urgency,
        "keywords_detected": list(set(keywords)),
        "routing": routing,
    }
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"  Saved to: {Colors.DIM}{filename}{Colors.END}")


def main():
    """Main entry point."""
    print_header("🎙️ VOICE COMPLAINT PROCESSING SYSTEM")
    
    # Check services
    print(f"{Colors.BOLD}Checking services...{Colors.END}")
    if not check_services():
        print(f"\n{Colors.RED}✗ Services not running!{Colors.END}")
        sys.exit(1)
    
    print(f"\n{Colors.GREEN}✓ System ready!{Colors.END}")
    
    # Input method
    print_section("INPUT METHOD")
    print("  1. Speak into microphone")
    print("  2. Use audio file")
    print("  3. Exit")
    
    choice = input("\n  Select (1-3): ").strip()
    
    audio_file = None
    
    if choice == "1":
        if not MICROPHONE_AVAILABLE:
            print(f"  {Colors.RED}Microphone not available{Colors.END}")
            return
        audio_file = capture_microphone_audio()
    
    elif choice == "2":
        file_path = input("  File path: ").strip()
        if not os.path.exists(file_path):
            print(f"  {Colors.RED}File not found{Colors.END}")
            return
        audio_file = file_path
    
    else:
        return
    
    if not audio_file:
        print(f"  {Colors.RED}No audio file{Colors.END}")
        return
    
    # SMS temporarily disabled
    phone_number = None
    
    # Process
    session_id = str(uuid4())[:13]
    
    # Step 1: Transcribe
    transcript, language_detected = transcribe_audio_with_feedback(audio_file)
    if not transcript:
        return
    
    # Step 1.5: Greet user in their language (using audio files)
    try:
        from audio_greeting_handler import create_greeting_handler
        print_section("🎙️ STEP 1.5: LANGUAGE-AWARE GREETING")
        
        greeting_handler = create_greeting_handler()
        greeting_success = greeting_handler.detect_and_greet(language_detected, display_only=True)
        
    except Exception as e:
        logger.warning(f"Audio greeting failed (continuing): {e}")
        print(f"  {Colors.YELLOW}⚠️  {e}{Colors.END}")
    
    # Step 2: Analyze and route
    routing = route_and_analyze(transcript, session_id, language_detected, phone_number=phone_number)
    
    # Get urgency from session
    urgency = SESSION_KEYWORDS[session_id]["urgency_levels"][-1] if SESSION_KEYWORDS[session_id]["urgency_levels"] else "LOW"
    keywords = SESSION_KEYWORDS[session_id]["keywords"]
    
    # Step 3: Show final action
    if routing:
        display_final_action(routing, urgency, keywords)
        save_results(transcript, urgency, keywords, routing, session_id)
    
    print_header(f"{Colors.GREEN}✅ COMPLETE{Colors.END}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⏹️  Interrupted{Colors.END}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}✗ Error: {e}{Colors.END}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
