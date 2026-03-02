"""Phase 4: Create 20 Service Task Types.

Usage:
    cd field-service-wessex
    python scripts/phase4_service_task_types.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from helpers import (
    console,
    find_or_create,
    get_client,
    save_state,
    validate_count,
)

# Grouped by scenario for clarity; all go into the same entity set
SERVICE_TASK_TYPES = [
    # — Water Leak Repair (6) —
    {
        "name": "Site Assessment & Traffic Management",
        "duration": 15,
        "description": "Assess leak location, set up barriers/signage, identify pipe route using CAT scanner",
    },
    {
        "name": "Isolate Water Supply",
        "duration": 10,
        "description": "Locate and operate stop valves to isolate affected section of mains or supply pipe",
    },
    {
        "name": "Excavate to Expose Pipe",
        "duration": 30,
        "description": "Hand/machine dig to expose damaged pipe section; support trench if depth >1.2m",
    },
    {
        "name": "Repair or Replace Pipe Section",
        "duration": 45,
        "description": "Apply repair clamp, slip coupling, or cut and replace with MDPE pipe",
    },
    {
        "name": "Pressure Test & Flush",
        "duration": 15,
        "description": "Restore supply, pressure test repair, flush until clear; chlorine residual >=0.2 mg/l",
    },
    {
        "name": "Reinstate & Customer Notification",
        "duration": 20,
        "description": "Backfill excavation, apply temporary/permanent reinstatement, notify customers",
    },
    # — Smart Meter Installation (6) —
    {
        "name": "Locate Meter Chamber & Stop Tap",
        "duration": 10,
        "description": "Find existing meter box/stop tap, assess access, condition, and chamber state",
    },
    {
        "name": "Remove Existing Meter",
        "duration": 10,
        "description": "Record final reading, photograph, disconnect and remove old meter",
    },
    {
        "name": "Install Smart Meter Unit",
        "duration": 15,
        "description": "Fit new smart meter with correct flow direction, new washers, antenna oriented upward",
    },
    {
        "name": "Commission & Signal Test",
        "duration": 10,
        "description": "Power on smart module, scan barcode, verify network connectivity (min 3 bars)",
    },
    {
        "name": "Verify Readings & Leak Check",
        "duration": 10,
        "description": "Compare readings, run water to confirm flow accuracy, check all joints for leaks",
    },
    {
        "name": "Customer Handover",
        "duration": 10,
        "description": "Explain smart meter benefits, assist with app setup, leave welcome pack",
    },
    # — Sewer Blockage Clearance (4) —
    {
        "name": "Site Assessment & Blockage Location",
        "duration": 15,
        "description": "Identify affected manholes, interview customer, assess symptoms and extent",
    },
    {
        "name": "CCTV Drain Survey",
        "duration": 20,
        "description": "Deploy CCTV camera to identify blockage type (fat/roots/debris) and exact location",
    },
    {
        "name": "High-Pressure Jetting",
        "duration": 30,
        "description": "Clear blockage using appropriate nozzle and jetting pressure, remove debris",
    },
    {
        "name": "Post-Clearance CCTV & Report",
        "duration": 15,
        "description": "Confirm clearance, record pipe condition, flag structural defects for future rehab",
    },
    # — Water Quality Investigation (4) —
    {
        "name": "Customer Interview & Visual Inspection",
        "duration": 10,
        "description": "Discuss symptoms, inspect affected taps, check internal plumbing for lead/corrosion",
    },
    {
        "name": "Pressure & Flow Testing",
        "duration": 10,
        "description": "Attach gauge to kitchen tap, record static and flow pressure (target >=1.0 bar)",
    },
    {
        "name": "Water Sampling & On-Site Testing",
        "duration": 15,
        "description": "Collect first-draw and flushed samples; test chlorine, pH, turbidity on-site",
    },
    {
        "name": "Flushing & Resolution",
        "duration": 15,
        "description": "Flush supply pipe until clear, confirm chlorine >=0.2 mg/l, dispatch samples to lab",
    },
]


def main():
    console.print("\n[bold magenta]═══ Phase 4: Service Task Types ═══[/bold magenta]")
    client = get_client()

    task_ids: dict[str, str] = {}

    for task in SERVICE_TASK_TYPES:
        name = task["name"]
        task_id = find_or_create(
            client,
            "msdyn_servicetasktypes",
            "msdyn_name",
            name,
            {
                "msdyn_estimatedduration": task["duration"],
                "msdyn_description": task["description"],
            },
        )
        task_ids[name] = task_id

    # Validate
    console.print("\n  Validating Phase 4...")
    all_names = [t["name"] for t in SERVICE_TASK_TYPES]
    ok = validate_count(
        client, "msdyn_servicetasktypes", "msdyn_name", all_names, "Service Task Types"
    )
    if not ok:
        sys.exit(1)

    console.print(
        f"\n  [green]✓ Phase 4 complete: {len(task_ids)} service task types[/green]"
    )
    save_state("phase4_service_task_types", task_ids)


if __name__ == "__main__":
    main()
