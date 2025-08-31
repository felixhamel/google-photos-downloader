"""
WebSocket connection manager for real-time updates
"""
import json
from typing import Dict, List
from fastapi import WebSocket
from datetime import datetime

from models.schemas import ProgressUpdate, StatusMessage


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Dict of session_id -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        
        self.active_connections[session_id].append(websocket)
        print(f"WebSocket connected for session: {session_id}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            
            # Clean up empty session lists
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        
        print(f"WebSocket disconnected for session: {session_id}")
    
    async def send_personal_message(self, session_id: str, message: str):
        """Send a message to all connections for a specific session."""
        if session_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[session_id]:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    print(f"Failed to send message to WebSocket: {e}")
                    disconnected.append(websocket)
            
            # Clean up disconnected websockets
            for ws in disconnected:
                self.disconnect(ws, session_id)
    
    async def send_progress_update(self, session_id: str, current: int, total: int, 
                                 percentage: float, speed_mbps: float, eta_seconds: int, status: str):
        """Send a progress update to all connections for a session."""
        update = ProgressUpdate(
            session_id=session_id,
            current=current,
            total=total,
            percentage=percentage,
            speed_mbps=speed_mbps,
            eta_seconds=eta_seconds,
            status=status
        )
        
        message = {
            "type": "progress",
            "data": update.dict()
        }
        
        await self.send_personal_message(session_id, json.dumps(message))
    
    async def send_status_message(self, session_id: str, message: str, level: str = "info"):
        """Send a status message to all connections for a session."""
        status = StatusMessage(
            session_id=session_id,
            message=message,
            level=level
        )
        
        message_data = {
            "type": "status",
            "data": status.dict()
        }
        
        await self.send_personal_message(session_id, json.dumps(message_data))
    
    async def broadcast_to_all(self, message: str):
        """Send a message to all active connections."""
        for session_id in self.active_connections:
            await self.send_personal_message(session_id, message)