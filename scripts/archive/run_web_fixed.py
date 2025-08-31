#!/usr/bin/env python3
"""
ABOUTME: Fixed web application launcher with proper dependencies
ABOUTME: Corrected version of run_web.py with all import issues resolved
"""
import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check and install required dependencies."""
    required_packages = [
        'fastapi>=0.104.0',
        'uvicorn[standard]>=0.24.0',
        'pydantic>=2.0.0',
        'python-multipart',
        'websockets',
        'google-auth-oauthlib>=1.0.0',
        'google-auth-httplib2>=0.2.0',
        'google-api-python-client>=2.0.0',
        'requests>=2.31.0',
        'python-dotenv'
    ]
    
    print("🔍 Checking dependencies...")
    
    # Check if requirements file exists
    requirements_file = Path("requirements-web.txt")
    if requirements_file.exists():
        print("📦 Installing from requirements-web.txt...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
    else:
        print("⚡ Installing individual packages...")
        for package in required_packages:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
                print(f"✅ Installed {package}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install {package}: {e}")
                return False
    
    return True

def main():
    """Main application launcher."""
    print("🚀 Google Photos Downloader - Web Version v2.0.0")
    print("=" * 50)
    
    # Change to the script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Check for credentials.json
    if not os.path.exists("credentials.json"):
        print("❌ ERROR: credentials.json not found!")
        print("📋 Please download OAuth2 credentials from Google Cloud Console")
        print("📖 See OAUTH_GUIDE.md for detailed instructions")
        return 1
    
    # Install dependencies
    if not check_dependencies():
        print("❌ Failed to install dependencies")
        return 1
    
    print("\n✅ All dependencies installed successfully!")
    print("🌐 Starting web server...")
    print("📱 Access the app at: http://127.0.0.1:8000")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start the web application
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())