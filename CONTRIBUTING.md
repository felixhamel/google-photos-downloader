# Contributing to Google Photos Downloader

Thank you for your interest in contributing! This document provides guidelines and information for contributors.

## 🚀 Quick Start for Contributors

### 1. Setup Development Environment
```bash
# Fork and clone your fork
git clone https://github.com/yourusername/google-photos-downloader.git
cd google-photos-downloader

# Run setup script
python setup_project.py

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows
```

### 2. Development Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit code ...

# Run tests and checks
python scripts/test.py

# Commit changes
git add .
git commit -m "feat: add amazing new feature"

# Push and create PR
git push origin feature/your-feature-name
```

## 📋 Development Guidelines

### Code Style
- **Formatting**: Use `black` for code formatting
- **Linting**: Follow `flake8` guidelines (max line length: 100)
- **Type Hints**: Add type hints for new functions
- **Docstrings**: Document all public functions and classes

### Testing
- **Unit Tests**: Add tests for new functionality
- **Integration Tests**: Test end-to-end workflows
- **Platform Testing**: Ensure changes work on all platforms
- **Manual Testing**: Test GUI interactions manually

### Commit Messages
Use conventional commit format:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `ci:` - CI/CD changes

## 🏗️ Architecture

### Project Structure
```
src/
├── google_photos_downloader.py  # Main application
├── version.py                   # Version information
└── utils/                       # Utility modules

tests/
├── test_downloader.py          # Core functionality tests
├── test_gui.py                 # GUI interaction tests
└── test_integration.py         # End-to-end tests

.github/
├── workflows/
│   ├── release.yml             # Build and release automation
│   └── test.yml               # Testing and quality checks
└── dependabot.yml             # Dependency updates
```

### Key Components
- **GooglePhotosDownloader**: Core API interaction class
- **GooglePhotosGUI**: GUI application class
- **DownloadStats**: Progress tracking and statistics
- **CI/CD Pipeline**: Automated testing and releases

## 🧪 Testing

### Running Tests Locally
```bash
# All tests and checks
python scripts/test.py

# Individual test types
pytest tests/ -v                # Unit tests
black --check src/ tests/       # Formatting
flake8 src/ tests/              # Linting
mypy src/                       # Type checking
```

### Testing on Multiple Platforms
The CI pipeline automatically tests on:
- **Windows**: Windows Server 2022
- **macOS**: macOS 12
- **Linux**: Ubuntu 22.04
- **Python Versions**: 3.9, 3.10, 3.11, 3.12

## 🚀 Release Process

### Automated Releases
1. **Create and push tag**:
   ```bash
   # Use helper script
   python scripts/release.py
   
   # Or manually
   git tag -a v1.2.0 -m "Release v1.2.0"
   git push origin v1.2.0
   ```

2. **GitHub Actions automatically**:
   - Builds executables for all platforms
   - Creates GitHub release
   - Uploads binaries as downloadable assets
   - Generates release notes

### Release Checklist
- [ ] All tests pass locally
- [ ] Version updated in `src/version.py`
- [ ] CHANGELOG.md updated
- [ ] Documentation updated if needed
- [ ] PR reviewed and merged to main
- [ ] Tag created and pushed

## 🤝 Contribution Types

### 🐛 Bug Fixes
- Fix existing issues
- Improve error handling
- Platform-specific fixes
- Performance optimizations

### ✨ New Features  
- GUI improvements
- New download options
- Additional file formats
- Integration features

### 📚 Documentation
- README improvements
- Setup guide enhancements
- Code documentation
- Troubleshooting guides

### 🔧 Infrastructure
- CI/CD improvements
- Build process enhancements
- Testing infrastructure
- Development tools

## 📞 Getting Help

- **Questions**: [GitHub Discussions](https://github.com/yourusername/google-photos-downloader/discussions)
- **Bugs**: [Create Issue](https://github.com/yourusername/google-photos-downloader/issues/new/choose)
- **Security**: Email security@yourproject.com (if applicable)

## 🎉 Recognition

Contributors are recognized in:
- GitHub contributors list
- Release notes for their contributions  
- Special thanks in major version releases

Thank you for contributing to Google Photos Downloader! 🙌
