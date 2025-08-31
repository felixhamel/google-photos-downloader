#!/usr/bin/env python3
"""
Startup script for Google Photos Downloader Web App
"""
import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path


def check_requirements():
    """Check if required packages are installed."""
    try:
        import fastapi
        import uvicorn
        import yaml
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e.name}")
        print("📦 Installing required packages...")
        
        # Install requirements
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "requirements-web.txt"
            ])
            print("✅ Successfully installed required packages")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages. Please install manually:")
            print("   pip install -r requirements-web.txt")
            return False


def check_credentials():
    """Check if credentials.json exists."""
    if not os.path.exists("credentials.json"):
        print("⚠️ Warning: credentials.json not found")
        print("📝 To use this app, you need to:")
        print("   1. Go to https://console.cloud.google.com/")
        print("   2. Enable Google Photos Library API")  
        print("   3. Create OAuth2 credentials")
        print("   4. Download as 'credentials.json' in this folder")
        print("\n🚀 You can still run the app to see the interface")
        return False
    else:
        print("✅ Found credentials.json")
        return True


def start_server():
    """Start the FastAPI server."""
    print("🚀 Starting Google Photos Downloader Web App...")
    print("📱 Local web interface will open automatically")
    print("🔗 URL: http://localhost:8000")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Change to the app directory
    app_dir = Path(__file__).parent / "app"
    os.chdir(app_dir)
    
    # Start server
    try:
        # Open browser after short delay
        import threading
        def open_browser():
            time.sleep(2)
            webbrowser.open("http://localhost:8000")
        
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Start FastAPI with uvicorn
        import uvicorn
        uvicorn.run(
            "main:app",
            host="127.0.0.1",  # Local only
            port=8000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    print("Google Photos Downloader v2.0 - Web Edition")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("app/main.py"):
        print("❌ Error: Please run this script from the project root directory")
        print("   The 'app' folder should be in the same directory as this script")
        sys.exit(1)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check credentials (warning only)
    check_credentials()
    
    # Create necessary directories
    Path("config").mkdir(exist_ok=True)
    Path("static").mkdir(exist_ok=True)
    
    print("\n🎯 Ready to start the web application!")
    input("📱 Press Enter to open the web interface...")
    
    # Start the server
    start_server()


if __name__ == "__main__":
    main()