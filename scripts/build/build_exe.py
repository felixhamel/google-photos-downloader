#!/usr/bin/env python3
"""
ABOUTME: PyInstaller build script for creating standalone executable
ABOUTME: Packages the Google Photos Downloader into a single .exe file
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


def main():
    """Build executable using PyInstaller."""
    print("🔧 Building Google Photos Downloader executable...")
    print("=" * 60)
    
    # Change to project root directory (2 levels up from scripts/build/)
    project_root = Path(__file__).parent.parent.parent.absolute()
    os.chdir(project_root)
    print(f"   Working directory: {project_root}")
    
    # Clean previous builds
    print("🧹 Cleaning previous builds...")
    for dir_name in ['build', 'dist', '__pycache__']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   Removed {dir_name}/")
    
    # Create spec file content
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Add all Python files that need to be included
a = Analysis(
    ['start_server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('static', 'static'),
        ('app', 'app'),
        ('cli_mode.py', '.'),
        ('requirements-web-windows.txt', '.'),
        ('OAUTH_GUIDE.md', '.'),
        ('README.md', '.'),
        ('INSTALL_WINDOWS.md', '.'),
    ],
    hiddenimports=[
        'app.main',
        'app.api.routes',
        'app.api.websockets',
        'app.core.config',
        'app.core.downloader',
        'app.core.session',
        'app.models.schemas',
        'uvicorn.main',
        'uvicorn.config',
        'uvicorn.server',
        'fastapi',
        'fastapi.staticfiles',
        'starlette.applications',
        'starlette.routing',
        'starlette.middleware',
        'google.auth.transport.requests',
        'google_auth_oauthlib.flow',
        'googleapiclient.discovery',
        'googleapiclient.errors',
        'cli_mode',
        'argparse',
        'datetime',
        'threading',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GooglePhotosDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    cofile=None,
    icon=None,
)
'''
    
    # Write spec file
    print("📝 Creating PyInstaller spec file...")
    with open('google_photos_downloader.spec', 'w') as f:
        f.write(spec_content)
    print("   Created google_photos_downloader.spec")
    
    # Run PyInstaller
    print("⚙️  Running PyInstaller...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            'google_photos_downloader.spec'
        ], check=True, capture_output=True, text=True)
        
        print("✅ Build completed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return 1
    
    # Check if executable was created (handle both Windows and Unix)
    exe_paths = [
        Path('dist/GooglePhotosDownloader.exe'),  # Windows
        Path('dist/GooglePhotosDownloader')       # macOS/Linux
    ]
    
    exe_path = None
    for path in exe_paths:
        if path.exists():
            exe_path = path
            break
    
    if exe_path:
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"🎉 Executable created: {exe_path}")
        print(f"📦 Size: {size_mb:.1f} MB")
        
        # Create distribution folder
        dist_folder = Path('distribution')
        if dist_folder.exists():
            shutil.rmtree(dist_folder)
        dist_folder.mkdir()
        
        # Copy executable (preserve name for cross-platform compatibility)
        exe_name = 'GooglePhotosDownloader.exe' if exe_path.suffix == '.exe' else 'GooglePhotosDownloader'
        target_exe = dist_folder / exe_name
        shutil.copy2(exe_path, target_exe)
        
        # Make executable on Unix systems
        if not exe_path.suffix == '.exe':
            os.chmod(target_exe, 0o755)
        
        # Copy documentation from project root
        project_root = Path.cwd()
        for doc in ['README.md', 'OAUTH_GUIDE.md', 'INSTALL_WINDOWS.md']:
            doc_path = project_root / doc
            if doc_path.exists():
                shutil.copy2(doc_path, dist_folder)
                print(f"   Copied {doc}")
        
        # Create setup instructions
        setup_instructions = '''# Google Photos Downloader - Portable Version

## What's in this folder:

1. **GooglePhotosDownloader.exe** - The main application (no Python installation needed!)
2. **OAUTH_GUIDE.md** - How to get Google credentials
3. **README.md** - General usage instructions

## Quick Setup:

### Step 1: Get Google Credentials
1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable "Google Photos Library API"
4. Create OAuth2 credentials (Desktop Application type)
5. Download the JSON file and rename it to "credentials.json"
6. Put credentials.json in the same folder as this executable

### Step 2: Run the Application
Double-click GooglePhotosDownloader.exe

The app will:
- Check for credentials.json
- Install any missing packages automatically
- Start the web server
- Open your browser to http://127.0.0.1:8000

## Family-Friendly Features:
- No Python installation required
- No command line needed
- Automatic browser opening
- French interface
- Real-time download progress
- Works completely offline (except for Google API)

## Troubleshooting:
- If antivirus blocks it: Add exception for GooglePhotosDownloader.exe
- If it doesn't start: Run as administrator once
- If browser doesn't open: Go to http://127.0.0.1:8000 manually

## File Organization:
Put this executable anywhere you want. It will:
- Create a downloads/ folder in the same location
- Save all photos there with timestamps
- Remember your settings between runs

No files are created outside of where you place the executable.
'''
        
        with open(dist_folder / 'SETUP_INSTRUCTIONS.txt', 'w', encoding='utf-8') as f:
            f.write(setup_instructions)
        
        print(f"📁 Distribution package created in: {dist_folder.absolute()}")
        print("\n🎯 Next steps:")
        print("1. Copy the entire 'distribution' folder to target computer")
        print("2. Follow SETUP_INSTRUCTIONS.txt to add credentials.json")
        print("3. Double-click GooglePhotosDownloader.exe to run")
        
        return 0
    else:
        print("❌ Executable not found after build")
        return 1


if __name__ == "__main__":
    sys.exit(main())