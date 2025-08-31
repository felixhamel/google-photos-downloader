#!/usr/bin/env python3
"""
Release helper script for Google Photos Downloader.
"""

import subprocess
import sys
import re
from pathlib import Path

def get_current_version():
    """Get current version from git tags."""
    try:
        result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "v0.0.0"

def bump_version(version, bump_type):
    """Bump version number."""
    clean_version = version.lstrip('v')
    parts = clean_version.split('.')
    
    if len(parts) != 3:
        parts = ['0', '0', '0']
    
    major, minor, patch = map(int, parts)
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    
    return f"v{major}.{minor}.{patch}"

def create_release(new_version):
    """Create and push a new release tag."""
    print(f"🏷️ Creating release {new_version}")
    
    # Create annotated tag
    subprocess.run(['git', 'tag', '-a', new_version, '-m', f'Release {new_version}'], check=True)
    
    # Push tag to trigger CI
    subprocess.run(['git', 'push', 'origin', new_version], check=True)
    
    print(f"✅ Release {new_version} created and pushed!")
    print(f"🔗 GitHub Actions will build executables automatically")

def main():
    current = get_current_version()
    print(f"📋 Current version: {current}")
    
    print("\n🎯 Select release type:")
    print("1. 🐛 Patch (bug fixes)")
    print("2. ✨ Minor (new features)") 
    print("3. 💥 Major (breaking changes)")
    print("4. 🎨 Custom version")
    
    choice = input("\nChoice (1-4): ").strip()
    
    if choice == '1':
        new_version = bump_version(current, 'patch')
    elif choice == '2':
        new_version = bump_version(current, 'minor')
    elif choice == '3':
        new_version = bump_version(current, 'major')
    elif choice == '4':
        custom = input("Enter version (e.g., v2.1.0): ").strip()
        if not re.match(r'^v?\d+\.\d+\.\d+
        """Create comprehensive .gitignore file."""
        gitignore_content = """# Google Photos Downloader - Git Ignore Rules

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Virtual Environment
venv/
env/
ENV/
env.bak/
venv.bak/
pyvenv.cfg

# IDE and Editors
.vscode/
.idea/
*.swp
*.swo
*~
.vimrc.local
.sublime-*

# OS Generated Files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
desktop.ini

# Google API Credentials (CRITICAL!)
credentials.json
token.json
client_secret*.json
service_account*.json

# User Data and Downloads
downloads/
photos/
GooglePhotos/
user_data/

# Logs and Temporary Files
*.log
logs/
temp/
tmp/
.tmp/

# Configuration Files with Sensitive Data
config/credentials.json
config/token.json
config/local_settings.json
.env
.env.local

# Test Outputs and Coverage
.coverage
.pytest_cache/
.tox/
htmlcov/
test_downloads/
coverage.xml
*.cover
.hypothesis/

# Build and Distribution
*.exe
*.dmg
*.app
*.deb
*.rpm
*.pkg
*.msi

# Development Tools
.mypy_cache/
.black
.flake8.log

# Documentation Build
docs/_build/
site/

# Backup Files
*.bak
*.backup
*~

# Local Development
local_config.py
debug_*.py
test_script.py
"""
        
        gitignore_file = self.project_path / ".gitignore"
        gitignore_file.write_text(gitignore_content)
        print(f"✅ Created: {gitignore_file}")
    
    def initialize_git_repository(self):
        """Initialize Git repository with CI/CD setup."""
        self.print_step("Initializing Git Repository with CI/CD", "🗃️")
        
        if not shutil.which("git"):
            print("⚠️ Git not found. Skipping repository initialization.")
            return
        
        # Initialize repository
        self.run_command(["git", "init"])
        self.run_command(["git", "config", "init.defaultBranch", "main"])
        
        # Add all files
        self.run_command(["git", "add", "."])
        
        # Initial commit
        self.run_command(["git", "commit", "-m", "🎉 Initial project setup with CI/CD pipeline\n\n- Complete project structure\n- GitHub Actions workflows\n- Multi-platform build support\n- Automated releases\n- Development tools"])
        
        print("✅ Git repository initialized")
        print("💡 Next steps:")
        print(f"   1. Create GitHub repository: https://github.com/new")
        print(f"   2. Add remote: git remote add origin https://github.com/yourusername/{self.project_name}.git")
        print(f"   3. Push: git push -u origin main")
        print(f"   4. Create first release: git tag v1.0.0 && git push origin v1.0.0")
    
    def print_completion_summary(self):
        """Print comprehensive setup completion summary."""
        print("
" + "="*70)
        print("🎉 ENHANCED PROJECT SETUP COMPLETE!")
        print("="*70)
        
        print(f"
📁 Project Location: {self.project_path}")
        
        print("
🚀 **Immediate Next Steps:**")
        print("1. 📋 Copy main application code:")
        print(f"   → Copy the enhanced Python GUI code into: src/google_photos_downloader.py")
        
        print("
2. 🔐 Setup Google API credentials:")
        print("   → Go to: https://console.cloud.google.com/")
        print("   → Enable Photos Library API")
        print("   → Create OAuth2 Desktop credentials") 
        print("   → Download as 'credentials.json' → place in config/ folder")
        
        print("
3. 🧪 Test locally:")
        if self.is_windows:
            print(f"   → run_windows.bat")
        else:
            print(f"   → ./run_unix.sh")
        
        print("
🔄 **CI/CD Pipeline Ready:**")
        print("4. 📤 Push to GitHub:")
        print(f"   → git remote add origin https://github.com/yourusername/{self.project_name}.git")
        print(f"   → git push -u origin main")
        
        print("
5. 🏷️ Create first release:")
        print(f"   → git tag v1.0.0")
        print(f"   → git push origin v1.0.0")
        print(f"   → ✨ GitHub Actions automatically builds executables!")
        
        print("
📊 **What You Get:**")
        print("   ✅ Multi-platform executables (Windows, macOS, Linux)")
        print("   ✅ Automated testing on all platforms") 
        print("   ✅ GitHub Releases with download links")
        print("   ✅ Dependency updates via Dependabot")
        print("   ✅ Issue templates and PR guidelines")
        print("   ✅ Professional documentation")
        
        print("
🔗 **Workflows Created:**")
        print("   📋 .github/workflows/release.yml - Builds & releases on tags")
        print("   🧪 .github/workflows/test.yml - Tests on PRs and pushes")
        print("   🤖 .github/dependabot.yml - Automated dependency updates")
        
        print("
🎯 **Release Process:**")
        print("   1. Make changes → commit → push")
        print("   2. Create tag: git tag v1.1.0")
        print("   3. Push tag: git push origin v1.1.0") 
        print("   4. 🤖 GitHub Actions builds executables automatically")
        print("   5. 📦 Users download from GitHub Releases page")
        
        print("
📚 **Documentation:**")
        print(f"   → README: {self.project_path}/README.md")
        print(f"   → Setup Guide: {self.project_path}/docs/SETUP.md")
        print(f"   → Contributing: {self.project_path}/CONTRIBUTING.md")
        
        print(f"
✅ **Ready for development and automated releases!** 🚀")
    
    def run_setup(self):
        """Execute the complete enhanced project setup."""
        print("🚀 Google Photos Downloader - Enhanced Setup with CI/CD")
        print("=" * 60)
        print(f"Project: {self.project_name}")
        print(f"Location: {self.project_path}")
        print(f"Platform: {platform.system()} {platform.release()}")
        
        try:
            # Check if project exists
            if self.project_path.exists():
                response = input(f"
⚠️ Directory '{self.project_name}' exists. Continue? (y/N): ")
                if response.lower() != 'y':
                    print("Setup cancelled.")
                    return False
            
            # Execute all setup steps
            self.create_directory_structure()
            self.create_github_workflows()
            self.create_github_templates()
            self.create_dependabot_config()
            
            if not self.create_virtual_environment():
                print("❌ Virtual environment setup failed")
                return False
            
            self.install_dependencies()
            self.create_requirements_file()
            self.create_version_file()
            self.create_main_application()
            self.create_config_files()
            self.create_run_scripts()
            self.create_tests()
            self.create_comprehensive_readme()
            self.create_contributing_guide()
            self.create_license()
            self.create_changelog()
            self.create_comprehensive_gitignore()
            self.create_build_scripts()
            self.create_release_script()
            self.create_setup_instructions()
            self.initialize_git_repository()
            
            self.print_completion_summary()
            return True
            
        except KeyboardInterrupt:
            print("

⚠️ Setup interrupted by user.")
            return False
        except Exception as e:
            print(f"
❌ Setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main setup function."""
    project_name = sys.argv[1] if len(sys.argv) > 1 else "google-photos-downloader"
    
    # Validate project name
    if not project_name.replace("-", "").replace("_", "").isalnum():
        print("❌ Invalid project name. Use letters, numbers, hyphens, underscores only.")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required. Current version:", sys.version)
        sys.exit(1)
    
    # Run enhanced setup
    setup = EnhancedProjectSetup(project_name)
    success = setup.run_setup()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
, custom):
            print("❌ Invalid format. Use v1.2.3")
            sys.exit(1)
        new_version = custom if custom.startswith('v') else f'v{custom}'
    else:
        print("❌ Invalid choice")
        sys.exit(1)
    
    print(f"\n📋 New version: {new_version}")
    if input("Create release? (y/N): ").strip().lower() == 'y':
        create_release(new_version)

if __name__ == '__main__':
    main()
