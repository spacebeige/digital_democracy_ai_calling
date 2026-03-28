#!/usr/bin/env python3
"""
Generate greeting MP3 using Sarvam Ritu TTS
"""

import os
import sys
sys.path.insert(0, '/home/parth/Desktop/delhi')

os.environ['CUDA_VISIBLE_DEVICES'] = ''

import asyncio
from pathlib import Path

try:
    from awaaz.src.pipeline.tts import TTSProcessor
    from awaaz.src.session_store import AWAAZSession
except ImportError as e:
    print(f"Error importing TTS: {e}")
    sys.exit(1)

async def create_greeting_audio():
    """Create greeting MP3 with clear, firm English pronunciation"""
    
    greeting_text = """Welcome to the Complaint Registration System.

Please speak clearly and describe your problem.

For example: My water supply is not working.

Or: There is a large pothole on the road.

Speak at a normal pace. We will understand your complaint.

When you are done speaking, please wait. Thank you."""
    
    print("Creating greeting audio with clear, firm English pronunciation...")
    print("Text:", greeting_text[:50], "...\n")
    
    # Create TTS processor
    tts = TTSProcessor(preferred_provider="sarvam")
    
    # Create session with English
    session = AWAAZSession(session_id="greeting")
    session.lang = "en"
    session.lang_name = "English"
    session.speaker = "male"  # Male voice for firmness
    session.emotion = "professional"
    session.pace = 0.85  # Slower for clarity
    
    # Output path
    output_path = "greeting_ritu.mp3"
    
    try:
        print("[TTS] Synthesizing with clear English pronunciation...")
        
        # Synthesize
        success = await tts.synthesize(
            text=greeting_text,
            language="en",
            session=session,
            output_path=output_path
        )
        
        if success and os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"\n✅ SUCCESS!")
            print(f"   File: {output_path}")
            print(f"   Size: {size_mb:.2f} MB")
            print(f"   Language: English")
            print(f"   Style: Clear, firm pronunciation")
            print(f"   Pace: 0.85x (slower for clarity)")
            
            # Try to play it
            print(f"\n▶️  Playing audio...\n")
            os.system(f"afplay {output_path} 2>/dev/null || mpv {output_path} 2>/dev/null || echo 'Audio file created, but player not available'")
        else:
            print(f"❌ TTS synthesis failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("\n" + "="*80)
    print("GREETING AUDIO GENERATOR - CLEAR ENGLISH PRONUNCIATION")
    print("="*80 + "\n")
    
    success = asyncio.run(create_greeting_audio())
    
    if success:
        print("\n" + "="*80)
        print("✨ Greeting audio ready with clear pronunciation!")
        print("="*80 + "\n")
        sys.exit(0)
    else:
        sys.exit(1)
