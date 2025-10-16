"""
Working Directory Plugin - Navigate directories and manage files
"""

import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from textual.widgets import Static, ListView, ListItem, Label, Input
from textual.containers import Vertical, Container, VerticalScroll
from textual.reactive import reactive
from textual.message import Message

from rc3.plugins.base import BasePlugin


class WorkingDirectoryChanged(Message):
    """Event fired when working directory is changed"""
    def __init__(self, new_directory: Path) -> None:
        self.new_directory = new_directory
        super().__init__()


class DirectoryListItem(ListItem):
    """Custom list item that stores file/folder metadata"""
    
    def __init__(self, path: Path, is_parent: bool = False, **kwargs):
        self.path = path
        self.is_parent = is_parent
        self.is_dir = path.is_dir() if not is_parent else True
        
        # Format display
        if is_parent:
            label_text = "[dim][D][/dim] .."
        else:
            prefix = "[cyan][D][/cyan]" if self.is_dir else "[green][F][/green]"
            name = path.name
            label_text = f"{prefix} {name}"
        
        super().__init__(Label(label_text), **kwargs)


class DirectoryNavigator(Vertical):
    """Main directory navigation widget"""
    
    can_focus = True
    
    current_path = reactive(Path.cwd())
    input_mode = reactive("")  # "", "create", "rename", "delete"
    input_target = reactive(None)
    
    def __init__(self):
        super().__init__()
        self.list_view = None
        self.path_header = None
        self.help_text = None
        self.input_widget = None
        self.input_prompt = None
    
    def compose(self):
        """Build the UI"""
        with Container(id="directory-container"):
            yield Static("[bold cyan]WORKING DIRECTORY[/bold cyan]", id="dir-title")
            yield Static(id="dir-path")
            yield ListView(id="dir-list")
            yield Static(id="dir-help")
            yield Static(id="input-prompt")
            yield Input(id="dir-input", placeholder="Enter value...")
    
    def on_mount(self):
        """Initialize after mount"""
        self.list_view = self.query_one("#dir-list", ListView)
        self.path_header = self.query_one("#dir-path", Static)
        self.help_text = self.query_one("#dir-help", Static)
        self.input_prompt = self.query_one("#input-prompt", Static)
        self.input_widget = self.query_one("#dir-input", Input)
        
        # Hide input initially
        self.input_widget.display = False
        self.input_prompt.display = False
        
        # Load current directory
        self.refresh_directory()
        self.update_help_text()
        
        # Focus this widget
        self.set_timer(0.01, lambda: self.focus())
    
    def watch_current_path(self, new_path: Path):
        """React to path changes"""
        self.refresh_directory()
        self.update_help_text()
    
    def watch_input_mode(self, new_mode: str):
        """React to input mode changes"""
        if new_mode:
            # Show input widgets
            self.input_widget.display = True
            self.input_prompt.display = True
            self.input_widget.value = ""
            
            # Set prompt text
            if new_mode == "create":
                self.input_prompt.update("[yellow]Create new folder:[/yellow]")
            elif new_mode == "rename":
                if self.input_target:
                    self.input_prompt.update(f"[yellow]Rename '{self.input_target.name}' to:[/yellow]")
                    self.input_widget.value = self.input_target.name
            elif new_mode == "delete":
                if self.input_target:
                    self.input_prompt.update(f"[red]Delete '{self.input_target.name}'? (y/N):[/red]")
            
            # Focus input
            self.input_widget.focus()
        else:
            # Hide input widgets
            self.input_widget.display = False
            self.input_prompt.display = False
            self.input_target = None
            self.focus()
        
        self.update_help_text()
    
    def refresh_directory(self):
        """Reload directory contents"""
        try:
            # Update path header
            self.path_header.update(f"[dim]{self.current_path}[/dim]")
            
            # Clear list
            self.list_view.clear()
            
            # Add parent directory entry if not at root
            if self.current_path.parent != self.current_path:
                self.list_view.append(DirectoryListItem(self.current_path.parent, is_parent=True))
            
            # List directories and files
            items = []
            try:
                for item in self.current_path.iterdir():
                    items.append(item)
            except PermissionError:
                self.app.notify("Permission denied reading directory", severity="error")
                return
            
            # Sort: directories first, then files, alphabetically
            dirs = sorted([i for i in items if i.is_dir()], key=lambda x: x.name.lower())
            files = sorted([i for i in items if i.is_file()], key=lambda x: x.name.lower())
            
            # Add to list
            for item in dirs + files:
                self.list_view.append(DirectoryListItem(item))
            
        except Exception as e:
            self.app.notify(f"Error reading directory: {str(e)}", severity="error")
    
    def update_help_text(self):
        """Update help text based on current mode"""
        if self.input_mode:
            self.help_text.update("[dim]Enter to confirm | Esc to cancel[/dim]")
        else:
            help_lines = [
                "[dim]↑↓jk Nav | ←h Parent | →l/Enter Open",
                "n New | r Rename | d Delete | o Open | e Explorer | s Set WorkDir[/dim]"
            ]
            self.help_text.update("\n".join(help_lines))
    
    def on_key(self, event) -> None:
        """Handle keyboard shortcuts"""
        key = event.key
        
        # Input mode handling
        if self.input_mode:
            if key == "escape":
                self.input_mode = ""
                event.prevent_default()
                event.stop()
            elif key == "enter":
                self.handle_input_submit()
                event.prevent_default()
                event.stop()
            return
        
        # Normal mode navigation
        if key == "j":
            if self.list_view.highlighted_child is None and len(self.list_view.children) > 0:
                self.list_view.index = 0
            else:
                self.list_view.action_cursor_down()
            event.prevent_default()
            event.stop()
        
        elif key == "k":
            if self.list_view.highlighted_child is None and len(self.list_view.children) > 0:
                self.list_view.index = 0
            else:
                self.list_view.action_cursor_up()
            event.prevent_default()
            event.stop()
        
        elif key == "down":
            if self.list_view.highlighted_child is None and len(self.list_view.children) > 0:
                self.list_view.index = 0
            else:
                self.list_view.action_cursor_down()
            event.prevent_default()
            event.stop()
        
        elif key == "up":
            if self.list_view.highlighted_child is None and len(self.list_view.children) > 0:
                self.list_view.index = 0
            else:
                self.list_view.action_cursor_up()
            event.prevent_default()
            event.stop()
        
        # Enter directory or open file
        elif key in ["enter", "l", "right"]:
            self.handle_enter_or_open()
            event.prevent_default()
            event.stop()
        
        # Go to parent directory
        elif key in ["h", "left", "backspace"]:
            self.go_to_parent()
            event.prevent_default()
            event.stop()
        
        # File operations
        elif key == "n":
            self.start_create_folder()
            event.prevent_default()
            event.stop()
        
        elif key == "r":
            self.start_rename()
            event.prevent_default()
            event.stop()
        
        elif key == "d":
            self.start_delete()
            event.prevent_default()
            event.stop()
        
        elif key == "o":
            self.open_in_system()
            event.prevent_default()
            event.stop()
        
        elif key == "s":
            self.set_working_directory()
            event.prevent_default()
            event.stop()
        
        elif key == "e":
            self.open_in_explorer()
            event.prevent_default()
            event.stop()
    
    def get_selected_item(self):
        """Get currently selected DirectoryListItem"""
        if self.list_view.highlighted_child:
            item = self.list_view.highlighted_child
            if isinstance(item, DirectoryListItem):
                return item
        return None
    
    def handle_enter_or_open(self):
        """Enter directory or open file"""
        item = self.get_selected_item()
        if not item:
            return
        
        if item.is_parent:
            self.go_to_parent()
        elif item.is_dir:
            # Navigate into directory
            self.current_path = item.path
        else:
            # Open file with system default
            self.open_in_system()
    
    def go_to_parent(self):
        """Navigate to parent directory"""
        parent = self.current_path.parent
        if parent != self.current_path:
            self.current_path = parent
    
    def start_create_folder(self):
        """Start create folder input mode"""
        self.input_mode = "create"
        self.input_target = None
    
    def start_rename(self):
        """Start rename input mode"""
        item = self.get_selected_item()
        if not item or item.is_parent:
            self.app.notify("Select an item to rename", severity="warning")
            return
        
        self.input_mode = "rename"
        self.input_target = item.path
    
    def start_delete(self):
        """Start delete confirmation mode"""
        item = self.get_selected_item()
        if not item or item.is_parent:
            self.app.notify("Select an item to delete", severity="warning")
            return
        
        self.input_mode = "delete"
        self.input_target = item.path
    
    def open_in_system(self):
        """Open selected item with system default application"""
        item = self.get_selected_item()
        if not item or item.is_parent:
            return
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(str(item.path))
            elif os.name == 'posix':  # Linux/Mac
                import subprocess
                if os.uname().sysname == 'Darwin':  # Mac
                    subprocess.run(['open', str(item.path)])
                else:  # Linux
                    subprocess.run(['xdg-open', str(item.path)])
            
            self.app.notify(f"Opened: {item.path.name}", severity="information")
        except Exception as e:
            self.app.notify(f"Failed to open: {str(e)}", severity="error")
    
    def set_working_directory(self):
        """Set current directory as working directory"""
        # Store in app state for other plugins to use
        if hasattr(self.app, 'working_directory'):
            self.app.working_directory = self.current_path
        else:
            self.app.working_directory = self.current_path
        
        # Also change the actual working directory
        try:
            os.chdir(self.current_path)
            self.app.notify(f"Working directory set: {self.current_path}", severity="information")
            
            # Fire event to notify other plugins (like Commands tab)
            self.post_message(WorkingDirectoryChanged(self.current_path))
        except Exception as e:
            self.app.notify(f"Failed to set working directory: {str(e)}", severity="error")
    
    def open_in_explorer(self):
        """Open current directory in Windows File Explorer"""
        try:
            if os.name == 'nt':  # Windows
                # Use explorer.exe to open the current directory
                subprocess.Popen(['explorer', str(self.current_path)])
                self.app.notify(f"Opened in Explorer: {self.current_path.name}", severity="information")
            elif os.name == 'posix':  # Linux/Mac
                if os.uname().sysname == 'Darwin':  # Mac
                    subprocess.Popen(['open', str(self.current_path)])
                else:  # Linux
                    subprocess.Popen(['xdg-open', str(self.current_path)])
                self.app.notify(f"Opened in file manager: {self.current_path.name}", severity="information")
        except Exception as e:
            self.app.notify(f"Failed to open explorer: {str(e)}", severity="error")
    
    def handle_input_submit(self):
        """Handle input submission based on mode"""
        value = self.input_widget.value.strip()
        
        if self.input_mode == "create":
            self.create_folder(value)
        elif self.input_mode == "rename":
            self.rename_item(value)
        elif self.input_mode == "delete":
            self.delete_item(value)
        
        # Exit input mode
        self.input_mode = ""
    
    def create_folder(self, name: str):
        """Create new folder"""
        if not name:
            self.app.notify("Folder name cannot be empty", severity="warning")
            return
        
        # Validate name (no invalid characters)
        invalid_chars = '<>:"/\\|?*'
        if any(c in name for c in invalid_chars):
            self.app.notify("Invalid folder name (contains special characters)", severity="error")
            return
        
        new_path = self.current_path / name
        
        try:
            new_path.mkdir(exist_ok=False)
            self.app.notify(f"Created folder: {name}", severity="information")
            self.refresh_directory()
        except FileExistsError:
            self.app.notify(f"Folder already exists: {name}", severity="warning")
        except Exception as e:
            self.app.notify(f"Failed to create folder: {str(e)}", severity="error")
    
    def rename_item(self, new_name: str):
        """Rename selected item"""
        if not new_name or not self.input_target:
            self.app.notify("Name cannot be empty", severity="warning")
            return
        
        # Validate name
        invalid_chars = '<>:"/\\|?*'
        if any(c in new_name for c in invalid_chars):
            self.app.notify("Invalid name (contains special characters)", severity="error")
            return
        
        new_path = self.input_target.parent / new_name
        
        try:
            self.input_target.rename(new_path)
            self.app.notify(f"Renamed to: {new_name}", severity="information")
            self.refresh_directory()
        except FileExistsError:
            self.app.notify(f"Item already exists: {new_name}", severity="warning")
        except Exception as e:
            self.app.notify(f"Failed to rename: {str(e)}", severity="error")
    
    def delete_item(self, confirmation: str):
        """Delete selected item with confirmation"""
        if not self.input_target:
            return
        
        if confirmation.lower() != 'y':
            self.app.notify("Delete cancelled", severity="information")
            return
        
        try:
            if self.input_target.is_dir():
                shutil.rmtree(self.input_target)
            else:
                self.input_target.unlink()
            
            self.app.notify(f"Deleted: {self.input_target.name}", severity="information")
            self.refresh_directory()
        except Exception as e:
            self.app.notify(f"Failed to delete: {str(e)}", severity="error")


class Plugin(BasePlugin):
    """Working Directory Plugin"""
    
    name = "Working Directory"
    description = "Navigate directories and manage files"
    
    def render(self):
        """Render the directory navigator interface"""
        return DirectoryNavigator()

