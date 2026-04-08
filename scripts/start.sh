#!/bin/bash

# MoE Router API Startup Script
# This script starts the MoE Router API server

echo "Starting MoE Router API..."

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(cd "$(dirname "$0")/.." && pwd)"

# Change to project directory
cd "$(dirname "$0")/.." || exit 1

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f ".installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch .installed
fi

# Check if Ollama is running
echo "Checking Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Warning: Ollama does not appear to be running."
    echo "Please start Ollama first with: ollama serve"
    echo "Continuing anyway..."
fi

# Start the server
echo ""
echo "========================================="
echo "MoE Router API starting on http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "========================================="
echo ""

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
