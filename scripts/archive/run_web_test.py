#!/usr/bin/env python3
"""
Direct test runner for Google Photos Downloader Web App (no user input required)
"""
import os
import sys
from pathlib import Path


def main():
    """Test the web app directly."""
    print("🧪 Testing Google Photos Downloader Web App...")
    
    # Change to the app directory
    if not os.path.exists("app/main.py"):
        print("❌ Error: app/main.py not found")
        sys.exit(1)
    
    # Start FastAPI directly
    try:
        print("🚀 Starting server on http://localhost:8000")
        print("🛑 Press Ctrl+C to stop")
        
        os.chdir("app")
        import uvicorn
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()