"""
Base plugin class for creating new plugins
"""

from abc import ABC, abstractmethod


class BasePlugin(ABC):
    """Base class for all RC3 plugins"""
    
    name = "Base Plugin"
    description = "Plugin description"
    version = "0.1.0"
    enabled = True
    
    def __init__(self, app):
        self.app = app
        self.config = app.config
    
    @abstractmethod
    def render(self):
        """Render the plugin's UI - must be implemented by subclass"""
        pass
    
    def on_load(self):
        """Called when plugin is loaded"""
        pass
    
    def on_unload(self):
        """Called when plugin is unloaded"""
        pass



