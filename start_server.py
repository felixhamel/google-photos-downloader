#!/usr/bin/env python3
"""
ABOUTME: Standalone server launcher for Windows/MacOS compatibility
ABOUTME: Replaces complex multiline batch script with simple Python launcher
"""
import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path

def main():
    """Launch the web server and open browser."""
    # Check if CLI mode was requested
    if len(sys.argv) > 1 and (sys.argv[1] == '--cli' or sys.argv[1] == '--help'):
        return launch_cli_mode()
    
    print("🚀 Google Photos Downloader - Web Version v2.0.0")
    print("=" * 50)
    
    # Change to script directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # Check for credentials.json
    if not os.path.exists("credentials.json"):
        print("❌ ERROR: credentials.json not found!")
        print("📋 Please download OAuth2 credentials from Google Cloud Console")
        print("📖 See OAUTH_GUIDE.md for detailed instructions")
        input("Press Enter to exit...")
        return 1
    
    print("✅ Found credentials.json")
    
    # Import and start server
    try:
        import uvicorn
        print("✅ Dependencies found")
        print("🌐 Starting web server on http://127.0.0.1:8000")
        print("📱 Opening browser automatically...")
        print("⏹️  Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Open browser after short delay
        def open_browser():
            time.sleep(2)
            try:
                webbrowser.open("http://127.0.0.1:8000")
            except Exception as e:
                print(f"⚠️  Could not open browser automatically: {e}")
                print("💻 Please open http://127.0.0.1:8000 manually")
        
        # Start browser opener in background
        import threading
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Start server
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Installing required packages...")
        return install_and_restart()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        input("Press Enter to exit...")
        return 1

def install_and_restart():
    """Install dependencies and restart."""
    try:
        # Try Windows-specific requirements first
        if os.path.exists("requirements-web-windows.txt"):
            print("📦 Installing Windows-compatible packages...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "--only-binary=all", "-r", "requirements-web-windows.txt"
            ], check=True)
        elif os.path.exists("requirements-web.txt"):
            print("📦 Installing from requirements-web.txt...")
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                "--only-binary=all", "-r", "requirements-web.txt"
            ], check=True)
        else:
            print("📦 Installing individual packages...")
            packages = [
                "fastapi==0.100.1",
                "uvicorn==0.23.2",
                "pydantic==1.10.13",
                "python-multipart==0.0.6",
                "websockets==11.0.3",
                "google-auth-oauthlib==0.7.1",
                "google-auth-httplib2==0.1.0",
                "google-api-python-client==2.100.0",
                "requests==2.31.0",
                "python-dotenv==1.0.0"
            ]
            
            for package in packages:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", 
                    "--only-binary=all", package
                ], check=True)
        
        print("✅ Dependencies installed successfully!")
        print("🔄 Restarting server...")
        
        # Restart this script
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("💡 Try running manually:")
        print(f"   {sys.executable} -m pip install --only-binary=all fastapi uvicorn")
        input("Press Enter to exit...")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        input("Press Enter to exit...")
        return 1

def launch_cli_mode():
    """Launch CLI mode."""
    try:
        # Import and run CLI mode
        import cli_mode
        import asyncio
        return asyncio.run(cli_mode.main())
    except ImportError:
        print("❌ CLI mode not available in this build")
        return 1
    except Exception as e:
        print(f"❌ CLI error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())