#!/bin/bash

# Enhanced Grievance System Startup Script
# Starts the FastAPI server with all enhanced features

set -e

echo "═══════════════════════════════════════════════════════════"
echo "   Enhanced Grievance System v2.2"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if we're in the right directory
if [ ! -f "backend/app/main.py" ]; then
    echo "❌ Error: Please run this script from the integration1 directory"
    echo "   cd /Users/ashwinagarkhed/integration1"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/app/services/summary_cache
mkdir -p backend/app/services/schemes_cache
mkdir -p outputs/json_results
mkdir -p logs

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated"
    echo "   Attempting to activate..."
    
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        echo "✓ Activated .venv"
    elif [ -d "venv" ]; then
        source venv/bin/activate
        echo "✓ Activated venv"
    else
        echo "❌ No virtual environment found. Please create one:"
        echo "   python -m venv .venv"
        echo "   source .venv/bin/activate"
        echo "   pip install -r requirements.txt"
        exit 1
    fi
fi

# Check if required packages are installed
echo ""
echo "📦 Checking dependencies..."
python -c "import fastapi, httpx, pydantic" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Missing dependencies. Installing..."
    pip install -r requirements.txt
else
    echo "✓ All dependencies installed"
fi

# Check environment variables
echo ""
echo "🔑 Checking environment variables..."
if [ -z "$SARVAM_API_KEY" ]; then
    echo "⚠️  SARVAM_API_KEY not set (optional)"
fi
if [ -z "$GROK_API_KEY" ]; then
    echo "⚠️  GROK_API_KEY not set (optional, needed for real-time scheme updates)"
fi

# Check if port 8000 is available
echo ""
echo "🔌 Checking port 8000..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8000 is already in use"
    echo "   Do you want to kill the existing process? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        PID=$(lsof -Pi :8000 -sTCP:LISTEN -t)
        kill -9 $PID 2>/dev/null
        echo "✓ Killed process $PID"
        sleep 1
    else
        echo "❌ Cannot start server while port 8000 is in use"
        exit 1
    fi
else
    echo "✓ Port 8000 is available"
fi

# Start the server
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🚀 Starting Enhanced Grievance System..."
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Features enabled:"
echo "  ✓ Vulgarity Detection (3-strike warning system)"
echo "  ✓ State-wise Government Schemes"
echo "  ✓ Enhanced AI Summary (urgency + emotion)"
echo "  ✓ Multilingual Support (10+ languages)"
echo "  ✓ Smart Caching (70-80% API reduction)"
echo ""
echo "Server starting at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "Enhanced Endpoints: http://localhost:8000/api/v1/enhanced/*"
echo ""
echo "Press Ctrl+C to stop the server"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Start server with auto-reload
python -m uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0
