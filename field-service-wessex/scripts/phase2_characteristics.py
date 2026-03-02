"""Phase 2: Create 7 characteristics and assign to Alan Steiner.

Usage:
    cd field-service-wessex
    python scripts/phase2_characteristics.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from helpers import (
    ALAN_STEINER_RESOURCE_ID,
    console,
    find_or_create,
    get_client,
    save_state,
)

# characteristictype: 1 = Skill, 2 = Certification
CHARACTERISTICS = [
    {"name": "Water Mains Repair", "characteristictype": 1},
    {"name": "Smart Meter Installation", "characteristictype": 1},
    {"name": "Drainage & Sewer Operations", "characteristictype": 1},
    {"name": "Water Quality Sampling", "characteristictype": 1},
    {"name": "CSCS Card (Water)", "characteristictype": 2},
    {"name": "Confined Space Entry", "characteristictype": 2},
    {"name": "NRSWA Street Works", "characteristictype": 2},
]


def main():
    console.print("\n[bold magenta]═══ Phase 2: Characteristics ═══[/bold magenta]")
    client = get_client()

    # Verify Alan Steiner exists
    console.print(f"\n  Looking up Alan Steiner ({ALAN_STEINER_RESOURCE_ID})...")
    try:
        resource = client.get(
            f"bookableresources({ALAN_STEINER_RESOURCE_ID})",
            {"$select": "bookableresourceid,name"},
        )
        console.print(
            f"  [green]✓ Found bookable resource: {resource.get('name')}[/green]"
        )
    except Exception as e:
        console.print(f"  [red]✗ Alan Steiner not found: {e}[/red]")
        sys.exit(1)

    # Create characteristics and link to resource
    char_ids: dict[str, str] = {}

    for char_def in CHARACTERISTICS:
        name = char_def["name"]
        ctype = char_def["characteristictype"]
        type_label = "Skill" if ctype == 1 else "Certification"

        char_id = find_or_create(
            client,
            "characteristics",
            "name",
            name,
            {"characteristictype": ctype},
        )
        char_ids[name] = char_id

        # Check if already linked to Alan Steiner
        existing_links = client.get(
            "bookableresourcecharacteristics",
            {
                "$filter": (
                    f"_resource_value eq {ALAN_STEINER_RESOURCE_ID} "
                    f"and _characteristic_value eq {char_id}"
                ),
                "$top": "1",
            },
        )
        if existing_links.get("value"):
            console.print(f"    [yellow]Already linked:[/yellow] {name} ({type_label})")
        else:
            result = client.post(
                "bookableresourcecharacteristics",
                {
                    "Resource@odata.bind": f"/bookableresources({ALAN_STEINER_RESOURCE_ID})",
                    "Characteristic@odata.bind": f"/characteristics({char_id})",
                },
            )
            if result:
                console.print(
                    f"    [green]Linked:[/green] {name} ({type_label}) → Alan Steiner"
                )
            else:
                console.print(f"    [red]✗ Failed to link {name}[/red]")
                sys.exit(1)

    # Validate: count all characteristics linked to Alan Steiner
    console.print("\n  Validating Phase 2...")
    all_links = client.get(
        "bookableresourcecharacteristics",
        {
            "$filter": f"_resource_value eq {ALAN_STEINER_RESOURCE_ID}",
            "$expand": "Characteristic($select=name,characteristictype)",
        },
    )
    linked = all_links.get("value", [])

    # Check our 7 are present
    linked_names = set()
    for link in linked:
        char = link.get("Characteristic", {})
        if char:
            linked_names.add(char.get("name"))

    expected_names = {c["name"] for c in CHARACTERISTICS}
    missing = expected_names - linked_names
    if missing:
        console.print(
            f"  [red]✗ VALIDATION FAILED — missing characteristics: {missing}[/red]"
        )
        sys.exit(1)

    for link in linked:
        char = link.get("Characteristic", {})
        if char and char.get("name") in expected_names:
            ctype = "Skill" if char.get("characteristictype") == 1 else "Certification"
            console.print(f"  [green]✓ {char['name']} ({ctype})[/green]")

    console.print(
        f"\n  [green]✓ Phase 2 complete: {len(expected_names)} characteristics "
        f"linked to Alan Steiner (total on resource: {len(linked)})[/green]"
    )
    save_state("phase2_characteristics", char_ids)


if __name__ == "__main__":
    main()
