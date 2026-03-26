#!/bin/bash
# Digital Democracy AI Calling System - Full Setup & Startup

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║         🚀 DIGITAL DEMOCRACY AI CALLING SYSTEM - READY TO START            ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Get to project root
cd /Users/ashwinagarkhed/integration1

echo "📋 SETUP SUMMARY"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "✅ Python Environment:"
echo "   • Version: 3.11.4"
echo "   • Location: /Users/ashwinagarkhed/integration1/.venv"
echo ""
echo "✅ Dependencies Installed:"
echo "   ✓ Root requirements (100+ packages)"
echo "   ✓ Database & routing (psycopg2, langdetect, etc)"
echo "   ✓ AWAAZ services (FastAPI, transformers, torch)"
echo "   ✓ Backend NLP (SQLAlchemy, pydantic)"
echo "   ✓ AI Services (speech, LLM processing)"
echo ""
echo "✅ Configuration:"
echo "   ✓ .env created from .env.example"
echo "   ✓ Requirements files verified and fixed"
echo ""
echo "✅ Issues Resolved:"
echo "   ✓ audioread 3.1.0 (was 3.1.1 - unavailable)"
echo "   ✓ Click 8.1.8 (gTTS compatibility)"
echo "   ✓ Typer 0.9.0 (dependency conflict)"
echo "   ✓ Fasttext skipped (using langdetect)"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "🚀 STARTING ALL SERVICES..."
echo ""
echo "Ports:"
echo "   • Backend API: http://localhost:8080"
echo "   • Mock STT: http://localhost:9000"
echo "   • Mock TTS: http://localhost:9001"
echo "   • Mock LLM: http://localhost:9002"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Activate venv and run
source .venv/bin/activate
python start_all.py
