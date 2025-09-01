"""
Core Google Photos downloader logic
"""
from __future__ import annotations

import os
import requests
import hashlib
import time
import asyncio
import json
import logging
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

try:
    from app.core.config import ConfigManager
except ImportError:
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
    
    def _validate_credentials_file(self) -> bool:
        """Validate the credentials.json file format and content."""
        try:
            self.update_status(f"Validating credentials file: {self.credentials_file}")
            
            if not os.path.exists(self.credentials_file):
                self.update_status(f"Error: Credentials file '{self.credentials_file}' not found")
                return False
            
            # Check file size
            file_size = os.path.getsize(self.credentials_file)
            self.update_status(f"Credentials file size: {file_size} bytes")
            
            if file_size == 0:
                self.update_status("Error: Credentials file is empty")
                return False
            
            # Validate JSON format and required fields
            with open(self.credentials_file, 'r') as f:
                creds_data = json.load(f)
            
            self.update_status("Credentials file JSON format is valid")
            
            # Check for required OAuth2 fields
            if 'installed' not in creds_data and 'web' not in creds_data:
                self.update_status("Error: Credentials file missing 'installed' or 'web' configuration")
                return False
            
            # Get the client config (prefer 'installed' for desktop apps)
            client_config = creds_data.get('installed') or creds_data.get('web')
            
            required_fields = ['client_id', 'client_secret', 'auth_uri', 'token_uri']
            missing_fields = [field for field in required_fields if field not in client_config]
            
            if missing_fields:
                self.update_status(f"Error: Credentials file missing required fields: {missing_fields}")
                return False
            
            self.update_status("Credentials file validation successful")
            self.update_status(f"Client ID: {client_config['client_id'][:20]}...")
            
            return True
            
        except json.JSONDecodeError as e:
            self.update_status(f"Error: Invalid JSON in credentials file: {e}")
            return False
        except Exception as e:
            self.update_status(f"Error validating credentials file: {e}")
            return False

    def _validate_token(self, creds: Credentials) -> bool:
        """Validate token structure and properties with comprehensive checks."""
        try:
            self.update_status("Validating OAuth token...")
            
            if not creds:
                self.update_status("Error: No credentials object provided")
                return False
            
            # Check basic token properties
            is_valid = creds.valid
            is_expired = creds.expired
            has_refresh = bool(creds.refresh_token)
            
            self.update_status(f"Token valid: {is_valid}")
            self.update_status(f"Token expired: {is_expired}")
            self.update_status(f"Has refresh token: {has_refresh}")
            
            # Validate access token presence and format
            if creds.token:
                self.update_status(f"Access token present: {creds.token[:20]}...")
                # Basic token format validation (should be a string)
                if not isinstance(creds.token, str) or len(creds.token) < 10:
                    self.update_status("Error: Access token appears to be invalid format")
                    return False
            else:
                self.update_status("Error: No access token present")
                return False
            
            # Check token expiry
            if creds.expiry:
                self.update_status(f"Token expires at: {creds.expiry}")
                time_until_expiry = (creds.expiry - datetime.utcnow()).total_seconds()
                self.update_status(f"Time until expiry: {time_until_expiry:.0f} seconds")
                
                # Warn if token expires very soon (less than 5 minutes)
                if time_until_expiry < 300:
                    self.update_status("Warning: Token expires very soon, may need refresh")
            else:
                self.update_status("Warning: No expiry time set for token")
            
            # Validate scopes if available
            if hasattr(creds, 'scopes') and creds.scopes:
                self.update_status(f"Token scopes: {creds.scopes}")
                # Check if required scopes are present
                required_scope = 'https://www.googleapis.com/auth/photoslibrary.readonly'
                if required_scope not in creds.scopes:
                    self.update_status(f"Warning: Required scope '{required_scope}' not found in token")
            
            # Final validation - token must be valid for use
            if not is_valid:
                if is_expired and has_refresh:
                    self.update_status("Token is expired but can be refreshed")
                    return True  # This is recoverable
                else:
                    self.update_status("Error: Token is invalid and cannot be refreshed")
                    return False
            
            self.update_status("Token validation successful")
            return True
            
        except Exception as e:
            self.update_status(f"Error validating token: {e}")
            return False

    def _initialize_service(self, creds: Credentials) -> bool:
        """Initialize Google Photos API service and validate it works with comprehensive error handling."""
        try:
            self.update_status("Initializing Google Photos API service...")
            
            # Pre-validation checks
            if not creds:
                self.update_status("Error: No credentials provided to service initialization")
                return False
                
            if not creds.valid:
                self.update_status("Error: Invalid credentials provided to service initialization")
                self.update_status(f"Credential status - Valid: {creds.valid}, Expired: {creds.expired}")
                return False
            
            # Clear any existing service
            self.service = None
            
            # Build the service with error handling
            try:
                self.update_status("Building Google Photos API service object...")
                self.service = build('photoslibrary', 'v1', credentials=creds, cache_discovery=False)
                self.update_status("Google Photos API service object created successfully")
            except Exception as e:
                self.update_status(f"Error building API service: {e}")
                return False
            
            # Validate service object
            if not self.service:
                self.update_status("Error: Service object is None after creation")
                return False
            
            # Test the service with multiple validation calls
            self.update_status("Testing API service functionality...")
            
            try:
                # Test 1: Try to get albums (lightweight call)
                self.update_status("Test 1: Fetching albums list...")
                test_response = self.service.albums().list(pageSize=1).execute()
                
                if 'albums' in test_response:
                    album_count = len(test_response['albums'])
                    self.update_status(f"Albums test successful - found {album_count} albums")
                else:
                    self.update_status("Albums test successful - no albums found (normal)")
                
                # Test 2: Try to search for media items (another lightweight call)
                self.update_status("Test 2: Testing media search capability...")
                search_body = {
                    'pageSize': 1,
                    'filters': {
                        'mediaTypeFilter': {
                            'mediaTypes': ['PHOTO']
                        }
                    }
                }
                
                media_response = self.service.mediaItems().search(body=search_body).execute()
                
                if 'mediaItems' in media_response:
                    media_count = len(media_response['mediaItems'])
                    self.update_status(f"Media search test successful - found {media_count} items")
                else:
                    self.update_status("Media search test successful - no media found")
                
                self.update_status("All API service tests passed successfully")
                return True
                
            except HttpError as e:
                error_details = str(e)
                status_code = getattr(e, 'resp', {}).get('status', 'unknown')
                
                self.update_status(f"API service test failed with HTTP {status_code} error: {error_details}")
                
                # Provide specific error guidance
                if '401' in str(status_code):
                    self.update_status("Error 401: Authentication failed - token may be invalid or expired")
                elif '403' in str(status_code):
                    self.update_status("Error 403: Access forbidden - check API permissions and scopes")
                elif '404' in str(status_code):
                    self.update_status("Error 404: API endpoint not found - check API version")
                elif '429' in str(status_code):
                    self.update_status("Error 429: Rate limit exceeded - too many requests")
                else:
                    self.update_status(f"HTTP Error {status_code}: {error_details}")
                
                return False
                
            except Exception as e:
                self.update_status(f"API service test failed with unexpected error: {e}")
                import traceback
                self.update_status(f"Service test error traceback: {traceback.format_exc()}")
                return False
                
        except Exception as e:
            self.update_status(f"Critical error during service initialization: {e}")
            import traceback
            self.update_status(f"Service initialization error traceback: {traceback.format_exc()}")
            return False

    def authenticate(self) -> bool:
        """Authenticate with Google Photos API using OAuth2 with comprehensive logging."""
        self.update_status("=== Starting OAuth Authentication Process ===")
        
        if not GOOGLE_APIS_AVAILABLE:
            self.update_status("Error: Google APIs not available - required packages not installed")
            self.update_status("Please install: pip install google-auth google-auth-oauthlib google-api-python-client")
            return False
        
        self.update_status("Google API packages are available")
        
        try:
            # Step 1: Validate credentials file
            self.update_status("Step 1: Validating credentials file...")
            if not self._validate_credentials_file():
                return False
            
            # Step 2: Load existing token if available
            self.update_status("Step 2: Checking for existing token...")
            if os.path.exists(self.token_file):
                self.update_status(f"Found existing token file: {self.token_file}")
                try:
                    self.creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
                    self.update_status("Successfully loaded existing token")
                    self._validate_token(self.creds)
                except Exception as e:
                    self.update_status(f"Error loading existing token: {e}")
                    self.creds = None
            else:
                self.update_status(f"No existing token file found at: {self.token_file}")
                self.creds = None
            
            # Step 3: Check if credentials are valid or need refresh/reauth
            self.update_status("Step 3: Checking credential validity...")
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.update_status("Token expired but refresh token available - attempting refresh...")
                    try:
                        self.creds.refresh(Request())
                        self.update_status("Token refresh successful")
                        
                        # Validate the refreshed token
                        if not self._validate_token(self.creds):
                            self.update_status("Error: Refreshed token validation failed")
                            self.creds = None
                        elif not self.creds.valid:
                            self.update_status("Error: Token still invalid after refresh")
                            self.creds = None
                            
                    except Exception as e:
                        self.update_status(f"Token refresh failed: {e}")
                        self.update_status("Will need to perform full OAuth flow")
                        self.creds = None
                else:
                    if self.creds:
                        self.update_status("Token invalid and no refresh token available")
                    else:
                        self.update_status("No valid credentials available")
                    
                    self.update_status("Starting OAuth authorization flow...")
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                        self.update_status("OAuth flow created successfully")
                        self.update_status("Opening browser for Google authentication...")
                        self.creds = flow.run_local_server(port=0)
                        self.update_status("OAuth flow completed successfully")
                        
                        # Validate the new token
                        if not self._validate_token(self.creds):
                            self.update_status("Error: New token validation failed")
                            return False
                        elif not self.creds.valid:
                            self.update_status("Error: New token is not valid")
                            return False
                            
                    except Exception as e:
                        self.update_status(f"OAuth flow failed: {e}")
                        return False
                
                # Step 4: Save new/refreshed credentials
                self.update_status("Step 4: Saving credentials...")
                try:
                    with open(self.token_file, 'w') as token:
                        token.write(self.creds.to_json())
                    self.update_status(f"Credentials saved to: {self.token_file}")
                except Exception as e:
                    self.update_status(f"Warning: Failed to save credentials: {e}")
            else:
                self.update_status("Existing credentials are valid")
            
            # Step 5: Initialize and test API service
            self.update_status("Step 5: Initializing API service...")
            if not self._initialize_service(self.creds):
                return False
            
            self.update_status("=== OAuth Authentication Successful ===")
            return True
            
        except Exception as e:
            self.update_status("=== OAuth Authentication Failed ===")
            self.update_status(f"Unexpected error during authentication: {e}")
            
            # Provide user-friendly error guidance
            error_str = str(e).lower()
            if 'permission' in error_str or 'access' in error_str:
                self.update_status("This appears to be a permissions issue. Check file permissions and try running as administrator if needed.")
            elif 'network' in error_str or 'connection' in error_str:
                self.update_status("This appears to be a network issue. Check your internet connection and firewall settings.")
            elif 'json' in error_str or 'decode' in error_str:
                self.update_status("This appears to be a file format issue. Check that your credentials.json file is valid.")
            elif 'import' in error_str or 'module' in error_str:
                self.update_status("This appears to be a missing dependency issue. Ensure all required packages are installed.")
            else:
                self.update_status("For detailed troubleshooting, check the application logs or contact support.")
            
            import traceback
            self.update_status(f"Full error traceback: {traceback.format_exc()}")
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
    
    def get_detailed_auth_status(self) -> Dict[str, Any]:
        """Get detailed authentication status with error information and suggestions."""
        status = {
            'authenticated': False,
            'message': '',
            'error_type': None,
            'error_details': None,
            'suggestions': [],
            'credentials_file_exists': os.path.exists(self.credentials_file),
            'token_file_exists': os.path.exists(self.token_file)
        }
        
        try:
            # Check if Google APIs are available
            if not GOOGLE_APIS_AVAILABLE:
                status.update({
                    'message': 'Google API packages not installed',
                    'error_type': 'missing_dependencies',
                    'error_details': 'Required Google API packages are not installed',
                    'suggestions': [
                        'Install required packages: pip install google-auth google-auth-oauthlib google-api-python-client',
                        'Check your Python environment and package installation'
                    ]
                })
                return status
            
            # Check credentials file
            if not status['credentials_file_exists']:
                status.update({
                    'message': 'Credentials file not found',
                    'error_type': 'missing_credentials',
                    'error_details': f'The credentials file "{self.credentials_file}" does not exist',
                    'suggestions': [
                        'Download OAuth2 credentials from Google Cloud Console',
                        'Save the credentials as "credentials.json" in the application directory',
                        'Ensure the file contains valid OAuth2 client configuration'
                    ]
                })
                return status
            
            # Validate credentials file format
            try:
                with open(self.credentials_file, 'r') as f:
                    creds_data = json.load(f)
                
                if 'installed' not in creds_data and 'web' not in creds_data:
                    status.update({
                        'message': 'Invalid credentials file format',
                        'error_type': 'invalid_credentials_format',
                        'error_details': 'Credentials file missing required OAuth2 configuration',
                        'suggestions': [
                            'Re-download credentials from Google Cloud Console',
                            'Ensure you download "Desktop Application" credentials',
                            'Verify the JSON file contains "installed" or "web" configuration'
                        ]
                    })
                    return status
                    
            except json.JSONDecodeError:
                status.update({
                    'message': 'Credentials file contains invalid JSON',
                    'error_type': 'invalid_json',
                    'error_details': 'The credentials file is not valid JSON format',
                    'suggestions': [
                        'Re-download credentials from Google Cloud Console',
                        'Check the file for syntax errors or corruption',
                        'Ensure the file was downloaded completely'
                    ]
                })
                return status
            except Exception as e:
                status.update({
                    'message': 'Error reading credentials file',
                    'error_type': 'file_read_error',
                    'error_details': str(e),
                    'suggestions': [
                        'Check file permissions',
                        'Ensure the file is not corrupted',
                        'Try re-downloading the credentials file'
                    ]
                })
                return status
            
            # Check existing token
            if status['token_file_exists']:
                try:
                    creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
                    
                    if creds and creds.valid:
                        # Test the service
                        try:
                            service = build('photoslibrary', 'v1', credentials=creds, cache_discovery=False)
                            test_response = service.albums().list(pageSize=1).execute()
                            
                            status.update({
                                'authenticated': True,
                                'message': 'Successfully authenticated with Google Photos API',
                                'suggestions': ['Authentication is working correctly']
                            })
                            return status
                            
                        except HttpError as e:
                            error_code = getattr(e, 'resp', {}).get('status', 'unknown')
                            if '401' in str(error_code):
                                status.update({
                                    'message': 'Token authentication failed',
                                    'error_type': 'token_invalid',
                                    'error_details': 'Access token is invalid or expired',
                                    'suggestions': [
                                        'Delete the token.json file to force re-authentication',
                                        'Run the authentication process again',
                                        'Check if your Google Cloud project is still active'
                                    ]
                                })
                            elif '403' in str(error_code):
                                status.update({
                                    'message': 'API access forbidden',
                                    'error_type': 'api_forbidden',
                                    'error_details': 'Access to Google Photos API is forbidden',
                                    'suggestions': [
                                        'Check if Google Photos API is enabled in your Google Cloud project',
                                        'Verify your OAuth2 scopes include Photos Library access',
                                        'Ensure your Google Cloud project has proper permissions'
                                    ]
                                })
                            else:
                                status.update({
                                    'message': f'API error: {error_code}',
                                    'error_type': 'api_error',
                                    'error_details': str(e),
                                    'suggestions': [
                                        'Check your internet connection',
                                        'Verify Google Photos API is accessible',
                                        'Try again in a few minutes'
                                    ]
                                })
                            return status
                            
                    elif creds and creds.expired:
                        if creds.refresh_token:
                            status.update({
                                'message': 'Token expired but can be refreshed',
                                'error_type': 'token_expired',
                                'error_details': 'Access token has expired but refresh token is available',
                                'suggestions': [
                                    'Run the authentication process to refresh the token',
                                    'The system will automatically refresh the token on next authentication'
                                ]
                            })
                        else:
                            status.update({
                                'message': 'Token expired and cannot be refreshed',
                                'error_type': 'token_expired_no_refresh',
                                'error_details': 'Access token has expired and no refresh token is available',
                                'suggestions': [
                                    'Delete the token.json file',
                                    'Run the authentication process again to get new tokens'
                                ]
                            })
                        return status
                    else:
                        status.update({
                            'message': 'Token is invalid',
                            'error_type': 'token_invalid',
                            'error_details': 'The stored token is not valid',
                            'suggestions': [
                                'Delete the token.json file',
                                'Run the authentication process again'
                            ]
                        })
                        return status
                        
                except Exception as e:
                    status.update({
                        'message': 'Error loading existing token',
                        'error_type': 'token_load_error',
                        'error_details': str(e),
                        'suggestions': [
                            'Delete the token.json file',
                            'Run the authentication process again',
                            'Check file permissions'
                        ]
                    })
                    return status
            else:
                # No token file exists
                status.update({
                    'message': 'Authentication required',
                    'error_type': 'no_token',
                    'error_details': 'No authentication token found',
                    'suggestions': [
                        'Run the authentication process to authorize the application',
                        'This will open a browser window for Google OAuth authorization',
                        'Make sure you have a valid credentials.json file'
                    ]
                })
                return status
                
        except Exception as e:
            status.update({
                'message': 'Unexpected error checking authentication status',
                'error_type': 'unexpected_error',
                'error_details': str(e),
                'suggestions': [
                    'Check application logs for more details',
                    'Ensure all required files are present',
                    'Try restarting the application'
                ]
            })
            return status
        
        # Fallback
        status.update({
            'message': 'Authentication status unknown',
            'error_type': 'unknown',
            'suggestions': ['Try running the authentication process']
        })
        return status

    def cancel_download(self):
        """Cancel the current download operation."""
        self.cancelled = True