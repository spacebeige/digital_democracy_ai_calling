#!/usr/bin/env python3
"""
Simple Demo - Process text input without microphone
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analytics.analytical_model import create_processor

def main():
    print("\n" + "="*80)
    print("  🎤 SIMPLE DEMO - TEXT INPUT TO ROUTING".center(80))
    print("="*80 + "\n")
    
    # Create processor
    print("[1/3] Initializing system...")
    processor = create_processor(use_groq=False)
    print("  ✓ System initialized\n")
    
    # Test complaint
    print("[2/3] Processing sample complaint...")
    complaint_text = "Fire in my house! Emergency help needed immediately!"
    
    # Process complaint
    analytical_model = processor.process_text(
        text=complaint_text,
        language="en",
        user_name="Test User",
        user_phone="9876543210",
        user_location="Mumbai"
    )
    
    print(f"  ✓ Complaint processed")
    print(f"    - Urgency: {analytical_model.urgency}")
    print(f"    - Department: {analytical_model.routing.primary_department}")
    print(f"    - Intent: {analytical_model.intent}\n")
    
    # Save results
    print("[3/3] Saving results...")
    saved_paths = processor.save_result_organized(analytical_model)
    print(f"  ✓ Saved to outputs/json_results/")
    
    print("\n" + "="*80)
    print("  ✅ ALL SYSTEMS OPERATIONAL".center(80))
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
