# Windows Installation Guide

## Option 1: Use the Executable (Recommended)

**No Python installation needed!**

1. Download [GooglePhotosDownloader-Windows.zip](https://github.com/felixhamel/google-photos-downloader/releases/latest/download/GooglePhotosDownloader-Windows.zip)
2. Extract the ZIP file to any folder you want
3. Follow the `OAUTH_GUIDE.md` inside to get Google credentials
4. Put your `credentials.json` file in the same folder as `GooglePhotosDownloader.exe`
5. Double-click `GooglePhotosDownloader.exe` to start

The app will automatically open in your web browser at http://127.0.0.1:8000

### Troubleshooting the Executable

**Windows blocks the executable:**
- Right-click the file → Properties → Check "Unblock" → OK
- Or add an exception in Windows Defender

**Executable won't start:**
- Make sure you extracted ALL files from the ZIP
- Don't run it directly from inside the ZIP file
- Try running as administrator once

## Option 2: Running from Source

If you want to run from Python source (for development):

### Prerequisites
- Python 3.8 or newer installed
- Make sure "Add Python to PATH" was checked during installation

### Installation
```cmd
# Download the source code
git clone https://github.com/felixhamel/google-photos-downloader.git
cd google-photos-downloader

# Install dependencies (Windows-safe versions)
pip install --only-binary=all -r requirements-web-windows.txt

# Start the app
python start_server.py
```

### If You Get "Rust/Cargo compilation required" Errors

This happens with newer Python packages. The `requirements-web-windows.txt` file uses older versions that don't need compilation, but if you still get errors:

```cmd
# Force older versions that don't need Rust
pip install --force-reinstall --only-binary=all fastapi==0.100.1 uvicorn==0.23.2 pydantic==1.10.13
```

### Command Line Usage

```cmd
# See all options
python cli_mode.py --help

# Download recent photos
python cli_mode.py --last-30-days

# Download specific date range
python cli_mode.py --start-date 2023-06-01 --end-date 2023-08-31 --output "Summer_2023"

# List your albums first
python cli_mode.py --list-albums
```

## Google Credentials Setup

Both methods (executable and source) need Google credentials:

1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable "Google Photos Library API"
4. Create OAuth2 credentials (Desktop Application type)
5. Download the JSON file and rename it to `credentials.json`
6. Put it in the same folder as the executable (or project root)

See `OAUTH_GUIDE.md` for detailed step-by-step instructions.

## What You'll Get

- French web interface at http://127.0.0.1:8000
- Real-time download progress
- Photos named with timestamps like `20230615_143022_IMG_1234.jpg`
- Can resume interrupted downloads
- Command line mode for automation

**Recommendation:** Use the executable version unless you're a developer. It's much easier and doesn't require Python setup.