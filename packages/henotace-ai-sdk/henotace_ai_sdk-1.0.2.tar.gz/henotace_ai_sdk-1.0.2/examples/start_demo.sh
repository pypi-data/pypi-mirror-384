#!/bin/bash

echo "🐍 Henotace AI Python SDK Demo Setup"
echo "======================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.7"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $python_version detected. Python $required_version or higher is required."
    exit 1
fi

echo "✅ Python $python_version detected"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check for API key
if [ -z "$HENOTACE_API_KEY" ]; then
    echo "⚠️  HENOTACE_API_KEY environment variable not set."
    echo "   You can set it with: export HENOTACE_API_KEY='your_api_key_here'"
    echo "   Or the demo will use a test key."
    echo ""
fi

echo "🚀 Starting demo server..."
echo "   Demo will be available at: http://localhost:5000"
echo "   Press Ctrl+C to stop the server"
echo ""

# Start the demo server
python3 demo_server.py
