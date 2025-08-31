# Deployment Guide

This guide covers how to set up and distribute the Google Photos Downloader.

## Prerequisites

- Python 3.8 or newer
- Internet connection for package installation
- Google Cloud Console account (for OAuth2 setup)

## Setting up Google OAuth2

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Photos Library API
4. Go to "Credentials" and create OAuth2 credentials
5. Choose "Desktop application" as the application type
6. Download the JSON file and rename it to `credentials.json`
7. Place it in the root directory of the project

## Installation Options

### Option 1: Simple setup (recommended)
```bash
# Windows users
run_web_windows_fixed.bat

# macOS/Linux users  
chmod +x run_web_macos.sh
./run_web_macos.sh

# Universal
python start_server.py
```

These scripts automatically install dependencies and launch the app.

### Option 2: Manual installation
```bash
# Install dependencies
pip install -r requirements-web.txt

# Windows users with compilation issues:
pip install --only-binary=all -r requirements-web-windows.txt

# Launch web interface
python start_server.py

# Or use command line
python cli_mode.py --help
```

## Distribution

When sharing this app with others:

**Include these files:**
- All Python source files
- `requirements-*.txt` files
- `credentials.json` (your OAuth2 app credentials)
- Documentation files
- Launch scripts

**Don't include:**
- `token.json` (user-specific, private)
- `downloads/` folder (user data)
- `sessions/` folder (download states)
- Virtual environment folders

## Troubleshooting

**"Python not found"**
- Install Python from python.org
- Make sure to check "Add to PATH" during Windows installation

**"Module not found" errors**
- Run `pip install -r requirements-web.txt`
- On Windows: use `requirements-web-windows.txt` instead

**"credentials.json not found"**
- Follow the OAuth2 setup steps above
- Make sure the file is named exactly `credentials.json`

**Browser doesn't open automatically**
- Manually navigate to http://127.0.0.1:8000
- Check if another program is using port 8000

## Platform-specific notes

**Windows:**
- Use the `.bat` launcher for best experience
- Pre-compiled packages avoid compilation issues
- Works on Windows 10 and 11

**macOS:**
- Use the `.sh` launcher 
- May need to allow the script to run (right-click → Open)
- Works on macOS 10.14+

**Linux:**
- Install Python3 and pip if not already installed
- Use the `.sh` launcher or run Python directly
- Tested on Ubuntu 18.04+

## Security considerations

- The app only requests read-only access to Google Photos
- User tokens are stored locally in `token.json`
- The app runs locally (127.0.0.1) and is not accessible from the internet
- No data is sent to external servers except Google's APIs

## Performance

- Downloads are concurrent (default: 5 simultaneous downloads)
- Progress is tracked in real-time via WebSocket
- Failed downloads are retried automatically
- Large files are downloaded in chunks for better memory usage

That's it! The app is designed to be as simple as possible to deploy and use.