# Setup Instructions - Google Photos Downloader

## 🎯 Complete Setup Guide

### Step 1: Project Setup
```bash
# Run the enhanced setup script
python setup_project.py google-photos-downloader
```

### Step 2: Copy Main Application
1. Open `src/google_photos_downloader.py`
2. Replace the placeholder with the complete application code from the artifact
3. Save the file

### Step 3: Google API Configuration

#### A. Google Cloud Console Setup
1. **Create Project**: Go to [Google Cloud Console](https://console.cloud.google.com/)
2. **Enable API**: Search "Photos Library API" → Enable
3. **Create Credentials**: 
   - "APIs & Services" → "Credentials" 
   - "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Desktop Application"
4. **Download**: Save as `config/credentials.json`

#### B. First Authentication
1. Run the application
2. Browser opens automatically
3. Login to Google → Grant permissions
4. Done! Token saved for future use

### Step 4: GitHub Repository (Optional)
```bash
# Create GitHub repo and push
git remote add origin https://github.com/yourusername/google-photos-downloader.git
git push -u origin main

# Create first release (triggers automated builds)
git tag v1.0.0
git push origin v1.0.0
```

## 🔄 Release Workflow

### Automated Releases
When you push a git tag (like `v1.0.0`), GitHub Actions automatically:

1. **🔨 Builds executables** for Windows, macOS, Linux
2. **🧪 Runs all tests** on multiple platforms
3. **📦 Creates GitHub release** with download links
4. **📝 Generates release notes** with changelog
5. **🚀 Publishes binaries** for users to download

### Creating a Release
```bash
# Option 1: Use helper script
python scripts/release.py

# Option 2: Manual
git tag v1.1.0
git push origin v1.1.0
```

### Release URLs
After pushing a tag, executables will be available at:
- Windows: `https://github.com/yourusername/google-photos-downloader/releases/download/v1.0.0/GooglePhotosDownloader-Windows.exe`
- macOS: `https://github.com/yourusername/google-photos-downloader/releases/download/v1.0.0/GooglePhotosDownloader-macOS`
- Linux: `https://github.com/yourusername/google-photos-downloader/releases/download/v1.0.0/GooglePhotosDownloader-Linux`

## 🧪 Development Workflow

### Local Development
```bash
# Activate environment
source venv/bin/activate  # or venv\Scripts\activate

# Run from source
python src/google_photos_downloader.py

# Run tests
python scripts/test.py

# Build executable locally
python scripts/build.py
```

### Code Quality
```bash
# Format code
black src/ tests/

# Check linting
flake8 src/ tests/

# Type checking
mypy src/
```

## 🔧 Troubleshooting

### Common Setup Issues

**"Virtual environment creation failed"**
```bash
python -m pip install --upgrade pip
python -m venv venv --clear
```

**"Google API dependencies failed"**
```bash
pip install --upgrade setuptools wheel
pip install -r requirements.txt --no-cache-dir
```

**"PyInstaller build fails"**
```bash
pip install --upgrade pyinstaller
# Try building without optimization:
pyinstaller --onefile src/google_photos_downloader.py
```

### GitHub Actions Issues

**"Workflow fails on credentials"**
- Ensure no actual credentials are committed to repository
- Check that credentials.json is in .gitignore

**"Build fails on specific platform"**
- Check the Actions logs for detailed error messages
- Platform-specific issues are logged separately

## 📁 Project Structure

```
google-photos-downloader/
├── 📂 .github/
│   ├── workflows/           # CI/CD automation
│   ├── ISSUE_TEMPLATE/      # Bug report templates
│   └── dependabot.yml       # Dependency updates
├── 📂 src/                  # Main source code
├── 📂 config/               # Configuration files
├── 📂 scripts/              # Build and utility scripts
├── 📂 tests/                # Unit tests
├── 📂 docs/                 # Documentation
├── 📂 assets/               # Icons and resources
├── 📋 requirements.txt      # Python dependencies
├── 📖 README.md            # Main documentation
├── 🤝 CONTRIBUTING.md      # Contribution guidelines
├── 📄 CHANGELOG.md         # Version history
├── 🔒 .gitignore          # Git ignore rules
├── 🎮 run_windows.bat      # Windows launcher
└── 🎮 run_unix.sh          # Unix launcher
```

## ✅ Verification

After setup, verify everything works:

1. **✅ Dependencies**: `pip list` shows all packages
2. **✅ Application**: Run and see GUI
3. **✅ Tests**: `python scripts/test.py` passes
4. **✅ Build**: `python scripts/build.py` creates executable
5. **✅ Git**: Repository initialized with workflows

---

**🎉 Your project is now ready for professional development and automated distribution!**
