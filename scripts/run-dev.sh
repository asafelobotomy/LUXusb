#!/bin/bash
# Test script for development

set -e

echo "Running LUXusb in development mode..."
echo ""
echo "⚠️  This will be run with current user privileges."
echo "    USB operations require root access."
echo ""

# Check for virtual environment
if [ -d ".venv" ]; then
    echo "✅ Using virtual environment (.venv)"
    .venv/bin/python -m luxusb "$@"
elif [ -d "venv" ]; then
    echo "✅ Using virtual environment (venv)"
    venv/bin/python -m luxusb "$@"
else
    echo "❌ No virtual environment found!"
    echo "Please create one first:"
    echo "  python3 -m venv .venv"
    echo "  .venv/bin/pip install -r requirements.txt"
    exit 1
fi
