"""CLI entry point for Raspberry Pi SSH client."""

import argparse
import logging
import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from .client import PiClient


console = Console()
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging to console and file."""
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, datefmt="%Y-%m-%d %H:%M:%S")


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Raspberry Pi 5 SSH Client"
    )
    parser.add_argument(
        "--cmd", "-c",
        type=str,
        help="Execute a single command"
    )
    parser.add_argument(
        "--info", "-i",
        action="store_true",
        help="Show system information"
    )
    parser.add_argument(
        "--memory", "-m",
        action="store_true",
        help="Show memory usage"
    )
    parser.add_argument(
        "--disk", "-d",
        action="store_true",
        help="Show disk usage"
    )
    parser.add_argument(
        "--containers",
        action="store_true",
        help="List Docker containers"
    )
    parser.add_argument(
        "--logs",
        type=str,
        metavar="CONTAINER",
        help="Show logs for a container"
    )
    parser.add_argument(
        "--shell", "-s",
        action="store_true",
        help="Open interactive shell (basic)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug logging"
    )
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    try:
        with PiClient() as pi:
            # Test connection
            result = pi.run("echo 'Connected'")
            if not result.success:
                console.print("[red]❌ Failed to connect to Raspberry Pi[/red]")
                return 1
            
            info = pi.get_system_info()
            console.print(Panel(
                f"[green]✓ Connected to Raspberry Pi[/green]\n"
                f"Host: {pi.host}\n"
                f"Hostname: {info.get('hostname', 'unknown')}\n"
                f"Model: {info.get('model', 'unknown')}\n"
                f"OS: {info.get('os', 'unknown')}",
                title="🍓 Raspberry Pi 5",
                box=box.ROUNDED
            ))
            
            # Handle commands
            if args.cmd:
                result = pi.run(args.cmd)
                if result.stdout:
                    console.print(result.stdout)
                if result.stderr:
                    console.print(f"[red]{result.stderr}[/red]")
                return 0 if result.success else 1
            
            elif args.info:
                show_system_info(pi)
            
            elif args.memory:
                show_memory_info(pi)
            
            elif args.disk:
                show_disk_info(pi)
            
            elif args.containers:
                show_containers(pi)
            
            elif args.logs:
                logs = pi.container_logs(args.logs)
                console.print(Panel(logs, title=f"Logs: {args.logs}", box=box.ROUNDED))
            
            elif args.shell:
                interactive_shell(pi)
            
            else:
                # Default: show summary
                show_summary(pi)
            
            return 0
    
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        return 1
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def show_summary(pi: PiClient) -> None:
    """Show a summary of the Pi status."""
    info = pi.get_system_info()
    memory = pi.get_memory_info()
    
    # System info
    console.print("\n[bold]System Status[/bold]")
    table = Table(box=box.SIMPLE)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Uptime", info.get("uptime", "unknown"))
    table.add_row("CPU Temp", f"{info.get('cpu_temp', '?')}°C")
    table.add_row("Memory", f"{memory['used_mb']} / {memory['total_mb']} MB ({memory['percent_used']}%)")
    table.add_row("Kernel", info.get("kernel", "unknown"))
    
    console.print(table)
    
    # Docker containers
    containers = pi.list_containers()
    if containers:
        console.print("\n[bold]Docker Containers[/bold]")
        show_containers(pi)
    
    console.print("\n[dim]Use --help for more options[/dim]")


def show_system_info(pi: PiClient) -> None:
    """Display detailed system information."""
    info = pi.get_system_info()
    
    table = Table(title="System Information", box=box.ROUNDED)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Hostname", info.get("hostname", "unknown"))
    table.add_row("Model", info.get("model", "unknown"))
    table.add_row("OS", info.get("os", "unknown"))
    table.add_row("Kernel", info.get("kernel", "unknown"))
    table.add_row("Uptime", info.get("uptime", "unknown"))
    
    cpu_temp = info.get("cpu_temp")
    if cpu_temp is not None:
        temp_color = "green" if cpu_temp < 50 else "yellow" if cpu_temp < 70 else "red"
        table.add_row("CPU Temp", f"[{temp_color}]{cpu_temp}°C[/{temp_color}]")
    
    console.print(table)


def show_memory_info(pi: PiClient) -> None:
    """Display memory usage."""
    memory = pi.get_memory_info()
    
    table = Table(title="Memory Usage", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="white")
    
    table.add_row("Total", f"{memory['total_mb']} MB")
    table.add_row("Used", f"{memory['used_mb']} MB")
    table.add_row("Free", f"{memory['free_mb']} MB")
    
    pct = memory['percent_used']
    pct_color = "green" if pct < 60 else "yellow" if pct < 80 else "red"
    table.add_row("Usage", f"[{pct_color}]{pct}%[/{pct_color}]")
    
    console.print(table)


def show_disk_info(pi: PiClient) -> None:
    """Display disk usage."""
    disks = pi.get_disk_info()
    
    table = Table(title="Disk Usage", box=box.ROUNDED)
    table.add_column("Device", style="cyan")
    table.add_column("Mount", style="white")
    table.add_column("Size", justify="right")
    table.add_column("Used", justify="right")
    table.add_column("Available", justify="right")
    table.add_column("Usage", justify="right")
    
    for disk in disks:
        pct = disk['percent_used'].replace('%', '')
        try:
            pct_val = int(pct)
            pct_color = "green" if pct_val < 60 else "yellow" if pct_val < 80 else "red"
            usage = f"[{pct_color}]{disk['percent_used']}[/{pct_color}]"
        except ValueError:
            usage = disk['percent_used']
        
        table.add_row(
            disk['device'],
            disk['mount'],
            disk['size'],
            disk['used'],
            disk['available'],
            usage,
        )
    
    console.print(table)


def show_containers(pi: PiClient) -> None:
    """Display Docker containers."""
    containers = pi.list_containers()
    
    if not containers:
        console.print("[dim]No Docker containers found[/dim]")
        return
    
    table = Table(title="Docker Containers", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Status")
    table.add_column("Image", style="dim")
    
    for c in containers:
        status = c['status']
        if 'Up' in status:
            status_display = f"[green]{status}[/green]"
        elif 'Exited' in status:
            status_display = f"[red]{status}[/red]"
        else:
            status_display = f"[yellow]{status}[/yellow]"
        
        table.add_row(c['name'], status_display, c['image'])
    
    console.print(table)


def interactive_shell(pi: PiClient) -> None:
    """Basic interactive shell."""
    console.print("\n[bold]Interactive Shell[/bold] (type 'exit' to quit)\n")
    
    while True:
        try:
            cmd = console.input(f"[cyan]{pi.user}@{pi.host}[/cyan]$ ")
            
            if cmd.lower() in ('exit', 'quit', 'q'):
                break
            
            if not cmd.strip():
                continue
            
            result = pi.run(cmd)
            
            if result.stdout:
                console.print(result.stdout)
            if result.stderr:
                console.print(f"[red]{result.stderr}[/red]")
        
        except KeyboardInterrupt:
            console.print("\n")
            break
        except EOFError:
            break
    
    console.print("[dim]Disconnected[/dim]")


if __name__ == "__main__":
    sys.exit(main())
