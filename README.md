# Google Photos Downloader

A simple tool to download your Google Photos library with multiple interface options.

## What it does

Downloads photos and videos from your Google Photos account to your local machine. Supports downloading by date ranges, specific albums, or recent photos. All downloads preserve original quality and include metadata.

## Quick Start

### 1. Get Google credentials

You need OAuth2 credentials from Google Cloud Console:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Photos Library API
4. Create OAuth2 credentials (Desktop application type)
5. Download the JSON file and rename it to `credentials.json`
6. Put it in this folder

### 2. Choose your interface

**Web interface** (recommended for most users):
```bash
python start_server.py
```
Opens http://127.0.0.1:8000 in your browser with a friendly interface.

**Command line** (good for automation):
```bash
# Download last 30 days
python cli_mode.py --last-30-days

# Download specific date range
python cli_mode.py --start-date 2023-06-01 --end-date 2023-08-31 --output "Summer 2023"

# List your albums first
python cli_mode.py --list-albums
```

**Original GUI** (if you prefer desktop apps):
```bash
python src/google_photos_downloader.py
```

## Installation

Install dependencies:
```bash
pip install -r requirements-web.txt
```

On Windows, if you get compilation errors:
```bash
pip install --only-binary=all -r requirements-web-windows.txt
```

## Features

- Downloads original quality photos and videos
- Organizes files with timestamps (e.g., `20230615_143022_photo.jpg`)
- Resumes interrupted downloads
- Real-time progress tracking
- Works on Windows, macOS, and Linux
- Multiple interface options (web, CLI, GUI)

## Common Issues

**"credentials.json not found"**: You need to set up Google API access first (see step 1 above).

**"Rust/Cargo compilation errors"** on Windows: Use `requirements-web-windows.txt` instead.

**"No photos found"**: Check your date ranges and make sure you have photos in Google Photos for those dates.

## How authentication works

Your `credentials.json` file identifies this app to Google. When you run it the first time, it opens a browser to log into your Google account and authorize access. This creates a `token.json` file that's tied to your specific Google account.

The app only has read-only access to your Google Photos - it can't modify or delete anything.

## Project Structure

```
├── start_server.py              # Web interface launcher
├── cli_mode.py                  # Command line interface  
├── src/google_photos_downloader.py  # Original GUI
├── app/                         # Web application code
├── static/                      # Web interface files
└── requirements-*.txt           # Dependencies
```

## License

MIT License - feel free to use and modify.

## Contributing

This is a personal project but pull requests are welcome. Please test your changes across different operating systems if possible.

---

Need help? Check `OAUTH_GUIDE.md` for detailed setup instructions or `INSTALL_WINDOWS.md` for Windows-specific troubleshooting.