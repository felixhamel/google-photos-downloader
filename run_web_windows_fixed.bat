@echo off
REM ABOUTME: Windows batch script launcher (FIXED VERSION)
REM ABOUTME: Simple wrapper that calls Python launcher script

title Google Photos Downloader - Web Version v2.0.0
echo.
echo ===================================================
echo 🚀 Google Photos Downloader - Web Version v2.0.0
echo ===================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python not found!
    echo.
    echo 📥 Please install Python from https://python.org
    echo ✅ Make sure to check "Add to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Launch the Python server script
echo 🚀 Starting Google Photos Downloader...
echo.
python start_server.py

echo.
echo 👋 Thanks for using Google Photos Downloader!
pause