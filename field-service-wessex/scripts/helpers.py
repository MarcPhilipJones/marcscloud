"""Shared helpers, constants, and HTML styles for Contoso Utilities demo scripts.

Every phase script imports from here to avoid duplication.
"""

import json
import os
import sys

# ─── Path setup ──────────────────────────────────────────────────────────────
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)
STATE_DIR = os.path.join(PROJECT_ROOT, "state")

sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from field_service_wessex.dataverse_client import (  # noqa: E402
    DataverseClient,
    extract_guid,
)
from rich.console import Console  # noqa: E402

console = Console()

# ─── Constants ────────────────────────────────────────────────────────────────
ALAN_STEINER_RESOURCE_ID = "b8dddd9c-3b61-ef11-bfe2-002248a36d0e"

# ─── Inline HTML styles (Dataverse strips <style> blocks) ────────────────────
H1 = 'style="font-family: Segoe UI, sans-serif; font-size: 18pt; color: #2c3e50; margin-bottom: 15px;"'
H2 = 'style="font-family: Segoe UI, sans-serif; font-size: 14pt; color: #2c3e50; margin-top: 20px; margin-bottom: 10px;"'
P = 'style="font-family: Segoe UI, sans-serif; font-size: 12pt; line-height: 1.6; margin-bottom: 15px;"'
LI = 'style="font-family: Segoe UI, sans-serif; font-size: 12pt; margin-bottom: 8px;"'
UL = 'style="margin: 0 0 15px 20px; padding: 0;"'


# ─── State persistence ───────────────────────────────────────────────────────


def save_state(phase_name: str, data: dict) -> None:
    """Save phase output to state/<phase_name>.json."""
    os.makedirs(STATE_DIR, exist_ok=True)
    path = os.path.join(STATE_DIR, f"{phase_name}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    console.print(f"  [dim]State saved → state/{phase_name}.json[/dim]")


def load_state(phase_name: str) -> dict:
    """Load phase output from state/<phase_name>.json. Halts if missing."""
    path = os.path.join(STATE_DIR, f"{phase_name}.json")
    if not os.path.exists(path):
        console.print(f"  [red]✗ Missing state file: state/{phase_name}.json[/red]")
        console.print("  [red]  Run the earlier phase first.[/red]")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


# ─── Dataverse helpers ────────────────────────────────────────────────────────


def get_client() -> DataverseClient:
    """Create a DataverseClient and verify connectivity."""
    client = DataverseClient()
    console.print(f"  [dim]Connecting to: {client.base_url}[/dim]")
    try:
        client.get("WhoAmI")
        console.print("  [green]✓ Connected to Dataverse[/green]")
    except Exception as e:
        console.print(f"  [red]✗ Connection failed: {e}[/red]")
        sys.exit(1)
    return client


def find_or_create(
    client: DataverseClient,
    entity_set: str,
    name_field: str,
    name_value: str,
    data: dict,
) -> str:
    """Find existing record by name or create new one. Returns GUID."""
    params = {
        "$filter": f"{name_field} eq '{name_value}'",
        "$top": "1",
    }
    try:
        result = client.get(entity_set, params)
        records = result.get("value", [])
        if records:
            for key in records[0]:
                if key.endswith("id") and key not in (
                    "@odata.etag",
                    "_transactioncurrencyid_value",
                ):
                    if isinstance(records[0][key], str) and len(records[0][key]) == 36:
                        console.print(f"  [yellow]Found:[/yellow] {name_value}")
                        return records[0][key]
    except Exception:
        pass

    data[name_field] = name_value
    result = client.post(entity_set, data)
    if result and "@odata.id" in result:
        guid = extract_guid(result["@odata.id"])
        console.print(f"  [green]Created:[/green] {name_value} ({guid})")
        return guid
    raise RuntimeError(f"Failed to create {name_value} in {entity_set}")


def find_record(
    client: DataverseClient,
    entity_set: str,
    name_field: str,
    name_value: str,
) -> str | None:
    """Find a record by name (contains). Returns GUID or None."""
    params = {"$filter": f"contains({name_field},'{name_value}')", "$top": "1"}
    try:
        result = client.get(entity_set, params)
        records = result.get("value", [])
        if records:
            for key in records[0]:
                if key.endswith("id") and key not in ("@odata.etag",):
                    if isinstance(records[0][key], str) and len(records[0][key]) == 36:
                        return records[0][key]
    except Exception:
        pass
    return None


def validate_count(
    client: DataverseClient,
    entity_set: str,
    name_field: str,
    name_values: list[str],
    label: str,
) -> bool:
    """Validate that all named records exist. Returns True if all found."""
    missing = []
    for name in name_values:
        if not find_record(client, entity_set, name_field, name):
            missing.append(name)
    if missing:
        console.print(
            f"  [red]✗ VALIDATION FAILED for {label} — missing: {missing}[/red]"
        )
        return False
    console.print(
        f"  [green]✓ Validated {label}: all {len(name_values)} records exist[/green]"
    )
    return True
