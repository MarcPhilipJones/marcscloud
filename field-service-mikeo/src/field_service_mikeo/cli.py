"""CLI interface for Field Service Work Order Types."""

import argparse
import sys
from uuid import UUID

from rich.console import Console
from rich.table import Table

from .work_order_types import WorkOrderType, WorkOrderTypeManager


console = Console()


def list_work_order_types(args: argparse.Namespace) -> None:
    """List all work order types."""
    manager = WorkOrderTypeManager()
    include_inactive = getattr(args, "all", False)
    
    with console.status("Fetching work order types..."):
        work_order_types = manager.list_all(active_only=not include_inactive)
    
    if not work_order_types:
        console.print("[yellow]No work order types found.[/yellow]")
        return
    
    table = Table(title="Work Order Types")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Incident Required", justify="center")
    table.add_column("Taxable", justify="center")
    table.add_column("Status", justify="center")
    
    for wot in work_order_types:
        status = "[green]Active[/green]" if wot.is_active else "[red]Inactive[/red]"
        incident = "✓" if wot.incident_required else ""
        taxable = "✓" if wot.taxable else ""
        
        table.add_row(
            str(wot.id) if wot.id else "",
            wot.name,
            incident,
            taxable,
            status,
        )
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(work_order_types)} work order type(s)[/dim]")


def get_work_order_type(args: argparse.Namespace) -> None:
    """Get details of a specific work order type."""
    manager = WorkOrderTypeManager()
    
    with console.status("Fetching work order type..."):
        work_order_type = manager.get_by_id(args.id)
    
    if not work_order_type:
        console.print(f"[red]Work order type with ID {args.id} not found.[/red]")
        sys.exit(1)
    
    console.print(f"\n[bold cyan]{work_order_type.name}[/bold cyan]")
    console.print(f"  ID: {work_order_type.id}")
    console.print(f"  Incident Required: {'Yes' if work_order_type.incident_required else 'No'}")
    console.print(f"  Taxable: {'Yes' if work_order_type.taxable else 'No'}")
    console.print(f"  Status: {'Active' if work_order_type.is_active else 'Inactive'}")


def create_work_order_type(args: argparse.Namespace) -> None:
    """Create a new work order type."""
    manager = WorkOrderTypeManager()
    
    work_order_type = WorkOrderType(
        id=None,
        name=args.name,
        incident_required=getattr(args, "incident_required", False),
        taxable=getattr(args, "taxable", False),
    )
    
    with console.status(f"Creating work order type '{args.name}'..."):
        new_id = manager.create(work_order_type)
    
    console.print(f"[green]✓ Created work order type:[/green] {args.name}")
    console.print(f"  ID: {new_id}")


def delete_work_order_type(args: argparse.Namespace) -> None:
    """Delete a work order type."""
    manager = WorkOrderTypeManager()
    
    # First, fetch to show name
    work_order_type = manager.get_by_id(args.id)
    if not work_order_type:
        console.print(f"[red]Work order type with ID {args.id} not found.[/red]")
        sys.exit(1)
    
    if not args.force:
        console.print(f"[yellow]Are you sure you want to delete '{work_order_type.name}'?[/yellow]")
        confirm = console.input("[dim]Type 'yes' to confirm: [/dim]")
        if confirm.lower() != "yes":
            console.print("[dim]Cancelled.[/dim]")
            return
    
    with console.status(f"Deleting work order type '{work_order_type.name}'..."):
        manager.delete(args.id)
    
    console.print(f"[green]✓ Deleted work order type:[/green] {work_order_type.name}")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="field-service",
        description="Manage Dynamics 365 Field Service Work Order Types",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all work order types")
    list_parser.add_argument("--all", "-a", action="store_true", help="Include inactive types")
    list_parser.set_defaults(func=list_work_order_types)
    
    # Get command
    get_parser = subparsers.add_parser("get", help="Get a specific work order type")
    get_parser.add_argument("--id", required=True, type=UUID, help="Work order type ID (GUID)")
    get_parser.set_defaults(func=get_work_order_type)
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new work order type")
    create_parser.add_argument("--name", "-n", required=True, help="Name of the work order type")
    create_parser.add_argument("--incident-required", "-i", action="store_true", help="Require incident type")
    create_parser.add_argument("--taxable", "-t", action="store_true", help="Mark as taxable")
    create_parser.set_defaults(func=create_work_order_type)
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a work order type")
    delete_parser.add_argument("--id", required=True, type=UUID, help="Work order type ID (GUID)")
    delete_parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    delete_parser.set_defaults(func=delete_work_order_type)
    
    args = parser.parse_args()
    
    try:
        args.func(args)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
