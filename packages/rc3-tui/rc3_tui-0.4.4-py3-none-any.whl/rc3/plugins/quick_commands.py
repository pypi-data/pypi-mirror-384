"""
Quick Commands Plugin - Execute predefined commands from config
"""

import os
import asyncio
from datetime import datetime
from textual.widgets import Static, ListView, ListItem, Label
from textual.containers import Vertical, Container, VerticalScroll
from textual.reactive import reactive
from textual.message import Message

from rc3.plugins.base import BasePlugin
from rc3.core.command_runner import CommandRunner


class CommandListItem(ListItem):
    """Custom list item that stores command data"""
    
    def __init__(self, index: int, command_data: dict, **kwargs):
        self.index = index
        self.command_data = command_data
        name = command_data.get("name", "Unnamed")
        desc = command_data.get("description", "")
        shortcut = command_data.get("shortcut", "")
        
        # Format: "[u]L[/u]ist Files              List files in current directory"
        # Find and underline the shortcut letter within the name
        formatted_name = self._underline_shortcut_in_name(name, shortcut)
        label = f"{formatted_name:<30} {desc}"
        
        super().__init__(Label(label), **kwargs)
    
    def _underline_shortcut_in_name(self, name: str, shortcut: str) -> str:
        """Underline the shortcut letter within the command name"""
        if not shortcut or len(shortcut) != 1:
            return name
        
        shortcut_lower = shortcut.lower()
        name_lower = name.lower()
        
        # Find first occurrence of shortcut letter (case-insensitive)
        for i, char in enumerate(name_lower):
            if char == shortcut_lower:
                # Found the letter - underline it using Rich markup
                underlined_name = name[:i] + f"[u]{name[i]}[/u]" + name[i+1:]
                return underlined_name
        
        # If shortcut letter not found in name, append it at the end
        return f"{name} [u]{shortcut}[/u]"


class CommandOutputPanel(Vertical):
    """Scrollable output panel with status"""
    
    current_command = reactive("")
    status = reactive("Ready")
    output_text = reactive("")
    
    def compose(self):
        yield Static(id="output-header")
        with VerticalScroll(id="output-scroll"):
            yield Static(id="output-content")
    
    def on_mount(self):
        self.update_display()
    
    def watch_current_command(self):
        self.update_display()
    
    def watch_status(self):
        self.update_display()
    
    def watch_output_text(self):
        self.update_display()
    
    def update_display(self):
        """Update the output display"""
        header = self.query_one("#output-header", Static)
        content = self.query_one("#output-content", Static)
        
        # Header with command name and status
        if self.current_command:
            status_color = {
                "Running": "yellow",
                "Success": "green",
                "Failed": "red",
                "Ready": "dim"
            }.get(self.status, "dim")
            header.update(f"[bold]OUTPUT:[/bold] {self.current_command}  [{status_color}][{self.status}][/{status_color}]")
        else:
            header.update("[dim]No command executed yet[/dim]")
        
        # Content with output text
        if self.output_text:
            content.update(self.output_text)
        else:
            content.update("[dim]Command output will appear here[/dim]")


class CommandExecutor(Vertical):
    """Main command execution widget"""
    
    # Make this widget focusable to receive keyboard events
    can_focus = True
    
    def __init__(self, commands: list):
        super().__init__()
        self.commands = commands
        self.runner = CommandRunner()
        self.output_panel = None
        self.list_view = None
        self.search_mode = False
        self.search_query = ""
        
        # Build shortcut map from YAML config
        self.shortcut_map = {}
        for i, cmd in enumerate(commands, 1):
            shortcut = cmd.get("shortcut", "").lower()
            if shortcut and len(shortcut) == 1:
                self.shortcut_map[shortcut] = i
    
    def compose(self):
        """Build the UI"""
        # Command list (top section)
        with Container(id="command-list-container"):
            yield Static(f"[bold cyan]QUICK COMMANDS[/bold cyan]  [dim][{len(self.commands)} loaded][/dim]", id="commands-header")
            yield Static(id="current-dir")
            yield ListView(id="command-list")
            yield Static(id="commands-help")
            yield Static(id="search-bar")
        
        # Output panel (bottom section)
        self.output_panel = CommandOutputPanel(id="output-panel")
        yield self.output_panel
    
    def on_mount(self):
        """Populate list and cache widget references after mount"""
        self.list_view = self.query_one("#command-list", ListView)
        
        # Populate list items after ListView is mounted
        for i, cmd in enumerate(self.commands, 1):
            self.list_view.append(CommandListItem(i, cmd))
        
        self.update_help_text()
        self.update_current_directory()
        # Focus the CommandExecutor widget immediately
        # Use set_timer to ensure focus happens after full mount
        self.set_timer(0.01, lambda: self.focus())
    
    def update_help_text(self):
        """Update help text based on current mode"""
        help_widget = self.query_one("#commands-help", Static)
        search_widget = self.query_one("#search-bar", Static)
        
        if self.search_mode:
            search_widget.update(f"[yellow]SEARCH:[/yellow] {self.search_query}_")
            help_widget.update("[dim]Type command name | [Enter] Execute | [Esc] Cancel[/dim]")
        else:
            search_widget.update("")
            # Simplified help text since shortcuts are now visual in the list
            help_text = "[dim]/ Search | Enter Run | ↑↓ j/k Navigate[/dim]"
            help_widget.update(help_text)
    
    def update_current_directory(self):
        """Update the current working directory display"""
        dir_widget = self.query_one("#current-dir", Static)
        current_dir = os.getcwd()
        dir_widget.update(f"[dim]Working Directory:[/dim] [yellow]{current_dir}[/yellow]")
    
    def on_working_directory_changed(self, event):
        """Handle working directory change events from Working Directory tab"""
        self.update_current_directory()
    
    def on_key(self, event) -> None:
        """Handle keyboard shortcuts at CommandExecutor level"""
        key = event.key
        
        # Search mode handling
        if self.search_mode:
            if key == "escape":
                # Exit search mode
                self.search_mode = False
                self.search_query = ""
                self.update_help_text()
                event.prevent_default()
                event.stop()
            elif key == "enter":
                # Execute matching command
                self.execute_search()
                event.prevent_default()
                event.stop()
            elif key == "backspace":
                # Remove last character
                self.search_query = self.search_query[:-1]
                self.update_help_text()
                event.prevent_default()
                event.stop()
            elif len(key) == 1 and key.isprintable():
                # Add character to search
                self.search_query += key.lower()
                self.update_help_text()
                event.prevent_default()
                event.stop()
            return
        
        # Normal mode handling
        # Slash to enter search mode
        if key == "slash" or key == "/":
            self.search_mode = True
            self.search_query = ""
            self.update_help_text()
            event.prevent_default()
            event.stop()
        
        # Single-letter shortcuts from YAML config
        elif key in self.shortcut_map:
            index = self.shortcut_map[key]
            self.execute_command_by_index(index)
            event.prevent_default()
            event.stop()
        
        # Vim-style navigation - pass to ListView
        elif key == "j":
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
        
        # Arrow keys for navigation
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
        
        # Enter to execute selected command
        elif key == "enter":
            if self.list_view.highlighted_child:
                item = self.list_view.highlighted_child
                if isinstance(item, CommandListItem):
                    self.execute_command_by_index(item.index)
                    event.prevent_default()
                    event.stop()
            elif len(self.list_view.children) > 0:
                # If nothing highlighted, execute first command
                self.list_view.index = 0
                item = self.list_view.highlighted_child
                if isinstance(item, CommandListItem):
                    self.execute_command_by_index(item.index)
                    event.prevent_default()
                    event.stop()
    
    def execute_search(self):
        """Execute command matching search query"""
        query = self.search_query.lower()
        
        # Find matching command by name or shortcut
        for i, cmd in enumerate(self.commands, 1):
            name = cmd.get("name", "").lower()
            shortcut = cmd.get("shortcut", "").lower()
            command = cmd.get("command", "").lower()
            
            if query in name or query == shortcut or query in command:
                self.execute_command_by_index(i)
                self.search_mode = False
                self.search_query = ""
                self.update_help_text()
                return
        
        # No match found
        self.app.notify(f"No command matches: {query}", severity="warning")
        self.search_mode = False
        self.search_query = ""
        self.update_help_text()
    
    def execute_command_by_index(self, index: int):
        """Execute a command by its index"""
        if 1 <= index <= len(self.commands):
            cmd_data = self.commands[index - 1]
            self.call_later(self.run_command_async, cmd_data)
    
    async def run_command_async(self, cmd_data: dict):
        """Run command asynchronously in background thread"""
        # Update current directory display
        self.update_current_directory()
        
        name = cmd_data.get("name", "Unnamed")
        command = cmd_data.get("command")
        shell = cmd_data.get("shell")
        cwd = cmd_data.get("cwd")
        
        # Update output panel
        self.output_panel.current_command = name
        self.output_panel.status = "Running"
        self.output_panel.output_text = f"[yellow]Executing:[/yellow] {command}\n[dim]Working directory: {cwd or 'current'}[/dim]\n\n"
        
        # Show notification
        self.app.notify(f"Executing: {name}", severity="information")
        
        # Run command in background thread
        start_time = datetime.now()
        try:
            success, stdout, stderr = await asyncio.to_thread(
                self.runner.run,
                command,
                shell=shell,
                cwd=cwd
            )
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Format output
            output_lines = []
            
            if stdout.strip():
                output_lines.append(f"[green]STDOUT:[/green]\n{stdout}")
            
            if stderr.strip():
                output_lines.append(f"[yellow]STDERR:[/yellow]\n{stderr}")
            
            if not stdout.strip() and not stderr.strip():
                output_lines.append("[dim]No output[/dim]")
            
            # Add footer with status
            status_color = "green" if success else "red"
            status_text = "SUCCESS" if success else "FAILED"
            output_lines.append(f"\n[{status_color}]═══ {status_text} ═══[/{status_color}]  [dim]Duration: {duration:.2f}s[/dim]")
            
            # Update output panel
            self.output_panel.status = "Success" if success else "Failed"
            self.output_panel.output_text = "\n".join(output_lines)
            
            # Show notification
            if success:
                self.app.notify(f"✓ {name} completed ({duration:.2f}s)", severity="information")
            else:
                self.app.notify(f"✗ {name} failed", severity="error")
        
        except Exception as e:
            # Handle execution errors
            self.output_panel.status = "Failed"
            self.output_panel.output_text = f"[red]ERROR:[/red]\n{str(e)}"
            self.app.notify(f"✗ {name} error: {str(e)}", severity="error")


class Plugin(BasePlugin):
    """Quick Commands Plugin"""
    
    name = "Quick Commands"
    description = "Execute predefined commands from config"
    
    def render(self):
        """Render the quick commands interface"""
        commands = self.config.get_commands("quick_commands")
        
        if not commands:
            return Static("No commands configured. Edit ~/.rc3/commands.yaml", classes="info")
        
        return CommandExecutor(commands)

