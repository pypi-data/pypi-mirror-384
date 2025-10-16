"""
System Info Plugin - Real-time system monitoring with live updates (async, non-blocking)
"""

import psutil
import platform
import asyncio
from datetime import datetime
from textual.widgets import Static
from textual.containers import Vertical, Horizontal, Container, VerticalScroll
from textual.reactive import reactive

from rc3.plugins.base import BasePlugin


class SystemMonitor(Container):
    """Live system monitoring widget with auto-refresh and expandable sections"""
    
    can_focus = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.refresh_interval = 2  # seconds
        self.system_info = {}
        self.metrics_widget = None
        self.processes_widget = None
        
        # Toggle states for expandable sections
        self.show_cpu_details = False
        self.show_memory_details = False
        self.show_disk_details = False
        self.show_network_details = False
        
        # Monitoring state
        self._monitoring_active = False
        self._update_timer = None
        
    def compose(self):
        """Compose the two-column layout"""
        # Create the two column widgets
        self.metrics_widget = Static("Loading metrics...", classes="metrics-content")
        self.processes_widget = Static("Loading processes...", classes="processes-content")
        
        # Use Horizontal container with VerticalScroll wrappers
        with Horizontal():
            with VerticalScroll(id="system-metrics"):
                yield self.metrics_widget
            with VerticalScroll(id="system-processes"):
                yield self.processes_widget
    
    def on_mount(self) -> None:
        """Initialize but DON'T start monitoring (lazy loading)"""
        self.get_static_system_info()
        
        # Display initial state but don't start timer
        if self.metrics_widget:
            self.metrics_widget.update("[dim]Monitoring paused - switch to this tab to start[/dim]")
        if self.processes_widget:
            self.processes_widget.update("[dim]Monitoring paused[/dim]")
        
        # Focus this widget
        self.set_timer(0.01, lambda: self.focus())
    
    def start_monitoring(self) -> None:
        """Start the monitoring timer (called when tab becomes visible)"""
        if self._monitoring_active:
            return  # Already running
        
        self._monitoring_active = True
        
        # Start updating (async worker)
        self.call_later(self.update_system_stats_async)
        self._update_timer = self.set_interval(
            self.refresh_interval, 
            lambda: self.call_later(self.update_system_stats_async)
        )
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring timer (called when tab becomes hidden)"""
        if not self._monitoring_active:
            return  # Already stopped
        
        self._monitoring_active = False
        
        # Stop the update timer
        if self._update_timer:
            self._update_timer.stop()
            self._update_timer = None
    
    def get_static_system_info(self) -> None:
        """Get static system information that doesn't change"""
        try:
            self.system_info = {
                'os': f"{platform.system()} {platform.release()}",
                'architecture': platform.machine(),
                'python': platform.python_version(),
                'cpu_cores': psutil.cpu_count(logical=True),
                'cpu_physical': psutil.cpu_count(logical=False),
            }
        except Exception as e:
            self.system_info = {'error': str(e)}
    
    async def update_system_stats_async(self) -> None:
        """Collect system stats in background thread (non-blocking)"""
        try:
            # All blocking psutil calls happen in background threads
            cpu_percent = await asyncio.to_thread(psutil.cpu_percent, interval=0.1)
            memory = await asyncio.to_thread(psutil.virtual_memory)
            disk = await asyncio.to_thread(psutil.disk_usage, '/')
            last_update = datetime.now().strftime("%H:%M:%S")
            
            # Collect additional metrics in background thread
            def collect_extended_metrics():
                metrics = {}
                
                # CPU details
                try:
                    metrics['cpu_freq'] = psutil.cpu_freq()
                    metrics['cpu_times'] = psutil.cpu_times()
                    metrics['cpu_per_core'] = psutil.cpu_percent(interval=0.1, percpu=True)
                except Exception:
                    metrics['cpu_freq'] = None
                    metrics['cpu_times'] = None
                    metrics['cpu_per_core'] = []
                
                # Memory details
                try:
                    metrics['swap_memory'] = psutil.swap_memory()
                except Exception:
                    metrics['swap_memory'] = None
                
                # Disk details
                try:
                    metrics['disk_io'] = psutil.disk_io_counters()
                    metrics['disk_partitions'] = psutil.disk_partitions()
                except Exception:
                    metrics['disk_io'] = None
                    metrics['disk_partitions'] = []
                
                # Network details
                try:
                    metrics['net_io'] = psutil.net_io_counters()
                    # Skip net_connections on Windows - it's extremely slow
                    if platform.system() != 'Windows':
                        metrics['net_connections'] = len(psutil.net_connections())
                    else:
                        metrics['net_connections'] = 0
                except Exception:
                    metrics['net_io'] = None
                    metrics['net_connections'] = 0
                
                # System details
                try:
                    metrics['boot_time'] = psutil.boot_time()
                    metrics['users'] = len(psutil.users())
                except Exception:
                    metrics['boot_time'] = None
                    metrics['users'] = 0
                
                return metrics
            
            # Collect processes and extended metrics
            def collect_processes():
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        info = proc.info
                        processes.append(info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                # Sort by CPU usage
                processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
                return processes[:20]
            
            # Run both collections in parallel
            processes, extended_metrics = await asyncio.gather(
                asyncio.to_thread(collect_processes),
                asyncio.to_thread(collect_extended_metrics)
            )
            
            # Build the data structure
            data = {
                'cpu_percent': cpu_percent,
                'memory': memory,
                'disk': disk,
                'processes': processes,
                'last_update': last_update,
                **extended_metrics
            }
            
            # Update UI on main thread
            self._update_ui_from_data(data)
            
        except Exception as e:
            self._update_ui_from_data({'error': str(e)})
    
    def _update_ui_from_data(self, data: dict) -> None:
        """Update UI widgets with collected data (runs on main thread)"""
        if not self.metrics_widget or not self.processes_widget:
            return
        
        if 'error' in data:
            if self.metrics_widget:
                self.metrics_widget.update(f"[red]Error: {data['error']}[/red]")
            if self.processes_widget:
                self.processes_widget.update(f"[red]Error: {data['error']}[/red]")
            return
        
        try:
            # Build LEFT COLUMN: System info and metrics
            metrics_lines = []
            metrics_lines.append("[bold cyan]SYSTEM INFORMATION[/bold cyan]")
            metrics_lines.append("")
            
            # Static system info
            if 'error' in self.system_info:
                metrics_lines.append(f"[red]Error: {self.system_info['error']}[/red]")
            else:
                metrics_lines.append(f"[bold]OS:[/bold] {self.system_info.get('os', 'N/A')}")
                metrics_lines.append(f"[bold]Architecture:[/bold] {self.system_info.get('architecture', 'N/A')}")
                metrics_lines.append(f"[bold]Python:[/bold] {self.system_info.get('python', 'N/A')}")
                metrics_lines.append(f"[bold]CPU Cores:[/bold] {self.system_info.get('cpu_cores', 'N/A')} logical, {self.system_info.get('cpu_physical', 'N/A')} physical")
            
            metrics_lines.append("")
            metrics_lines.append("[bold yellow]REAL-TIME METRICS[/bold yellow]")
            metrics_lines.append("")
            
            # CPU Usage
            cpu_percent = data['cpu_percent']
            cpu_bar = self.create_bar(cpu_percent, width=35)
            cpu_toggle = "[green]●[/green]" if self.show_cpu_details else "[dim]○[/dim]"
            metrics_lines.append(f"[bold]CPU Usage:[/bold] {cpu_percent:.1f}%  {cpu_toggle}[dim]c[/dim]")
            metrics_lines.append(cpu_bar)
            
            # CPU Details (if toggled)
            if self.show_cpu_details:
                if data.get('cpu_freq'):
                    freq = data['cpu_freq']
                    metrics_lines.append(f"  [dim]Frequency:[/dim] {freq.current:.0f}MHz ({freq.min:.0f}-{freq.max:.0f}MHz)")
                if data.get('cpu_per_core'):
                    core_usage = ", ".join([f"{core:.0f}%" for core in data['cpu_per_core'][:4]])
                    metrics_lines.append(f"  [dim]Per-core:[/dim] {core_usage}")
            metrics_lines.append("")
            
            # Memory Usage
            memory = data['memory']
            memory_percent = memory.percent
            memory_bar = self.create_bar(memory_percent, width=35)
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            memory_toggle = "[green]●[/green]" if self.show_memory_details else "[dim]○[/dim]"
            metrics_lines.append(f"[bold]Memory:[/bold] {memory_percent:.1f}%  {memory_toggle}[dim]m[/dim]")
            metrics_lines.append(f"({memory_used_gb:.1f} / {memory_total_gb:.1f} GB)")
            metrics_lines.append(memory_bar)
            
            # Memory Details (if toggled)
            if self.show_memory_details:
                if data.get('swap_memory'):
                    swap = data['swap_memory']
                    swap_used_gb = swap.used / (1024**3)
                    swap_total_gb = swap.total / (1024**3)
                    metrics_lines.append(f"  [dim]Swap:[/dim] {swap.percent:.1f}% ({swap_used_gb:.1f}/{swap_total_gb:.1f} GB)")
            metrics_lines.append("")
            
            # Disk Usage
            disk = data['disk']
            disk_percent = disk.percent
            disk_bar = self.create_bar(disk_percent, width=35)
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            disk_toggle = "[green]●[/green]" if self.show_disk_details else "[dim]○[/dim]"
            metrics_lines.append(f"[bold]Disk:[/bold] {disk_percent:.1f}%  {disk_toggle}[dim]d[/dim]")
            metrics_lines.append(f"({disk_used_gb:.1f} / {disk_total_gb:.1f} GB)")
            metrics_lines.append(disk_bar)
            
            # Disk Details (if toggled)
            if self.show_disk_details:
                if data.get('disk_io'):
                    io = data['disk_io']
                    read_mb = io.read_bytes / (1024**2)
                    write_mb = io.write_bytes / (1024**2)
                    metrics_lines.append(f"  [dim]I/O:[/dim] {read_mb:.0f}MB read, {write_mb:.0f}MB written")
                if data.get('disk_partitions'):
                    partitions = len([p for p in data['disk_partitions'] if 'rw' in p.opts])
                    metrics_lines.append(f"  [dim]Partitions:[/dim] {partitions} mounted")
            metrics_lines.append("")
            
            # Network Details (if toggled)
            if self.show_network_details:
                network_toggle = "[green]●[/green]"
                metrics_lines.append(f"[bold]Network:[/bold] {network_toggle}[dim]n[/dim]")
                if data.get('net_io'):
                    net = data['net_io']
                    sent_mb = net.bytes_sent / (1024**2)
                    recv_mb = net.bytes_recv / (1024**2)
                    metrics_lines.append(f"  [dim]I/O:[/dim] {sent_mb:.1f}MB sent, {recv_mb:.1f}MB received")
                if data.get('net_connections') and platform.system() != 'Windows':
                    metrics_lines.append(f"  [dim]Connections:[/dim] {data['net_connections']} active")
                elif platform.system() == 'Windows':
                    metrics_lines.append(f"  [dim]Connections:[/dim] (disabled on Windows for performance)")
                metrics_lines.append("")
            
            # Help text
            metrics_lines.append("")
            metrics_lines.append(f"[dim]Updated: {data['last_update']}[/dim]")
            metrics_lines.append(f"[dim]Refresh: {self.refresh_interval}s[/dim]")
            metrics_lines.append("[dim]Shortcuts: c=CPU, m=Memory, d=Disk, n=Network, a=All[/dim]")
            
            # Build RIGHT COLUMN: Process list
            process_lines = []
            process_lines.append("[bold green]TOP PROCESSES[/bold green]")
            process_lines.append("")
            
            process_lines.append(f"{'PID':<8} {'NAME':<28} {'CPU%':<8} {'MEM%':<8}")
            process_lines.append("─" * 60)
            
            # Show top 20 processes
            count = 0
            for proc in data['processes']:
                pid = str(proc['pid'])
                name = (proc['name'] or 'N/A')[:27]
                cpu = f"{proc['cpu_percent'] or 0:.1f}"
                mem = f"{proc['memory_percent'] or 0:.1f}"
                process_lines.append(f"{pid:<8} {name:<28} {cpu:<8} {mem:<8}")
                count += 1
            
            process_lines.append("")
            process_lines.append(f"[dim]Showing {count} processes[/dim]")
            
            # Update both widgets
            if self.metrics_widget:
                self.metrics_widget.update("\n".join(metrics_lines))
            if self.processes_widget:
                self.processes_widget.update("\n".join(process_lines))
            
        except Exception as e:
            if self.metrics_widget:
                self.metrics_widget.update(f"[red]Error rendering: {e}[/red]")
            if self.processes_widget:
                self.processes_widget.update(f"[red]Error rendering: {e}[/red]")
    
    def create_bar(self, percent: float, width: int = 40) -> str:
        """Create a visual progress bar for percentages"""
        filled = int((percent / 100) * width)
        empty = width - filled
        
        # Color based on percentage
        if percent < 60:
            color = "green"
        elif percent < 80:
            color = "yellow"
        else:
            color = "red"
        
        bar = f"[{color}]{'█' * filled}[/{color}]{'░' * empty}"
        return bar
    
    def on_key(self, event) -> None:
        """Handle keyboard shortcuts for expandable sections"""
        key = event.key.lower()
        
        if key == 'c':
            self.show_cpu_details = not self.show_cpu_details
            event.prevent_default()
            event.stop()
        elif key == 'm':
            self.show_memory_details = not self.show_memory_details
            event.prevent_default()
            event.stop()
        elif key == 'd':
            self.show_disk_details = not self.show_disk_details
            event.prevent_default()
            event.stop()
        elif key == 'n':
            self.show_network_details = not self.show_network_details
            event.prevent_default()
            event.stop()
        elif key == 'a':
            # Toggle all details
            all_on = all([self.show_cpu_details, self.show_memory_details, 
                         self.show_disk_details, self.show_network_details])
            self.show_cpu_details = not all_on
            self.show_memory_details = not all_on
            self.show_disk_details = not all_on
            self.show_network_details = not all_on
            event.prevent_default()
            event.stop()
        
        # Force refresh to show updated details
        if key in ['c', 'm', 'd', 'n', 'a']:
            self.call_later(self.update_system_stats_async)


class Plugin(BasePlugin):
    """Real-time system monitoring plugin"""
    
    name = "System"
    description = "Real-time system monitoring with live updates"
    
    def render(self):
        """Render the system monitoring interface"""
        return SystemMonitor(id="system-monitor")
