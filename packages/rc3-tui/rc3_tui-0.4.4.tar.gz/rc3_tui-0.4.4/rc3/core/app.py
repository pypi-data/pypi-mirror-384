"""
Main TUI application with blended layout (sidebar + tabs + content)
"""

from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Header, Footer, TabbedContent, TabPane, Static
from textual.keys import Keys
from textual.message import Message

from rc3.core.plugin_manager import PluginManager
from rc3.core.config_manager import ConfigManager
from rc3.core.command_runner import CommandRunner
import os


class WorkingDirectoryChanged(Message):
    """Event fired when working directory is changed"""
    def __init__(self, new_directory) -> None:
        self.new_directory = new_directory
        super().__init__()


class RC3App(App):
    """RC3 Command Center - Modular CLI Dashboard"""
    
    CSS_PATH = None
    TITLE = "RC3 Command Center v0.4.4"
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+d", "toggle_dark", "Toggle Dark Mode"),
        Binding("ctrl+r", "reload_plugins", "Reload Plugins"),
        Binding("left", "previous_tab", "Previous Tab"),
        Binding("right", "next_tab", "Next Tab"),
        Binding("1", "switch_tab_1", "Navigator"),
        Binding("2", "switch_tab_2", "Commands"),
        Binding("3", "switch_tab_3", "System"),
        Binding("4", "switch_tab_4", "Tools"),
        Binding("5", "switch_tab_5", "Files"),
    ]
    
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.plugins = PluginManager(self)
        self.plugins.load_plugins()  # Load plugins before compose() runs
        self.current_tab = "commands"
        
        # Lazy loading: track which tabs have been initialized
        self.initialized_tabs = set()
        self.tab_widgets = {}  # Cache plugin widget references
    
    def compose(self) -> ComposeResult:
        """Build the UI layout with lazy loading"""
        yield Header()
        
        # Full-width content area with tabs
        # Only render Navigator tab initially, others use placeholders
        with TabbedContent(id="tabs"):
            with TabPane("Navigator", id="tab-navigator"):
                widget = self.plugins.render_plugin("navigator")
                self.tab_widgets["tab-navigator"] = widget
                self.initialized_tabs.add("tab-navigator")
                yield widget
            
            with TabPane("Commands", id="tab-commands"):
                yield Static("[dim]Loading...[/dim]", id="placeholder-commands")
            
            with TabPane("System", id="tab-system"):
                yield Static("[dim]Loading...[/dim]", id="placeholder-system")
            
            with TabPane("Tools", id="tab-tools"):
                yield Static("[dim]Loading...[/dim]", id="placeholder-tools")
            
            with TabPane("Files", id="tab-files"):
                yield Static("[dim]Loading...[/dim]", id="placeholder-files")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize on startup"""
        # Load CSS from the correct path
        try:
            css_path = Path(__file__).parent.parent / "assets" / "theme.tcss"
            if css_path.exists():
                self.stylesheet.read_all(str(css_path))
        except Exception as e:
            # CSS loading failed, but continue without it
            pass
        
        # Plugins are already loaded in __init__()
        
        # Ensure Navigator tab is active on startup - direct approach
        self.set_timer(0.1, self._set_default_tab)
        
        self.notify("RC3 Command Center loaded", severity="information")
    
    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Handle tab activation - lazy load and start monitoring"""
        tab_id = event.pane.id
        
        # Lazy initialize tab if not already done
        if tab_id not in self.initialized_tabs:
            self._initialize_tab(tab_id)
        
        # Notify widgets about visibility change
        self._notify_tab_visibility(tab_id, visible=True)
        
        # Stop monitoring on previously active tab
        if hasattr(self, '_previous_tab') and self._previous_tab != tab_id:
            self._notify_tab_visibility(self._previous_tab, visible=False)
        
        self._previous_tab = tab_id
    
    def _initialize_tab(self, tab_id: str) -> None:
        """Lazily initialize a tab's plugin on first activation"""
        plugin_map = {
            "tab-commands": ("command_reference", "placeholder-commands"),
            "tab-system": ("system_info", "placeholder-system"),
            "tab-tools": ("dev_tools", "placeholder-tools"),
            "tab-files": ("file_browser", "placeholder-files"),
        }
        
        if tab_id not in plugin_map:
            return
        
        plugin_name, placeholder_id = plugin_map[tab_id]
        
        try:
            # Get the tab pane
            tabs = self.query_one("#tabs", TabbedContent)
            pane = tabs.get_pane(tab_id)
            
            # Remove placeholder
            placeholder = pane.query_one(f"#{placeholder_id}")
            placeholder.remove()
            
            # Mount the actual plugin widget
            widget = self.plugins.render_plugin(plugin_name)
            pane.mount(widget)
            
            # Cache widget reference
            self.tab_widgets[tab_id] = widget
            self.initialized_tabs.add(tab_id)
            
        except Exception as e:
            self.notify(f"Failed to load tab: {str(e)}", severity="error")
    
    def _notify_tab_visibility(self, tab_id: str, visible: bool) -> None:
        """Notify a tab's widget about visibility change"""
        widget = self.tab_widgets.get(tab_id)
        if widget:
            # Call start/stop monitoring if the widget supports it
            if visible and hasattr(widget, 'start_monitoring'):
                widget.start_monitoring()
            elif not visible and hasattr(widget, 'stop_monitoring'):
                widget.stop_monitoring()
    
    def _set_default_tab(self) -> None:
        """Set the default tab after the UI is fully loaded"""
        try:
            tabs = self.query_one("#tabs", TabbedContent)
            tabs.active = "tab-navigator"
            self.current_tab = "navigator"
            # Focus the navigator widget
            self.focus_current_tab_content()
        except Exception:
            pass
    
    def switch_tab(self, tab_name: str) -> None:
        """Switch to a specific tab and focus its content"""
        tabs = self.query_one("#tabs", TabbedContent)
        tab_map = {
            "navigator": "tab-navigator",
            "commands": "tab-commands",
            "system": "tab-system", 
            "tools": "tab-tools",
            "files": "tab-files"
        }
        
        target_tab_id = tab_map.get(tab_name, "tab-navigator")
        tabs.active = target_tab_id
        self.current_tab = tab_name
        
        # Focus the content widget after switching tabs
        self.call_after_refresh(self.focus_current_tab_content)
    
    def focus_current_tab_content(self) -> None:
        """Focus the main content widget in the current tab (optimized)"""
        try:
            tabs = self.query_one("#tabs", TabbedContent)
            active_tab_id = tabs.active
            
            # Use cached widget reference instead of querying
            widget = self.tab_widgets.get(active_tab_id)
            if widget and hasattr(widget, 'can_focus') and widget.can_focus:
                widget.focus()
        except Exception:
            # If focus fails, silently continue
            pass
    
    def action_previous_tab(self) -> None:
        """Switch to previous tab"""
        tabs = self.query_one("#tabs", TabbedContent)
        tab_order = ["tab-navigator", "tab-commands", "tab-system", "tab-tools", "tab-files"]
        current_index = tab_order.index(tabs.active)
        previous_index = (current_index - 1) % len(tab_order)
        tabs.active = tab_order[previous_index]
        self.call_after_refresh(self.focus_current_tab_content)
    
    def action_next_tab(self) -> None:
        """Switch to next tab"""
        tabs = self.query_one("#tabs", TabbedContent)
        tab_order = ["tab-navigator", "tab-commands", "tab-system", "tab-tools", "tab-files"]
        current_index = tab_order.index(tabs.active)
        next_index = (current_index + 1) % len(tab_order)
        tabs.active = tab_order[next_index]
        self.call_after_refresh(self.focus_current_tab_content)
    
    def action_switch_tab_1(self) -> None:
        """Switch to Navigator tab"""
        self.switch_tab("navigator")
    
    def action_switch_tab_2(self) -> None:
        """Switch to Commands tab"""
        self.switch_tab("commands")
    
    def action_switch_tab_3(self) -> None:
        """Switch to System tab"""
        self.switch_tab("system")
    
    def action_switch_tab_4(self) -> None:
        """Switch to Tools tab"""
        self.switch_tab("tools")
    
    def action_switch_tab_5(self) -> None:
        """Switch to Files tab"""
        self.switch_tab("files")
    
    
    def action_toggle_dark(self) -> None:
        """Toggle dark mode"""
        self.dark = not self.dark
        self.notify(f"Dark mode: {'ON' if self.dark else 'OFF'}")
    
    def action_reload_plugins(self) -> None:
        """Reload all plugins"""
        self.plugins.reload()
        self.notify("Plugins reloaded!", severity="information")
    
    def on_key(self, event) -> None:
        """Handle global keyboard events and route tab-specific keys"""
        key = event.key
        
        # Handle number keys directly for immediate tab switching
        if key == "1":
            self.action_switch_tab_1()  # Navigator
            event.prevent_default()
            event.stop()
            return
        elif key == "2":
            self.action_switch_tab_2()  # Commands
            event.prevent_default()
            event.stop()
            return
        elif key == "3":
            self.action_switch_tab_3()  # System
            event.prevent_default()
            event.stop()
            return
        elif key == "4":
            self.action_switch_tab_4()  # Tools
            event.prevent_default()
            event.stop()
            return
        elif key == "5":
            self.action_switch_tab_5()  # Files
            event.prevent_default()
            event.stop()
            return
        
        # Handle other global keys - let bindings handle these
        if key in ["q", "ctrl+c", "ctrl+d", "ctrl+r", "left", "right"]:
            # These are handled by the binding system
            return
        
        # For all other keys, ensure the active tab's widget gets focus
        # and let the event propagate to child widgets
        self.ensure_active_tab_focused()
    
    def ensure_active_tab_focused(self) -> None:
        """Ensure the active tab's main widget is focused for keyboard input (optimized)"""
        try:
            tabs = self.query_one("#tabs", TabbedContent)
            active_tab_id = tabs.active
            
            # Use cached widget reference instead of querying
            widget = self.tab_widgets.get(active_tab_id)
            if widget and hasattr(widget, 'can_focus') and widget.can_focus:
                widget.focus()
        except Exception:
            # If focus fails, silently continue
            pass
    
    def on_working_directory_changed(self, event):
        """Handle working directory change events and relay to all plugins"""
        # Relay the event to all widgets that might be interested
        for widget in self.query("*"):
            if hasattr(widget, 'on_working_directory_changed'):
                widget.post_message(event)


