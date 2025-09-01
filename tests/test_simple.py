#!/usr/bin/env python3
"""
ABOUTME: Simple test script for CI/CD validation
ABOUTME: Tests basic imports and functionality only
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_imports():
    """Test basic imports."""
    try:
        import cli_mode
        print("✅ CLI mode imports successfully")
        
        # Test CLI help
        import subprocess
        result = subprocess.run([sys.executable, "cli_mode.py", "--help"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ CLI help command works")
        else:
            print("❌ CLI help command failed")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_web_imports():
    """Test web app imports if available.""" 
    try:
        if os.path.exists('app/main.py'):
            from app.main import app
            print("✅ Web app imports successfully")
        else:
            print("⚠️  Web app files not found (optional)")
        return True
    except Exception as e:
        print(f"❌ Web import failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running Simple Project Tests")
    print("=" * 50)
    
    success = True
    success &= test_basic_imports()
    success &= test_web_imports()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)