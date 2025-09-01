#!/usr/bin/env python3
"""
"""
import sys
import os
import importlib.util
from pathlib import Path

def test_python_version():
    """Test Python version compatibility."""
    print("🔍 Testing Python version...")
    if sys.version_info < (3, 8):
        print(f"❌ Python {sys.version} is too old. Need Python 3.8+")
        return False
    print(f"✅ Python {sys.version} is compatible")
    return True

def test_credentials():
    """Test for credentials.json file."""
    print("🔍 Testing credentials.json...")
    if not os.path.exists("credentials.json"):
        print("⚠️  credentials.json not found (expected for fresh install)")
        print("📋 Users will need to add this file")
        return True  # Not blocking
    print("✅ credentials.json found")
    return True

def test_static_files():
    """Test static files exist."""
    print("🔍 Testing static files...")
    static_files = [
        "static/index.html",
        "static/js/app.js"
    ]
    
    for file_path in static_files:
        if not os.path.exists(file_path):
            print(f"❌ Missing static file: {file_path}")
            return False
        print(f"✅ Found: {file_path}")
    return True

def test_app_structure():
    """Test app directory structure."""
    print("🔍 Testing app structure...")
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/api/__init__.py", 
        "app/api/routes.py",
        "app/api/websockets.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/core/downloader.py",
        "app/core/session.py",
        "app/models/__init__.py",
        "app/models/schemas.py"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Missing app file: {file_path}")
            return False
        print(f"✅ Found: {file_path}")
    return True

def test_requirements():
    """Test requirements files."""
    print("🔍 Testing requirements files...")
    req_files = [
        "requirements-web.txt",
        "requirements-web-windows.txt"
    ]
    
    for file_path in req_files:
        if not os.path.exists(file_path):
            print(f"❌ Missing requirements: {file_path}")
            return False
        print(f"✅ Found: {file_path}")
    return True

def test_imports():
    """Test critical imports without installing dependencies."""
    print("🔍 Testing import structure...")
    
    # Add current directory to Python path for testing
    sys.path.insert(0, os.getcwd())
    
    try:
        # Test app modules can be imported
        import app
        import app.models.schemas
        import app.core.config
        import app.core.session
        print("✅ App modules import correctly")
    except ImportError as e:
        print(f"❌ Import error in app modules: {e}")
        return False
    
    try:
        # Test that we can check for optional dependencies
        import importlib.util
        
        # Check if FastAPI would be importable (without actually importing)
        fastapi_spec = importlib.util.find_spec("fastapi")
        if fastapi_spec is None:
            print("⚠️  FastAPI not installed (expected for fresh install)")
        else:
            print("✅ FastAPI is available")
        
        return True
    except Exception as e:
        print(f"❌ Error testing imports: {e}")
        return False

def test_launch_scripts():
    """Test launch scripts exist and have correct permissions."""
    print("🔍 Testing launch scripts...")
    
    scripts = [
        ("start_server.py", False),
        ("run_web_windows_fixed.bat", False),
        ("run_web_macos.sh", True)  # Should be executable
    ]
    
    for script, should_be_executable in scripts:
        if not os.path.exists(script):
            print(f"❌ Missing launch script: {script}")
            return False
        
        if should_be_executable and not os.access(script, os.X_OK):
            print(f"⚠️  {script} is not executable (fixing...)")
            os.chmod(script, 0o755)
        
        print(f"✅ Found: {script}")
    
    return True

def main():
    """Run all tests."""
    print("🧪 Google Photos Downloader - Setup Validation")
    print("=" * 50)
    
    # Change to script directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    tests = [
        test_python_version,
        test_app_structure,
        test_static_files,
        test_requirements,
        test_imports,
        test_launch_scripts,
        test_credentials
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Project is ready for deployment.")
        print("🚀 Users can run:")
        print("   Windows: run_web_windows_fixed.bat")
        print("   macOS/Linux: ./run_web_macos.sh")
        print("   Cross-platform: python start_server.py")
        return 0
    else:
        print("❌ Some tests failed. Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())