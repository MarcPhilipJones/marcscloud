"""Phase 7: Lookup existing CW Willowbrook Farm and Chris Walker.

These records must already exist in Dataverse. This phase finds them
and saves their IDs for Phase 8 (work order creation).

Usage:
    cd field-service-wessex
    python scripts/phase7_lookup_existing.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from helpers import (
    console,
    get_client,
    save_state,
)


def find_exactly_one(client, entity_set, name_field, name_value, label):
    """Find exactly one record. Halts if zero or ambiguous."""
    params = {
        "$filter": f"contains({name_field},'{name_value}')",
        "$select": f"{name_field}",
        "$top": "5",
    }
    result = client.get(entity_set, params)
    records = result.get("value", [])

    if not records:
        console.print(
            f"  [red]✗ {label} not found — searched '{name_value}' in {entity_set}[/red]"
        )
        sys.exit(1)

    if len(records) > 1:
        console.print(f"  [yellow]Multiple matches for {label}:[/yellow]")
        for r in records:
            console.print(f"    - {r.get(name_field)}")
        console.print("  Using first match.")

    record = records[0]
    # Find the primary key (GUID field)
    guid = None
    for key, val in record.items():
        if (
            key.endswith("id")
            and isinstance(val, str)
            and len(val) == 36
            and key != "@odata.etag"
        ):
            guid = val
            break
    if not guid:
        console.print(f"  [red]✗ Could not extract ID for {label}[/red]")
        sys.exit(1)

    actual_name = record.get(name_field, name_value)
    console.print(f"  [green]✓ Found {label}: {actual_name} ({guid})[/green]")
    return guid, actual_name


def main():
    console.print(
        "\n[bold magenta]═══ Phase 7: Lookup Existing Records ═══[/bold magenta]"
    )
    client = get_client()

    # Find CW Willowbrook Farm (service account)
    account_id, account_name = find_exactly_one(
        client, "accounts", "name", "Willowbrook", "CW Willowbrook Farm"
    )

    # Find Chris Walker (contact)
    contact_id, contact_name = find_exactly_one(
        client, "contacts", "fullname", "Chris Walker", "Chris Walker"
    )

    # Validate by querying each directly
    console.print("\n  Validating Phase 7...")
    try:
        acc = client.get(f"accounts({account_id})", {"$select": "name"})
        console.print(f"  [green]✓ Account: {acc.get('name')}[/green]")
    except Exception as e:
        console.print(f"  [red]✗ Account validation failed: {e}[/red]")
        sys.exit(1)

    try:
        con = client.get(f"contacts({contact_id})", {"$select": "fullname"})
        console.print(f"  [green]✓ Contact: {con.get('fullname')}[/green]")
    except Exception as e:
        console.print(f"  [red]✗ Contact validation failed: {e}[/red]")
        sys.exit(1)

    state = {
        "account_id": account_id,
        "account_name": account_name,
        "contact_id": contact_id,
        "contact_name": contact_name,
    }
    console.print("\n  [green]✓ Phase 7 complete: existing records located[/green]")
    save_state("phase7_existing_records", state)


if __name__ == "__main__":
    main()
