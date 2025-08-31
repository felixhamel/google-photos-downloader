#!/usr/bin/env python3
"""
Unit tests for Google Photos Downloader
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open, call
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from google_photos_downloader import (
    GooglePhotosDownloader,
    DownloadStats,
    GooglePhotosGUI
)


class TestDownloadStats(unittest.TestCase):
    """Test the DownloadStats class."""
    
    def setUp(self):
        self.stats = DownloadStats()
    
    def test_initialization(self):
        """Test initial state of stats."""
        self.assertIsNone(self.stats.start_time)
        self.assertEqual(self.stats.completed_files, 0)
        self.assertEqual(self.stats.total_files, 0)
        self.assertEqual(self.stats.total_bytes, 0)
        self.assertEqual(self.stats.completed_bytes, 0)
    
    def test_start(self):
        """Test starting statistics tracking."""
        self.stats.start(100)
        self.assertIsNotNone(self.stats.start_time)
        self.assertEqual(self.stats.total_files, 100)
        self.assertEqual(self.stats.completed_files, 0)
    
    def test_update(self):
        """Test updating statistics."""
        self.stats.start(10)
        self.stats.update(1024)
        self.assertEqual(self.stats.completed_files, 1)
        self.assertEqual(self.stats.completed_bytes, 1024)
        
        self.stats.update(2048)
        self.assertEqual(self.stats.completed_files, 2)
        self.assertEqual(self.stats.completed_bytes, 3072)
    
    @patch('time.time')
    def test_get_speed_mbps(self, mock_time):
        """Test download speed calculation."""
        # Setup time mock
        mock_time.side_effect = [1000, 1010]  # 10 seconds elapsed
        
        self.stats.start(10)
        self.stats.update(10 * 1024 * 1024)  # 10 MB
        
        speed = self.stats.get_speed_mbps()
        self.assertAlmostEqual(speed, 1.0, places=1)  # 10 MB / 10 sec = 1 MB/s
    
    @patch('time.time')
    def test_get_eta_seconds(self, mock_time):
        """Test ETA calculation."""
        # Setup time mock
        mock_time.side_effect = [1000, 1010]  # 10 seconds elapsed
        
        self.stats.start(10)
        self.stats.completed_files = 2  # 2 files in 10 seconds
        
        eta = self.stats.get_eta_seconds()
        self.assertEqual(eta, 40)  # 8 remaining files at 0.2 files/sec = 40 seconds
    
    def test_get_eta_seconds_edge_cases(self):
        """Test ETA edge cases."""
        # No files completed
        self.stats.start(10)
        self.assertIsNone(self.stats.get_eta_seconds())
        
        # All files completed
        self.stats.start(10)
        self.stats.completed_files = 10
        self.assertIsNone(self.stats.get_eta_seconds())


class TestGooglePhotosDownloader(unittest.TestCase):
    """Test the GooglePhotosDownloader class."""
    
    def setUp(self):
        self.downloader = GooglePhotosDownloader()
    
    def test_initialization(self):
        """Test downloader initialization."""
        self.assertEqual(self.downloader.credentials_file, 'credentials.json')
        self.assertEqual(self.downloader.token_file, 'token.json')
        self.assertIsNone(self.downloader.service)
        self.assertIsNone(self.downloader.creds)
        self.assertFalse(self.downloader.cancelled)
    
    def test_set_callbacks(self):
        """Test setting callbacks."""
        progress_cb = Mock()
        status_cb = Mock()
        
        self.downloader.set_callbacks(progress_cb, status_cb)
        self.assertEqual(self.downloader.progress_callback, progress_cb)
        self.assertEqual(self.downloader.status_callback, status_cb)
    
    def test_update_status_with_callback(self):
        """Test status updates with callback."""
        status_cb = Mock()
        self.downloader.set_callbacks(status_callback=status_cb)
        
        self.downloader.update_status("Test message")
        status_cb.assert_called_once_with("Test message")
    
    def test_update_status_without_callback(self):
        """Test status updates without callback (print)."""
        with patch('builtins.print') as mock_print:
            self.downloader.update_status("Test message")
            mock_print.assert_called_once_with("Test message")
    
    @patch('time.time')
    def test_update_progress_with_callback(self, mock_time):
        """Test progress updates with callback."""
        mock_time.return_value = 1000
        progress_cb = Mock()
        self.downloader.set_callbacks(progress_callback=progress_cb)
        self.downloader.stats.start(100)
        
        self.downloader.update_progress(10, 100, 10.0)
        progress_cb.assert_called_once()
        
        # Check callback arguments
        call_args = progress_cb.call_args[0]
        self.assertEqual(call_args[0], 10)  # current
        self.assertEqual(call_args[1], 100)  # total
        self.assertEqual(call_args[2], 10.0)  # percentage
    
    def test_date_to_google_format(self):
        """Test date conversion to Google Photos API format."""
        date = datetime(2024, 3, 15)
        result = self.downloader.date_to_google_format(date)
        
        self.assertEqual(result, {
            'year': 2024,
            'month': 3,
            'day': 15
        })
    
    @patch('google_photos_downloader.build')
    @patch('google_photos_downloader.Credentials')
    @patch('os.path.exists')
    def test_authenticate_with_existing_valid_token(self, mock_exists, mock_creds_class, mock_build):
        """Test authentication with existing valid token."""
        mock_exists.return_value = True
        
        # Create mock credentials
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds_class.from_authorized_user_file.return_value = mock_creds
        
        result = self.downloader.authenticate()
        
        self.assertTrue(result)
        self.assertEqual(self.downloader.creds, mock_creds)
        mock_build.assert_called_once_with('photoslibrary', 'v1', credentials=mock_creds)
    
    @patch('google_photos_downloader.build')
    @patch('google_photos_downloader.Request')
    @patch('google_photos_downloader.Credentials')
    @patch('os.path.exists')
    def test_authenticate_with_expired_token(self, mock_exists, mock_creds_class, mock_request, mock_build):
        """Test authentication with expired token that needs refresh."""
        mock_exists.return_value = True
        
        # Create mock credentials
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token"
        mock_creds_class.from_authorized_user_file.return_value = mock_creds
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = self.downloader.authenticate()
        
        self.assertTrue(result)
        mock_creds.refresh.assert_called_once()
        mock_file.assert_called_once_with('token.json', 'w')
    
    @patch('google_photos_downloader.build')
    @patch('google_photos_downloader.InstalledAppFlow')
    @patch('os.path.exists')
    def test_authenticate_new_user(self, mock_exists, mock_flow_class, mock_build):
        """Test authentication for new user (no existing token)."""
        def exists_side_effect(path):
            if path == 'token.json':
                return False
            elif path == 'credentials.json':
                return True
            return False
        
        mock_exists.side_effect = exists_side_effect
        
        # Create mock flow
        mock_flow = Mock()
        mock_creds = Mock()
        mock_creds.to_json.return_value = '{"token": "test"}'
        mock_flow.run_local_server.return_value = mock_creds
        mock_flow_class.from_client_secrets_file.return_value = mock_flow
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = self.downloader.authenticate()
        
        self.assertTrue(result)
        mock_flow.run_local_server.assert_called_once_with(port=0)
        mock_file.assert_called_once_with('token.json', 'w')
    
    def test_authenticate_missing_credentials_file(self):
        """Test authentication fails when credentials.json is missing."""
        with patch('os.path.exists', return_value=False):
            result = self.downloader.authenticate()
            self.assertFalse(result)
    
    def test_cancel_download(self):
        """Test cancelling download."""
        self.assertFalse(self.downloader.cancelled)
        self.downloader.cancel_download()
        self.assertTrue(self.downloader.cancelled)
    
    @patch('requests.get')
    @patch('builtins.open', new_callable=mock_open)
    async def test_download_media_item_async_photo(self, mock_file, mock_get):
        """Test downloading a photo item."""
        # Create test item
        item = {
            'filename': 'test.jpg',
            'baseUrl': 'https://example.com/photo',
            'mediaMetadata': {
                'creationTime': '2024-01-15T14:30:00Z',
                'photo': {}
            }
        }
        
        # Mock response
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'data1', b'data2']
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            success, size = await self.downloader.download_media_item_async(item, output_path)
        
        self.assertTrue(success)
        self.assertEqual(size, 10)  # len(b'data1') + len(b'data2')
        
        # Check download URL for photo
        mock_get.assert_called_with(
            'https://example.com/photo=d',
            stream=True,
            timeout=30
        )
    
    @patch('requests.get')
    @patch('builtins.open', new_callable=mock_open)
    async def test_download_media_item_async_video(self, mock_file, mock_get):
        """Test downloading a video item."""
        # Create test item
        item = {
            'filename': 'test.mp4',
            'baseUrl': 'https://example.com/video',
            'mediaMetadata': {
                'creationTime': '2024-01-15T14:30:00Z',
                'video': {}
            }
        }
        
        # Mock response
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'video_data']
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            success, size = await self.downloader.download_media_item_async(item, output_path)
        
        self.assertTrue(success)
        
        # Check download URL for video
        mock_get.assert_called_with(
            'https://example.com/video=dv',
            stream=True,
            timeout=30
        )
    
    async def test_download_media_item_async_skip_existing(self):
        """Test skipping download of existing file."""
        item = {
            'filename': 'test.jpg',
            'baseUrl': 'https://example.com/photo',
            'mediaMetadata': {
                'creationTime': '2024-01-15T14:30:00Z',
                'photo': {}
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Create existing file
            test_file = output_path / '20240115_143000_test.jpg'
            test_file.write_text('existing content')
            
            with patch('requests.get') as mock_get:
                success, size = await self.downloader.download_media_item_async(item, output_path)
            
            self.assertTrue(success)
            self.assertEqual(size, len('existing content'))
            mock_get.assert_not_called()  # Should not download
    
    @patch('requests.get')
    async def test_download_media_item_async_with_retry(self, mock_get):
        """Test download with retry logic."""
        item = {
            'filename': 'test.jpg',
            'baseUrl': 'https://example.com/photo',
            'mediaMetadata': {
                'creationTime': '2024-01-15T14:30:00Z',
                'photo': {}
            }
        }
        
        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = Exception("Network error")
        
        mock_response_success = Mock()
        mock_response_success.iter_content.return_value = [b'data']
        mock_response_success.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_response_fail, mock_response_success]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            success, size = await self.downloader.download_media_item_async(item, output_path)
        
        self.assertTrue(success)
        self.assertEqual(mock_get.call_count, 2)  # Called twice due to retry
    
    async def test_download_media_item_async_cancelled(self):
        """Test download cancellation."""
        item = {
            'filename': 'test.jpg',
            'baseUrl': 'https://example.com/photo',
            'mediaMetadata': {
                'creationTime': '2024-01-15T14:30:00Z',
                'photo': {}
            }
        }
        
        self.downloader.cancelled = True
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            success, size = await self.downloader.download_media_item_async(item, output_path)
        
        self.assertFalse(success)
        self.assertEqual(size, 0)


class TestGooglePhotosGUI(unittest.TestCase):
    """Test the GooglePhotosGUI class."""
    
    @patch('google_photos_downloader.tk.Tk')
    def setUp(self, mock_tk):
        """Set up test GUI."""
        self.mock_root = Mock()
        mock_tk.return_value = self.mock_root
        
        with patch.object(GooglePhotosGUI, 'setup_ui'):
            with patch.object(GooglePhotosGUI, 'setup_callbacks'):
                self.gui = GooglePhotosGUI()
    
    def test_initialization(self):
        """Test GUI initialization."""
        self.assertIsNotNone(self.gui.root)
        self.assertIsNotNone(self.gui.downloader)
        self.assertIsNone(self.gui.download_thread)
        self.assertFalse(self.gui.is_downloading)
    
    def test_browse_folder(self):
        """Test folder browsing."""
        with patch('google_photos_downloader.filedialog.askdirectory') as mock_dialog:
            mock_dialog.return_value = '/new/path'
            
            self.gui.folder_var = Mock()
            self.gui.browse_folder()
            
            self.gui.folder_var.set.assert_called_once_with('/new/path')
    
    def test_browse_folder_cancelled(self):
        """Test folder browsing when cancelled."""
        with patch('google_photos_downloader.filedialog.askdirectory') as mock_dialog:
            mock_dialog.return_value = ''  # User cancelled
            
            self.gui.folder_var = Mock()
            initial_value = self.gui.folder_var.get.return_value
            
            self.gui.browse_folder()
            
            self.gui.folder_var.set.assert_not_called()
    
    @patch('google_photos_downloader.CALENDAR_AVAILABLE', True)
    def test_get_date_values_with_calendar(self):
        """Test getting date values with calendar widget."""
        from datetime import date
        
        # Mock DateEntry widgets
        self.gui.start_date_picker = Mock()
        self.gui.start_date_picker.get_date.return_value = date(2024, 1, 1)
        
        self.gui.end_date_picker = Mock()
        self.gui.end_date_picker.get_date.return_value = date(2024, 12, 31)
        
        start_dt, end_dt = self.gui.get_date_values()
        
        self.assertEqual(start_dt.date(), date(2024, 1, 1))
        self.assertEqual(end_dt.date(), date(2024, 12, 31))
    
    @patch('google_photos_downloader.CALENDAR_AVAILABLE', False)
    def test_get_date_values_without_calendar(self):
        """Test getting date values without calendar widget."""
        self.gui.start_date_var = Mock()
        self.gui.start_date_var.get.return_value = '2024-01-01'
        
        self.gui.end_date_var = Mock()
        self.gui.end_date_var.get.return_value = '2024-12-31'
        
        start_dt, end_dt = self.gui.get_date_values()
        
        self.assertEqual(start_dt, datetime(2024, 1, 1))
        self.assertEqual(end_dt, datetime(2024, 12, 31))
    
    @patch('google_photos_downloader.messagebox.showerror')
    def test_validate_inputs_invalid_dates(self, mock_error):
        """Test input validation with invalid date range."""
        with patch.object(self.gui, 'get_date_values') as mock_get_dates:
            # End date before start date
            mock_get_dates.return_value = (
                datetime(2024, 12, 31),
                datetime(2024, 1, 1)
            )
            
            result = self.gui.validate_inputs()
            
            self.assertFalse(result)
            mock_error.assert_called_once()
    
    @patch('google_photos_downloader.messagebox.askyesno')
    def test_validate_inputs_large_date_range(self, mock_yesno):
        """Test input validation with large date range."""
        with patch.object(self.gui, 'get_date_values') as mock_get_dates:
            # 6 years range
            mock_get_dates.return_value = (
                datetime(2018, 1, 1),
                datetime(2024, 12, 31)
            )
            
            self.gui.folder_var = Mock()
            self.gui.folder_var.get.return_value = '/valid/path'
            
            mock_yesno.return_value = False  # User says no
            
            result = self.gui.validate_inputs()
            
            self.assertFalse(result)
            mock_yesno.assert_called_once()
    
    @patch('google_photos_downloader.messagebox.showerror')
    def test_validate_inputs_empty_folder(self, mock_error):
        """Test input validation with empty folder."""
        with patch.object(self.gui, 'get_date_values') as mock_get_dates:
            mock_get_dates.return_value = (
                datetime(2024, 1, 1),
                datetime(2024, 12, 31)
            )
            
            self.gui.folder_var = Mock()
            self.gui.folder_var.get.return_value = ''
            
            result = self.gui.validate_inputs()
            
            self.assertFalse(result)
            mock_error.assert_called_once()
    
    def test_cancel_download(self):
        """Test cancelling download."""
        self.gui.is_downloading = True
        self.gui.cancel_button = Mock()
        self.gui.downloader = Mock()
        self.gui.status_text = Mock()  # Add mock for status_text
        self.gui.root = Mock()  # Add mock for root
        
        self.gui.cancel_download()
        
        self.gui.downloader.cancel_download.assert_called_once()
        self.gui.cancel_button.config.assert_called_once_with(state='disabled')
    
    def test_download_complete(self):
        """Test download completion."""
        self.gui.download_button = Mock()
        self.gui.cancel_button = Mock()
        self.gui.downloader = Mock()
        self.gui.downloader.cancelled = False
        self.gui.root = Mock()
        
        with patch('google_photos_downloader.messagebox.showinfo') as mock_info:
            self.gui.download_complete()
        
        self.assertFalse(self.gui.is_downloading)
        self.gui.download_button.config.assert_called_once_with(state='normal')
        self.gui.cancel_button.config.assert_called_once_with(state='disabled')
        self.gui.root.bell.assert_called_once()
        mock_info.assert_called_once()
    
    @patch('google_photos_downloader.messagebox.askyesno')
    def test_on_closing_with_download(self, mock_yesno):
        """Test closing window with download in progress."""
        self.gui.is_downloading = True
        self.gui.downloader = Mock()
        self.gui.root = Mock()
        
        mock_yesno.return_value = True  # User confirms
        
        self.gui.on_closing()
        
        self.gui.downloader.cancel_download.assert_called_once()
        self.gui.root.destroy.assert_called_once()
    
    def test_on_closing_without_download(self):
        """Test closing window without download."""
        self.gui.is_downloading = False
        self.gui.root = Mock()
        
        self.gui.on_closing()
        
        self.gui.root.destroy.assert_called_once()


if __name__ == '__main__':
    unittest.main()