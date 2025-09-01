#!/usr/bin/env python3
"""
Command line interface for downloading Google Photos.
"""
import os
import sys
import argparse
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

# Add current directory to path for imports
sys.path.insert(0, os.getcwd())

try:
    from app.core.downloader import GooglePhotosDownloader
    from app.core.config import ConfigManager
    from app.core.session import DownloadSession
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📦 Please install dependencies: pip install -r requirements-web.txt")
    sys.exit(1)


class CLIDownloader:
    """Command-line interface for Google Photos Downloader."""
    
    def __init__(self):
        """Initialize CLI downloader."""
        self.config = ConfigManager()
        self.downloader = None
        self.session = None
    
    def print_header(self):
        """Print application header."""
        print("\n" + "=" * 60)
        print("🚀 Google Photos Downloader - CLI Mode v2.0.0")
        print("=" * 60)
        print("📱 Web Mode: python start_server.py")
        print("🖥️  GUI Mode: python src/google_photos_downloader.py")
        print("⌨️  CLI Mode: python cli_mode.py [options]")
        print("=" * 60 + "\n")
    
    def authenticate(self) -> bool:
        """Authenticate with Google Photos API."""
        print("🔐 Authenticating with Google Photos API...")
        
        if not os.path.exists("credentials.json"):
            print("❌ ERROR: credentials.json not found!")
            print("📋 Please download OAuth2 credentials from Google Cloud Console")
            print("📖 See OAUTH_GUIDE.md for detailed instructions")
            return False
        
        self.downloader = GooglePhotosDownloader(config=self.config)
        
        # Set up CLI callbacks
        def progress_callback(current, total, percentage, speed, eta):
            eta_str = f"{eta//60}m {eta%60}s" if eta else "Calculating..."
            print(f"\r📥 Progress: {current}/{total} ({percentage:.1f}%) "
                  f"Speed: {speed:.1f} MB/s ETA: {eta_str}", end="", flush=True)
        
        def status_callback(message):
            print(f"\n📢 {message}")
        
        self.downloader.set_callbacks(progress_callback, status_callback)
        
        if self.downloader.authenticate():
            print("✅ Authentication successful!")
            return True
        else:
            print("❌ Authentication failed!")
            return False
    
    async def list_albums(self) -> bool:
        """List all available albums."""
        print("📂 Fetching albums...")
        
        try:
            albums = await self.downloader.get_albums_async()
            
            if not albums:
                print("📭 No albums found")
                return True
            
            print(f"\n📚 Found {len(albums)} albums:")
            print("-" * 60)
            
            for i, album in enumerate(albums, 1):
                title = album.get('title', 'Untitled')
                count = album.get('mediaItemsCount', 0)
                album_id = album['id']
                
                print(f"{i:3d}. {title}")
                print(f"     📸 {count} items")
                print(f"     🆔 {album_id}")
                print()
            
            return True
            
        except Exception as e:
            print(f"❌ Error fetching albums: {e}")
            return False
    
    async def download_by_date_range(self, start_date: datetime, end_date: datetime, 
                                   output_dir: str, media_types: List[str]) -> bool:
        """Download photos by date range."""
        print(f"📅 Downloading photos from {start_date.date()} to {end_date.date()}")
        print(f"📁 Output directory: {output_dir}")
        print(f"🎭 Media types: {', '.join(media_types)}")
        
        try:
            # Create session
            self.session = DownloadSession()
            self.session.output_dir = output_dir
            self.session.download_params = {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'media_types': media_types
            }
            
            # Get media items
            print("\n🔍 Searching for media items...")
            media_items = await self.downloader.get_media_items_async(
                start_date=start_date,
                end_date=end_date,
                media_types=media_types
            )
            
            if not media_items:
                print("📭 No media items found for the specified criteria")
                return True
            
            print(f"✅ Found {len(media_items)} items to download")
            
            # Setup session
            self.session.media_items = media_items
            self.session.total_items = len(media_items)
            self.session.save_state()
            
            # Start download
            self.downloader.stats.start(len(media_items))
            
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            print(f"\n📥 Starting download to {output_path}")
            print("⏹️  Press Ctrl+C to cancel\n")
            
            success_count = 0
            failed_count = 0
            
            for i, item in enumerate(media_items, 1):
                if self.downloader.cancelled:
                    break
                
                try:
                    success, file_size = await self.downloader.download_media_item_async(
                        item, output_path
                    )
                    
                    if success:
                        success_count += 1
                        self.session.mark_completed(item['id'])
                    else:
                        failed_count += 1
                        self.session.mark_failed(item['id'])
                    
                    # Update progress
                    percentage = (i / len(media_items)) * 100
                    self.downloader.stats.update(file_size)
                    
                    # Save state periodically
                    if i % 10 == 0:
                        self.session.save_state()
                
                except KeyboardInterrupt:
                    print("\n\n⏹️  Download cancelled by user")
                    self.downloader.cancelled = True
                    break
                except Exception as e:
                    print(f"\n❌ Error downloading {item.get('filename', 'unknown')}: {e}")
                    failed_count += 1
                    self.session.mark_failed(item['id'])
            
            # Final status
            self.session.save_state()
            print(f"\n\n📊 Download Summary:")
            print(f"✅ Successfully downloaded: {success_count} items")
            if failed_count > 0:
                print(f"❌ Failed downloads: {failed_count} items")
            print(f"📁 Files saved to: {output_path}")
            
            # Cleanup if fully completed
            if failed_count == 0 and success_count > 0:
                self.session.cleanup()
                print("🧹 Session cleaned up (fully completed)")
            
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Download error: {e}")
            return False
    
    async def download_by_album(self, album_id: str, output_dir: str) -> bool:
        """Download photos from specific album."""
        print(f"📂 Downloading album: {album_id}")
        print(f"📁 Output directory: {output_dir}")
        
        try:
            # Get media items from album
            print("\n🔍 Fetching album contents...")
            media_items = await self.downloader.get_album_media_items_async(album_id)
            
            if not media_items:
                print("📭 No media items found in this album")
                return True
            
            print(f"✅ Found {len(media_items)} items to download")
            
            # Setup session
            self.session = DownloadSession()
            self.session.output_dir = output_dir
            self.session.media_items = media_items
            self.session.total_items = len(media_items)
            self.session.download_params = {'album_id': album_id}
            self.session.save_state()
            
            # Create output directory with album name
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            print(f"\n📥 Starting download to {output_path}")
            print("⏹️  Press Ctrl+C to cancel\n")
            
            success_count = 0
            failed_count = 0
            
            for i, item in enumerate(media_items, 1):
                if self.downloader.cancelled:
                    break
                
                try:
                    success, file_size = await self.downloader.download_media_item_async(
                        item, output_path
                    )
                    
                    if success:
                        success_count += 1
                        self.session.mark_completed(item['id'])
                    else:
                        failed_count += 1
                        self.session.mark_failed(item['id'])
                    
                    # Save state periodically
                    if i % 10 == 0:
                        self.session.save_state()
                
                except KeyboardInterrupt:
                    print("\n\n⏹️  Download cancelled by user")
                    self.downloader.cancelled = True
                    break
                except Exception as e:
                    print(f"\n❌ Error downloading {item.get('filename', 'unknown')}: {e}")
                    failed_count += 1
                    self.session.mark_failed(item['id'])
            
            # Final status
            self.session.save_state()
            print(f"\n\n📊 Download Summary:")
            print(f"✅ Successfully downloaded: {success_count} items")
            if failed_count > 0:
                print(f"❌ Failed downloads: {failed_count} items")
            print(f"📁 Files saved to: {output_path}")
            
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Download error: {e}")
            return False
    
    def list_sessions(self):
        """List available download sessions."""
        sessions = DownloadSession.list_sessions()
        
        if not sessions:
            print("📭 No download sessions found")
            return
        
        print(f"💾 Found {len(sessions)} download sessions:")
        print("-" * 80)
        
        for session in sessions:
            session_id = session['session_id']
            created = session['created_at']
            total = session['total_items']
            completed = session['completed_items']
            failed = session.get('failed_items', 0)
            progress = (completed / total * 100) if total > 0 else 0
            
            print(f"🆔 Session: {session_id}")
            print(f"📅 Created: {created}")
            print(f"📊 Progress: {completed}/{total} ({progress:.1f}%)")
            if failed > 0:
                print(f"❌ Failed: {failed}")
            print(f"📁 Output: {session['output_dir']}")
            print()
    
    async def resume_session(self, session_id: str) -> bool:
        """Resume a download session."""
        print(f"🔄 Resuming session: {session_id}")
        
        # Load session
        session = DownloadSession.load_state(session_id)
        if not session:
            print("❌ Session not found")
            return False
        
        remaining_items = session.get_remaining_items()
        if not remaining_items:
            print("✅ Session already completed")
            return True
        
        print(f"📥 Resuming download of {len(remaining_items)} remaining items")
        
        # Continue with remaining items
        output_path = Path(session.output_dir)
        success_count = 0
        failed_count = 0
        
        for i, item in enumerate(remaining_items, 1):
            if self.downloader.cancelled:
                break
            
            try:
                success, file_size = await self.downloader.download_media_item_async(
                    item, output_path
                )
                
                if success:
                    success_count += 1
                    session.mark_completed(item['id'])
                else:
                    failed_count += 1
                    session.mark_failed(item['id'])
                
                # Update progress
                total_remaining = len(remaining_items)
                percentage = (i / total_remaining) * 100
                print(f"\r📥 Progress: {i}/{total_remaining} ({percentage:.1f}%)", end="", flush=True)
                
                # Save state periodically
                if i % 10 == 0:
                    session.save_state()
            
            except KeyboardInterrupt:
                print("\n\n⏹️  Download cancelled by user")
                break
            except Exception as e:
                print(f"\n❌ Error downloading {item.get('filename', 'unknown')}: {e}")
                failed_count += 1
                session.mark_failed(item['id'])
        
        # Final status
        session.save_state()
        print(f"\n\n📊 Resume Summary:")
        print(f"✅ Successfully downloaded: {success_count} items")
        if failed_count > 0:
            print(f"❌ Failed downloads: {failed_count} items")
        
        return success_count > 0


def parse_date(date_str: str) -> datetime:
    """Parse date string in various formats."""
    formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%d/%m/%Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Invalid date format: {date_str}")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Google Photos Downloader - CLI Mode',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List albums
  python cli_mode.py --list-albums
  
  # Download by date range
  python cli_mode.py --start-date 2023-01-01 --end-date 2023-12-31 --output downloads/2023
  
  # Download specific album
  python cli_mode.py --album-id ABC123XYZ --output downloads/album
  
  # List sessions
  python cli_mode.py --list-sessions
  
  # Resume session
  python cli_mode.py --resume SESSION_ID
        """
    )
    
    # Authentication
    parser.add_argument('--no-auth', action='store_true', help='Skip authentication (for listing sessions)')
    
    # Actions
    parser.add_argument('--list-albums', action='store_true', help='List all available albums')
    parser.add_argument('--list-sessions', action='store_true', help='List download sessions')
    parser.add_argument('--resume', metavar='SESSION_ID', help='Resume a download session')
    
    # Download options
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--album-id', type=str, help='Album ID to download')
    parser.add_argument('--output', type=str, default='downloads', help='Output directory')
    parser.add_argument('--media-types', nargs='+', choices=['PHOTO', 'VIDEO'], 
                       default=['PHOTO', 'VIDEO'], help='Media types to download')
    
    # Convenience options
    parser.add_argument('--last-30-days', action='store_true', help='Download photos from last 30 days')
    parser.add_argument('--last-year', action='store_true', help='Download photos from last year')
    
    args = parser.parse_args()
    
    cli = CLIDownloader()
    cli.print_header()
    
    # Handle non-auth actions
    if args.list_sessions:
        cli.list_sessions()
        return 0
    
    # Authenticate (unless skipped)
    if not args.no_auth:
        if not cli.authenticate():
            return 1
    
    try:
        # List albums
        if args.list_albums:
            success = await cli.list_albums()
            return 0 if success else 1
        
        # Resume session
        if args.resume:
            if not cli.downloader:
                print("❌ Authentication required for resume")
                return 1
            success = await cli.resume_session(args.resume)
            return 0 if success else 1
        
        # Date range downloads
        if args.start_date and args.end_date:
            try:
                start_date = parse_date(args.start_date)
                end_date = parse_date(args.end_date)
                success = await cli.download_by_date_range(
                    start_date, end_date, args.output, args.media_types
                )
                return 0 if success else 1
            except ValueError as e:
                print(f"❌ Date error: {e}")
                return 1
        
        # Convenience date ranges
        if args.last_30_days:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            success = await cli.download_by_date_range(
                start_date, end_date, args.output, args.media_types
            )
            return 0 if success else 1
        
        if args.last_year:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            success = await cli.download_by_date_range(
                start_date, end_date, args.output, args.media_types
            )
            return 0 if success else 1
        
        # Album download
        if args.album_id:
            success = await cli.download_by_album(args.album_id, args.output)
            return 0 if success else 1
        
        # No action specified
        parser.print_help()
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled by user")
        return 130


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(130)