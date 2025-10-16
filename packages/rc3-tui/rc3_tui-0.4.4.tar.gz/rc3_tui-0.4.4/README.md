# RC3 Command Center v0.4.4

A professional CLI dashboard for developers - keyboard-driven command execution with optimized performance and lazy loading.

## Features

- **Navigator Tab**: Unified split-screen interface combining directory browsing and instant command execution - browse with hjkl, execute with any letter key
- **Command Reference Tab**: Never forget your shortcuts - comprehensive list of all available commands with descriptions
- **Quick Commands**: Execute predefined commands from YAML configuration
- **System Monitoring**: Real-time CPU, memory, disk, and process monitoring (on-demand only)
- **Developer Tools**: Git operations and system utilities
- **File Browser**: Interactive file explorer with create, rename, delete, and open operations
- **Plugin System**: Auto-discovery of modular plugins with lazy loading
- **Professional UI**: Clean, minimal interface with instant tab navigation
- **Global Access**: Install once, use anywhere with `rc3` command
- **Performance Optimized**: Instant tab switching, minimal CPU usage, lazy plugin loading

## Performance

**v0.3.8 Optimization Highlights:**
- ⚡ **Instant Tab Switching**: <50ms tab switches (was 200-500ms)
- 🔋 **70% CPU Reduction**: System monitoring only runs when visible
- 🚀 **60% Faster Startup**: Lazy loading reduces startup time from ~2s to ~0.8s
- 💾 **Smart Resource Usage**: Only active tabs consume resources
- 🎯 **Optimized Focus**: Direct widget references eliminate DOM queries

The TUI now delivers desktop-app-level responsiveness with minimal system overhead.

## Installation

```powershell
cd rc3_tui
pip install -e .
```

## Usage

Simply run:
```powershell
rc3
```

### Navigation

- **Tab Navigation**: Use arrow keys (`←` `→`) or number keys (`1`-`5`)
  - `1` - Navigator (Primary Interface)
  - `2` - Commands (Quick Reference)
  - `3` - System Monitor
  - `4` - Developer Tools
  - `5` - File Browser

- **Navigator Tab** (Tab 1 - Primary Interface):
  - **Left Panel** - Directory browser (always visible)
    - `hjkl` or `↑↓←→` - Navigate files/folders (Vim-style)
    - `Enter` or `l/→` - Enter directory or open file
    - `h/←` or `Backspace` - Go to parent directory
    - `n` - Create new folder
    - `r` - Rename selected item
    - `d` - Delete selected item (y to confirm)
    - `o` - Open in system default application
    - `e` - Open current directory in Explorer
  - **Right Panel** - Command output display
  - **Letter Keys** - Execute commands instantly (e.g., press `g` for git status)
    - Commands auto-execute in currently browsed directory
    - Output appears in right panel
    - **Note**: `h`, `j`, `k`, `l` are reserved for navigation

- **Commands Tab** (Tab 2): Reference list of all available shortcuts - never forget your commands!

- **System Tab** (Tab 3): Press `c` (CPU), `m` (Memory), `d` (Disk), `n` (Network), `a` (All) for detailed views

- **Tools Tab** (Tab 4): Developer tools and utilities

- **Files Tab** (Tab 5): Alternative file browser

- **Global Controls**:
  - **Quit**: `q` or `Ctrl+C`
  - **Dark Mode**: `Ctrl+D` to toggle
  - **Reload**: `Ctrl+R` to reload plugins

- **Navigator Tab Shortcuts**:
  - **Smart Git Commit**: `g` - AI-powered commit & push from current directory (see below)

## Smart Git Commit (Hotkey: `g` in Navigator Tab)

The `g` hotkey in the Navigator tab (Tab 1) provides AI-powered git automation using OpenAI's Codex CLI:

**What it does:**
1. 🔍 Finds the git root directory from your current location
2. 📊 Analyzes all modified, staged, and untracked files
3. 📝 Generates a conventional commit message using Codex CLI
4. 📦 Stages all changes (`git add .`)
5. 💾 Commits with the AI-generated message
6. 🚀 Pushes to the remote repository

**Requirements:**
- OpenAI Codex CLI installed and authenticated
  ```powershell
  npm install -g @openai/codex
  # or
  brew install codex
  ```
- Sign in with your ChatGPT account:
  ```powershell
  codex
  # Then select "Sign in with ChatGPT"
  ```

**Usage:**
1. Switch to Navigator tab (press `1` or click Navigator)
2. Navigate to your project directory
3. Press `g` to run the automation

The automation will:
- Find the git root starting from the current Navigator directory
- Analyze all your changes in the repository
- Generate a smart commit message in conventional format (feat:, fix:, refactor:, etc.)
- Stage, commit, and push automatically

**Conventional Commit Format:**
Generated messages follow best practices:
- `feat: add new feature`
- `fix: resolve bug in parser`
- `refactor: optimize performance`
- `docs: update README`
- `chore: update dependencies`

**Error Handling:**
- Falls back to `"chore: automated commit"` if Codex fails
- Validates git repository before proceeding
- Provides step-by-step notifications in the TUI
- Handles edge cases (untracked files, no changes, etc.)

**Example Workflow:**
1. Make code changes in your project
2. Open RC3 TUI: `rc3`
3. Press `1` to switch to Navigator tab
4. Navigate to your project directory (or any subdirectory)
5. Press `g`
6. Watch as changes are analyzed, committed, and pushed automatically

## Configuration

Configuration files are stored in `~/.rc3/`:

### commands.yaml

Define your custom commands:

```yaml
quick_commands:
  - name: "Edit in Vim"
    shortcut: "v"
    command: "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'vim {file}'"
    shell: "powershell"
    description: "Open selected file in vim (new terminal)"
  
  - name: "Open in VSCode"
    shortcut: "c"
    command: "code {path}"
    shell: "powershell"
    description: "Open selected file in VS Code"
  
  - name: "Git Log"
    shortcut: "l"
    command: "git log --oneline -10"
    shell: "powershell"
    description: "Show recent git commits"
  
  - name: "Git Diff File"
    shortcut: "f"
    command: "git diff {file}"
    shell: "powershell"
    description: "Show git diff for selected file"
```

**Important - Reserved Keys in Navigator Tab:**
- **Navigation keys:** `h`, `j`, `k`, `l` - Vim-style navigation
- **File operations:** `n`, `r`, `d`, `o`, `e`, `t` - Create, rename, delete, open, explorer, terminal
- **Git automation:** `g` - Smart Git Commit (AI-powered)
- Available for custom commands: `b`, `c`, `f`, `m`, `p`, `s`, `u`, `v`, `w`, `x`, `y`, `z`

**Example shortcuts in use:**
- `v` - Edit in Vim
- `s` - Git Status  
- `f` - Git Diff File

**Dynamic File Placeholders:**
- Use `{file}` in your commands to reference the selected filename (e.g., `README.md`)
- Use `{path}` in your commands to reference the full path (e.g., `C:\Users\rc3\README.md`)
- Examples:
  - `vim {file}` - Edit the selected file
  - `code {path}` - Open in VS Code
  - `git diff {file}` - Show git changes
  - `Start-Process powershell -ArgumentList '-Command', 'vim {file}'` - Open in new terminal

### config.yaml

Application settings:

```yaml
theme: "dark"
plugins:
  enabled:
    - quick_commands
    - system_info
    - dev_tools
    - working_directory
```

## Creating Plugins

Create a new file in `rc3/plugins/`:

```python
# rc3/plugins/my_plugin.py
from textual.widgets import Static
from rc3.plugins.base import BasePlugin

class Plugin(BasePlugin):
    name = "My Plugin"
    description = "My custom plugin"
    
    def render(self):
        return Static("Hello from my plugin!")
```

That's it! The plugin will be auto-discovered on next launch.

## Project Structure

```
rc3_tui/
├── rc3/
│   ├── core/              # Core engine
│   │   ├── app.py         # Main TUI app
│   │   ├── plugin_manager.py
│   │   ├── config_manager.py
│   │   └── command_runner.py
│   ├── plugins/           # Extensible plugins
│   │   ├── base.py        # Plugin base class
│   │   ├── quick_commands.py
│   │   ├── system_info.py
│   │   ├── dev_tools.py
│   │   ├── working_directory.py
│   │   └── file_browser.py
│   └── assets/
│       └── theme.tcss     # Styling
├── pyproject.toml
├── README.md
└── agent.md              # Agent integration guide
```

## Development

Install with dev dependencies:

```powershell
pip install -e ".[dev]"
```

Run with hot reload:

```powershell
textual run --dev rc3
```

## Current Status

### Completed Features ✅
- [x] **Quick Commands** - Interactive keyboard-driven command execution
  - Keyboard-first design: Single-letter shortcuts from YAML config
  - Slash command search: Type `/git` then Enter to execute
  - Vim-style navigation (j/k) and arrow keys
  - Async command execution (non-blocking UI)
  - Live output display with scrollable, color-coded status
  - Command timing and duration tracking
  - Tab-scoped shortcuts (no conflicts with global navigation)
- [x] **Real-time System Monitoring** - Live updates every 2s with color-coded progress bars
  - **Conditional monitoring** - Only runs when System tab is visible (70% CPU savings)
  - **Async/non-blocking** - Background threads eliminate UI lag (asyncio.to_thread())
  - **Lazy loading** - Initializes on first tab access, not at startup
  - Two-column layout: metrics (left) and processes (right)
  - CPU usage (per-core and aggregate)
  - Memory usage with GB details
  - Disk usage with GB details
  - Top 20 processes by CPU usage (auto-refreshing, scrollable)
  - **Expandable details** with keyboard toggles (c, m, d, n, a)
  - **CPU details**: Frequency, per-core usage
  - **Memory details**: Swap memory, breakdown
  - **Disk details**: I/O stats, partitions
  - **Network details**: Connections, I/O (optimized for Windows)
  - Cross-platform compatibility (works with any Textual version)
- [x] **Working Directory Navigator** - Interactive file explorer
  - Keyboard-driven navigation (vim + arrow keys)
  - Create folders with inline input prompts
  - Rename files/folders with validation
  - Delete with confirmation (y/N)
  - Open files/folders in system default applications
  - Set working directory for command execution
  - Cross-platform support (Windows, Linux, macOS)
  - Sorted display: directories first, then files
- [x] Developer Tools plugin (Git operations, system utilities)
- [x] Professional tab-based navigation
- [x] Global command installation (`rc3`)
- [x] Plugin auto-discovery system
- [x] Dark/light mode toggle

### Recent Updates ✅
- [x] **v0.3.9 Smart Git Automation** (Oct 2025)
  - AI-powered git commit message generation using Codex CLI
  - Global hotkey `g` for instant commit & push workflow
  - Automatic git root detection
  - Conventional commit format (feat:, fix:, refactor:, etc.)
  - Full error handling with fallback messages
- [x] **v0.3.8 Performance Optimization** (Oct 2025)
  - Instant tab switching with lazy plugin loading
  - Conditional system monitoring (only runs when tab is visible)
  - 70% CPU reduction when not viewing System tab
  - Optimized focus logic with cached widget references
  - Removed expensive Windows operations (net_connections)
- [x] **Tab-Scoped Hotkeys** - Press number keys (1-5) to switch tabs, then immediately use tab-specific shortcuts
- [x] **Auto-Focus System** - No manual tabbing required, widgets auto-focus when switching tabs
- [x] **Conflict Resolution** - Dark mode moved to Ctrl+D, tab-specific keys work without conflicts

### Future Enhancements 🚀
- [ ] Command history and favorites
- [ ] Search/filter commands with fuzzy matching
- [ ] Live output streaming (real-time command output)
- [ ] Historical charts for system metrics
- [ ] Alert thresholds for resource usage
- [ ] Advanced file operations (copy, paste, multi-select)
- [ ] File preview panel in Working Directory Navigator
- [ ] Docker container management
- [ ] Network monitoring tools
- [ ] Custom theme support
- [ ] Plugin marketplace

## License

MIT



