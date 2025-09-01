"""
WebSocket connection manager for real-time updates.
"""
from __future__ import annotations

import json
import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a WebSocket connection and add to session."""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        
        self.active_connections[session_id].add(websocket)
        print(f"WebSocket connected for session {session_id}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection from session."""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            
            # Clean up empty sessions
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        
        print(f"WebSocket disconnected for session {session_id}")
    
    async def send_progress_update(self, session_id: str, current: int, total: int, 
                                 percentage: float, speed: float, eta: Optional[int], 
                                 status: str = "downloading"):
        """Send progress update to all connections for a session."""
        if session_id not in self.active_connections:
            return
        
        eta_str = f"{eta//60}m {eta%60}s" if eta else "Calculating..."
        
        message = {
            "type": "progress",
            "session_id": session_id,
            "current": current,
            "total": total,
            "percentage": percentage,
            "speed": f"{speed:.1f} MB/s",
            "eta": eta_str,
            "status": status,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self._broadcast_to_session(session_id, message)
    
    async def send_status_message(self, session_id: str, message: str, 
                                level: str = "info"):
        """Send status message to all connections for a session."""
        if session_id not in self.active_connections:
            return
        
        status_message = {
            "type": "status",
            "session_id": session_id,
            "message": message,
            "level": level,  # info, warning, error, success
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self._broadcast_to_session(session_id, status_message)
    
    async def send_completion_message(self, session_id: str, total_downloaded: int, 
                                    total_failed: int, output_dir: str):
        """Send completion message to all connections for a session."""
        if session_id not in self.active_connections:
            return
        
        completion_message = {
            "type": "completion",
            "session_id": session_id,
            "total_downloaded": total_downloaded,
            "total_failed": total_failed,
            "output_dir": output_dir,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self._broadcast_to_session(session_id, completion_message)
    
    async def _broadcast_to_session(self, session_id: str, message: dict):
        """Broadcast message to all connections in a session."""
        if session_id not in self.active_connections:
            return
        
        connections = self.active_connections[session_id].copy()
        disconnected = []
        
        for connection in connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending message to WebSocket: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection, session_id)