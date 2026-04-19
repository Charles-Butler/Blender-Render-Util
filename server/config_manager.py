#!/usr/bin/env python3
"""
Configuration Manager for Blender Render Monitor
Handles reading and writing persistent configuration settings
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """Manages application configuration with persistent storage"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize config manager

        Args:
            config_path: Path to config file (defaults to config.json in same directory)
        """
        if config_path is None:
            import os
            config_dir = os.environ.get('RENDER_MANAGER_CONFIG_DIR')
            if config_dir:
                config_path = Path(config_dir) / "config.json"
            else:
                config_path = Path(__file__).parent / "config.json"

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file, creating default if doesn't exist"""
        if not self.config_path.exists():
            return self._create_default_config()

        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading config: {e}")
            return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        default_config = {
            "blender": {
                "executable_path": "/Applications/Blender.app/Contents/MacOS/Blender",
                "last_blend_file": "",
                "recent_blend_files": []
            },
            "render": {
                "last_project_name": "",
                "default_output_dir": "./renders",
                "last_batch_count": 0
            },
            "current_render": {
                "project_name": "",
                "blend_file": "",
                "configured_batches": [],
                "total_frames": 0,
                "status": "idle",
                "log_file": "",
                "output_dir": "",
                "timestamp": ""
            },
            "server": {
                "default_port": 8081,
                "host": "0.0.0.0"
            },
            "ui": {
                "theme": "dark",
                "auto_start_monitoring": True
            }
        }

        # Save default config
        self._save_config(default_config)
        return default_config

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving config: {e}")

    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation

        Args:
            *keys: Path to config value (e.g., 'blender', 'executable_path')
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, *keys: str, value: Any) -> None:
        """
        Set configuration value using dot notation

        Args:
            *keys: Path to config value (e.g., 'blender', 'executable_path')
            value: Value to set
        """
        if len(keys) == 0:
            return

        # Navigate to parent dict
        current = self.config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set value
        current[keys[-1]] = value

        # Save to file
        self._save_config(self.config)

    def add_recent_blend_file(self, filepath: str) -> None:
        """
        Add a blend file to recent files list

        Args:
            filepath: Path to blend file
        """
        recent = self.get('blender', 'recent_blend_files', default=[])

        # Remove if already exists
        if filepath in recent:
            recent.remove(filepath)

        # Add to front
        recent.insert(0, filepath)

        # Keep only last 10
        recent = recent[:10]

        # Update config
        self.set('blender', 'recent_blend_files', value=recent)
        self.set('blender', 'last_blend_file', value=filepath)

    def get_recent_blend_files(self) -> list:
        """Get list of recent blend files"""
        return self.get('blender', 'recent_blend_files', default=[])

    def get_last_blend_file(self) -> str:
        """Get last used blend file"""
        return self.get('blender', 'last_blend_file', default='')

    def get_blender_executable(self) -> str:
        """Get Blender executable path"""
        return self.get('blender', 'executable_path', default='/Applications/Blender.app/Contents/MacOS/Blender')

    def set_blender_executable(self, path: str) -> None:
        """Set Blender executable path"""
        self.set('blender', 'executable_path', value=path)

    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration"""
        return self.config

    def update_render_settings(self, project_name: str, batch_count: int) -> None:
        """Update render settings"""
        self.set('render', 'last_project_name', value=project_name)
        self.set('render', 'last_batch_count', value=batch_count)

    def save_active_render(self, render_config: Dict[str, Any]) -> None:
        """
        Save active render configuration for persistence across restarts

        Args:
            render_config: Full render configuration including batches
        """
        self.set('monitoring', 'active_render', value=render_config)
        self.set('monitoring', 'current_log_file', value=render_config.get('log_file', ''))

    def get_active_render(self) -> Optional[Dict[str, Any]]:
        """Get active render configuration if one exists"""
        return self.get('monitoring', 'active_render', default=None)

    def clear_active_render(self) -> None:
        """Clear active render configuration"""
        if 'monitoring' in self.config:
            if 'active_render' in self.config['monitoring']:
                del self.config['monitoring']['active_render']
            self._save_config(self.config)

    def save_batch_profile(self, profile_name: str, batches: list) -> None:
        """
        Save a batch profile for reuse

        Args:
            profile_name: Name for this profile (e.g., "last", "default", custom name)
            batches: List of batch configurations
        """
        if 'batch_profiles' not in self.config:
            self.config['batch_profiles'] = {}

        self.config['batch_profiles'][profile_name] = {
            'batches': batches,
            'saved_at': datetime.now().isoformat(),
            'total_frames': sum(b['end'] - b['start'] + 1 for b in batches),
            'batch_count': len(batches)
        }
        self._save_config(self.config)

    def get_batch_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a saved batch profile

        Args:
            profile_name: Name of the profile to retrieve

        Returns:
            Profile data or None if not found
        """
        return self.get('batch_profiles', profile_name, default=None)

    def get_all_batch_profiles(self) -> Dict[str, Any]:
        """Get all saved batch profiles"""
        return self.get('batch_profiles', default={})

    def delete_batch_profile(self, profile_name: str) -> bool:
        """
        Delete a batch profile

        Args:
            profile_name: Name of profile to delete

        Returns:
            True if deleted, False if not found
        """
        if 'batch_profiles' in self.config and profile_name in self.config['batch_profiles']:
            del self.config['batch_profiles'][profile_name]
            self._save_config(self.config)
            return True
        return False

    def update_current_render(self, render_data: Dict[str, Any]) -> None:
        """
        Update current render configuration in config.json
        This is the primary storage for render state - faster than memory

        Args:
            render_data: Render configuration data
        """
        if 'current_render' not in self.config:
            self.config['current_render'] = {}

        # Merge with existing data
        self.config['current_render'].update(render_data)
        self._save_config(self.config)

    def get_current_render(self) -> Dict[str, Any]:
        """Get current render configuration from config.json"""
        return self.get('current_render', default={
            'project_name': '',
            'blend_file': '',
            'configured_batches': [],
            'total_frames': 0,
            'status': 'idle',
            'log_file': '',
            'output_dir': '',
            'timestamp': ''
        })

    def clear_current_render(self) -> None:
        """Clear current render configuration"""
        self.config['current_render'] = {
            'project_name': '',
            'blend_file': '',
            'configured_batches': [],
            'total_frames': 0,
            'status': 'idle',
            'log_file': '',
            'output_dir': '',
            'timestamp': ''
        }
        self._save_config(self.config)


# Global config instance
_config_instance = None

def get_config() -> ConfigManager:
    """Get global config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
