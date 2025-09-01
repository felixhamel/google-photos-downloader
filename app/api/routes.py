"""
API routes for Google Photos Downloader
"""
from __future__ import annotations

import asyncio
from typing import List
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

try:
    from app.models.schemas import (
        DownloadRequest, ResumeRequest, ApiResponse, AuthStatus,
        AlbumInfo, SessionInfo, ConfigUpdate, ErrorResponse
    )
except ImportError:
    from models.schemas import (
        DownloadRequest, ResumeRequest, ApiResponse, AuthStatus,
        AlbumInfo, SessionInfo, ConfigUpdate, ErrorResponse
    )
try:
    from app.core.downloader import GooglePhotosDownloader
    from app.core.session import DownloadSession
    from app.core.config import ConfigManager
    from app.api.websockets import ConnectionManager
except ImportError:
    from core.downloader import GooglePhotosDownloader
    from core.session import DownloadSession
    from core.config import ConfigManager
    from api.websockets import ConnectionManager

router = APIRouter()
config = ConfigManager()
connection_manager = ConnectionManager()

# Global downloader instance
downloader = None


@router.get("/auth/status", response_model=AuthStatus)
async def get_auth_status():
    """Check authentication status with detailed error information."""
    global downloader
    
    try:
        if not downloader:
            downloader = GooglePhotosDownloader(config=config)
        
        # Get detailed status without triggering full authentication
        status_info = downloader.get_detailed_auth_status()
        
        return AuthStatus(**status_info)
        
    except Exception as e:
        return AuthStatus(
            authenticated=False,
            message="Error checking authentication status",
            error_type="status_check_error",
            error_details=str(e),
            suggestions=[
                "Check application logs for more details",
                "Ensure all required files are present",
                "Try restarting the application"
            ]
        )


@router.post("/auth/authenticate")
async def authenticate():
    """Trigger authentication process with detailed error handling."""
    global downloader
    
    try:
        if not downloader:
            downloader = GooglePhotosDownloader(config=config)
        
        # Capture status messages during authentication
        auth_messages = []
        
        def capture_status(message: str):
            auth_messages.append(message)
        
        downloader.set_callbacks(status_callback=capture_status)
        
        if downloader.authenticate():
            return ApiResponse(
                success=True,
                message="Authentication successful - Google Photos API access granted"
            )
        else:
            # Get detailed error information
            status_info = downloader.get_detailed_auth_status()
            
            error_detail = {
                "error_type": status_info.get('error_type', 'authentication_failed'),
                "error_details": status_info.get('error_details', 'Authentication process failed'),
                "suggestions": status_info.get('suggestions', []),
                "auth_messages": auth_messages[-10:]  # Last 10 messages
            }
            
            raise HTTPException(
                status_code=401, 
                detail=f"Authentication failed: {status_info.get('message', 'Unknown error')}"
            )
            
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        # Get detailed error information for unexpected errors
        try:
            status_info = downloader.get_detailed_auth_status() if downloader else {}
            error_detail = {
                "error_type": "unexpected_error",
                "error_details": str(e),
                "suggestions": status_info.get('suggestions', [
                    "Check application logs for more details",
                    "Ensure all required files are present",
                    "Try restarting the application"
                ])
            }
        except:
            error_detail = {"error_type": "critical_error", "error_details": str(e)}
        
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")


@router.get("/albums", response_model=List[AlbumInfo])
async def get_albums():
    """Get list of albums from Google Photos."""
    global downloader
    
    try:
        if not downloader or not downloader.service:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        albums = await downloader.get_albums_async()
        return [
            AlbumInfo(
                id=album['id'],
                title=album.get('title', 'Untitled'),
                media_items_count=int(album.get('mediaItemsCount', 0)),
                cover_photo_url=album.get('coverPhotoBaseUrl')
            )
            for album in albums
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download/start")
async def start_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Start a new download."""
    global downloader
    
    try:
        if not downloader or not downloader.service:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Create new session
        session = DownloadSession()
        session.output_dir = request.output_dir
        session.download_params = request.dict()
        
        # Set up callbacks for real-time updates - FIXED asyncio issue
        async def progress_callback(current, total, percentage, speed, eta):
            await connection_manager.send_progress_update(
                session.session_id, current, total, percentage, speed, eta, "downloading"
            )
        
        async def status_callback(message):
            await connection_manager.send_status_message(session.session_id, message)
        
        downloader.set_callbacks(progress_callback, status_callback)
        
        # Start download in background
        background_tasks.add_task(
            _run_download,
            downloader, session, request
        )
        
        return ApiResponse(
            success=True,
            message="Download started",
            session_id=session.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download/resume")
async def resume_download(request: ResumeRequest, background_tasks: BackgroundTasks):
    """Resume a download session."""
    global downloader
    
    try:
        if not downloader or not downloader.service:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Load session
        session = DownloadSession.load_state(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Set up callbacks - FIXED asyncio issue
        async def progress_callback(current, total, percentage, speed, eta):
            await connection_manager.send_progress_update(
                session.session_id, current, total, percentage, speed, eta, "resuming"
            )
        
        async def status_callback(message):
            await connection_manager.send_status_message(session.session_id, message)
        
        downloader.set_callbacks(progress_callback, status_callback)
        
        # Resume download in background
        background_tasks.add_task(_resume_download, downloader, session)
        
        return ApiResponse(
            success=True,
            message="Download resumed",
            session_id=session.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download/cancel/{session_id}")
async def cancel_download(session_id: str):
    """Cancel a download session."""
    global downloader
    
    try:
        if downloader:
            downloader.cancel_download()
        
        # Notify via WebSocket
        await connection_manager.send_status_message(
            session_id, "Download cancelled by user", "warning"
        )
        
        return ApiResponse(
            success=True,
            message="Download cancelled"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[SessionInfo])
async def get_sessions():
    """Get list of available download sessions."""
    try:
        sessions_data = DownloadSession.list_sessions()
        return [
            SessionInfo(
                session_id=s['session_id'],
                created_at=s['created_at'],
                last_updated=s['last_updated'],
                total_items=s['total_items'],
                completed_items=s['completed_items'],
                failed_items=s.get('failed_items', 0),
                output_dir=s['output_dir'],
                progress_percentage=(s['completed_items'] / s['total_items'] * 100) if s['total_items'] > 0 else 0
            )
            for s in sessions_data
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a download session."""
    try:
        session = DownloadSession()
        session.session_id = session_id
        session.cleanup()
        
        return ApiResponse(
            success=True,
            message="Session deleted"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{section}")
async def get_config_section(section: str):
    """Get configuration section."""
    try:
        return config.get_section(section)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/update")
async def update_config(request: ConfigUpdate):
    """Update configuration."""
    try:
        config.set(f"{request.section}.{request.key}", request.value)
        config.save_config()
        
        return ApiResponse(
            success=True,
            message="Configuration updated"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _run_download(downloader: GooglePhotosDownloader, session: DownloadSession, request: DownloadRequest):
    """Background task to run download."""
    try:
        media_types = [mt.value for mt in request.media_types]
        
        if request.source_type.value == "date_range":
            # Get media items for date range
            media_items = await downloader.get_media_items_async(
                start_date=request.start_date,
                end_date=request.end_date,
                media_types=media_types
            )
        elif request.source_type.value == "album":
            # Get media items for album
            media_items = await downloader.get_media_items_async(
                album_id=request.album_id
            )
        else:
            raise ValueError("Invalid source type")
        
        if not media_items:
            await connection_manager.send_status_message(
                session.session_id, "No items found for the specified criteria", "warning"
            )
            return
        
        session.media_items = media_items
        session.total_items = len(media_items)
        session.save_state()
        
        # Start downloading
        await _download_items(downloader, session, media_items)
        
    except Exception as e:
        await connection_manager.send_status_message(
            session.session_id, f"Download error: {str(e)}", "error"
        )


async def _resume_download(downloader: GooglePhotosDownloader, session: DownloadSession):
    """Background task to resume download."""
    try:
        remaining_items = session.get_remaining_items()
        if not remaining_items:
            await connection_manager.send_status_message(
                session.session_id, "No remaining items to download", "info"
            )
            return
        
        await _download_items(downloader, session, remaining_items)
        
    except Exception as e:
        await connection_manager.send_status_message(
            session.session_id, f"Resume error: {str(e)}", "error"
        )


async def _download_items(downloader: GooglePhotosDownloader, session: DownloadSession, items: list):
    """Download items with concurrent workers - FIXED asyncio conflicts."""
    from pathlib import Path
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import asyncio
    import functools
    
    output_path = Path(session.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    max_workers = config.get('download.max_workers', 5)
    success_count = 0
    failed_count = 0
    
    # Get current event loop
    loop = asyncio.get_event_loop()
    
    # Use ThreadPoolExecutor for concurrent downloads
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit download tasks - run in executor to avoid blocking
        future_to_item = {}
        for item in items:
            if downloader.cancelled:
                break
            
            # Use loop.run_in_executor instead of creating new event loops
            future = loop.run_in_executor(
                executor,
                functools.partial(_download_item_sync_fixed, downloader, item, output_path)
            )
            future_to_item[future] = item
        
        # Process completed downloads
        completed = 0
        total_items = len(items)
        
        for future in asyncio.as_completed(future_to_item.keys()):
            if downloader.cancelled:
                break
            
            item = future_to_item[future]
            try:
                success, file_size = await future
                completed += 1
                
                # Update progress
                percentage = (completed / total_items) * 100
                downloader.stats.update(file_size)
                
                # Send progress update via WebSocket
                await connection_manager.send_progress_update(
                    session.session_id, completed, total_items, percentage,
                    downloader.stats.get_speed_mbps(), downloader.stats.get_eta_seconds(),
                    "downloading"
                )
                
                if success:
                    success_count += 1
                    session.mark_completed(item['id'])
                else:
                    failed_count += 1
                    session.mark_failed(item['id'])
                
                # Save state periodically
                if completed % 10 == 0:
                    session.save_state()
                
            except Exception as e:
                failed_count += 1
                session.mark_failed(item['id'])
                await connection_manager.send_status_message(
                    session.session_id, f"Error downloading {item.get('filename', 'unknown')}: {str(e)}", "error"
                )
    
    # Final status
    session.save_state()
    
    if success_count > 0:
        await connection_manager.send_status_message(
            session.session_id, f"Download complete! {success_count} items downloaded successfully.", "success"
        )
        # Clean up completed session
        if failed_count == 0:
            session.cleanup()
    
    if failed_count > 0:
        await connection_manager.send_status_message(
            session.session_id, f"{failed_count} items failed to download.", "warning"
        )


def _download_item_sync_fixed(downloader: GooglePhotosDownloader, item: dict, output_path: Path):
    """Synchronous download without creating new event loops."""
    try:
        # Convert async method to sync using requests directly
        filename = item['filename']
        media_metadata = item['mediaMetadata']
        
        # Create safe filename with timestamp
        from datetime import datetime
        import os
        
        creation_time = media_metadata['creationTime']
        timestamp = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
        safe_timestamp = timestamp.strftime('%Y%m%d_%H%M%S')
        
        name, ext = os.path.splitext(filename)
        safe_filename = f"{safe_timestamp}_{name}{ext}"
        file_path = output_path / safe_filename
        
        # Skip if exact file already exists
        if file_path.exists():
            existing_size = file_path.stat().st_size
            return True, existing_size
        
        # Determine download URL based on media type
        if 'photo' in media_metadata:
            download_url = f"{item['baseUrl']}=d"  # Original quality photo
        elif 'video' in media_metadata:
            download_url = f"{item['baseUrl']}=dv"  # Original quality video
        else:
            return False, 0
        
        # Download with retry logic
        import requests
        import time
        
        max_retries = 3
        for attempt in range(max_retries):
            if downloader.cancelled:
                return False, 0
                
            try:
                timeout = downloader.config.get('download.timeout', 30)
                chunk_size = downloader.config.get('download.chunk_size', 8192)
                
                response = requests.get(download_url, stream=True, timeout=timeout)
                response.raise_for_status()
                
                # Create temporary file first
                temp_file = file_path.with_suffix(f"{file_path.suffix}.tmp")
                file_size = 0
                
                with open(temp_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if downloader.cancelled:
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
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return False, 0
        
        return False, 0
        
    except Exception as e:
        return False, 0