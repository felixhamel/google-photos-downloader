"""
ABOUTME: Configuration management for Google Photos downloader
ABOUTME: Handles app settings, user preferences, and environment configuration
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration manager."""
        self.config_file = Path(config_file)
        self.config = self._load_default_config()
        
        # Load existing config if available
        if self.config_file.exists():
            self.load_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        return {
            "download": {
                "max_workers": 5,
                "timeout": 30,
                "chunk_size": 8192,
                "retry_attempts": 3,
                "retry_delay": 2,
                "output_dir": "downloads"
            },
            "api": {
                "credentials_file": "credentials.json",
                "token_file": "token.json",
                "scopes": ["https://www.googleapis.com/auth/photoslibrary.readonly"]
            },
            "app": {
                "debug": False,
                "log_level": "INFO",
                "session_cleanup_days": 7
            }
        }
    
    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                saved_config = json.load(f)
                # Merge with defaults (keeping any new defaults)
                self._merge_config(self.config, saved_config)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
    
    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def _merge_config(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config_section = self.config
        
        # Navigate to the parent section
        for k in keys[:-1]:
            if k not in config_section:
                config_section[k] = {}
            config_section = config_section[k]
        
        # Set the final value
        config_section[keys[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self.config.get(section, {})
    
    def update_section(self, section: str, updates: Dict[str, Any]) -> None:
        """Update entire configuration section."""
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section].update(updates)