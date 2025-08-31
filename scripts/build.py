#!/usr/bin/env python3
"""
Build script for Google Photos Downloader.
Creates distributable executables for the current platform.
"""

import sys
import subprocess
import platform
import shutil
from pathlib import Path

def check_dependencies():
    """Check if required build tools are available."""
    try:
        import PyInstaller
        print("✅ PyInstaller available")
        return True
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True

def create_icon():
    """Create application icon if it doesn't exist."""
    icon_path = Path("assets/icon.ico")
    if icon_path.exists():
        print("✅ Icon already exists")
        return
    
    try:
        from PIL import Image, ImageDraw
        
        icon_path.parent.mkdir(exist_ok=True)
        
        # Create 64x64 icon
        img = Image.new('RGBA', (64, 64), (70, 130, 180, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw camera icon
        draw.rectangle([10, 20, 54, 50], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=2)
        draw.ellipse([20, 25, 44, 45], fill=(200, 200, 200, 255), outline=(0, 0, 0, 255), width=2)
        draw.ellipse([26, 29, 38, 41], fill=(100, 100, 100, 255))
        draw.rectangle([45, 15, 50, 20], fill=(255, 255, 0, 255))
        
        img.save(icon_path, format='ICO', sizes=[(64, 64), (32, 32), (16, 16)])
        print("✅ Created application icon")
        
    except ImportError:
        print("⚠️ Pillow not available, skipping icon creation")

def build_executable():
    """Build standalone executable."""
    if not check_dependencies():
        return False
    
    create_icon()
    
    print(f"🔨 Building executable for {platform.system()}...")
    
    # Base PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "GooglePhotosDownloader",
        "src/google_photos_downloader.py"
    ]
    
    # Add platform-specific options
    if platform.system() == "Windows":
        cmd.extend(["--windowed"])  # Hide console on Windows
        if Path("assets/icon.ico").exists():
            cmd.extend(["--icon", "assets/icon.ico"])
    elif platform.system() == "Darwin":  # macOS
        cmd.extend(["--windowed"])
        cmd.extend(["--osx-bundle-identifier", "com.googlephotos.downloader"])
    
    # Add optimization flags
    cmd.extend([
        "--optimize", "2",
        "--strip",  # Remove debug symbols
        "--noupx"   # Disable UPX compression (can cause antivirus issues)
    ])
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ Build successful!")
        
        # Show output location
        dist_path = Path("dist")
        executables = list(dist_path.glob("GooglePhotosDownloader*"))
        if executables:
            exe_path = executables[0]
            size = exe_path.stat().st_size / (1024 * 1024)  # MB
            print(f"📁 Executable: {exe_path}")
            print(f"📊 Size: {size:.1f} MB")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False

def clean_build():
    """Clean build artifacts."""
    print("🧹 Cleaning build artifacts...")
    
    dirs_to_clean = ["build", "dist", "__pycache__"]
    files_to_clean = ["*.spec"]
    
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"✅ Removed: {dir_name}/")
    
    for pattern in files_to_clean:
        for file_path in Path(".").glob(pattern):
            file_path.unlink()
            print(f"✅ Removed: {file_path}")

def main():
    """Main build function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Google Photos Downloader")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    parser.add_argument("--version", action="store_true", help="Show version info")
    
    args = parser.parse_args()
    
    if args.clean:
        clean_build()
        return
    
    if args.version:
        try:
            sys.path.insert(0, "src")
            from version import __version__
            print(f"Google Photos Downloader v{__version__}")
        except ImportError:
            print("Version information not available")
        return
    
    # Default: build executable
    print("🏗️ Google Photos Downloader - Build Script")
    print("=" * 50)
    
    success = build_executable()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
