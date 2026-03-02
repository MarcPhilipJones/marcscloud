#!/usr/bin/env python
"""
Retrieve Case metadata from Dynamics 365 Customer Service:
- Subjects (from subjects entity)
- Case Origins (caseorigincode option set on incident)
- Priorities (prioritycode option set on incident)

Usage:
    python -m powerplatform.get_case_metadata
    or
    python src/powerplatform/get_case_metadata.py
"""

import sys
import os

# Ensure the src directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from typing import Any
from rich.console import Console
from rich.table import Table

from powerplatform.client import DataverseClient


console = Console()


def get_option_set_values(client: DataverseClient, entity_name: str, attribute_name: str) -> list[dict[str, Any]]:
    """
    Retrieve option set (picklist) values for a given entity attribute.
    
    Uses the Dataverse Web API EntityDefinitions to get picklist metadata.
    
    Args:
        client: DataverseClient instance
        entity_name: Logical name of the entity (e.g., 'incident')
        attribute_name: Logical name of the attribute (e.g., 'caseorigincode')
    
    Returns:
        List of dicts with 'value' and 'label' keys
    """
    endpoint = (
        f"EntityDefinitions(LogicalName='{entity_name}')"
        f"/Attributes(LogicalName='{attribute_name}')"
        f"/Microsoft.Dynamics.CRM.PicklistAttributeMetadata"
        f"?$select=LogicalName&$expand=OptionSet($select=Options)"
    )
    
    data = client._request("GET", endpoint)
    
    options = data.get("OptionSet", {}).get("Options", [])
    return [
        {
            "value": opt.get("Value"),
            "label": opt.get("Label", {}).get("UserLocalizedLabel", {}).get("Label", "Unknown"),
        }
        for opt in options
    ]


def display_option_set(title: str, options: list[dict[str, Any]], icon: str = "📋") -> None:
    """Display option set values in a formatted table."""
    table = Table(title=f"{icon} {title}")
    table.add_column("Value", style="cyan", justify="right")
    table.add_column("Label", style="white")
    
    for opt in sorted(options, key=lambda x: x["value"]):
        table.add_row(str(opt["value"]), opt["label"])
    
    console.print(table)
    console.print(f"[dim]Total: {len(options)} options[/dim]\n")


def display_subjects(client: DataverseClient) -> None:
    """Display subjects in a hierarchical table."""
    subjects = client.get_subjects()
    
    table = Table(title="📂 Subjects")
    table.add_column("ID", style="dim", max_width=36)
    table.add_column("Title", style="cyan")
    table.add_column("Description", style="white", max_width=50)
    table.add_column("Parent", style="dim")
    
    for subject in subjects:
        parent = "Yes" if subject.parent_id else "-"
        desc = subject.description[:47] + "..." if subject.description and len(subject.description) > 50 else (subject.description or "-")
        table.add_row(
            subject.id[:8] + "...",
            subject.title,
            desc,
            parent,
        )
    
    console.print(table)
    console.print(f"[dim]Total: {len(subjects)} subjects[/dim]\n")


def main():
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════════════[/]")
    console.print("[bold]       DYNAMICS 365 CUSTOMER SERVICE - CASE METADATA[/]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════════════[/]\n")
    
    try:
        with DataverseClient() as client:
            # 1. Get Subjects
            console.print("[bold green]1. SUBJECTS[/] (from 'subjects' entity)\n")
            try:
                display_subjects(client)
            except Exception as e:
                console.print(f"[red]Error fetching subjects: {e}[/]\n")
            
            # 2. Get Case Origins (caseorigincode)
            console.print("[bold green]2. CASE ORIGINS[/] (from 'incident.caseorigincode' option set)\n")
            try:
                origins = get_option_set_values(client, "incident", "caseorigincode")
                display_option_set("Case Origins", origins, "📍")
            except Exception as e:
                console.print(f"[red]Error fetching case origins: {e}[/]\n")
            
            # 3. Get Priorities (prioritycode)
            console.print("[bold green]3. PRIORITIES[/] (from 'incident.prioritycode' option set)\n")
            try:
                priorities = get_option_set_values(client, "incident", "prioritycode")
                display_option_set("Priorities", priorities, "⚡")
            except Exception as e:
                console.print(f"[red]Error fetching priorities: {e}[/]\n")
            
            # Bonus: Status codes
            console.print("[bold green]4. STATUS CODES[/] (from 'incident.statuscode' option set)\n")
            try:
                statuses = get_option_set_values(client, "incident", "statuscode")
                display_option_set("Status Codes", statuses, "🔄")
            except Exception as e:
                console.print(f"[red]Error fetching statuses: {e}[/]\n")
    
    except Exception as e:
        console.print(f"[bold red]Failed to connect to Dataverse:[/] {e}")
        console.print("\n[yellow]Make sure you have the following environment variables set:[/]")
        console.print("  • DATAVERSE_BASE_URL")
        console.print("  • DATAVERSE_TENANT_ID")
        console.print("  • DATAVERSE_CLIENT_ID")
        console.print("  • DATAVERSE_CLIENT_SECRET")
        sys.exit(1)
    
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════════════[/]")
    console.print("[green]✓ Done![/]\n")


if __name__ == "__main__":
    main()
