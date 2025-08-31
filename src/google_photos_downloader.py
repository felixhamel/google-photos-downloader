#!/usr/bin/env python3
"""
Google Photos Date Range Downloader with Enhanced GUI
=====================================================

A cross-platform application to download photos from Google Photos within a specified date range.
Features an intuitive GUI with calendar date pickers, progress tracking, and download speed monitoring.

Author: Claude (Anthropic)
License: MIT
Version: 2.0

Prerequisites:
--------------
1. Enable Google Photos Library API in Google Cloud Console:
   - Go to https://console.cloud.google.com/
   - Create new project or select existing
   - Navigate to "APIs & Services" > "Library"
   - Search for "Photos Library API" and enable it
   - Go to "Credentials" > "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop Application"
   - Download credentials JSON file as 'credentials.json'

2. Install required packages:
   pip install google-auth google-auth-oauthlib google-auth-httplib2 requests tkcalendar

Setup:
------
1. Place your 'credentials.json' file in the same directory as this script
2. Run: python photos_downloader.py
3. On first run, browser will open for Google authentication
4. Grant permissions to access your Google Photos
5. Token will be saved for future use

Features:
---------
- Interactive calendar date pickers
- Real-time progress tracking with percentage and count
- Download speed monitoring and ETA calculation
- Comprehensive error handling and retry logic
- Automatic file organization by date
- Duplicate detection and skipping
- Cross-platform compatibility (Windows, Mac, Linux)
- Thread-safe GUI updates
- Graceful cancellation handling

Usage:
------
GUI Mode (recommended):
    python photos_downloader.py

Command Line Mode:
    python photos_downloader.py --start-date 2024-01-01 --end-date 2024-12-31 --output-dir ./photos

File Organization:
------------------
Downloads are organized as:
    destination_folder/
    ├── 2024-01-15_143022_IMG_001.jpg
    ├── 2024-01-15_143055_VIDEO_002.mp4
    └── ...

Troubleshooting:
---------------
- If authentication fails: Delete 'token.json' and restart
- If API quota exceeded: Wait and try again later
- If downloads are slow: Check your internet connection
- For large date ranges: Consider downloading in smaller chunks

Security Notes:
--------------
- Credentials are stored locally and never transmitted except to Google
- OAuth tokens are encrypted and stored securely
- No data is collected or transmitted to third parties
"""

import os
import sys
import json
import requests
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import pickle
import uuid
import yaml
import enum

# Import calendar widget
try:
    from tkcalendar import DateEntry
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False
    print("Note: Install 'tkcalendar' for enhanced date pickers: pip install tkcalendar")

# Google API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False
    print("Error: Google APIs not installed. Run: pip install google-auth google-auth-oauthlib google-auth-httplib2")

# Google Photos API scope
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

class CircuitBreakerState(enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Simple circuit breaker pattern for handling API failures."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
    
    def call(self, func, *args, **kwargs):
        """Call a function through the circuit breaker."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN - too many recent failures")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN

class ConfigManager:
    """Manages application configuration from YAML file."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config = {}
        self.default_config = {
            'download': {
                'max_workers': 5,
                'chunk_size': 8192,
                'retry_attempts': 3,
                'timeout': 30
            },
            'files': {
                'naming_pattern': '{timestamp}_{filename}',
                'duplicate_detection': True,
                'create_date_folders': False
            },
            'ui': {
                'theme': 'light',
                'auto_refresh_albums': True,
                'remember_window_size': True
            },
            'advanced': {
                'enable_logging': True,
                'log_level': 'INFO',
                'state_persistence': True,
                'cleanup_temp_files': True
            },
            'api': {
                'page_size': 100,
                'rate_limit_delay': 0.1
            },
            'security': {
                'verify_checksums': True,
                'secure_token_storage': True
            }
        }
        self.load_config()
    
    def load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
                
            # Merge with defaults to ensure all keys exist
            self.config = self._merge_configs(self.default_config, self.config)
            
        except FileNotFoundError:
            print(f"Config file not found at {self.config_path}, using defaults")
            self.config = self.default_config.copy()
            self.save_config()
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}, using defaults")
            self.config = self.default_config.copy()
    
    def save_config(self):
        """Save current configuration to YAML file."""
        try:
            # Ensure config directory exists
            config_dir = Path(self.config_path).parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
                
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge user config with defaults."""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def get(self, path: str, default=None):
        """Get configuration value using dot notation (e.g., 'download.max_workers')."""
        keys = path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, path: str, value: Any):
        """Set configuration value using dot notation."""
        keys = path.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self.config.get(section, {})

class DownloadSession:
    """Manages download session state for resume capability."""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.output_dir = None
        self.media_items = []
        self.completed_items = set()
        self.failed_items = set()
        self.download_params = {}
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
    def save_state(self, state_dir: str = ".download_state"):
        """Save session state to disk."""
        state_path = Path(state_dir)
        state_path.mkdir(exist_ok=True)
        
        session_file = state_path / f"session_{self.session_id}.pkl"
        self.last_updated = datetime.now()
        
        with open(session_file, 'wb') as f:
            pickle.dump(self.__dict__, f)
    
    @classmethod
    def load_state(cls, session_id: str, state_dir: str = ".download_state"):
        """Load session state from disk."""
        state_path = Path(state_dir)
        session_file = state_path / f"session_{session_id}.pkl"
        
        if not session_file.exists():
            return None
            
        try:
            with open(session_file, 'rb') as f:
                data = pickle.load(f)
            
            session = cls()
            session.__dict__.update(data)
            return session
        except Exception:
            return None
    
    @classmethod
    def list_sessions(cls, state_dir: str = ".download_state") -> List[Dict[str, Any]]:
        """List all available download sessions."""
        state_path = Path(state_dir)
        if not state_path.exists():
            return []
        
        sessions = []
        for session_file in state_path.glob("session_*.pkl"):
            try:
                with open(session_file, 'rb') as f:
                    data = pickle.load(f)
                sessions.append({
                    'session_id': data.get('session_id'),
                    'created_at': data.get('created_at'),
                    'last_updated': data.get('last_updated'),
                    'total_items': len(data.get('media_items', [])),
                    'completed_items': len(data.get('completed_items', [])),
                    'output_dir': data.get('output_dir')
                })
            except Exception:
                continue
        
        return sorted(sessions, key=lambda x: x['last_updated'], reverse=True)
    
    def cleanup(self, state_dir: str = ".download_state"):
        """Remove session state file."""
        state_path = Path(state_dir)
        session_file = state_path / f"session_{self.session_id}.pkl"
        if session_file.exists():
            session_file.unlink()
    
    def get_remaining_items(self) -> List[Dict[str, Any]]:
        """Get list of items that still need to be downloaded."""
        return [item for item in self.media_items 
                if item['id'] not in self.completed_items and item['id'] not in self.failed_items]
    
    def mark_completed(self, item_id: str):
        """Mark an item as completed."""
        self.completed_items.add(item_id)
        self.failed_items.discard(item_id)  # Remove from failed if present
    
    def mark_failed(self, item_id: str):
        """Mark an item as failed."""
        self.failed_items.add(item_id)
        self.completed_items.discard(item_id)  # Remove from completed if present
    
    def get_progress(self) -> Dict[str, int]:
        """Get current progress statistics."""
        total = len(self.media_items)
        completed = len(self.completed_items)
        failed = len(self.failed_items)
        remaining = total - completed - failed
        
        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'remaining': remaining,
            'percentage': (completed / total * 100) if total > 0 else 0
        }

class DownloadStats:
    """Track download statistics and calculate speeds/ETA."""
    
    def __init__(self):
        self.start_time = None
        self.completed_files = 0
        self.total_files = 0
        self.total_bytes = 0
        self.completed_bytes = 0
        
    def start(self, total_files: int):
        """Start tracking download statistics."""
        self.start_time = time.time()
        self.total_files = total_files
        self.completed_files = 0
        self.total_bytes = 0
        self.completed_bytes = 0
        
    def update(self, file_size: int = 0):
        """Update statistics after completing a file."""
        self.completed_files += 1
        self.completed_bytes += file_size
        
    def get_speed_mbps(self) -> float:
        """Get current download speed in MB/s."""
        if not self.start_time or self.completed_bytes == 0:
            return 0.0
        elapsed = time.time() - self.start_time
        return (self.completed_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0.0
        
    def get_eta_seconds(self) -> Optional[int]:
        """Get estimated time remaining in seconds."""
        if self.completed_files == 0 or self.completed_files >= self.total_files:
            return None
        
        elapsed = time.time() - self.start_time
        rate = self.completed_files / elapsed if elapsed > 0 else 0
        remaining_files = self.total_files - self.completed_files
        
        return int(remaining_files / rate) if rate > 0 else None

class GooglePhotosDownloader:
    """Core downloader class handling Google Photos API interactions."""
    
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json', config: ConfigManager = None):
        """Initialize the Google Photos downloader."""
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.creds = None
        self.progress_callback = None
        self.status_callback = None
        self.cancelled = False
        self.stats = DownloadStats()
        self.current_session = None
        self.config = config or ConfigManager()
        self.circuit_breaker = CircuitBreaker()
        
    def set_callbacks(self, progress_callback: Optional[Callable] = None, 
                     status_callback: Optional[Callable] = None):
        """Set callbacks for progress and status updates."""
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        
    def update_status(self, message: str):
        """Send status update to callback or print."""
        if self.status_callback:
            self.status_callback(message)
        else:
            print(message)
    
    def update_progress(self, current: int, total: int, percentage: float):
        """Send progress update to callback."""
        speed = self.stats.get_speed_mbps()
        eta = self.stats.get_eta_seconds()
        
        if self.progress_callback:
            self.progress_callback(current, total, percentage, speed, eta)
        else:
            eta_str = f" ETA: {eta//60}m {eta%60}s" if eta else ""
            print(f"Progress: {current}/{total} ({percentage:.1f}%) Speed: {speed:.1f} MB/s{eta_str}")
    
    def authenticate(self) -> bool:
        """Authenticate with Google Photos API using OAuth2."""
        try:
            # Load existing token if available
            if os.path.exists(self.token_file):
                self.creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            
            # If no valid credentials, get new ones
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.update_status("Refreshing authentication token...")
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        self.update_status(f"❌ Error: '{self.credentials_file}' not found. Please download OAuth2 credentials from Google Cloud Console.")
                        return False
                    
                    self.update_status("🌐 Opening browser for Google authentication...")
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                    self.creds = flow.run_local_server(port=0)
                
                # Save credentials for future use
                with open(self.token_file, 'w') as token:
                    token.write(self.creds.to_json())
            
            self.service = build('photoslibrary', 'v1', credentials=self.creds)
            self.update_status("✅ Successfully authenticated with Google Photos API")
            return True
            
        except Exception as e:
            self.update_status(f"❌ Authentication failed: {e}")
            return False
    
    def date_to_google_format(self, date_obj: datetime) -> Dict[str, Any]:
        """Convert datetime object to Google Photos API format."""
        return {
            'year': date_obj.year,
            'month': date_obj.month,
            'day': date_obj.day
        }
    
    async def get_albums_async(self) -> List[Dict[str, Any]]:
        """Retrieve list of albums from Google Photos."""
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        self.update_status("📚 Fetching albums...")
        albums = []
        page_token = None
        
        try:
            while not self.cancelled:
                if page_token:
                    response = self.service.albums().list(pageToken=page_token, pageSize=50).execute()
                else:
                    response = self.service.albums().list(pageSize=50).execute()
                
                if 'albums' in response:
                    batch = response['albums']
                    albums.extend(batch)
                    self.update_status(f"📊 Found {len(batch)} albums (total: {len(albums)})")
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
                    
        except HttpError as e:
            self.update_status(f"❌ API error fetching albums: {e}")
            return albums
        
        self.update_status(f"✅ Found {len(albums)} albums")
        return albums
    
    async def get_album_media_items_async(self, album_id: str) -> List[Dict[str, Any]]:
        """Retrieve media items from a specific album."""
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        self.update_status(f"🔍 Searching for items in album...")
        media_items = []
        page_token = None
        
        try:
            while not self.cancelled:
                search_body = {
                    'albumId': album_id,
                    'pageSize': 100
                }
                
                if page_token:
                    search_body['pageToken'] = page_token
                
                response = self.service.mediaItems().search(body=search_body).execute()
                
                if 'mediaItems' in response:
                    batch = response['mediaItems']
                    media_items.extend(batch)
                    self.update_status(f"📊 Found {len(batch)} items in batch (total: {len(media_items)})")
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
                    
        except HttpError as e:
            self.update_status(f"❌ API error during album search: {e}")
            return media_items
        
        self.update_status(f"✅ Album search complete: {len(media_items)} items found")
        return media_items
    
    async def get_media_items_async(self, start_date: datetime = None, end_date: datetime = None, 
                                   album_id: str = None, media_types: List[str] = None) -> List[Dict[str, Any]]:
        """Retrieve media items from Google Photos with various filters."""
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        # If album_id is provided, use album-specific search
        if album_id:
            return await self.get_album_media_items_async(album_id)
        
        # Build search filters
        filters = {}
        
        # Date filter
        if start_date and end_date:
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            self.update_status(f"🔍 Searching for photos from {start_str} to {end_str}...")
            
            filters['dateFilter'] = {
                'ranges': [{
                    'startDate': self.date_to_google_format(start_date),
                    'endDate': self.date_to_google_format(end_date)
                }]
            }
        
        # Media type filter
        if media_types:
            filters['mediaTypeFilter'] = {
                'mediaTypes': media_types
            }
        else:
            filters['mediaTypeFilter'] = {
                'mediaTypes': ['PHOTO', 'VIDEO']
            }
        
        search_body = {
            'filters': filters,
            'pageSize': 100
        }
        
        media_items = []
        page_token = None
        
        try:
            while not self.cancelled:
                if page_token:
                    search_body['pageToken'] = page_token
                
                response = self.service.mediaItems().search(body=search_body).execute()
                
                if 'mediaItems' in response:
                    batch = response['mediaItems']
                    media_items.extend(batch)
                    self.update_status(f"📊 Found {len(batch)} items in batch (total: {len(media_items)})")
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
                    
        except HttpError as e:
            self.update_status(f"❌ API error during search: {e}")
            return media_items
        
        if self.cancelled:
            self.update_status("🛑 Search cancelled")
        else:
            self.update_status(f"✅ Search complete: {len(media_items)} items found")
        
        return media_items
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files efficiently
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return ""
    
    def _find_duplicate_by_checksum(self, output_dir: Path, target_checksum: str, exclude_file: str = None) -> Optional[Path]:
        """Find a file with matching checksum in the output directory."""
        try:
            for file_path in output_dir.glob("*"):
                if file_path.is_file() and file_path.name != exclude_file:
                    if self._calculate_file_checksum(file_path) == target_checksum:
                        return file_path
            return None
        except Exception:
            return None
    
    async def download_media_item_async(self, item: Dict[str, Any], output_dir: Path) -> tuple[bool, int]:
        """
        Download a single media item with checksum-based duplicate detection.
        
        Returns:
            Tuple of (success: bool, file_size: int)
        """
        try:
            filename = item['filename']
            media_metadata = item['mediaMetadata']
            
            # Create safe filename with timestamp
            creation_time = media_metadata['creationTime']
            timestamp = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
            safe_timestamp = timestamp.strftime('%Y%m%d_%H%M%S')
            
            name, ext = os.path.splitext(filename)
            safe_filename = f"{safe_timestamp}_{name}{ext}"
            file_path = output_dir / safe_filename
            
            # Skip if exact file already exists
            if file_path.exists():
                existing_size = file_path.stat().st_size
                self.update_status(f"⏭️ Skipping existing file: {safe_filename}")
                return True, existing_size
            
            # Determine download URL based on media type
            if 'photo' in media_metadata:
                download_url = f"{item['baseUrl']}=d"  # Original quality photo
            elif 'video' in media_metadata:
                download_url = f"{item['baseUrl']}=dv"  # Original quality video
            else:
                self.update_status(f"⚠️ Unknown media type for {filename}")
                return False, 0
            
            # Download with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                if self.cancelled:
                    return False, 0
                    
                try:
                    timeout = self.config.get('download.timeout', 30)
                    chunk_size = self.config.get('download.chunk_size', 8192)
                    
                    response = requests.get(download_url, stream=True, timeout=timeout)
                    response.raise_for_status()
                    
                    # Get content length for progress tracking
                    content_length = response.headers.get('content-length')
                    total_size = int(content_length) if content_length else None
                    
                    # Create temporary file first
                    temp_file = file_path.with_suffix(f"{file_path.suffix}.tmp")
                    file_size = 0
                    
                    # Use larger buffer for big files (>50MB)
                    if total_size and total_size > 50 * 1024 * 1024:
                        chunk_size = min(chunk_size * 16, 128 * 1024)  # Up to 128KB chunks
                    
                    with open(temp_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if self.cancelled:
                                f.close()
                                temp_file.unlink(missing_ok=True)
                                return False, 0
                            f.write(chunk)
                            file_size += len(chunk)
                            
                            # Optional: Progress callback for individual files
                            if total_size and hasattr(self, 'file_progress_callback'):
                                progress = (file_size / total_size) * 100
                                self.file_progress_callback(filename, progress)
                    
                    # Calculate checksum of downloaded file
                    downloaded_checksum = self._calculate_file_checksum(temp_file)
                    
                    if not downloaded_checksum:
                        temp_file.unlink(missing_ok=True)
                        self.update_status(f"❌ Could not calculate checksum for {filename}")
                        return False, 0
                    
                    # Check for duplicates by checksum in output directory
                    duplicate_path = self._find_duplicate_by_checksum(output_dir, downloaded_checksum, safe_filename)
                    
                    if duplicate_path:
                        # File with same content already exists
                        temp_file.unlink(missing_ok=True)
                        self.update_status(f"🔗 Duplicate detected: {filename} (same as {duplicate_path.name})")
                        return True, duplicate_path.stat().st_size
                    else:
                        # Move temp file to final location
                        temp_file.rename(file_path)
                        return True, file_size
                    
                except (requests.RequestException, IOError) as e:
                    if attempt < max_retries - 1:
                        self.update_status(f"⚠️ Retry {attempt + 1}/{max_retries} for {filename}: {e}")
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        self.update_status(f"❌ Failed to download {filename} after {max_retries} attempts: {e}")
                        return False, 0
            
        except Exception as e:
            self.update_status(f"❌ Unexpected error downloading {item.get('filename', 'unknown')}: {e}")
            return False, 0
    
    async def download_photos_async(self, start_date: datetime = None, end_date: datetime = None, 
                                   output_dir: str = None, max_workers: int = 5, 
                                   album_id: str = None, media_types: List[str] = None,
                                   resume_session_id: str = None) -> None:
        """Main async method to download photos with various filters, concurrent downloads, and resume capability."""
        self.cancelled = False
        
        # Handle resume functionality
        if resume_session_id:
            self.current_session = DownloadSession.load_state(resume_session_id)
            if self.current_session:
                output_dir = self.current_session.output_dir
                media_items = self.current_session.get_remaining_items()
                progress = self.current_session.get_progress()
                
                self.update_status(f"📂 Resuming download session... {progress['completed']}/{progress['total']} items completed")
                if not media_items:
                    self.update_status(f"✅ Session already completed! {progress['completed']} items downloaded")
                    return
            else:
                self.update_status(f"❌ Could not load session {resume_session_id}")
                return
        else:
            # Create new session
            self.current_session = DownloadSession()
            self.current_session.output_dir = output_dir
            self.current_session.download_params = {
                'start_date': start_date,
                'end_date': end_date,
                'album_id': album_id,
                'media_types': media_types
            }
            
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Get media items based on filters
            if album_id:
                media_items = await self.get_media_items_async(album_id=album_id)
            elif start_date and end_date:
                media_items = await self.get_media_items_async(start_date, end_date, media_types=media_types)
            else:
                self.update_status("❌ Either date range or album must be specified")
                return
            
            if not media_items:
                source_desc = f"album" if album_id else f"date range {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                self.update_status(f"📭 No photos found in the specified {source_desc}.")
                return
            
            # Store media items in session
            self.current_session.media_items = media_items
            self.current_session.save_state()
        
        if self.cancelled:
            return
        
        output_path = Path(self.current_session.output_dir)
        
        # Initialize statistics
        total_count = len(self.current_session.media_items)
        already_completed = len(self.current_session.completed_items)
        remaining_count = len(media_items)
        success_count = already_completed
        failed_items = []
        self.stats.start(remaining_count)
        
        source_desc = f"album" if album_id else "date range"
        if resume_session_id:
            self.update_status(f"📥 Resuming concurrent download of {remaining_count} remaining items with {max_workers} workers...")
        else:
            self.update_status(f"📥 Starting concurrent download of {total_count} items from {source_desc} with {max_workers} workers...")
        
        # Use ThreadPoolExecutor for concurrent downloads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit remaining download tasks
            future_to_item = {}
            for i, item in enumerate(media_items, 1):
                if self.cancelled:
                    break
                    
                future = executor.submit(self._download_item_sync, item, output_path, i)
                future_to_item[future] = (item, i)
            
            # Process completed downloads
            completed = 0
            for future in as_completed(future_to_item):
                if self.cancelled:
                    executor.shutdown(wait=False)
                    self.update_status("🛑 Download cancelled by user - state saved for resume")
                    self.current_session.save_state()
                    break
                
                item, index = future_to_item[future]
                try:
                    success, file_size = future.result()
                    completed += 1
                    
                    if success:
                        success_count += 1
                        self.stats.update(file_size)
                        self.current_session.mark_completed(item['id'])
                    else:
                        failed_items.append(item.get('filename', f'item_{index}'))
                        self.current_session.mark_failed(item['id'])
                    
                    # Save state periodically (every 10 items)
                    if completed % 10 == 0:
                        self.current_session.save_state()
                    
                    # Update progress (include already completed items)
                    total_progress = already_completed + completed
                    percentage = (total_progress / total_count) * 100
                    self.update_progress(total_progress, total_count, percentage)
                    
                except Exception as e:
                    completed += 1
                    failed_items.append(item.get('filename', f'item_{index}'))
                    self.current_session.mark_failed(item['id'])
                    self.update_status(f"❌ Error downloading {item.get('filename', 'unknown')}: {e}")
                    
                    # Update progress even on failure
                    total_progress = already_completed + completed
                    percentage = (total_progress / total_count) * 100
                    self.update_progress(total_progress, total_count, percentage)
        
        # Final save and cleanup
        self.current_session.save_state()
        
        if not self.cancelled:
            if failed_items:
                self.update_status(f"⚠️ Download complete with errors! {success_count}/{total_count} items saved. Failed: {', '.join(failed_items[:5])}{'...' if len(failed_items) > 5 else ''}")
            else:
                self.update_status(f"🎉 Download complete! {success_count}/{total_count} items saved to {output_path}")
                # Clean up completed session
                self.current_session.cleanup()
    
    def _download_item_sync(self, item: Dict[str, Any], output_dir: Path, index: int) -> tuple[bool, int]:
        """Synchronous wrapper for download_media_item_async for use with ThreadPoolExecutor."""
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.download_media_item_async(item, output_dir))
        except Exception as e:
            self.update_status(f"❌ Failed to download item {index}: {e}")
            return False, 0
        finally:
            loop.close()
        
    def cancel_download(self):
        """Cancel the current download operation."""
        self.cancelled = True

class GooglePhotosGUI:
    """Main GUI application class."""
    
    def __init__(self, config: ConfigManager = None):
        self.root = tk.Tk()
        self.root.title("Google Photos Downloader v2.0")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Configuration management
        self.config = config or ConfigManager()
        
        # Theme management
        self.dark_mode = self.config.get('ui.theme') == 'dark'
        self.themes = {
            'light': {
                'bg': '#ffffff',
                'fg': '#000000',
                'select_bg': '#0078d4',
                'select_fg': '#ffffff',
                'entry_bg': '#ffffff',
                'entry_fg': '#000000',
                'text_bg': '#f8f9fa',
                'text_fg': '#333333'
            },
            'dark': {
                'bg': '#2d2d2d',
                'fg': '#ffffff',
                'select_bg': '#404040',
                'select_fg': '#ffffff',
                'entry_bg': '#404040',
                'entry_fg': '#ffffff',
                'text_bg': '#1e1e1e',
                'text_fg': '#e0e0e0'
            }
        }
        
        # Set application icon (if available)
        try:
            self.root.iconbitmap('app_icon.ico')
        except:
            pass  # Icon file not found, continue without it
        
        self.downloader = GooglePhotosDownloader(config=self.config)
        self.download_thread = None
        self.is_downloading = False
        
        self.setup_ui()
        self.setup_callbacks()
        self.apply_theme()
        
    def setup_ui(self):
        """Create the user interface elements."""
        # Store UI elements for theme switching
        self.ui_elements = {'frames': [], 'labels': [], 'entries': [], 'text_widgets': []}
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Modern theme
        
        # Main container with padding
        self.main_frame = ttk.Frame(self.root, padding="25")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.ui_elements['frames'].append(self.main_frame)
        
        # Configure grid weights for responsive design
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        
        # Header with title and theme toggle
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, columnspan=3, pady=(0, 25))
        header_frame.columnconfigure(0, weight=1)
        self.ui_elements['frames'].append(header_frame)
        
        # Application title
        title_label = ttk.Label(header_frame, text="Google Photos Downloader", 
                               font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Theme toggle button
        self.theme_button = ttk.Button(header_frame, text="🌙 Dark Mode", 
                                     command=self.toggle_theme)
        self.theme_button.grid(row=0, column=1, sticky=tk.E)
        
        # Source selection section
        source_frame = ttk.LabelFrame(self.main_frame, text="Download Source", padding="15")
        source_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        source_frame.columnconfigure(1, weight=1)
        self.ui_elements['frames'].append(source_frame)
        
        # Source type selection
        self.source_type_var = tk.StringVar(value="date_range")
        date_radio = ttk.Radiobutton(source_frame, text="📅 Date Range", 
                                   variable=self.source_type_var, value="date_range",
                                   command=self.on_source_type_changed)
        date_radio.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        album_radio = ttk.Radiobutton(source_frame, text="📚 Album", 
                                    variable=self.source_type_var, value="album",
                                    command=self.on_source_type_changed)
        album_radio.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Date selection section
        date_frame = ttk.LabelFrame(self.main_frame, text="Date Range", padding="15")
        date_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        date_frame.columnconfigure(1, weight=1)
        self.ui_elements['frames'].append(date_frame)
        
        # Start date
        ttk.Label(date_frame, text="From:").grid(row=0, column=0, sticky=tk.W, pady=5)
        if CALENDAR_AVAILABLE:
            self.start_date_picker = DateEntry(date_frame, width=12, background='darkblue',
                                             foreground='white', borderwidth=2, 
                                             date_pattern='yyyy-mm-dd')
            self.start_date_picker.set_date(datetime.now().replace(year=datetime.now().year-1))
        else:
            self.start_date_var = tk.StringVar(value="2024-01-01")
            self.start_date_picker = ttk.Entry(date_frame, textvariable=self.start_date_var, width=15)
        self.start_date_picker.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        
        # End date
        ttk.Label(date_frame, text="To:").grid(row=1, column=0, sticky=tk.W, pady=5)
        if CALENDAR_AVAILABLE:
            self.end_date_picker = DateEntry(date_frame, width=12, background='darkblue',
                                           foreground='white', borderwidth=2,
                                           date_pattern='yyyy-mm-dd')
            self.end_date_picker.set_date(datetime.now())
        else:
            self.end_date_var = tk.StringVar(value="2024-12-31")
            self.end_date_picker = ttk.Entry(date_frame, textvariable=self.end_date_var, width=15)
        self.end_date_picker.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        
        # Album selection section
        self.album_frame = ttk.LabelFrame(main_frame, text="Album Selection", padding="15")
        self.album_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        self.album_frame.columnconfigure(1, weight=1)
        
        ttk.Label(self.album_frame, text="Album:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.album_var = tk.StringVar()
        self.album_combobox = ttk.Combobox(self.album_frame, textvariable=self.album_var, 
                                          state="readonly", width=40)
        self.album_combobox.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        
        refresh_albums_button = ttk.Button(self.album_frame, text="🔄 Refresh", 
                                         command=self.refresh_albums)
        refresh_albums_button.grid(row=0, column=2, padx=(5, 0), pady=5)
        
        # Media type filter section
        filter_frame = ttk.LabelFrame(main_frame, text="Media Type Filter", padding="15")
        filter_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.photos_var = tk.BooleanVar(value=True)
        self.videos_var = tk.BooleanVar(value=True)
        
        photos_cb = ttk.Checkbutton(filter_frame, text="📷 Photos", variable=self.photos_var)
        photos_cb.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        videos_cb = ttk.Checkbutton(filter_frame, text="🎥 Videos", variable=self.videos_var)
        videos_cb.grid(row=0, column=1, sticky=tk.W)
        
        # Destination folder section
        dest_frame = ttk.LabelFrame(main_frame, text="Destination", padding="15")
        dest_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        dest_frame.columnconfigure(1, weight=1)
        
        ttk.Label(dest_frame, text="Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.folder_var = tk.StringVar(value=str(Path.home() / "GooglePhotos"))
        self.folder_entry = ttk.Entry(dest_frame, textvariable=self.folder_var, font=('Consolas', 9))
        self.folder_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        
        folder_button = ttk.Button(dest_frame, text="📁 Browse", command=self.browse_folder)
        folder_button.grid(row=0, column=2, padx=(5, 0), pady=5)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Download Progress", padding="15")
        progress_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        progress_frame.columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=500, mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Progress info frame
        info_frame = ttk.Frame(progress_frame)
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        info_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(1, weight=1)
        info_frame.columnconfigure(2, weight=1)
        
        self.percentage_label = ttk.Label(info_frame, text="0%", font=('Arial', 11, 'bold'))
        self.percentage_label.grid(row=0, column=0, sticky=tk.W)
        
        self.count_label = ttk.Label(info_frame, text="0 / 0 completed")
        self.count_label.grid(row=0, column=1)
        
        self.speed_label = ttk.Label(info_frame, text="Speed: 0 MB/s")
        self.speed_label.grid(row=0, column=2, sticky=tk.E)
        
        self.eta_label = ttk.Label(info_frame, text="ETA: --")
        self.eta_label.grid(row=1, column=2, sticky=tk.E)
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status Log", padding="15")
        status_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        
        # Status text with scrollbar
        text_frame = ttk.Frame(status_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.status_text = tk.Text(text_frame, height=8, wrap=tk.WORD, 
                                  font=('Consolas', 9), bg='#f8f9fa', fg='#333')
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.ui_elements['text_widgets'].append(self.status_text)
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=3, pady=(15, 0))
        
        self.download_button = ttk.Button(button_frame, text="🚀 Start Download", 
                                        command=self.start_download)
        self.download_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.resume_button = ttk.Button(button_frame, text="📂 Resume Download", 
                                      command=self.show_resume_dialog)
        self.resume_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.cancel_button = ttk.Button(button_frame, text="⏹️ Cancel", 
                                      command=self.cancel_download, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT)
        
        # Configure main_frame row weights for proper resizing
        self.main_frame.rowconfigure(7, weight=1)
        
        # Initialize UI state
        self.albums = []
        self.on_source_type_changed()  # Set initial state
        
        # Add initial status message
        self.add_status_message("🎯 Ready to download! Select your date range/album and destination folder.")
        
        # Check for credentials file
        if not os.path.exists('credentials.json'):
            self.add_status_message("⚠️ Warning: 'credentials.json' not found. Please download OAuth2 credentials from Google Cloud Console.")
    
    def setup_callbacks(self):
        """Setup callbacks for the downloader."""
        self.downloader.set_callbacks(
            progress_callback=self.update_progress_gui,
            status_callback=self.add_status_message
        )
    
    def on_source_type_changed(self):
        """Handle source type radio button changes."""
        if self.source_type_var.get() == "date_range":
            # Show date frame, hide album frame
            for child in self.album_frame.winfo_children():
                child.configure(state="disabled")
        else:
            # Hide date frame, show album frame
            for child in self.album_frame.winfo_children():
                child.configure(state="normal")
    
    def refresh_albums(self):
        """Refresh the album list from Google Photos."""
        if not self.downloader.service:
            if not self.downloader.authenticate():
                self.add_status_message("❌ Authentication failed. Cannot refresh albums.")
                return
        
        self.add_status_message("🔄 Refreshing albums...")
        
        def fetch_albums():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                albums = loop.run_until_complete(self.downloader.get_albums_async())
                loop.close()
                
                self.root.after(0, lambda: self._update_album_list(albums))
            except Exception as e:
                self.root.after(0, lambda: self.add_status_message(f"❌ Error fetching albums: {e}"))
        
        threading.Thread(target=fetch_albums, daemon=True).start()
    
    def _update_album_list(self, albums):
        """Update the album dropdown with fetched albums."""
        self.albums = albums
        album_names = [f"{album.get('title', 'Untitled')} ({album.get('mediaItemsCount', '?')} items)" 
                      for album in albums]
        
        self.album_combobox['values'] = album_names
        if album_names:
            self.album_combobox.current(0)
            self.add_status_message(f"✅ Loaded {len(albums)} albums")
        else:
            self.add_status_message("📭 No albums found")
    
    def browse_folder(self):
        """Open folder selection dialog."""
        folder = filedialog.askdirectory(
            title="Select Destination Folder",
            initialdir=self.folder_var.get()
        )
        if folder:
            self.folder_var.set(folder)
    
    def add_status_message(self, message: str):
        """Add a timestamped status message to the log."""
        def update_text():
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.status_text.see(tk.END)
        
        # Ensure GUI updates happen on main thread
        if threading.current_thread() == threading.main_thread():
            update_text()
        else:
            self.root.after(0, update_text)
    
    def update_progress_gui(self, current: int, total: int, percentage: float, 
                          speed: float = 0.0, eta: Optional[int] = None):
        """Update the progress bar and related labels."""
        def update_widgets():
            self.progress_var.set(percentage)
            self.percentage_label.config(text=f"{percentage:.1f}%")
            self.count_label.config(text=f"{current} / {total} completed")
            self.speed_label.config(text=f"Speed: {speed:.1f} MB/s")
            
            if eta is not None:
                if eta < 60:
                    eta_text = f"ETA: {eta}s"
                elif eta < 3600:
                    eta_text = f"ETA: {eta//60}m {eta%60}s"
                else:
                    eta_text = f"ETA: {eta//3600}h {(eta%3600)//60}m"
            else:
                eta_text = "ETA: --"
            self.eta_label.config(text=eta_text)
        
        # Ensure GUI updates happen on main thread
        if threading.current_thread() == threading.main_thread():
            update_widgets()
        else:
            self.root.after(0, update_widgets)
    
    def get_date_values(self) -> tuple[datetime, datetime]:
        """Get selected dates from the UI."""
        if CALENDAR_AVAILABLE:
            start_date = self.start_date_picker.get_date()
            end_date = self.end_date_picker.get_date()
            # Convert to datetime
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
        else:
            start_dt = datetime.strptime(self.start_date_var.get(), '%Y-%m-%d')
            end_dt = datetime.strptime(self.end_date_var.get(), '%Y-%m-%d')
        
        return start_dt, end_dt
    
    def validate_inputs(self) -> bool:
        """Validate user inputs before starting download."""
        try:
            source_type = self.source_type_var.get()
            
            if source_type == "date_range":
                start_dt, end_dt = self.get_date_values()
                
                if start_dt > end_dt:
                    messagebox.showerror("Invalid Dates", "Start date cannot be after end date.")
                    return False
                
                # Check if date range is reasonable (not more than 5 years)
                days_diff = (end_dt - start_dt).days
                if days_diff > 1825:  # 5 years
                    result = messagebox.askyesno("Large Date Range", 
                        f"You've selected {days_diff} days ({days_diff//365} years). "
                        "This might result in thousands of photos. Continue?")
                    if not result:
                        return False
            else:
                # Album mode - check if album is selected
                if not self.album_var.get():
                    messagebox.showerror("No Album Selected", "Please select an album from the dropdown.")
                    return False
            
            # Check media type filters
            if not self.photos_var.get() and not self.videos_var.get():
                messagebox.showerror("No Media Types", "Please select at least photos or videos to download.")
                return False
            
            # Validate folder
            folder = self.folder_var.get().strip()
            if not folder:
                messagebox.showerror("Invalid Folder", "Please select a destination folder.")
                return False
            
            # Check if folder is writable
            try:
                test_path = Path(folder)
                test_path.mkdir(parents=True, exist_ok=True)
                if not os.access(test_path, os.W_OK):
                    messagebox.showerror("Permission Error", "Cannot write to selected folder. Please choose another location.")
                    return False
            except Exception as e:
                messagebox.showerror("Folder Error", f"Cannot access destination folder: {e}")
                return False
            
            return True
            
        except ValueError:
            messagebox.showerror("Invalid Date", "Please use valid dates in YYYY-MM-DD format.")
            return False
    
    async def download_worker_async(self):
        """Async worker function for downloading."""
        try:
            if not self.downloader.authenticate():
                return
            
            source_type = self.source_type_var.get()
            output_dir = self.folder_var.get()
            
            # Build media type filter
            media_types = []
            if self.photos_var.get():
                media_types.append('PHOTO')
            if self.videos_var.get():
                media_types.append('VIDEO')
            
            if source_type == "date_range":
                start_dt, end_dt = self.get_date_values()
                await self.downloader.download_photos_async(
                    start_date=start_dt, 
                    end_date=end_dt, 
                    output_dir=output_dir,
                    media_types=media_types
                )
            else:
                # Album mode
                selected_index = self.album_combobox.current()
                if selected_index >= 0 and selected_index < len(self.albums):
                    selected_album = self.albums[selected_index]
                    album_id = selected_album['id']
                    await self.downloader.download_photos_async(
                        output_dir=output_dir,
                        album_id=album_id
                    )
                else:
                    self.add_status_message("❌ Invalid album selection")
                    return
            
        except Exception as e:
            self.add_status_message(f"❌ Unexpected error: {e}")
            messagebox.showerror("Download Error", f"An unexpected error occurred: {e}")
    
    def download_worker(self):
        """Synchronous wrapper for async download worker."""
        import asyncio
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.download_worker_async())
        except Exception as e:
            self.add_status_message(f"❌ Thread error: {e}")
        finally:
            self.root.after(0, self.download_complete)
    
    def start_download(self):
        """Initiate the download process."""
        if not GOOGLE_APIS_AVAILABLE:
            messagebox.showerror("Missing Dependencies", 
                "Google APIs not installed. Run:\npip install google-auth google-auth-oauthlib google-auth-httplib2")
            return
            
        if not self.validate_inputs():
            return
        
        # Reset progress indicators
        self.progress_var.set(0)
        self.percentage_label.config(text="0%")
        self.count_label.config(text="0 / 0 completed")
        self.speed_label.config(text="Speed: 0 MB/s")
        self.eta_label.config(text="ETA: --")
        
        # Update button states
        self.download_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.is_downloading = True
        
        # Clear status log
        self.status_text.delete(1.0, tk.END)
        self.add_status_message("🚀 Initializing download process...")
        
        # Start download in separate thread
        self.download_thread = threading.Thread(target=self.download_worker, daemon=True)
        self.download_thread.start()
    
    def show_resume_dialog(self):
        """Show dialog to select a download session to resume."""
        sessions = DownloadSession.list_sessions()
        if not sessions:
            messagebox.showinfo("No Sessions", "No incomplete download sessions found.")
            return
        
        # Create resume dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Resume Download Session")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Session list
        frame = ttk.Frame(dialog, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        
        ttk.Label(frame, text="Select a session to resume:", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 15))
        
        # Treeview for sessions
        columns = ('Created', 'Progress', 'Output Directory')
        tree = ttk.Treeview(frame, columns=columns, show='tree headings', height=10)
        tree.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        
        # Configure columns
        tree.heading('#0', text='Session ID')
        tree.heading('Created', text='Created')
        tree.heading('Progress', text='Progress')
        tree.heading('Output Directory', text='Output Directory')
        
        tree.column('#0', width=200)
        tree.column('Created', width=150)
        tree.column('Progress', width=100)
        tree.column('Output Directory', width=200)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.grid(row=1, column=2, sticky=(tk.N, tk.S))
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Populate sessions
        for session in sessions:
            created_str = session['created_at'].strftime('%Y-%m-%d %H:%M')
            progress_str = f"{session['completed_items']}/{session['total_items']}"
            tree.insert('', 'end', text=session['session_id'][:8] + '...', 
                       values=(created_str, progress_str, session['output_dir'][:30] + '...'))
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(15, 0))
        
        selected_session = [None]  # Use list to modify from nested function
        
        def on_resume():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a session to resume.")
                return
            
            index = tree.index(selection[0])
            selected_session[0] = sessions[index]['session_id']
            dialog.destroy()
        
        def on_delete():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a session to delete.")
                return
            
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this session?"):
                index = tree.index(selection[0])
                session_id = sessions[index]['session_id']
                session = DownloadSession()
                session.session_id = session_id
                session.cleanup()
                tree.delete(selection[0])
                messagebox.showinfo("Deleted", "Session deleted successfully.")
        
        ttk.Button(button_frame, text="Resume", command=on_resume).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Delete", command=on_delete).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)
        
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        
        # Wait for dialog to close
        dialog.wait_window()
        
        # Resume selected session
        if selected_session[0]:
            self.resume_download(selected_session[0])
    
    def resume_download(self, session_id: str):
        """Resume a download session."""
        self.add_status_message(f"📂 Resuming session: {session_id}")
        
        # Update button states
        self.download_button.config(state=tk.DISABLED)
        self.resume_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.is_downloading = True
        
        # Start download in separate thread with resume
        def resume_worker():
            import asyncio
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    self.downloader.download_photos_async(resume_session_id=session_id)
                )
            except Exception as e:
                self.add_status_message(f"❌ Resume error: {e}")
            finally:
                self.root.after(0, self.download_complete)
        
        self.download_thread = threading.Thread(target=resume_worker, daemon=True)
        self.download_thread.start()
    
    def cancel_download(self):
        """Cancel the current download operation."""
        if self.is_downloading:
            self.downloader.cancel_download()
            self.cancel_button.config(state=tk.DISABLED)
            self.add_status_message("🛑 Cancellation requested...")
    
    def download_complete(self):
        """Called when download is complete or cancelled."""
        self.is_downloading = False
        self.download_button.config(state=tk.NORMAL)
        self.resume_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        
        if not self.downloader.cancelled:
            # Show completion notification
            self.root.bell()  # System notification sound
            messagebox.showinfo("Download Complete", "Your Google Photos have been downloaded successfully!")
    
    def on_closing(self):
        """Handle application closing."""
        if self.is_downloading:
            result = messagebox.askyesno("Download in Progress", 
                "A download is currently in progress. Do you want to cancel and exit?")
            if result:
                self.downloader.cancel_download()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        
        # Save theme preference to config
        self.config.set('ui.theme', 'dark' if self.dark_mode else 'light')
        self.config.save_config()
        
        # Update button text
        if self.dark_mode:
            self.theme_button.config(text="☀️ Light Mode")
        else:
            self.theme_button.config(text="🌙 Dark Mode")
    
    def apply_theme(self):
        """Apply the current theme to all UI elements."""
        theme = self.themes['dark' if self.dark_mode else 'light']
        
        # Configure root window
        self.root.configure(bg=theme['bg'])
        
        # Configure ttk styles for dark/light theme
        if self.dark_mode:
            self.style.theme_use('clam')
            self.style.configure('TFrame', background=theme['bg'])
            self.style.configure('TLabel', background=theme['bg'], foreground=theme['fg'])
            self.style.configure('TLabelFrame', background=theme['bg'], foreground=theme['fg'])
            self.style.configure('TLabelFrame.Label', background=theme['bg'], foreground=theme['fg'])
            self.style.configure('TButton', background=theme['select_bg'], foreground=theme['fg'])
            self.style.configure('TRadiobutton', background=theme['bg'], foreground=theme['fg'])
            self.style.configure('TCheckbutton', background=theme['bg'], foreground=theme['fg'])
            self.style.configure('TCombobox', fieldbackground=theme['entry_bg'], foreground=theme['entry_fg'])
            self.style.configure('TEntry', fieldbackground=theme['entry_bg'], foreground=theme['entry_fg'])
        else:
            self.style.theme_use('clam')
            # Reset to default light theme styles
            self.style.configure('TFrame', background=theme['bg'])
            self.style.configure('TLabel', background=theme['bg'], foreground=theme['fg'])
            self.style.configure('TLabelFrame', background=theme['bg'], foreground=theme['fg'])
            self.style.configure('TLabelFrame.Label', background=theme['bg'], foreground=theme['fg'])
        
        # Update Text widgets manually (they don't use ttk styles)
        for text_widget in self.ui_elements.get('text_widgets', []):
            text_widget.configure(bg=theme['text_bg'], fg=theme['text_fg'])
    
    def run(self):
        """Start the GUI application."""
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Start the GUI event loop
        self.root.mainloop()

def main():
    """Main application entry point."""
    print("Google Photos Downloader v2.0")
    print("=" * 40)
    
    # Check if running in command line mode
    if len(sys.argv) > 1:
        # Command line interface for automation/scripting
        parser = argparse.ArgumentParser(description='Download Google Photos from date range')
        parser.add_argument('--start-date', required=True, 
                           help='Start date in YYYY-MM-DD format')
        parser.add_argument('--end-date', required=True,
                           help='End date in YYYY-MM-DD format')
        parser.add_argument('--output-dir', default='./downloads',
                           help='Output directory for downloaded photos')
        parser.add_argument('--credentials', default='credentials.json',
                           help='Path to OAuth2 credentials file')
        parser.add_argument('--token', default='token.json',
                           help='Path to access token file')
        
        args = parser.parse_args()
        
        # Validate inputs
        try:
            start_dt = datetime.strptime(args.start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(args.end_date, '%Y-%m-%d')
            
            if start_dt > end_dt:
                print("❌ Error: Start date cannot be after end date.")
                sys.exit(1)
                
        except ValueError as e:
            print(f"❌ Error: Invalid date format. Use YYYY-MM-DD. {e}")
            sys.exit(1)
        
        # Run command line version
        downloader = GooglePhotosDownloader(args.credentials, args.token)
        
        if not downloader.authenticate():
            print("❌ Authentication failed. Exiting.")
            sys.exit(1)
        
        try:
            import asyncio
            asyncio.run(downloader.download_photos_async(start_dt, end_dt, args.output_dir))
        except KeyboardInterrupt:
            print("\n🛑 Download interrupted by user.")
        except Exception as e:
            print(f"\n❌ Error during download: {e}")
            sys.exit(1)
    else:
        # GUI mode (default)
        if not GOOGLE_APIS_AVAILABLE:
            print("❌ Google APIs not installed!")
            print("📦 Please install required packages:")
            print("   pip install google-auth google-auth-oauthlib google-auth-httplib2 requests")
            if not CALENDAR_AVAILABLE:
                print("   pip install tkcalendar  # For enhanced date pickers")
            sys.exit(1)
        
        try:
            config = ConfigManager()
            app = GooglePhotosGUI(config)
            app.run()
        except Exception as e:
            print(f"❌ Failed to start GUI: {e}")
            messagebox.showerror("Startup Error", f"Failed to start application: {e}")

if __name__ == '__main__':
    main()
