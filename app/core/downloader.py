"""
Core Google Photos downloader logic
"""
import os
import requests
import hashlib
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

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

from core.session import DownloadSession
from core.config import ConfigManager

# Google Photos API scope
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']


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
        if not GOOGLE_APIS_AVAILABLE:
            self.update_status("Error: Google APIs not available")
            return False
            
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
                        self.update_status(f"Error: '{self.credentials_file}' not found. Please download OAuth2 credentials from Google Cloud Console.")
                        return False
                    
                    self.update_status("Opening browser for Google authentication...")
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                    self.creds = flow.run_local_server(port=0)
                
                # Save credentials for future use
                with open(self.token_file, 'w') as token:
                    token.write(self.creds.to_json())
            
            self.service = build('photoslibrary', 'v1', credentials=self.creds)
            self.update_status("Successfully authenticated with Google Photos API")
            return True
            
        except Exception as e:
            self.update_status(f"Authentication failed: {e}")
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
        
        self.update_status("Fetching albums...")
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
                    self.update_status(f"Found {len(batch)} albums (total: {len(albums)})")
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
                    
        except HttpError as e:
            self.update_status(f"API error fetching albums: {e}")
            return albums
        
        self.update_status(f"Found {len(albums)} albums")
        return albums
    
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
            self.update_status(f"Searching for photos from {start_str} to {end_str}...")
            
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
                    self.update_status(f"Found {len(batch)} items in batch (total: {len(media_items)})")
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
                    
        except HttpError as e:
            self.update_status(f"API error during search: {e}")
            return media_items
        
        if self.cancelled:
            self.update_status("Search cancelled")
        else:
            self.update_status(f"Search complete: {len(media_items)} items found")
        
        return media_items
    
    async def get_album_media_items_async(self, album_id: str) -> List[Dict[str, Any]]:
        """Retrieve media items from a specific album."""
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        self.update_status(f"Searching for items in album...")
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
                    self.update_status(f"Found {len(batch)} items in batch (total: {len(media_items)})")
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
                    
        except HttpError as e:
            self.update_status(f"API error during album search: {e}")
            return media_items
        
        self.update_status(f"Album search complete: {len(media_items)} items found")
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
    
    async def download_media_item_async(self, item: Dict[str, Any], output_dir: Path) -> Tuple[bool, int]:
        """Download a single media item with checksum-based duplicate detection."""
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
                self.update_status(f"Skipping existing file: {safe_filename}")
                return True, existing_size
            
            # Determine download URL based on media type
            if 'photo' in media_metadata:
                download_url = f"{item['baseUrl']}=d"  # Original quality photo
            elif 'video' in media_metadata:
                download_url = f"{item['baseUrl']}=dv"  # Original quality video
            else:
                self.update_status(f"Unknown media type for {filename}")
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
                    
                    # Move temp file to final location
                    temp_file.rename(file_path)
                    return True, file_size
                    
                except (requests.RequestException, IOError) as e:
                    if attempt < max_retries - 1:
                        self.update_status(f"Retry {attempt + 1}/{max_retries} for {filename}: {e}")
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        self.update_status(f"Failed to download {filename} after {max_retries} attempts: {e}")
                        return False, 0
            
        except Exception as e:
            self.update_status(f"Unexpected error downloading {item.get('filename', 'unknown')}: {e}")
            return False, 0
    
    def cancel_download(self):
        """Cancel the current download operation."""
        self.cancelled = True