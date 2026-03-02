#!/usr/bin/env python3
"""Local Pi status display script using rich."""

import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box


def run(cmd: str) -> str:
    """Run a shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout.strip()
    except Exception:
        return ""


def get_system_info() -> dict:
    """Gather system information."""
    info = {}
    
    # Hostname
    info["hostname"] = run("hostname")
    
    # OS
    info["os"] = run("cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"'")
    
    # Model
    info["model"] = run("cat /proc/cpuinfo | grep 'Model' | head -1 | cut -d':' -f2").strip()
    
    # Kernel
    info["kernel"] = run("uname -r")
    
    # Uptime
    info["uptime"] = run("uptime -p").replace("up ", "")
    
    # CPU temp
    try:
        temp = int(run("cat /sys/class/thermal/thermal_zone0/temp"))
        info["cpu_temp"] = round(temp / 1000, 1)
    except (ValueError, TypeError):
        info["cpu_temp"] = "?"
    
    # Memory
    mem_line = run("free -m | grep Mem")
    parts = mem_line.split()
    if len(parts) >= 3:
        total = int(parts[1])
        used = int(parts[2])
        percent = round((used / total) * 100, 1) if total > 0 else 0
        info["memory"] = f"{used} / {total} MB ({percent}%)"
    else:
        info["memory"] = "?"
    
    # Disk
    disk_line = run("df -h / | tail -1")
    parts = disk_line.split()
    if len(parts) >= 5:
        info["disk"] = f"{parts[2]} / {parts[1]} ({parts[4]} used)"
    else:
        info["disk"] = "?"
    
    return info


def get_containers() -> list[dict]:
    """Get Docker container information."""
    output = run("docker ps -a --format '{{.Names}}|{{.Status}}|{{.Image}}' 2>/dev/null")
    if not output:
        return []
    
    containers = []
    for line in output.split("\n"):
        parts = line.split("|")
        if len(parts) >= 3:
            status = parts[1]
            # Determine health status
            if "healthy" in status.lower():
                health = "✓"
                style = "green"
            elif "unhealthy" in status.lower():
                health = "✗"
                style = "red"
            elif status.lower().startswith("up"):
                health = "●"
                style = "green"
            else:
                health = "○"
                style = "dim"
            
            containers.append({
                "name": parts[0],
                "status": status,
                "image": parts[2],  # Full image name like the Windows version
                "health": health,
                "style": style,
            })
    
    return containers


def main():
    # Force colors even when no TTY (e.g., via paramiko SSH)
    console = Console(force_terminal=True)
    info = get_system_info()
    
    # Header panel - matching the Windows version style
    console.print(Panel(
        f"[green]✓ Connected to Raspberry Pi[/green]\n"
        f"Host: 192.168.0.111\n"
        f"Hostname: {info['hostname']}\n"
        f"Model: {info['model']}\n"
        f"OS: {info['os']}",
        title="[red]🍓[/red] Raspberry Pi 5",
        box=box.ROUNDED
    ))
    
    # System Status table
    console.print("\n[bold]System Status[/bold]")
    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Uptime", info["uptime"])
    table.add_row("CPU Temp", f"{info['cpu_temp']}°C")
    table.add_row("Memory", info["memory"])
    table.add_row("Disk", info["disk"])
    table.add_row("Kernel", info["kernel"])
    
    console.print(table)
    
    # Docker containers table - matching the Windows version style
    containers = get_containers()
    if containers:
        console.print("\n[bold]Docker Containers[/bold]")
        docker_table = Table(box=box.ROUNDED)
        docker_table.add_column("Name", style="cyan")
        docker_table.add_column("Status")
        docker_table.add_column("Image", style="dim")
        
        for c in containers:
            docker_table.add_row(
                c["name"],
                f"[{c['style']}]{c['status']}[/{c['style']}]",
                c["image"],
            )
        
        console.print(docker_table)


if __name__ == "__main__":
    main()
