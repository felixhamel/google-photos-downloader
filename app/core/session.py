"""
ABOUTME: Download session management with state persistence
ABOUTME: Handles download progress tracking and resume capability
"""
import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class DownloadSession:
    """Manages download session state and persistence."""
    
    def __init__(self, session_id: str = None):
        """Initialize download session."""
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.total_items = 0
        self.completed_items = 0
        self.failed_items = 0
        self.output_dir = ""
        self.download_params = {}
        self.media_items = []
        self.completed_item_ids = set()
        self.failed_item_ids = set()
        self.session_dir = Path("sessions") / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
    
    def save_state(self) -> None:
        """Save session state to disk."""
        self.last_updated = datetime.now()
        
        state = {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'total_items': self.total_items,
            'completed_items': self.completed_items,
            'failed_items': self.failed_items,
            'output_dir': self.output_dir,
            'download_params': self.download_params,
            'media_items': self.media_items,
            'completed_item_ids': list(self.completed_item_ids),
            'failed_item_ids': list(self.failed_item_ids)
        }
        
        state_file = self.session_dir / "state.json"
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    @classmethod
    def load_state(cls, session_id: str) -> Optional['DownloadSession']:
        """Load session state from disk."""
        session_dir = Path("sessions") / session_id
        state_file = session_dir / "state.json"
        
        if not state_file.exists():
            return None
        
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            session = cls(session_id)
            session.created_at = datetime.fromisoformat(state['created_at'])
            session.last_updated = datetime.fromisoformat(state['last_updated'])
            session.total_items = state['total_items']
            session.completed_items = state['completed_items']
            session.failed_items = state.get('failed_items', 0)
            session.output_dir = state['output_dir']
            session.download_params = state['download_params']
            session.media_items = state['media_items']
            session.total_items = len(session.media_items)
            session.completed_item_ids = set(state['completed_item_ids'])
            session.failed_item_ids = set(state.get('failed_item_ids', []))
            
            return session
            
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None
    
    @classmethod
    def list_sessions(cls) -> List[Dict[str, Any]]:
        """List all available sessions."""
        sessions_dir = Path("sessions")
        if not sessions_dir.exists():
            return []
        
        sessions = []
        for session_dir in sessions_dir.iterdir():
            if session_dir.is_dir():
                state_file = session_dir / "state.json"
                if state_file.exists():
                    try:
                        with open(state_file, 'r') as f:
                            state = json.load(f)
                        sessions.append(state)
                    except Exception:
                        continue
        
        # Sort by last updated (newest first)
        sessions.sort(key=lambda x: x.get('last_updated', ''), reverse=True)
        return sessions
    
    def mark_completed(self, item_id: str) -> None:
        """Mark an item as completed."""
        self.completed_item_ids.add(item_id)
        self.completed_items = len(self.completed_item_ids)
    
    def mark_failed(self, item_id: str) -> None:
        """Mark an item as failed."""
        self.failed_item_ids.add(item_id)
        self.failed_items = len(self.failed_item_ids)
    
    def get_remaining_items(self) -> List[Dict[str, Any]]:
        """Get list of items not yet downloaded."""
        if not self.media_items:
            return []
        
        completed_and_failed = self.completed_item_ids.union(self.failed_item_ids)
        return [
            item for item in self.media_items 
            if item['id'] not in completed_and_failed
        ]
    
    def cleanup(self) -> None:
        """Clean up session files."""
        import shutil
        if self.session_dir.exists():
            shutil.rmtree(self.session_dir)