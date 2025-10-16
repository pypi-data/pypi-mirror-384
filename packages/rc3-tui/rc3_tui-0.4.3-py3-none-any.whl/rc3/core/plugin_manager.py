"""
Plugin manager with auto-discovery and loading
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Dict, Any

from textual.widgets import Static


class PluginManager:
    """Discovers and manages plugins"""
    
    def __init__(self, app):
        self.app = app
        self.plugins: Dict[str, Any] = {}
        self.plugins_dir = Path(__file__).parent.parent / "plugins"
    
    def load_plugins(self):
        """Auto-discover and load all plugins"""
        if not self.plugins_dir.exists():
            self.app.notify("Plugins directory not found", severity="warning")
            return
        
        # Import plugins package to discover modules
        import rc3.plugins
        
        # Find all Python files in plugins directory
        for importer, modname, ispkg in pkgutil.iter_modules(rc3.plugins.__path__):
            if modname.startswith('_'):
                continue
            
            try:
                # Import the plugin module
                module = importlib.import_module(f'rc3.plugins.{modname}')
                
                # Look for Plugin class
                if hasattr(module, 'Plugin'):
                    plugin_class = getattr(module, 'Plugin')
                    plugin_instance = plugin_class(self.app)
                    self.plugins[modname] = plugin_instance
                    
            except Exception as e:
                self.app.notify(f"Failed to load plugin {modname}: {e}", severity="error")
    
    def reload(self):
        """Reload all plugins"""
        self.plugins.clear()
        self.load_plugins()
    
    def render_plugin(self, plugin_name: str):
        """Render a specific plugin's UI"""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name].render()
        else:
            return Static(f"Plugin '{plugin_name}' not found", classes="error")
    
    def get_plugin(self, plugin_name: str):
        """Get a plugin instance by name"""
        return self.plugins.get(plugin_name)


