"""
Configuration manager for loading YAML configs
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".rc3"
        self.config_file = self.config_dir / "config.yaml"
        self.commands_file = self.config_dir / "commands.yaml"
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize default configs if they don't exist
        self._init_defaults()
        
        # Load configurations
        self.config = self._load_yaml(self.config_file)
        self.commands = self._load_yaml(self.commands_file)
    
    def _init_defaults(self):
        """Create default config files if they don't exist"""
        if not self.config_file.exists():
            default_config = {
                "theme": "dark",
                "plugins": {
                    "enabled": ["quick_commands", "system_info", "working_directory"]
                }
            }
            self._save_yaml(self.config_file, default_config)
        
        if not self.commands_file.exists():
            default_commands = {
                "quick_commands": [
                    {
                        "name": "List Files",
                        "shortcut": "l",
                        "command": "Get-ChildItem | Format-Table Name, Length, LastWriteTime",
                        "shell": "powershell",
                        "description": "List files in current directory"
                    }
                ]
            }
            self._save_yaml(self.commands_file, default_commands)
    
    def _load_yaml(self, filepath: Path) -> Dict[str, Any]:
        """Load YAML file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            return {}
    
    def _save_yaml(self, filepath: Path, data: Dict[str, Any]):
        """Save YAML file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        except Exception as e:
            pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def get_commands(self, category: str = "quick_commands") -> list:
        """Get commands for a category"""
        return self.commands.get(category, [])
    
    def get_favorites(self) -> list:
        """Get list of favorite directory paths"""
        return self.config.get("favorites", [])
    
    def add_favorite(self, path: str) -> bool:
        """Add a directory to favorites (no duplicates). Returns True if added."""
        favorites = self.get_favorites()
        
        # Normalize path
        normalized_path = str(Path(path).resolve())
        
        # Check for duplicates
        if normalized_path in favorites:
            return False
        
        favorites.append(normalized_path)
        self.config["favorites"] = favorites
        self.save_config()
        return True
    
    def remove_favorite(self, path: str) -> bool:
        """Remove a directory from favorites. Returns True if removed."""
        favorites = self.get_favorites()
        
        # Normalize path
        normalized_path = str(Path(path).resolve())
        
        if normalized_path in favorites:
            favorites.remove(normalized_path)
            self.config["favorites"] = favorites
            self.save_config()
            return True
        
        return False
    
    def save_config(self):
        """Save current config back to file"""
        self._save_yaml(self.config_file, self.config)


