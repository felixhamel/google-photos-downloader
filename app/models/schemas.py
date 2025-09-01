"""
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class MediaType(str, Enum):
    """Supported media types."""
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"


class SourceType(str, Enum):
    """Download source types."""
    DATE_RANGE = "date_range" 
    ALBUM = "album"


class DownloadRequest(BaseModel):
    """Request model for starting a download."""
    source_type: SourceType
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    album_id: Optional[str] = None
    media_types: List[MediaType] = [MediaType.PHOTO, MediaType.VIDEO]
    output_dir: str = Field(..., description="Output directory path")
    max_concurrent: int = Field(default=5, ge=1, le=20)


class ResumeRequest(BaseModel):
    """Request model for resuming a download."""
    session_id: str


class ApiResponse(BaseModel):
    """Generic API response."""
    success: bool
    message: str
    session_id: Optional[str] = None


class AuthStatus(BaseModel):
    """Authentication status response."""
    authenticated: bool
    message: str


class AlbumInfo(BaseModel):
    """Album information."""
    id: str
    title: str
    media_items_count: int
    cover_photo_url: Optional[str] = None


class SessionInfo(BaseModel):
    """Download session information."""
    session_id: str
    created_at: datetime
    last_updated: datetime
    total_items: int
    completed_items: int
    failed_items: int = 0
    output_dir: str
    progress_percentage: float


class ConfigUpdate(BaseModel):
    """Configuration update request."""
    section: str
    key: str
    value: Any


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)