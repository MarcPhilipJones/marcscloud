#!/usr/bin/env python
"""Update hidden subjects to make them visible in the UI."""
import sys
sys.path.insert(0, 'src')
from rich.console import Console
from powerplatform.client import DataverseClient

console = Console()


def main():
    """Find and update subjects with null featuremask to make them visible."""
    with DataverseClient() as client:
        # First, find all subjects with null featuremask
        console.print("\n[bold]Finding hidden subjects (featuremask is null)...[/bold]\n")
        
        data = client._request(
            "GET",
            "subjects?$select=subjectid,title,featuremask&$filter=featuremask eq null&$orderby=title"
        )
        hidden_subjects = data.get("value", [])
        
        if not hidden_subjects:
            console.print("[green]No hidden subjects found - all subjects are visible![/green]")
            return
        
        console.print(f"Found {len(hidden_subjects)} hidden subjects:\n")
        for s in hidden_subjects:
            console.print(f"  • {s['title']} ({s['subjectid']})")
        
        console.print("\n[bold]Updating Subject Visibility[/bold]\n")
        
        success_count = 0
        fail_count = 0
        
        for subject in hidden_subjects:
            subject_id = subject["subjectid"]
            title = subject["title"]
            try:
                # Use the update method which handles PATCH properly
                client.update("subjects", subject_id, {"featuremask": 1})
                console.print(f"[green]✓[/green] {title} - now visible")
                success_count += 1
            except Exception as e:
                console.print(f"[red]✗[/red] {title} - failed: {e}")
                fail_count += 1
        
        console.print(f"\n[bold]Complete:[/bold] {success_count} updated, {fail_count} failed")
        
        # Verify the changes
        if success_count > 0:
            console.print("\n[bold]Verifying changes...[/bold]\n")
            data = client._request(
                "GET",
                "subjects?$select=subjectid,title,featuremask&$orderby=title"
            )
            all_subjects = data.get("value", [])
            
            # Check the ones we updated
            updated_ids = {s["subjectid"] for s in hidden_subjects}
            for s in all_subjects:
                if s["subjectid"] in updated_ids:
                    fm = s.get("featuremask")
                    status = "[green]✓ Visible[/green]" if fm == 1 else f"[yellow]featuremask={fm}[/yellow]"
                    console.print(f"  {s['title']}: {status}")


if __name__ == "__main__":
    main()
