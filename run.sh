#!/bin/bash
# Google Photos Downloader - Run Script

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Installing dependencies..."
    venv/bin/pip install --upgrade pip
    venv/bin/pip install -r requirements.txt
fi

# Run the application
echo "Starting Google Photos Downloader..."
venv/bin/python src/google_photos_downloader.py "$@"