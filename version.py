"""
ABOUTME: Version information for Google Photos Downloader
ABOUTME: Single source of truth for version across all components
"""

__version__ = "2.0.0"
__author__ = "Felix Hamel"
__email__ = ""
__description__ = "Google Photos Downloader with Web and CLI interfaces"

VERSION_INFO = {
    "version": __version__,
    "author": __author__,
    "description": __description__,
    "features": [
        "Web interface with French translation",
        "Command-line interface", 
        "Portable executable builds",
        "Real-time download progress",
        "Session management",
        "Multi-platform support"
    ]
}

def get_version_string():
    """Get formatted version string."""
    return f"Google Photos Downloader v{__version__}"

def get_full_version_info():
    """Get complete version information."""
    return VERSION_INFO