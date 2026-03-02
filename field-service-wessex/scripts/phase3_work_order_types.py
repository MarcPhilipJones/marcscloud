"""Phase 3: Create 4 Work Order Types.

Usage:
    cd field-service-wessex
    python scripts/phase3_work_order_types.py
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

WORK_ORDER_TYPES = [
    "Water Leak Repair",
    "Smart Meter Installation",
    "Sewer Blockage Clearance",
    "Water Quality Investigation",
]


def main():
    console.print("\n[bold magenta]═══ Phase 3: Work Order Types ═══[/bold magenta]")
    client = get_client()

    wot_ids: dict[str, str] = {}

    for name in WORK_ORDER_TYPES:
        wot_id = find_or_create(
            client,
            "msdyn_workordertypes",
            "msdyn_name",
            name,
            {
                "msdyn_incidentrequired": True,
                "msdyn_taxable": False,
            },
        )
        wot_ids[name] = wot_id

    # Validate
    console.print("\n  Validating Phase 3...")
    ok = validate_count(
        client,
        "msdyn_workordertypes",
        "msdyn_name",
        WORK_ORDER_TYPES,
        "Work Order Types",
    )
    if not ok:
        sys.exit(1)

    console.print(
        f"\n  [green]✓ Phase 3 complete: {len(wot_ids)} work order types[/green]"
    )
    save_state("phase3_work_order_types", wot_ids)


if __name__ == "__main__":
    main()
