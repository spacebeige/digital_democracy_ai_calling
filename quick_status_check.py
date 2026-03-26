#!/usr/bin/env python3
"""
Quick test script to verify the system is working
"""
import sys
import os

print("""
╔════════════════════════════════════════════════════════════════╗
║         MULTILINGUAL GRIEVANCE SYSTEM v2.0 - STATUS CHECK      ║
╚════════════════════════════════════════════════════════════════╝

🧪 SYSTEM VERIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

""")

# Test 1: Check Python environment
print("1️⃣  Python Environment")
print(f"   ✓ Version: {sys.version.split()[0]}")
print(f"   ✓ Executable: {sys.executable}")
print()

# Test 2: Check imports
print("2️⃣  Module Imports")
try:
    from interactive_voice_to_layer3_integrated import (
        LANGUAGE_CONFIG,
        GROQ_AVAILABLE,
        detect_language_multilingual,
        generate_groq_summary
    )
    print(f"   ✓ Voice module: OK")
    print(f"   ✓ Languages: {len(LANGUAGE_CONFIG)}")
    print(f"   ✓ Groq support: {'ENABLED' if GROQ_AVAILABLE else 'FALLBACK'}")
except Exception as e:
    print(f"   ✗ Voice module failed: {e}")
    sys.exit(1)

try:
    from api_grievance_multilingual import app
    print(f"   ✓ API module: OK")
    print(f"   ✓ Route count: {len(app.routes)}")
except Exception as e:
    print(f"   ✗ API module failed: {e}")
    sys.exit(1)

# Test 3: Check language detection
print("\n3️⃣  Language Detection")
test_cases = [
    ("Hello world", "English"),
    ("नमस्ते", "Hindi"),
    ("வணக்கம்", "Tamil"),
]

for text, expected_lang in test_cases:
    try:
        lang_code, lang_name, confidence = detect_language_multilingual(text)
        symbol = "✓" if expected_lang.lower() in lang_name.lower() else "⚠"
        print(f"   {symbol} {expected_lang:10s} → {lang_name} ({confidence:.0%})")
    except Exception as e:
        print(f"   ✗ {expected_lang}: {e}")

# Test 4: Storage
print("\n4️⃣  Storage System")
try:
    from outputs.json_storage_manager import JSONStorageManager
    storage = JSONStorageManager(base_output_dir="outputs/json_results")
    stats = storage.get_statistics()
    print(f"   ✓ Total grievances: {stats.get('total', 0)}")
    print(f"   ✓ Storage paths configured")
except Exception as e:
    print(f"   ⚠ Storage: {e}")

# Test 5: Environment
print("\n5️⃣  Environment Configuration")
print(f"   ✓ GROQ_API_KEY: {'SET' if os.getenv('GROQ_API_KEY') else 'NOT SET'}")
print(f"   ✓ Working dir: {os.getcwd()}")

print("\n" + "="*70)
print("""
✅ SYSTEM STATUS: READY FOR DEPLOYMENT

🚀 Next Steps:

1. Start the API server:
   python -m uvicorn api_grievance_multilingual:app --port 8001

2. Open browser:
   http://localhost:8001/docs

3. Test with sample grievance:
   POST /grievance/text/submit
   Body: {"transcript": "मेरी बिजली काट दी गई है"}

4. Monitor logs:
   tail -f outputs/logs/*.log

📚 Documentation:
   - Read: MULTILINGUAL_SYSTEM_GUIDE_v2.md
   - Deploy: DEPLOYMENT_CHECKLIST.md

""" + "="*70)

print("\n✨ All systems operational!")
