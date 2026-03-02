#!/usr/bin/env python3
"""
Configuration Manager for Blender Render Monitor
Handles reading and writing persistent configuration settings
"""

import json
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


# Global config instance
_config_instance = None

def get_config() -> ConfigManager:
    """Get global config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
