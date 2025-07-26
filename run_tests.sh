#!/bin/bash

echo "🚀 Studium Backend Test Suite"
echo "================================"

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo "Running test suite..."
python test_runner.py

# Run pytest if available
if command -v pytest &> /dev/null; then
    echo "Running pytest..."
    pytest tests/ -v
else
    echo "pytest not available, skipping unit tests"
fi

echo "✅ Test suite completed!"