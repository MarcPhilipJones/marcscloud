#!/usr/bin/env python
"""
Migrate records from "Statements & Documents" to "Statements and Documents" 
and delete the old subject.
"""
import sys
sys.path.insert(0, 'src')
from rich.console import Console
from powerplatform.client import DataverseClient

console = Console()


def main():
    with DataverseClient() as client:
        # Find both subjects
        console.print("\n[bold]Finding subject records...[/bold]\n")
        
        data = client._request(
            "GET",
            "subjects?$select=subjectid,title&$filter=contains(title,'Statements')"
        )
        subjects = data.get("value", [])
        
        old_subject = None
        new_subject = None
        
        for s in subjects:
            if s["title"] == "Statements & Documents":
                old_subject = s
            elif s["title"] == "Statements and Documents":
                new_subject = s
        
        if not old_subject:
            console.print("[yellow]'Statements & Documents' not found - may have already been deleted.[/yellow]")
            return
        
        if not new_subject:
            console.print("[red]'Statements and Documents' not found - cannot migrate![/red]")
            return
        
        old_id = old_subject["subjectid"]
        new_id = new_subject["subjectid"]
        
        console.print(f"  Old: '{old_subject['title']}' ({old_id})")
        console.print(f"  New: '{new_subject['title']}' ({new_id})")
        
        # Find cases that use the old subject
        console.print("\n[bold]Finding cases using 'Statements & Documents'...[/bold]\n")
        
        cases_data = client._request(
            "GET",
            f"incidents?$select=incidentid,title,ticketnumber&$filter=_subjectid_value eq {old_id}"
        )
        cases = cases_data.get("value", [])
        
        if cases:
            console.print(f"Found {len(cases)} case(s) to migrate:\n")
            for case in cases:
                console.print(f"  • {case.get('ticketnumber', 'N/A')}: {case.get('title', 'Untitled')}")
            
            # Update cases to use new subject
            console.print("\n[bold]Migrating cases...[/bold]\n")
            
            for case in cases:
                case_id = case["incidentid"]
                case_title = case.get("title", "Untitled")
                try:
                    client.update("incidents", case_id, {
                        "subjectid@odata.bind": f"/subjects({new_id})"
                    })
                    console.print(f"[green]✓[/green] Migrated: {case_title}")
                except Exception as e:
                    console.print(f"[red]✗[/red] Failed to migrate '{case_title}': {e}")
                    return  # Don't delete subject if migration failed
        else:
            console.print("[dim]No cases found using 'Statements & Documents'[/dim]")
        
        # Check for any other entity references (knowledge articles, etc.)
        # For now, we'll just check cases as they're the primary use
        
        # Delete the old subject
        console.print("\n[bold]Deleting 'Statements & Documents' subject...[/bold]\n")
        
        try:
            client.delete("subjects", old_id)
            console.print(f"[green]✓[/green] Deleted 'Statements & Documents' ({old_id})")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to delete subject: {e}")
            console.print("[yellow]The subject may be referenced by other records.[/yellow]")
            return
        
        # Verify deletion
        console.print("\n[bold]Verifying...[/bold]\n")
        
        data = client._request(
            "GET",
            "subjects?$select=subjectid,title&$filter=contains(title,'Statements')"
        )
        remaining = data.get("value", [])
        
        for s in remaining:
            console.print(f"  • {s['title']} ({s['subjectid']})")
        
        if len(remaining) == 1 and remaining[0]["title"] == "Statements and Documents":
            console.print("\n[green bold]✓ Migration complete! Only 'Statements and Documents' remains.[/green bold]")
        else:
            console.print(f"\n[yellow]Found {len(remaining)} subject(s) with 'Statements' in the title.[/yellow]")


if __name__ == "__main__":
    main()
