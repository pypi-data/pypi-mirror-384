"""
Command Reference Plugin - Display all available Navigator commands
"""

from textual.widgets import Static, DataTable
from textual.containers import Vertical, Container, VerticalScroll

from rc3.plugins.base import BasePlugin


class CommandReferenceWidget(Vertical):
    """Display command reference table"""
    
    can_focus = True
    
    def __init__(self, commands: list):
        super().__init__()
        self.commands = commands
        self.table = None
    
    def compose(self):
        """Build the UI"""
        with Container(id="command-ref-container"):
            yield Static("[bold cyan]COMMAND REFERENCE[/bold cyan]", id="ref-header")
            yield Static("[dim]Available shortcuts in Navigator tab (Tab 1)[/dim]", id="ref-subtitle")
            yield DataTable(id="command-table")
            yield Static(id="ref-help")
    
    def on_mount(self):
        """Initialize after mount"""
        self.table = self.query_one("#command-table", DataTable)
        help_text = self.query_one("#ref-help", Static)
        
        # Configure table
        self.table.cursor_type = "row"
        self.table.zebra_stripes = True
        
        # Add columns
        self.table.add_column("Shortcut", width=10)
        self.table.add_column("Command Name", width=30)
        self.table.add_column("Description", width=50)
        self.table.add_column("Shell", width=12)
        
        # Populate table with commands
        if not self.commands:
            self.table.add_row("[dim]No commands configured[/dim]", "", "", "")
        else:
            # Sort by shortcut for easy lookup
            sorted_commands = sorted(self.commands, key=lambda x: x.get("shortcut", "").lower())
            
            for cmd in sorted_commands:
                shortcut = cmd.get("shortcut", "?")
                name = cmd.get("name", "Unnamed")
                desc = cmd.get("description", "")
                shell = cmd.get("shell", "default")
                
                # Highlight if shortcut conflicts with nav keys
                nav_keys = {'h', 'j', 'k', 'l'}
                if shortcut.lower() in nav_keys:
                    shortcut_display = f"[red]{shortcut}[/red] ⚠"
                else:
                    shortcut_display = f"[yellow]{shortcut}[/yellow]"
                
                self.table.add_row(
                    shortcut_display,
                    f"[green]{name}[/green]",
                    desc,
                    f"[dim]{shell}[/dim]"
                )
        
        # Add reserved navigation keys section
        self.table.add_row("", "", "", "")
        self.table.add_row("[bold cyan]═══ RESERVED NAVIGATION KEYS ═══[/bold cyan]", "", "", "")
        self.table.add_row("[yellow]h[/yellow]", "Navigate Left", "Go to parent directory", "")
        self.table.add_row("[yellow]j[/yellow]", "Navigate Down", "Move cursor down", "")
        self.table.add_row("[yellow]k[/yellow]", "Navigate Up", "Move cursor up", "")
        self.table.add_row("[yellow]l[/yellow]", "Navigate Right", "Enter directory/open file", "")
        
        # Add file operation keys
        self.table.add_row("", "", "", "")
        self.table.add_row("[bold cyan]═══ FILE OPERATIONS ═══[/bold cyan]", "", "", "")
        self.table.add_row("[yellow]n[/yellow]", "New Folder", "Create new folder in current directory", "")
        self.table.add_row("[yellow]r[/yellow]", "Rename", "Rename selected file/folder", "")
        self.table.add_row("[yellow]d[/yellow]", "Delete", "Delete selected file/folder", "")
        self.table.add_row("[yellow]o[/yellow]", "Open", "Open with system default application", "")
        self.table.add_row("[yellow]e[/yellow]", "Explorer", "Open current directory in Explorer", "")
        self.table.add_row("[yellow]t[/yellow]", "Terminal", "Open terminal in current directory", "")
        
        # Add git automation
        self.table.add_row("", "", "", "")
        self.table.add_row("[bold cyan]═══ GIT AUTOMATION ═══[/bold cyan]", "", "", "")
        self.table.add_row("[yellow]g[/yellow]", "[bold]Smart Git Commit[/bold]", "AI-powered: analyze, stage, commit & push", "[green]Codex[/green]")
        
        # Add placeholder info
        self.table.add_row("", "", "", "")
        self.table.add_row("[bold cyan]═══ COMMAND PLACEHOLDERS ═══[/bold cyan]", "", "", "")
        self.table.add_row("[yellow]{file}[/yellow]", "Selected Filename", "Name of file/folder selected in Navigator", "")
        self.table.add_row("[yellow]{path}[/yellow]", "Selected Full Path", "Absolute path to selected file/folder", "")
        
        # Help text
        help_text.update(
            "[dim]↑↓ Navigate | Press '1' to return to Navigator tab | "
            f"Custom Commands: {len(self.commands)} | Built-in: 9 shortcuts (hjkl, nordet, g) | "
            "[yellow]g[/yellow] = AI Git Commit[/dim]"
        )
        
        # Focus the table
        self.set_timer(0.01, lambda: self.table.focus())
    
    def on_key(self, event) -> None:
        """Handle keyboard shortcuts"""
        key = event.key
        
        # Allow arrow keys and j/k for navigation
        if key in ["j", "down"]:
            self.table.action_cursor_down()
            event.prevent_default()
            event.stop()
        elif key in ["k", "up"]:
            self.table.action_cursor_up()
            event.prevent_default()
            event.stop()


class Plugin(BasePlugin):
    """Command Reference Plugin"""
    
    name = "Command Reference"
    description = "Display all available Navigator commands"
    
    def render(self):
        """Render the command reference interface"""
        commands = self.config.get_commands("quick_commands")
        
        if not commands:
            commands = []
        
        return CommandReferenceWidget(commands)

