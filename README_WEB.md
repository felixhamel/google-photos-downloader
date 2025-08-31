# Google Photos Downloader v2.0 - Web Edition

🚀 **A modern web-based replacement for the broken GUI**, built with FastAPI + HTML/JS + Tailwind CSS.

## ✨ Features

- **🌐 Modern Web Interface**: Clean, responsive design that works in any browser
- **📱 Mobile-Friendly**: Optimized for desktop and mobile devices
- **⚡ Real-Time Progress**: Live updates via WebSockets during downloads
- **🎯 Local-Only**: Runs locally on your machine (127.0.0.1:8000)
- **📂 Session Resume**: Pause and resume downloads anytime
- **🎨 Dark/Light Mode**: Toggle between themes
- **📊 Advanced Progress Tracking**: Speed, ETA, and detailed statistics

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements-web.txt
```

### 2. Start the Web App
```bash
cd app
uvicorn main:app --host 127.0.0.1 --port 8000
```

### 3. Open in Browser
Navigate to: http://127.0.0.1:8000

## 🔧 Setup Google Photos API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable **Google Photos Library API**  
3. Create **OAuth2 credentials** (Desktop Application)
4. Download as `credentials.json` in the project root

## 📁 Project Structure

```
google-photos-downloader/
├── app/                    # FastAPI Web Application
│   ├── main.py            # FastAPI app entry point
│   ├── api/               # API routes and WebSocket handlers
│   ├── core/              # Core business logic
│   └── models/            # Pydantic schemas
├── static/                # Frontend assets
│   ├── index.html         # Main web interface
│   └── js/app.js          # JavaScript application
├── requirements-web.txt   # Web app dependencies
└── run_web.py            # User-friendly startup script
```

## 🌟 Key Improvements Over GUI Version

- **✅ Actually Works**: No more empty windows or crashes
- **🔄 Real-Time Updates**: See progress as it happens  
- **💾 Session Management**: Resume interrupted downloads
- **📊 Better Analytics**: Speed tracking, ETA, completion rates
- **🎨 Modern UX**: Intuitive interface with notifications
- **📱 Cross-Platform**: Works on any device with a browser

## 🛠 API Endpoints

- **GET** `/` - Web interface
- **GET** `/api/auth/status` - Check authentication
- **GET** `/api/albums` - List Google Photos albums  
- **POST** `/api/download/start` - Start new download
- **POST** `/api/download/resume` - Resume existing session
- **GET** `/api/sessions` - List download sessions
- **WS** `/ws/{session_id}` - Real-time progress updates

## 🔒 Security & Privacy

- **Local Only**: Web app runs on 127.0.0.1 (localhost)
- **No External Connections**: Data stays on your machine
- **OAuth2 Secure**: Uses Google's official authentication
- **No Data Collection**: Zero telemetry or tracking

## 🎯 Usage

1. **Authenticate**: The app will guide you through Google authentication
2. **Choose Source**: Select date range or specific album
3. **Set Destination**: Pick where to save your photos
4. **Start Download**: Click "Start Download" and watch the progress
5. **Resume Later**: If interrupted, use "Resume Session" to continue

## 🔧 Configuration

The app uses `config/config.yaml` for settings:

```yaml
download:
  max_workers: 5          # Concurrent downloads
  chunk_size: 8192        # Download chunk size
  timeout: 30             # Request timeout

files:
  duplicate_detection: true    # Skip duplicate files
  naming_pattern: '{timestamp}_{filename}'  # File naming
```

## 🚨 Troubleshooting

- **Port 8000 in use**: Use `--port 8001` to change port
- **Authentication fails**: Check `credentials.json` file exists
- **No albums show**: Click "Refresh" after authenticating
- **Downloads fail**: Check internet connection and Google API quotas

---

**This web version completely replaces the broken GUI and provides a much better user experience!** 🎉