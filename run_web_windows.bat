@echo off
:: ABOUTME: Windows batch script to launch Google Photos Downloader web app
:: ABOUTME: Automatically installs dependencies, starts server, and opens Chrome browser

title Google Photos Downloader - Web Version v2.0.0
echo.
echo ==================================================
echo 🚀 Google Photos Downloader - Web Version v2.0.0
echo ==================================================
echo.

:: Change to script directory
cd /d "%~dp0"

:: Check for credentials.json
if not exist "credentials.json" (
    echo ❌ ERROR: credentials.json not found!
    echo.
    echo 📋 Please download OAuth2 credentials from Google Cloud Console
    echo 📖 See OAUTH_GUIDE.md for detailed instructions
    echo.
    pause
    exit /b 1
)

echo ✅ Found credentials.json
echo.

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python not found!
    echo 📥 Please install Python from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
echo.

:: Install dependencies
echo 🔍 Checking and installing dependencies...
echo.

:: Check if requirements file exists
if exist "requirements-web.txt" (
    echo 📦 Installing from requirements-web.txt...
    python -m pip install -r requirements-web.txt
) else (
    echo ⚡ Installing individual packages...
    python -m pip install fastapi>=0.104.0
    python -m pip install "uvicorn[standard]>=0.24.0"
    python -m pip install pydantic>=2.0.0
    python -m pip install python-multipart
    python -m pip install websockets
    python -m pip install google-auth-oauthlib>=1.0.0
    python -m pip install google-auth-httplib2>=0.2.0
    python -m pip install google-api-python-client>=2.0.0
    python -m pip install requests>=2.31.0
    python -m pip install python-dotenv
)

if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ✅ All dependencies installed successfully!
echo.

:: Start the web server in background
echo 🌐 Starting web server...
echo 📱 The app will open automatically in Chrome
echo 🔗 Server URL: http://127.0.0.1:8000
echo ⏹️  Close this window to stop the server
echo --------------------------------------------------
echo.

:: Wait a moment for server to start, then open Chrome
start "" cmd /c "timeout /t 3 >nul && start chrome http://127.0.0.1:8000"

:: Start the web application (this will block until stopped)
python -c "
import uvicorn
import sys
import os

try:
    print('🚀 Server starting...')
    uvicorn.run(
        'app.main:app',
        host='127.0.0.1',
        port=8000,
        reload=True,
        log_level='info'
    )
except KeyboardInterrupt:
    print('\n🛑 Server stopped by user')
    sys.exit(0)
except Exception as e:
    print(f'❌ Error starting server: {e}')
    input('Press Enter to exit...')
    sys.exit(1)
"

echo.
echo 👋 Thanks for using Google Photos Downloader!
pause