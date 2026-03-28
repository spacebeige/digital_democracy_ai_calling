#!/usr/bin/env python3
"""
CPU-Optimized Wrapper for Voice Processing
Automatically disables GPU/CUDA to avoid libcublas errors
"""
import os
import sys

# Disable CUDA/GPU before importing any ML libraries
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

# Now import the main script
import asyncio
from interactive_voice_to_layer3_integrated import main

if __name__ == "__main__":
    print("\n" + "="*80)
    print("  🎤 CPU-OPTIMIZED VOICE PROCESSING (GPU DISABLED)".center(80))
    print("="*80 + "\n")
    print("✓ CUDA disabled")
    print("✓ Running on CPU only")
    print("✓ Using faster-whisper with CPU backend\n")
    print("="*80 + "\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
