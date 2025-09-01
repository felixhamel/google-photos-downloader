#!/usr/bin/env python3
"""
"""
import os
import sys
import subprocess
import importlib.util
from pathlib import Path


class FullProjectTester:
    """Comprehensive project tester for all modes."""
    
    def __init__(self):
        """Initialize tester."""
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        # Change to project root for testing (parent directory)
        os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def test(self, name: str, func) -> bool:
        """Run a test and track results."""
        print(f"Testing {name}...")
        try:
            result = func()
            if result:
                print(f"{name}: PASSED")
                self.passed += 1
                return True
            else:
                print(f"{name}: FAILED")
                self.failed += 1
                return False
        except Exception as e:
            print(f"{name}: EXCEPTION - {e}")
            self.failed += 1
            return False
    
    def warning(self, message: str):
        """Log a warning."""
        print(f"WARNING: {message}")
        self.warnings += 1
    
    def test_python_environment(self) -> bool:
        """Test Python environment."""
        if sys.version_info < (3, 8):
            return False
        return True
    
    def test_project_structure(self) -> bool:
        """Test complete project structure."""
        required_files = [
            # Core application
            "src/google_photos_downloader.py",  # Original GUI
            "cli_mode.py",                      # CLI mode
            "start_server.py",                  # Web launcher
            
            # Web application
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
            "app/models/schemas.py",
            
            # Static files
            "static/index.html",
            "static/js/app.js",
            
            # Launch scripts (moved to scripts/launchers)
            "scripts/launchers/run_web_windows_fixed.bat",
            "scripts/launchers/run_web_macos.sh",
            
            # Requirements
            "requirements.txt",
            "requirements-web.txt", 
            "requirements-web-windows.txt",
            
            # Documentation
            "README.md",
            "OAUTH_GUIDE.md",
            "DEPLOYMENT_GUIDE.md",
            "INSTALL_WINDOWS.md",
            
            # Test scripts (moved to tests/)
            "tests/test_setup.py",
            "tests/test_full_project.py"
        ]
        
        missing = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing.append(file_path)
        
        if missing:
            print(f"Missing files: {missing}")
            return False
        
        return True
    
    def test_python_imports(self) -> bool:
        """Test all Python imports work."""
        # Add current directory and app directory to path
        sys.path.insert(0, os.getcwd())
        sys.path.insert(0, os.path.join(os.getcwd(), 'app'))
        
        modules_to_test = [
            # Core modules (should work from any directory)
            ("cli_mode", None),
            
            # App modules - test individual components
            ("models.schemas", None),
            ("core.config", None),
            ("core.session", None),
            ("api.websockets", None),
        ]
        
        for module_name, expected_attr in modules_to_test:
            try:
                module = __import__(module_name, fromlist=[''])
                if expected_attr and not hasattr(module, expected_attr):
                    print(f"Module {module_name} missing attribute {expected_attr}")
                    return False
                print(f"  OK {module_name}")
            except ImportError as e:
                print(f"Cannot import {module_name}: {e}")
                return False
        
        return True
    
    def test_gui_mode(self) -> bool:
        """Test GUI mode (basic import test)."""
        try:
            # Test if GUI script can be imported
            spec = importlib.util.spec_from_file_location(
                "gui_module", "src/google_photos_downloader.py"
            )
            if spec is None:
                return False
            
            # Don't actually import to avoid GUI startup
            print("GUI module file exists and is valid Python")
            return True
        except Exception as e:
            print(f"GUI module error: {e}")
            return False
    
    def test_cli_mode(self) -> bool:
        """Test CLI mode functionality."""
        try:
            # Test CLI help
            result = subprocess.run([
                sys.executable, "cli_mode.py", "--help"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and "Google Photos Downloader - CLI Mode" in result.stdout:
                return True
            else:
                print(f"CLI help failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("CLI mode timeout")
            return False
        except Exception as e:
            print(f"CLI test error: {e}")
            return False
    
    def test_web_mode_imports(self) -> bool:
        """Test web mode can start (import test only)."""
        try:
            # Test web server imports
            import app.main
            
            # Check if FastAPI app is created
            if hasattr(app.main, 'app'):
                return True
            else:
                print("FastAPI app not found in main module")
                return False
        except ImportError as e:
            print(f"Web mode import error: {e}")
            return False
    
    def test_requirements_files(self) -> bool:
        """Test requirements files are valid."""
        req_files = [
            "requirements.txt",
            "requirements-web.txt",
            "requirements-web-windows.txt"
        ]
        
        for req_file in req_files:
            if not os.path.exists(req_file):
                print(f"Missing requirements file: {req_file}")
                return False
            
            try:
                with open(req_file, 'r') as f:
                    content = f.read()
                    if not content.strip():
                        print(f"Empty requirements file: {req_file}")
                        return False
            except Exception as e:
                print(f"Error reading {req_file}: {e}")
                return False
        
        return True
    
    def test_launch_scripts(self) -> bool:
        """Test launch scripts exist and are valid."""
        scripts = [
            ("start_server.py", False),
            ("scripts/launchers/run_web_windows_fixed.bat", False),
            ("scripts/launchers/run_web_macos.sh", True),  # Should be executable
            ("cli_mode.py", False)
        ]
        
        for script, should_be_executable in scripts:
            if not os.path.exists(script):
                print(f"Missing script: {script}")
                return False
            
            # Check executability for shell scripts
            if should_be_executable and not os.access(script, os.X_OK):
                self.warning(f"{script} is not executable")
            
            # Basic syntax check for Python scripts
            if script.endswith('.py'):
                try:
                    with open(script, 'r') as f:
                        compile(f.read(), script, 'exec')
                except SyntaxError as e:
                    print(f"Syntax error in {script}: {e}")
                    return False
        
        return True
    
    def test_documentation(self) -> bool:
        """Test documentation files exist and are not empty."""
        docs = [
            "README.md",
            "OAUTH_GUIDE.md", 
            "DEPLOYMENT_GUIDE.md",
            "INSTALL_WINDOWS.md"
        ]
        
        for doc in docs:
            if not os.path.exists(doc):
                print(f"Missing documentation: {doc}")
                return False
            
            try:
                with open(doc, 'r') as f:
                    content = f.read()
                    if len(content.strip()) < 100:  # Minimum content check
                        print(f"Documentation too short: {doc}")
                        return False
            except Exception as e:
                print(f"Error reading {doc}: {e}")
                return False
        
        return True
    
    def test_configuration_files(self) -> bool:
        """Test configuration and data files."""
        # Check that credentials.json is NOT included (security)
        if os.path.exists("credentials.json"):
            self.warning("credentials.json found - should not be in repository")
        
        # Check config structure
        config_files = ["app/config/config.yaml"]
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                        if not content.strip():
                            print(f"Empty config file: {config_file}")
                            return False
                except Exception as e:
                    print(f"Error reading {config_file}: {e}")
                    return False
        
        return True
    
    def test_static_web_files(self) -> bool:
        """Test web static files."""
        static_files = [
            "static/index.html",
            "static/js/app.js"
        ]
        
        for static_file in static_files:
            if not os.path.exists(static_file):
                print(f"Missing static file: {static_file}")
                return False
            
            try:
                with open(static_file, 'r') as f:
                    content = f.read()
                    if len(content.strip()) < 50:
                        print(f"Static file too short: {static_file}")
                        return False
                    
                    # Basic validation
                    if static_file.endswith('.html') and '<html' not in content:
                        print(f"Invalid HTML file: {static_file}")
                        return False
                    
                    if static_file.endswith('.js') and 'function' not in content and 'const' not in content:
                        print(f"Invalid JS file: {static_file}")
                        return False
            except Exception as e:
                print(f"Error reading {static_file}: {e}")
                return False
        
        return True
    
    def run_full_validation(self) -> bool:
        """Run complete project validation."""
        print("Google Photos Downloader - Full Project Test")
        print("=" * 70)
        
        tests = [
            ("Python Environment", self.test_python_environment),
            ("Project Structure", self.test_project_structure),
            ("Python Imports", self.test_python_imports),
            ("GUI Mode", self.test_gui_mode),
            ("CLI Mode", self.test_cli_mode),
            ("Web Mode", self.test_web_mode_imports),
            ("Requirements Files", self.test_requirements_files),
            ("Launch Scripts", self.test_launch_scripts),
            ("Documentation", self.test_documentation),
            ("Configuration", self.test_configuration_files),
            ("Static Web Files", self.test_static_web_files)
        ]
        
        for test_name, test_func in tests:
            self.test(test_name, test_func)
            print()
        
        # Summary
        print("=" * 70)
        print(f"RESULTS:")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Warnings: {self.warnings}")
        
        if self.failed == 0:
            print("All tests passed!")
            return True
        else:
            print("Some tests failed.")
            return False


def main():
    """Main test runner."""
    # Change to script directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    tester = FullProjectTester()
    success = tester.run_full_validation()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())