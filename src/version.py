"""Version information for Google Photos Downloader."""

__version__ = "1.0.0"
__author__ = "Google Photos Downloader Team"
__email__ = "your-email@example.com"
__description__ = "Download photos from Google Photos with an intuitive GUI"
__url__ = "https://github.com/yourusername/google-photos-downloader"

def get_version():
    """Return the current version string."""
    return __version__

def get_version_info():
    """Return detailed version information."""
    return {
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "url": __url__
    }
