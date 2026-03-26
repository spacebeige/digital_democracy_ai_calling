#!/bin/bash
# ✅ CORRECT STARTUP - Digital Democracy AI Calling System
# This script uses the CORRECT venv (.venv not awaaz/.venv)

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║  🎙️ INTERACTIVE VOICE TO LAYER 3 ROUTING - CORRECT STARTUP               ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Change to project root
cd /Users/ashwinagarkhed/integration1

# CRITICAL: Use the ROOT .venv (NOT awaaz/.venv)
echo "📁 Project Directory: /Users/ashwinagarkhed/integration1"
echo "🐍 Using Python Environment: .venv (ROOT)"
echo ""

# Activate the CORRECT venv
source .venv/bin/activate

# Verify packages are available
echo "✓ Verifying packages..."
python3 -c "
import sounddevice
import soundfile  
import langdetect
import google.cloud.speech
print('✓ All packages available!')
" 2>/dev/null && echo "" || echo "❌ Missing packages"

echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "🚀 Starting interactive voice processing system..."
echo ""

# Run the script
python3 interactive_voice_to_layer3_enhanced.py
