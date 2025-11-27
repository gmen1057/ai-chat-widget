#!/bin/bash
# Start AI Chat Widget

set -e

cd "$(dirname "$0")/backend"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Start server
echo "Starting AI Chat Widget on port ${PORT:-8080}..."
echo "Open http://localhost:${PORT:-8080} in your browser"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --reload
