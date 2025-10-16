"""
File Browser Plugin - Navigate and manage files
"""

import os
from pathlib import Path
from textual.widgets import Static, Button, Input, DirectoryTree
from textual.containers import Vertical, Horizontal
from textual.message import Message

from rc3.plugins.base import BasePlugin


class Plugin(BasePlugin):
    """File browser and management plugin"""
    
    name = "File Browser"
    description = "Navigate and manage files"
    
    def render(self):
        """Render the file browser interface"""
        browser_text = "File Browser\n\n"
        
        # Current directory
        current_dir = Path.cwd()
        browser_text += f"Current: {current_dir}\n\n"
        
        # Quick navigation
        browser_text += "Quick Navigation:\n"
        common_dirs = [
            {"name": "Home", "path": str(Path.home())},
            {"name": "Sandbox", "path": "C:/Users/rc3/Documents/sandbox"},
            {"name": "Desktop", "path": str(Path.home() / "Desktop")},
            {"name": "Documents", "path": str(Path.home() / "Documents")},
            {"name": "Downloads", "path": str(Path.home() / "Downloads")},
        ]
        
        for i, dir_info in enumerate(common_dirs, 1):
            browser_text += f"  {i}. {dir_info['name']}\n"
        
        browser_text += "\nCurrent Directory Contents:\n"
        
        try:
            # List current directory contents
            items = list(current_dir.iterdir())
            items.sort(key=lambda x: (x.is_file(), x.name.lower()))
            
            for item in items[:20]:  # Limit to 20 items
                if item.is_dir():
                    browser_text += f"  [DIR]  {item.name}/\n"
                else:
                    size = item.stat().st_size if item.is_file() else 0
                    browser_text += f"  [FILE] {item.name} ({size} bytes)\n"
            
            if len(items) > 20:
                browser_text += f"  ... and {len(items) - 20} more items\n"
                
        except Exception as e:
            browser_text += f"  Error listing directory: {e}\n"
        
        browser_text += "\nFile Operations:\n"
        browser_text += "  Refresh\n"
        browser_text += "  New File\n"
        browser_text += "  New Folder\n"
        browser_text += "  Delete\n"
        
        browser_text += "\nUse arrow keys to navigate • Enter to open • Tab to navigate"
        
        return Static(browser_text, classes="info")
    
    def _navigate_to(self, path: str):
        """Navigate to a specific directory"""
        try:
            target_path = Path(path)
            if target_path.exists() and target_path.is_dir():
                os.chdir(target_path)
                self.current_path.update(f"📍 Current: {target_path}")
                self.app.notify(f"Navigated to {target_path}", severity="information")
                
                # Refresh the directory tree
                tree = self.query_one("#dir-tree", DirectoryTree)
                tree.path = target_path
                tree.reload()
            else:
                self.app.notify(f"Directory not found: {path}", severity="error")
        except Exception as e:
            self.app.notify(f"Navigation failed: {e}", severity="error")
    
    def _file_operation(self, action: str):
        """Perform file operations"""
        if action == "refresh":
            try:
                tree = self.query_one("#dir-tree", DirectoryTree)
                tree.reload()
                self.app.notify("Directory tree refreshed", severity="information")
            except Exception as e:
                self.app.notify(f"Refresh failed: {e}", severity="error")
        elif action == "new_file":
            self.app.notify("New file creation coming soon", severity="information")
        elif action == "new_folder":
            self.app.notify("New folder creation coming soon", severity="information")
        elif action == "delete":
            self.app.notify("File deletion coming soon", severity="information")
