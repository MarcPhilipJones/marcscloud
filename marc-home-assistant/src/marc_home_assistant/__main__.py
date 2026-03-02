"""CLI entry point for Marc Home Assistant."""

import argparse
import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from .client import HomeAssistantClient


console = Console()


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Marc Home Assistant - Connect to Home Assistant on Raspberry Pi 5"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all entities"
    )
    parser.add_argument(
        "--domain", "-d",
        type=str,
        help="Filter by domain (e.g., light, switch, sensor)"
    )
    parser.add_argument(
        "--entity", "-e",
        type=str,
        help="Get state of a specific entity"
    )
    parser.add_argument(
        "--service", "-s",
        type=str,
        help="Call a service (format: domain.service, e.g., light.turn_on)"
    )
    parser.add_argument(
        "--on",
        action="store_true",
        help="Turn entity on"
    )
    parser.add_argument(
        "--off",
        action="store_true",
        help="Turn entity off"
    )
    parser.add_argument(
        "--toggle", "-t",
        action="store_true",
        help="Toggle entity"
    )
    
    args = parser.parse_args()
    
    try:
        client = HomeAssistantClient()
        
        # Check connection
        if not client.check_api():
            console.print("[red]❌ Cannot connect to Home Assistant API[/red]")
            return 1
        
        config = client.get_config()
        console.print(Panel(
            f"[green]✓ Connected to Home Assistant[/green]\n"
            f"Location: {config.location_name}\n"
            f"Version: {config.version}",
            title="Marc Home Assistant",
            box=box.ROUNDED
        ))
        
        # Handle commands
        if args.entity:
            if args.on:
                client.turn_on(args.entity)
                console.print(f"[green]✓ Turned on {args.entity}[/green]")
            elif args.off:
                client.turn_off(args.entity)
                console.print(f"[green]✓ Turned off {args.entity}[/green]")
            elif args.toggle:
                client.toggle(args.entity)
                console.print(f"[green]✓ Toggled {args.entity}[/green]")
            else:
                # Just show entity state
                state = client.get_state(args.entity)
                if state:
                    show_entity_detail(state)
                else:
                    console.print(f"[red]Entity not found: {args.entity}[/red]")
                    return 1
        
        elif args.service and args.entity:
            parts = args.service.split(".")
            if len(parts) != 2:
                console.print("[red]Service must be in format: domain.service[/red]")
                return 1
            domain, service = parts
            client.call_service(domain, service, args.entity)
            console.print(f"[green]✓ Called {args.service} on {args.entity}[/green]")
        
        elif args.list or args.domain:
            states = client.get_states()
            
            if args.domain:
                states = [s for s in states if s.domain == args.domain]
            
            show_entity_table(states, args.domain)
        
        else:
            # Show summary by default
            show_summary(client)
        
        return 0
        
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        return 1
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def show_summary(client: HomeAssistantClient) -> None:
    """Show a summary of Home Assistant entities."""
    states = client.get_states()
    
    # Count by domain
    domains: dict[str, int] = {}
    for state in states:
        domains[state.domain] = domains.get(state.domain, 0) + 1
    
    table = Table(title="Entity Summary", box=box.ROUNDED)
    table.add_column("Domain", style="cyan")
    table.add_column("Count", justify="right", style="green")
    
    for domain, count in sorted(domains.items()):
        table.add_row(domain, str(count))
    
    table.add_row("─" * 20, "─" * 5, style="dim")
    table.add_row("Total", str(len(states)), style="bold")
    
    console.print(table)
    console.print("\n[dim]Use --list to see all entities, or --domain <name> to filter[/dim]")


def show_entity_table(states: list, domain: str = None) -> None:
    """Display entities in a table."""
    title = f"{domain.title()} Entities" if domain else "All Entities"
    table = Table(title=title, box=box.ROUNDED)
    table.add_column("Entity ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("State", justify="center")
    table.add_column("Last Changed", style="dim")
    
    for state in sorted(states, key=lambda s: s.entity_id):
        # Color state based on value
        state_style = "green" if state.is_on else "red" if state.state.lower() == "off" else "yellow"
        state_display = f"[{state_style}]{state.state}[/{state_style}]"
        
        last_changed = ""
        if state.last_changed:
            last_changed = state.last_changed.strftime("%Y-%m-%d %H:%M")
        
        table.add_row(
            state.entity_id,
            state.name,
            state_display,
            last_changed
        )
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(states)} entities[/dim]")


def show_entity_detail(state) -> None:
    """Show detailed information about an entity."""
    from rich.syntax import Syntax
    import json
    
    # State badge
    state_style = "green" if state.is_on else "red" if state.state.lower() == "off" else "yellow"
    
    console.print(Panel(
        f"[bold]{state.name}[/bold]\n"
        f"Entity ID: [cyan]{state.entity_id}[/cyan]\n"
        f"State: [{state_style}]{state.state}[/{state_style}]\n"
        f"Domain: {state.domain}\n"
        f"Last Changed: {state.last_changed.strftime('%Y-%m-%d %H:%M:%S') if state.last_changed else 'Unknown'}\n"
        f"Last Updated: {state.last_updated.strftime('%Y-%m-%d %H:%M:%S') if state.last_updated else 'Unknown'}",
        title=f"Entity: {state.entity_id}",
        box=box.ROUNDED
    ))
    
    if state.attributes:
        console.print("\n[bold]Attributes:[/bold]")
        attrs_json = json.dumps(state.attributes, indent=2, default=str)
        console.print(Syntax(attrs_json, "json", theme="monokai"))


if __name__ == "__main__":
    sys.exit(main())
