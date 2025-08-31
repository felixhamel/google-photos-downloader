"""
Google Photos Downloader Package

A cross-platform application to download photos from Google Photos within a specified date range.
"""

from .google_photos_downloader import (
    GooglePhotosDownloader,
    GooglePhotosGUI,
    DownloadStats,
    main
)
from .version import __version__, get_version, get_version_info

__all__ = [
    'GooglePhotosDownloader',
    'GooglePhotosGUI',
    'DownloadStats',
    'main',
    '__version__',
    'get_version',
    'get_version_info'
]