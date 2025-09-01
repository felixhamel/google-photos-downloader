# Google Photos Downloader

I got tired of Google Photos not having a proper export feature, so I made this.

## What it does

Downloads your photos and videos from Google Photos to your computer. You can grab everything, just recent stuff, or specific date ranges. The original quality is preserved.

## Getting started

First you need to get credentials from Google (I know, it's annoying but necessary):

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Make a new project 
3. Enable the "Google Photos Library API"
4. Create OAuth2 credentials (pick "Desktop application")
5. Download the JSON file, rename it to `credentials.json` and put it here

Then pick how you want to use it:

**Web version** (easiest):
```bash
python start_server.py
```
This opens http://127.0.0.1:8000 in your browser.

**Command line** (for scripts):
```bash
python cli_mode.py --last-30-days
python cli_mode.py --start-date 2023-06-01 --end-date 2023-08-31
```

**Original desktop app**:
```bash
python src/google_photos_downloader.py
```
(Though this one had some issues, which is why I made the web version)

## Setup

You'll need Python 3.8+ installed.

```bash
pip install -r requirements-web.txt
```

Windows users: if you get weird compilation errors, try:
```bash
pip install --only-binary=all -r requirements-web-windows.txt
```

## What it can do

- Downloads full quality photos and videos
- Names files with timestamps like `20230615_143022_photo.jpg`
- Can resume if it gets interrupted
- Shows progress in real-time
- Works on Windows, Mac, Linux

## Troubleshooting

**"credentials.json not found"** - You skipped the Google setup step above

**Compilation errors on Windows** - Use the Windows-specific requirements file

**"No photos found"** - Double-check your date ranges

## How the Google login works

The `credentials.json` file just tells Google what app this is. When you run it the first time, it opens your browser to log into your Google account. If you say yes, it creates a `token.json` file that lets it access your photos.

Don't worry - it only has read access. It can't delete or modify anything.

## License

MIT - do whatever you want with this code.