#!/bin/bash
# ABOUTME: MacOS/Linux shell script launcher
# ABOUTME: Cross-platform launcher for Google Photos Downloader

echo ""
echo "===================================================="
echo "🚀 Google Photos Downloader - Web Version v2.0.0"
echo "===================================================="
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Check for Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ ERROR: Python not found!"
    echo ""
    echo "📥 Please install Python:"
    echo "   macOS: brew install python3"
    echo "   Linux: apt install python3 (Ubuntu/Debian)"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Use python3 if available, otherwise python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo "✅ Python found: $($PYTHON_CMD --version)"
echo ""

# Launch the Python server script
echo "🚀 Starting Google Photos Downloader..."
echo ""
$PYTHON_CMD start_server.py

echo ""
echo "👋 Thanks for using Google Photos Downloader!"