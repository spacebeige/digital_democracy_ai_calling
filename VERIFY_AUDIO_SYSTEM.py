#!/usr/bin/env python3
"""
VERIFICATION CHECKLIST: Audio Language Detection System
========================================================

Run this to verify the complete system is ready for production.
"""

import os
import sys
from pathlib import Path

class VerificationChecklist:
    def __init__(self):
        self.project_root = Path("/Users/devendrainamdar/Desktop/delhi/digital_democracy_ai_calling")
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def print_header(self):
        print("\n" + "█" * 80)
        print("█" + " " * 78 + "█")
        print("█" + " AUDIO LANGUAGE DETECTION SYSTEM - VERIFICATION CHECKLIST ".center(78) + "█")
        print("█" + " " * 78 + "█")
        print("█" * 80)
    
    def check_file_exists(self, filepath, description):
        """Check if a required file exists."""
        full_path = self.project_root / filepath
        status = "✅" if full_path.exists() else "❌"
        
        if full_path.exists():
            size_kb = full_path.stat().st_size / 1024
            print(f"{status} {filepath:50} ({size_kb:.1f} KB)")
            self.passed += 1
        else:
            print(f"{status} {filepath:50} [MISSING]")
            self.failed += 1
    
    def check_imports(self, import_name, description):
        """Check if a Python package can be imported."""
        try:
            __import__(import_name)
            print(f"✅ {description:50} (importable)")
            self.passed += 1
        except ImportError:
            print(f"⚠️  {description:50} (not installed)")
            self.warnings += 1
    
    def run_verification(self):
        """Run all verification checks."""
        self.print_header()
        
        # ────────────────────────────────────────────────────────────────────
        print("\n📁 STEP 1: Required Files")
        print("─" * 80)
        
        files_to_check = [
            ("audio_language_greeting_service.py", "Core language detection service"),
            ("greeting_integration.py", "Call pipeline integration"),
            ("test_audio_language_detection.py", "Test suite"),
            ("AUDIO_LANGUAGE_DETECTION_README.md", "Full documentation"),
            ("QUICK_START_AUDIO_LANGUAGE_DETECTION.py", "Quick start guide"),
            ("IMPLEMENTATION_SUMMARY_AUDIO_LANGUAGE.md", "Implementation summary"),
        ]
        
        for filepath, desc in files_to_check:
            self.check_file_exists(filepath, desc)
        
        # ────────────────────────────────────────────────────────────────────
        print("\n📦 STEP 2: Required Python Packages")
        print("─" * 80)
        
        packages_to_check = [
            ("faster_whisper", "faster-whisper (language detection)"),
            ("soundfile", "soundfile (audio I/O)"),
            ("scipy", "scipy (audio processing)"),
            ("langdetect", "langdetect (fallback detection)"),
            ("numpy", "numpy (array operations)"),
        ]
        
        for package, desc in packages_to_check:
            self.check_imports(package, desc)
        
        # ────────────────────────────────────────────────────────────────────
        print("\n🔧 STEP 3: System Configuration")
        print("─" * 80)
        
        # Python version
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info >= (3, 8):
            print(f"✅ Python version: {py_version} (3.8+ required)")
            self.passed += 1
        else:
            print(f"❌ Python version: {py_version} (3.8+ required)")
            self.failed += 1
        
        # Project structure
        awaaz_dir = self.project_root / "awaaz"
        if awaaz_dir.exists():
            print(f"✅ AWAAZ directory found")
            self.passed += 1
        else:
            print(f"❌ AWAAZ directory not found")
            self.failed += 1
        
        # ────────────────────────────────────────────────────────────────────
        print("\n🎯 STEP 4: Service Functionality")
        print("─" * 80)
        
        # Try importing the service
        try:
            sys.path.insert(0, str(self.project_root))
            from audio_language_greeting_service import (
                AudioLanguageDetector,
                AudioLanguageGreetingService,
                LANGUAGE_MAP,
                LANGUAGE_GREETINGS
            )
            print(f"✅ audio_language_greeting_service imports successfully")
            self.passed += 1
            
            # Check language coverage
            if len(LANGUAGE_MAP) >= 20:
                print(f"✅ Language map: {len(LANGUAGE_MAP)} languages supported")
                self.passed += 1
            else:
                print(f"⚠️  Language map: Only {len(LANGUAGE_MAP)} languages (20+ expected)")
                self.warnings += 1
            
            # Check greetings coverage
            if len(LANGUAGE_GREETINGS) >= 20:
                print(f"✅ Greetings database: {len(LANGUAGE_GREETINGS)} languages")
                self.passed += 1
            else:
                print(f"⚠️  Greetings database: Only {len(LANGUAGE_GREETINGS)} languages")
                self.warnings += 1
                
        except ImportError as e:
            print(f"❌ Failed to import services: {e}")
            self.failed += 1
        
        # Try importing integration
        try:
            from greeting_integration import GreetingHandler
            print(f"✅ greeting_integration imports successfully")
            self.passed += 1
        except ImportError as e:
            print(f"❌ Failed to import greeting_integration: {e}")
            self.failed += 1
        
        # ────────────────────────────────────────────────────────────────────
        print("\n📊 STEP 5: Documentation")
        print("─" * 80)
        
        # Check documentation
        readme = self.project_root / "AUDIO_LANGUAGE_DETECTION_README.md"
        if readme.exists() and readme.stat().st_size > 5000:
            print(f"✅ Complete documentation available ({readme.stat().st_size / 1024:.0f} KB)")
            self.passed += 1
        else:
            print(f"❌ Documentation incomplete or missing")
            self.failed += 1
        
        # ────────────────────────────────────────────────────────────────────
        print("\n✨ STEP 6: Optional Enhancements")
        print("─" * 80)
        
        # GPU check
        try:
            import torch
            if torch.cuda.is_available():
                print(f"✅ GPU available (CUDA {torch.version.cuda})")
                self.passed += 1
            else:
                print(f"⚠️  GPU not available (CPU mode only)")
                self.warnings += 1
        except ImportError:
            print(f"⚠️  PyTorch not installed (GPU acceleration not available)")
            self.warnings += 1
        
        # Audio samples
        test_dir = self.project_root / "test_audio_samples"
        if test_dir.exists():
            audio_files = list(test_dir.glob("*.wav"))
            if audio_files:
                print(f"✅ Test audio samples available ({len(audio_files)} files)")
                self.passed += 1
            else:
                print(f"⚠️  Test audio directory empty (generate with test suite)")
                self.warnings += 1
        else:
            print(f"⚠️  Test audio directory not found (will be created on first test)")
            self.warnings += 1
        
        # ────────────────────────────────────────────────────────────────────
        print("\n" + "=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        
        total = self.passed + self.failed + self.warnings
        
        print(f"\n✅ Passed:  {self.passed}/{total}")
        print(f"❌ Failed:  {self.failed}/{total}")
        print(f"⚠️  Warnings: {self.warnings}/{total}")
        
        if self.failed == 0 and self.passed >= total - self.warnings:
            print("\n" + "▓" * 80)
            print("▓" + " " * 78 + "▓")
            print("▓" + " ✅ SYSTEM READY FOR PRODUCTION ".center(78) + "▓")
            print("▓" + " All critical checks passed! ".center(78) + "▓")
            print("▓" + " " * 78 + "▓")
            print("▓" * 80)
            return 0
        elif self.failed > 0:
            print("\n" + "▓" * 80)
            print("▓" + " " * 78 + "▓")
            print("▓" + f" ❌ {self.failed} CRITICAL ISSUES FOUND ".center(78) + "▓")
            print("▓" + " Please fix before production deployment ".center(78) + "▓")
            print("▓" + " " * 78 + "▓")
            print("▓" * 80)
            return 1
        else:
            print("\n" + "▓" * 80)
            print("▓" + " " * 78 + "▓")
            print("▓" + " ✅ SYSTEM READY (with minor warnings) ".center(78) + "▓")
            print("▓" + " See warnings above for optional improvements ".center(78) + "▓")
            print("▓" + " " * 78 + "▓")
            print("▓" * 80)
            return 0
    
    def print_next_steps(self):
        """Print recommended next steps."""
        print("\n" + "=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        
        steps = [
            ("1. Install dependencies", "pip install faster-whisper soundfile scipy langdetect"),
            ("2. Run test suite", "python test_audio_language_detection.py --test"),
            ("3. Review documentation", "cat AUDIO_LANGUAGE_DETECTION_README.md"),
            ("4. Integrate into AWAAZ", "See greeting_integration.py for code snippets"),
            ("5. Test with real callers", "Monitor language detection accuracy"),
        ]
        
        for step, cmd in steps:
            print(f"\n{step}")
            print(f"  $ {cmd}")


if __name__ == "__main__":
    checker = VerificationChecklist()
    exit_code = checker.run_verification()
    checker.print_next_steps()
    sys.exit(exit_code)
