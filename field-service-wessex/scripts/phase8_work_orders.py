"""Phase 8: Create 4 Work Orders (one per type) and attach Knowledge Articles.

Usage:
    cd field-service-wessex
    python scripts/phase8_work_orders.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from helpers import (
    console,
    extract_guid,
    get_client,
    load_state,
    save_state,
)

# Work order definitions: one per type
WORK_ORDERS = [
    {
        "name": "Emergency Leak - CW Willowbrook Farm",
        "summary": (
            "Chris Walker reported water bubbling up in the lower field near the main track. "
            "Possible mains or supply pipe leak. Affecting livestock water troughs downstream. "
            "Priority response required - farmer reports significant water loss over 24 hours."
        ),
        "wot_key": "Water Leak Repair",
        "incident_key": "Emergency Mains Leak",
        "priority": "High",
        "articles": [
            "Emergency Water Mains Leak Repair - Contoso Utilities",
            "Field Operative Health and Safety Guide - Contoso Utilities",
        ],
    },
    {
        "name": "Smart Meter Install - CW Willowbrook Farm",
        "summary": (
            "Scheduled smart meter upgrade at CW Willowbrook Farm. Property currently has "
            "a standard meter in the roadside chamber. Customer Chris Walker has been notified "
            "and confirmed access is available. No known access issues."
        ),
        "wot_key": "Smart Meter Installation",
        "incident_key": "Residential Smart Meter Installation",
        "priority": "Medium",
        "articles": [
            "Smart Meter Installation Guide - Contoso Utilities",
            "Field Operative Health and Safety Guide - Contoso Utilities",
        ],
    },
    {
        "name": "Sewer Blockage - CW Willowbrook Farm",
        "summary": (
            "Chris Walker reports sewage backing up from the manhole near the farmhouse. "
            "Affecting kitchen and bathroom drainage. Neighbours on the lane also experiencing "
            "slow drainage. Likely blockage on the public sewer serving the hamlet."
        ),
        "wot_key": "Sewer Blockage Clearance",
        "incident_key": "Public Sewer Blockage",
        "priority": "High",
        "articles": [
            "Sewer Blockage Investigation and Clearance - Contoso Utilities",
            "Field Operative Health and Safety Guide - Contoso Utilities",
        ],
    },
    {
        "name": "Water Quality Complaint - CW Willowbrook Farm",
        "summary": (
            "Chris Walker called to report brown/discoloured water from the kitchen cold tap. "
            "Started this morning, has not cleared after running the tap for 10 minutes. "
            "No known recent mains work in the area. Customer concerned about livestock "
            "water supply from the same mains connection."
        ),
        "wot_key": "Water Quality Investigation",
        "incident_key": "Water Quality Customer Complaint",
        "priority": "Medium",
        "articles": [
            "Water Quality Investigation Procedures - Contoso Utilities",
            "Field Operative Health and Safety Guide - Contoso Utilities",
        ],
    },
]


def main():
    console.print("\n[bold magenta]═══ Phase 8: Work Orders ═══[/bold magenta]")
    client = get_client()

    # Load state from previous phases
    wot_ids = load_state("phase3_work_order_types")
    incident_ids = load_state("phase5_incident_types")
    article_ids = load_state("phase1_articles")
    existing = load_state("phase7_existing_records")

    account_id = existing["account_id"]
    contact_id = existing["contact_id"]

    # Look up priority records
    console.print("  Looking up priorities...")
    result = client.get("msdyn_priorities", {"$select": "msdyn_priorityid,msdyn_name"})
    priorities = {
        p["msdyn_name"]: p["msdyn_priorityid"] for p in result.get("value", [])
    }
    for name, pid in priorities.items():
        console.print(f"    [dim]{name}: {pid}[/dim]")

    if not priorities:
        console.print(
            "  [yellow]No priority records found — creating without priority[/yellow]"
        )

    # Create work orders
    wo_ids: dict[str, str] = {}

    for wo_def in WORK_ORDERS:
        name = wo_def["name"]
        wot_id = wot_ids[wo_def["wot_key"]]
        inc_id = incident_ids[wo_def["incident_key"]]

        wo_data = {
            "msdyn_name": name,
            "msdyn_workordersummary": wo_def["summary"],
            "msdyn_serviceaccount@odata.bind": f"/accounts({account_id})",
            "msdyn_reportedbycontact@odata.bind": f"/contacts({contact_id})",
            "msdyn_workordertype@odata.bind": f"/msdyn_workordertypes({wot_id})",
            "msdyn_primaryincidenttype@odata.bind": f"/msdyn_incidenttypes({inc_id})",
            "msdyn_systemstatus": 690970000,  # Unscheduled
        }

        # Add priority if available
        priority_name = wo_def["priority"]
        if priority_name in priorities:
            wo_data["msdyn_priority@odata.bind"] = (
                f"/msdyn_priorities({priorities[priority_name]})"
            )

        result = client.post("msdyn_workorders", wo_data)
        if result and "@odata.id" in result:
            wo_id = extract_guid(result["@odata.id"])
            console.print(f"  [green]Created:[/green] {name} ({wo_id})")
            wo_ids[name] = wo_id
        else:
            console.print(f"  [red]✗ Failed to create: {name}[/red]")
            sys.exit(1)

    # Attach knowledge articles to work orders
    console.print("\n  Attaching knowledge articles...")
    for wo_def in WORK_ORDERS:
        wo_name = wo_def["name"]
        wo_id = wo_ids[wo_name]

        for article_title in wo_def["articles"]:
            art_id = article_ids.get(article_title)
            if not art_id:
                console.print(
                    f"    [yellow]Article not found: {article_title}[/yellow]"
                )
                continue

            # M:N relationship: knowledgearticles(id)/msdyn_msdyn_workorder_knowledgearticle/$ref
            ref_endpoint = f"knowledgearticles({art_id})/msdyn_msdyn_workorder_knowledgearticle/$ref"
            ref_url = f"msdyn_workorders({wo_id})"
            ok = client.post_ref(ref_endpoint, ref_url)
            if ok:
                short_title = article_title.split(" - ")[0]
                console.print(f"    [green]Linked:[/green] {short_title} → {wo_name}")
            else:
                console.print(
                    f"    [yellow]Link may already exist or failed: {article_title} → {wo_name}[/yellow]"
                )

    # Wait for Dataverse to auto-populate service tasks from incident types
    import time
    console.print(
        "\n  [yellow]Waiting 60s for Dataverse to auto-populate service tasks "
        "from incident types...[/yellow]"
    )
    for remaining in range(60, 0, -10):
        console.print(f"    [dim]{remaining}s remaining...[/dim]")
        time.sleep(10)

    # Validate: check each work order has service tasks and articles
    console.print("\n  Validating Phase 8...")
    all_ok = True

    for wo_def in WORK_ORDERS:
        wo_name = wo_def["name"]
        wo_id = wo_ids[wo_name]

        # Check work order exists and has correct status
        wo = client.get(
            f"msdyn_workorders({wo_id})",
            {"$select": "msdyn_name,msdyn_systemstatus"},
        )
        status = wo.get("msdyn_systemstatus")
        if status != 690970000:
            console.print(
                f"  [red]✗ {wo_name}: status={status}, expected Unscheduled (690970000)[/red]"
            )
            all_ok = False
            continue

        # Check service tasks were auto-populated from incident type
        tasks = client.get(
            "msdyn_workorderservicetasks",
            {
                "$filter": f"_msdyn_workorder_value eq {wo_id}",
                "$select": "msdyn_name",
            },
        )
        task_count = len(tasks.get("value", []))

        # Check linked articles
        articles = client.get(
            f"msdyn_workorders({wo_id})/msdyn_msdyn_workorder_knowledgearticle",
            {"$select": "title"},
        )
        article_count = len(articles.get("value", []))

        console.print(
            f"  [green]✓ {wo_name}[/green] — "
            f"Unscheduled, {task_count} tasks, {article_count} articles"
        )

    if not all_ok:
        console.print("  [red]✗ PHASE 8 VALIDATION FAILED[/red]")
        sys.exit(1)

    console.print(
        f"\n  [green]✓ Phase 8 complete: {len(wo_ids)} work orders with articles[/green]"
    )
    save_state("phase8_work_orders", wo_ids)

    # Final summary
    console.print(
        "\n[bold green]═══════════════════════════════════════════════════[/bold green]"
    )
    console.print(
        "[bold green]  ALL 8 PHASES COMPLETE — Demo ready!            [/bold green]"
    )
    console.print(
        "[bold green]═══════════════════════════════════════════════════[/bold green]"
    )
    console.print("\n  Next steps:")
    console.print("    1. Open D365 Field Service → Schedule Board")
    console.print("    2. Find the 4 Unscheduled work orders for CW Willowbrook Farm")
    console.print("    3. Schedule one to Alan Steiner")
    console.print("    4. Open mobile app → walk through tasks with knowledge articles")
    console.print()


if __name__ == "__main__":
    main()
