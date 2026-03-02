"""Phase 5: Create 4 Incident Types and link Service Tasks to each.

Usage:
    cd field-service-wessex
    python scripts/phase5_incident_types.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from helpers import (
    console,
    find_or_create,
    get_client,
    load_state,
    save_state,
)

# Each incident type: name, duration (min), work_order_type key, ordered task names
INCIDENT_TYPES = [
    {
        "name": "Emergency Mains Leak",
        "duration": 135,
        "description": "Emergency response to reported mains or supply pipe water leak",
        "wot_key": "Water Leak Repair",
        "tasks": [
            "Site Assessment & Traffic Management",
            "Isolate Water Supply",
            "Excavate to Expose Pipe",
            "Repair or Replace Pipe Section",
            "Pressure Test & Flush",
            "Reinstate & Customer Notification",
        ],
    },
    {
        "name": "Residential Smart Meter Installation",
        "duration": 65,
        "description": "Install or upgrade residential water meter to smart meter",
        "wot_key": "Smart Meter Installation",
        "tasks": [
            "Locate Meter Chamber & Stop Tap",
            "Remove Existing Meter",
            "Install Smart Meter Unit",
            "Commission & Signal Test",
            "Verify Readings & Leak Check",
            "Customer Handover",
        ],
    },
    {
        "name": "Public Sewer Blockage",
        "duration": 80,
        "description": "Investigate and clear blockage on the public sewer network",
        "wot_key": "Sewer Blockage Clearance",
        "tasks": [
            "Site Assessment & Blockage Location",
            "CCTV Drain Survey",
            "High-Pressure Jetting",
            "Post-Clearance CCTV & Report",
        ],
    },
    {
        "name": "Water Quality Customer Complaint",
        "duration": 50,
        "description": "Investigate customer report of discoloured water, taste/smell, or low pressure",
        "wot_key": "Water Quality Investigation",
        "tasks": [
            "Customer Interview & Visual Inspection",
            "Pressure & Flow Testing",
            "Water Sampling & On-Site Testing",
            "Flushing & Resolution",
        ],
    },
]


def main():
    console.print("\n[bold magenta]═══ Phase 5: Incident Types ═══[/bold magenta]")
    client = get_client()

    # Load state from previous phases
    wot_ids = load_state("phase3_work_order_types")
    task_ids = load_state("phase4_service_task_types")

    incident_ids: dict[str, str] = {}

    for it_def in INCIDENT_TYPES:
        name = it_def["name"]
        wot_id = wot_ids[it_def["wot_key"]]

        # Create incident type
        it_id = find_or_create(
            client,
            "msdyn_incidenttypes",
            "msdyn_name",
            name,
            {
                "msdyn_estimatedduration": it_def["duration"],
                "msdyn_description": it_def["description"],
                "msdyn_defaultworkordertype@odata.bind": f"/msdyn_workordertypes({wot_id})",
            },
        )
        incident_ids[name] = it_id

        # Link service tasks in order
        console.print(f"    Linking {len(it_def['tasks'])} tasks...")
        for order, task_name in enumerate(it_def["tasks"], start=1):
            task_type_id = task_ids[task_name]

            # Check if already linked
            existing = client.get(
                "msdyn_incidenttypeservicetasks",
                {
                    "$filter": (
                        f"_msdyn_incidenttype_value eq {it_id} "
                        f"and _msdyn_tasktype_value eq {task_type_id}"
                    ),
                    "$top": "1",
                },
            )
            if existing.get("value"):
                console.print(
                    f"      [yellow]Already linked:[/yellow] {order}. {task_name}"
                )
                continue

            link_name = f"Step {order} - {task_name}"
            result = client.post(
                "msdyn_incidenttypeservicetasks",
                {
                    "msdyn_name": link_name,
                    "msdyn_incidenttype@odata.bind": f"/msdyn_incidenttypes({it_id})",
                    "msdyn_tasktype@odata.bind": f"/msdyn_servicetasktypes({task_type_id})",
                    "msdyn_lineorder": order,
                },
            )
            if result:
                console.print(f"      [green]Linked:[/green] {order}. {task_name}")
            else:
                console.print(f"      [red]✗ Failed to link: {task_name}[/red]")
                sys.exit(1)

    # Validate: check each incident type has correct task count
    console.print("\n  Validating Phase 5...")
    all_ok = True
    for it_def in INCIDENT_TYPES:
        name = it_def["name"]
        it_id = incident_ids[name]
        expected_count = len(it_def["tasks"])

        linked_tasks = client.get(
            "msdyn_incidenttypeservicetasks",
            {
                "$filter": f"_msdyn_incidenttype_value eq {it_id}",
                "$select": "msdyn_name,msdyn_lineorder",
                "$orderby": "msdyn_lineorder asc",
            },
        )
        actual = linked_tasks.get("value", [])
        if len(actual) < expected_count:
            console.print(
                f"  [red]✗ {name}: expected {expected_count} tasks, found {len(actual)}[/red]"
            )
            all_ok = False
        else:
            task_list = ", ".join(
                t.get("msdyn_name", "?") for t in actual[:expected_count]
            )
            console.print(
                f"  [green]✓ {name}: {len(actual)} tasks[/green] — {task_list}"
            )

    if not all_ok:
        console.print("  [red]✗ PHASE 5 VALIDATION FAILED[/red]")
        sys.exit(1)

    console.print(
        f"\n  [green]✓ Phase 5 complete: {len(incident_ids)} incident types with linked tasks[/green]"
    )
    save_state("phase5_incident_types", incident_ids)


if __name__ == "__main__":
    main()
