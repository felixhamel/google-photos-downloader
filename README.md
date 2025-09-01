# Google Photos Downloader

I got tired of Google Photos not having a proper export feature, so I made this.

## Quick Start (No Python needed!)

**Just want to use it?** Download the executable for your system:

- **Windows**: [GooglePhotosDownloader-Windows.zip](https://github.com/felixhamel/google-photos-downloader/releases/latest/download/GooglePhotosDownloader-Windows.zip)
- **macOS**: [GooglePhotosDownloader-macOS.tar.gz](https://github.com/felixhamel/google-photos-downloader/releases/latest/download/GooglePhotosDownloader-macOS.tar.gz)  

1. Download and extract the ZIP/tar.gz file
2. Follow the `OAUTH_GUIDE.md` inside to get Google credentials
3. Put your `credentials.json` file in the same folder
4. Double-click the executable to start

That's it! The web interface opens automatically at http://127.0.0.1:8000

## What it does

Downloads your photos and videos from Google Photos to your computer. You can grab everything, just recent stuff, or specific date ranges. The original quality is preserved and files get named with timestamps like `20230615_143022_photo.jpg`.

## Features

- **No installation required** - Just download and run the executable
- **Web interface** in French with real-time progress
- **Command line mode** for automation (run with `--help`)
- **Resume downloads** if interrupted
- **Original quality** preservation
- **Cross-platform** - Windows, macOS, Linux

## For Developers

If you want to run from source or contribute:

```bash
# Clone the repo
git clone https://github.com/felixhamel/google-photos-downloader.git
cd google-photos-downloader

# Install dependencies
pip install -r requirements-web.txt

# Windows users with compilation errors:
pip install --only-binary=all -r requirements-web-windows.txt

# Run the web interface
python start_server.py

# Or use command line
python cli_mode.py --last-30-days
```

## Google Setup

You need to get credentials from Google (one-time setup):

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Make a new project and enable "Google Photos Library API"
3. Create OAuth2 credentials (pick "Desktop application")
4. Download the JSON file, rename it to `credentials.json`
5. Put it in the same folder as the executable (or project root if running from source)

See `OAUTH_GUIDE.md` for detailed instructions.

## Troubleshooting

**"credentials.json not found"** - You need to set up Google API access first

**Executable won't run** - Make sure you extracted all files from the ZIP, don't run it from inside the archive

**"No photos found"** - Check your date ranges and make sure you have photos in Google Photos for those dates

## License

MIT - do whatever you want with this code.