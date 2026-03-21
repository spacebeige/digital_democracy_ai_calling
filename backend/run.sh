#!/bin/bash

# Quick Start Script for Ticketing System

echo "🚀 Starting Ticketing State Machine Backend..."
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

echo "📦 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies."
    exit 1
fi

echo ""
echo "✅ Dependencies installed successfully!"
echo ""
echo "🎯 Starting FastAPI server..."
echo ""
echo "📍 API Documentation: http://localhost:8000/docs"
echo "📍 Alternative Docs: http://localhost:8000/redoc"
echo ""

# Start uvicorn server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
