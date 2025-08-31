#!/usr/bin/env python3
"""
Setup script for Google Photos Downloader
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read version from version.py
version = {}
with open("src/version.py") as fp:
    exec(fp.read(), version)

setup(
    name="google-photos-downloader",
    version=version['__version__'],
    author="Google Photos Downloader Team",
    author_email="your-email@example.com",
    description="Download photos from Google Photos with an intuitive GUI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/google-photos-downloader",
    packages=find_packages(),
    package_dir={'': 'src'},
    py_modules=['google_photos_downloader', 'version'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "google-auth>=2.17.0",
        "google-auth-oauthlib>=1.0.0",
        "google-auth-httplib2>=0.2.0",
        "google-api-python-client>=2.88.0",
        "requests>=2.31.0",
        "tkcalendar>=1.6.1",
        "pillow>=10.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pyinstaller>=6.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "google-photos-downloader=google_photos_downloader:main",
            "gphotos=google_photos_downloader:main",
        ],
        "gui_scripts": [
            "google-photos-gui=google_photos_downloader:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)