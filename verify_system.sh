#!/bin/bash
# Comprehensive system verification and setup guide

cd /Users/ashwinagarkhed/integration1

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║        ✅ DIGITAL DEMOCRACY AI - SYSTEM VERIFICATION & QUICK START        ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Activate the CORRECT venv
source .venv/bin/activate

echo "📋 ENVIRONMENT VERIFICATION"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# Check Python version
PYTHON_VERSION=$(/Users/ashwinagarkhed/integration1/.venv/bin/python3 --version)
echo "Python Version: $PYTHON_VERSION"

# Check venv path
VENV_PATH=$(/Users/ashwinagarkhed/integration1/.venv/bin/python3 -c "import sys; print(sys.prefix)")
echo "Active venv:    $VENV_PATH"

echo ""
echo "📦 CRITICAL PACKAGES"
echo "════════════════════════════════════════════════════════════════════════════"

/Users/ashwinagarkhed/integration1/.venv/bin/python3 << 'EOF'
import sys
packages = [
    ('sounddevice', 'Microphone input'),
    ('soundfile', 'Audio file handling'),
    ('langdetect', 'Language detection'),
    ('faster_whisper', 'Speech-to-text'),
    ('gtts', 'Text-to-speech'),
    ('google.cloud.speech', 'Cloud speech API'),
    ('fastapi', 'Web framework'),
    ('psycopg2', 'Database'),
    ('requests', 'HTTP client'),
    ('librosa', 'Audio analysis'),
]

all_ok = True
for pkg, desc in packages:
    try:
        mod = __import__(pkg.replace('-', '_'))
        print(f"✓ {pkg:<25} - {desc}")
    except ImportError as e:
        print(f"✗ {pkg:<25} - {desc} [MISSING]")
        all_ok = False

print("")
if all_ok:
    print("✅ ALL PACKAGES AVAILABLE - System ready!")
else:
    print("❌ Some packages missing - Please reinstall requirements")
EOF

echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# List available scripts
echo "🚀 AVAILABLE COMMANDS"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Option 1: Start ALL services (Backend + Mock STT/TTS/LLM)"
echo "  $ python start_all.py"
echo ""
echo "Option 2: Interactive voice to Layer 3 routing"
echo "  $ python3 interactive_voice_to_layer3_enhanced.py"
echo ""
echo "Option 3: Run with automated script"
echo "  $ ./run_voice_interactive.sh"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

echo "📝 NEXT STEPS"
echo ""
echo "1. First time? Start ALL services in Terminal 1:"
echo "   python start_all.py"
echo ""
echo "2. In Terminal 2, run voice processing:"
echo "   python3 interactive_voice_to_layer3_enhanced.py"
echo ""
echo "3. When prompted in Terminal 2:"
echo "   - Select option 1 for microphone (requires audio input)"
echo "   - Select option 2 for audio file"
echo "   - Select option 3 to exit"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "✨ Remember: Always use '.venv' not 'awaaz/.venv'"
echo ""
