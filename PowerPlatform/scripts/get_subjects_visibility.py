#!/usr/bin/env python
"""Retrieve all subjects with visibility status from Dynamics 365."""
import sys
sys.path.insert(0, 'src')
from rich.console import Console
from rich.table import Table
from powerplatform.client import DataverseClient

console = Console()


def main():
    """Get all subjects and display with visibility status."""
    with DataverseClient() as client:
        # Query subjects with featuremask (visibility control)
        # featuremask = 1 means visible, 0 means hidden
        data = client._request(
            "GET",
            "subjects?$select=subjectid,title,description,featuremask,_parentsubject_value&$orderby=title"
        )
        subjects = data.get("value", [])
        
        # Build parent lookup for hierarchical display
        subject_map = {s["subjectid"]: s for s in subjects}
        
        table = Table(title=f"📂 Subjects Visibility Status ({len(subjects)} total)")
        table.add_column("Title", style="cyan")
        table.add_column("Parent", style="dim")
        table.add_column("Feature Mask", justify="center")
        table.add_column("Visible", justify="center")
        table.add_column("Subject ID", style="dim", max_width=36)
        
        hidden_count = 0
        visible_count = 0
        
        for subject in subjects:
            parent_id = subject.get("_parentsubject_value")
            parent_title = "-"
            if parent_id and parent_id in subject_map:
                parent_title = subject_map[parent_id].get("title", parent_id[:8])
            
            featuremask = subject.get("featuremask")
            is_visible = featuremask == 1 if featuremask is not None else "N/A"
            
            if is_visible is True:
                visible_style = "[green]✓ Yes[/green]"
                visible_count += 1
            elif is_visible is False:
                visible_style = "[red]✗ No[/red]"
                hidden_count += 1
            else:
                visible_style = "[yellow]?[/yellow]"
            
            table.add_row(
                subject.get("title", ""),
                parent_title,
                str(featuremask) if featuremask is not None else "null",
                visible_style,
                subject["subjectid"],
            )
        
        console.print(table)
        console.print(f"\n[green]Visible: {visible_count}[/green]  |  [red]Hidden: {hidden_count}[/red]  |  Total: {len(subjects)}")


if __name__ == "__main__":
    main()
