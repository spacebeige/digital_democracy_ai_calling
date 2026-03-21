#!/bin/bash

# AI Grievance System - Quick Start Script
# Run this script to set up and start the application

echo "=========================================="
echo "AI Grievance System - Quick Start"
echo "=========================================="
echo ""

# Check Python
echo "Checking Python installation..."
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi
echo "✓ Python found"
echo ""

# Check PostgreSQL
echo "Checking PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL not found in PATH"
    echo "Please start PostgreSQL manually and run: psql -U postgres -f database_setup.sql"
else
    echo "✓ PostgreSQL found"
    echo "Setting up database..."
    psql -U postgres -f database_setup.sql 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✓ Database setup complete"
    else
        echo "⚠️  Database setup may have issues (check if grievance_db already exists)"
    fi
fi
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements_hackathon.txt -q
echo "✓ Dependencies installed"
echo ""

# Start server
echo "Starting FastAPI server..."
echo "=========================================="
echo "Backend: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "=========================================="
echo ""
echo "Open these URLs in your browser:"
echo "  • User Page: file://$(pwd)/user.html"
echo "  • Officer Dashboard: file://$(pwd)/officer.html"
echo "  • Compliance Dashboard: file://$(pwd)/compliance.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

python main.py
