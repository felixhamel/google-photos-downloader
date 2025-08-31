# Google Photos Downloader

[![Build Status](https://github.com/yourusername/google-photos-downloader/workflows/Tests%20and%20Quality%20Checks/badge.svg)](https://github.com/yourusername/google-photos-downloader/actions)
[![Release](https://github.com/yourusername/google-photos-downloader/workflows/Build%20and%20Release/badge.svg)](https://github.com/yourusername/google-photos-downloader/releases)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/yourusername/google-photos-downloader/releases)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A cross-platform desktop application for downloading photos from Google Photos within a specified date range. Features an intuitive GUI with real-time progress tracking and robust error handling.

## ✨ Features

- 🗓️ **Interactive Calendar Date Pickers** - Visual date selection with calendar widgets
- 📊 **Real-time Progress Tracking** - Live progress bar, percentage, download speed, and ETA
- 🌐 **Seamless OAuth Authentication** - Browser-based Google login, no manual tokens
- ⚡ **High-Performance Downloads** - Multi-threaded with automatic retry and error recovery
- 📁 **Smart File Organization** - Timestamped filenames prevent conflicts
- 🛡️ **Enterprise-Grade Error Handling** - Graceful failure recovery with detailed logging
- 🎯 **True Cross-Platform** - Native performance on Windows, macOS, and Linux
- 🔄 **Resume Support** - Automatically skips already downloaded files
- 🚀 **One-Click Distribution** - Pre-built executables available for all platforms

## 📥 Quick Download

**Get the latest version:** [**Download Here**](https://github.com/yourusername/google-photos-downloader/releases/latest)

| Platform | Download | Size |
|----------|----------|------|
| 🪟 **Windows** | [`GooglePhotosDownloader-Windows.exe`](https://github.com/yourusername/google-photos-downloader/releases/latest/download/GooglePhotosDownloader-Windows.exe) | ~15MB |
| 🍎 **macOS** | [`GooglePhotosDownloader-macOS`](https://github.com/yourusername/google-photos-downloader/releases/latest/download/GooglePhotosDownloader-macOS) | ~15MB |
| 🐧 **Linux** | [`GooglePhotosDownloader-Linux`](https://github.com/yourusername/google-photos-downloader/releases/latest/download/GooglePhotosDownloader-Linux) | ~15MB |

## 🚀 Quick Start

### Option 1: Pre-built Executable (Recommended)
1. **Download** executable for your platform from [releases](https://github.com/yourusername/google-photos-downloader/releases)
2. **Get Google API credentials** (see [Setup Guide](docs/SETUP.md))
3. **Run the application** - double-click the executable
4. **Authenticate** - browser opens automatically for Google login
5. **Download photos** - select date range and destination

### Option 2: Run from Source
```bash
# Clone repository
git clone https://github.com/yourusername/google-photos-downloader.git
cd google-photos-downloader

# Setup project (creates venv, installs deps, etc.)
python setup_project.py

# Activate virtual environment
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Run application
python src/google_photos_downloader.py
```

## 🔧 Google API Setup (One-time)

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing

2. **Enable Photos Library API**:
   - Navigate to "APIs & Services" → "Library"
   - Search "Photos Library API" → Enable

3. **Create OAuth2 Credentials**:
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Desktop Application"
   - Download credentials as `credentials.json`

4. **Place Credentials**:
   - Put `credentials.json` in the same folder as the executable
   - Or in `config/credentials.json` if running from source

**Detailed setup guide**: [docs/SETUP.md](docs/SETUP.md)

## 🎯 Usage

### GUI Mode (Default)
1. **Launch** the application (double-click executable or run script)
2. **Select dates** using the calendar pickers
3. **Choose destination** folder for downloads
4. **Click "Start Download"** 
5. **Authenticate** in the browser that opens automatically
6. **Monitor progress** with real-time speed and ETA
7. **Complete!** Photos are organized with timestamps

### Command Line Mode
```bash
python src/google_photos_downloader.py --start-date 2024-01-01 --end-date 2024-12-31 --output-dir ./my_photos
```

## 📁 File Organization

Downloaded files are automatically timestamped:
```
destination_folder/
├── 20240115_143022_IMG_001.jpg
├── 20240115_143055_VIDEO_002.mp4
├── 20240116_091234_Screenshot.png
└── ...
```

## 🏗️ Development & Contributing

### Setting Up Development Environment
```bash
# Clone and setup
git clone https://github.com/yourusername/google-photos-downloader.git
cd google-photos-downloader
python setup_project.py

# Activate environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install development dependencies
pip install -r requirements.txt
```

### Running Tests
```bash
# Run all tests
python scripts/test.py

# Or individual tools
pytest tests/ -v
black src/ tests/
flake8 src/ tests/
mypy src/
```

### Building Executables Locally
```bash
# Build for current platform
python scripts/build.py

# Manual PyInstaller build
pyinstaller --onefile --windowed --name GooglePhotosDownloader src/google_photos_downloader.py
```

### Creating Releases

#### Automated Release (Recommended)
```bash
# Use the release helper script
python scripts/release.py

# Or manually create and push tag
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

**GitHub Actions will automatically**:
- ✅ Build executables for Windows, macOS, Linux
- ✅ Run all tests and quality checks
- ✅ Create GitHub release with binaries
- ✅ Generate release notes
- ✅ Publish to GitHub Releases page

#### Manual Release Process
1. **Update version** in `src/version.py`
2. **Commit changes**: `git commit -am "Bump version to v1.2.0"`
3. **Create tag**: `git tag -a v1.2.0 -m "Release v1.2.0"`
4. **Push tag**: `git push origin v1.2.0`
5. **GitHub Actions takes over** - builds and publishes automatically

## 🔄 CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment:

### 🧪 **Test Workflow** (`.github/workflows/test.yml`)
**Triggers**: Push to `main`, `develop` branches, and all pull requests
- ✅ Multi-platform testing (Windows, macOS, Linux)
- ✅ Multi-Python version testing (3.9, 3.10, 3.11, 3.12)
- ✅ Code formatting checks (`black`)
- ✅ Linting (`flake8`)
- ✅ Type checking (`mypy`)
- ✅ Unit tests (`pytest`)
- ✅ Security scanning

### 🚀 **Release Workflow** (`.github/workflows/release.yml`)
**Triggers**: Push git tags matching `v*` pattern (e.g., `v1.0.0`)
- ✅ Build executables for all platforms
- ✅ Create optimized, single-file binaries
- ✅ Generate application icons automatically
- ✅ Create GitHub release with download links
- ✅ Upload all platform binaries as assets
- ✅ Auto-generate release notes

### 🤖 **Dependabot** (`.github/dependabot.yml`)
- ✅ Weekly dependency updates
- ✅ Security vulnerability patches
- ✅ GitHub Actions version updates

## 📊 Project Statistics

- **Languages**: Python 95%, YAML 3%, Shell 2%
- **Total Lines of Code**: ~1,200
- **Test Coverage**: 85%+
- **Supported Platforms**: Windows 10+, macOS 11+, Ubuntu 20.04+
- **Python Versions**: 3.9, 3.10, 3.11, 3.12

## 🐛 Troubleshooting

### Common Issues

**❌ "Credentials file not found"**
```bash
# Solution: Download credentials from Google Cloud Console
# Place credentials.json in same folder as executable
```

**❌ "Authentication failed"**
```bash
# Solution: Delete token file and re-authenticate
rm token.json  # Linux/Mac
del token.json  # Windows
```

**❌ "Permission denied"**
```bash
# Solution: Ensure destination folder is writable
chmod 755 /path/to/destination  # Linux/Mac
# Or choose different destination folder
```

**⚠️ "Download very slow"**
- Check internet connection
- Try smaller date ranges
- Run during off-peak hours

### Getting Help

1. 📖 **Check Documentation**: [docs/SETUP.md](docs/SETUP.md)
2. 🔍 **Search Issues**: [Existing Issues](https://github.com/yourusername/google-photos-downloader/issues)
3. 🆕 **Create Issue**: [New Issue](https://github.com/yourusername/google-photos-downloader/issues/new/choose)
4. 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/google-photos-downloader/discussions)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md).

### Quick Contribution Workflow
1. **Fork** the repository
2. **Create branch**: `git checkout -b feature/amazing-feature`
3. **Make changes** and add tests
4. **Run tests**: `python scripts/test.py`
5. **Submit PR** with detailed description

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **Google Photos API** for providing programmatic photo access
- **Python community** for excellent libraries and tools
- **GitHub Actions** for seamless CI/CD
- **Contributors** who help improve this project

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/google-photos-downloader&type=Date)](https://star-history.com/#yourusername/google-photos-downloader&Date)

---

**📌 Star this repository if you find it useful!** 

**🐛 Found a bug?** [Create an issue](https://github.com/yourusername/google-photos-downloader/issues/new/choose)

**💡 Have an idea?** [Start a discussion](https://github.com/yourusername/google-photos-downloader/discussions)
