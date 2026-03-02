"""
Prison Service Field Service Demo - Create Work Orders

Creates 10 work orders for the Prison Service demo:
- 5 x Printer Installation work orders
- 5 x Network Cable Trunking work orders

Each work order has a realistic description relevant to a prison environment.

Usage:
    cd field-service-mikeo
    python scripts/create_prison_work_orders.py
"""

import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx
from dotenv import load_dotenv


# Load environment from mcp-dataverse-server folder
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.dirname(PROJECT_ROOT)
MCP_DATAVERSE_ENV = os.path.join(WORKSPACE_ROOT, "mcp-dataverse-server", ".env")

if os.path.exists(MCP_DATAVERSE_ENV):
    load_dotenv(MCP_DATAVERSE_ENV)
else:
    load_dotenv()


@dataclass
class DataverseConfig:
    base_url: str
    tenant_id: str
    client_id: str
    client_secret: str

    @classmethod
    def from_env(cls) -> "DataverseConfig":
        return cls(
            base_url=os.getenv("DATAVERSE_BASE_URL", "").rstrip("/"),
            tenant_id=os.getenv("DATAVERSE_TENANT_ID", ""),
            client_id=os.getenv("DATAVERSE_CLIENT_ID", ""),
            client_secret=os.getenv("DATAVERSE_CLIENT_SECRET", ""),
        )

    @property
    def api_url(self) -> str:
        return f"{self.base_url}/api/data/v9.2"


class DataverseClient:
    """Simple Dataverse client for work order creation."""

    def __init__(self, config: DataverseConfig):
        self.config = config
        self._token: str | None = None

    def _get_token(self) -> str:
        if self._token:
            return self._token

        token_url = f"https://login.microsoftonline.com/{self.config.tenant_id}/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "resource": self.config.base_url,
        }

        response = httpx.post(token_url, data=data, timeout=30.0)
        response.raise_for_status()
        result = response.json()

        if "access_token" not in result:
            raise RuntimeError(f"Failed to get token: {result.get('error_description', 'Unknown error')}")

        self._token = result["access_token"]
        return self._token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "Prefer": "return=representation",
        }

    def get(self, entity_set: str, filter_expr: str | None = None, select: list[str] | None = None) -> list[dict[str, Any]]:
        """Query entity set."""
        url = f"{self.config.api_url}/{entity_set}"
        params = {}
        if filter_expr:
            params["$filter"] = filter_expr
        if select:
            params["$select"] = ",".join(select)

        response = httpx.get(url, headers=self._headers(), params=params, timeout=30.0)
        response.raise_for_status()
        return response.json().get("value", [])

    def create(self, entity_set: str, data: dict[str, Any]) -> str:
        """Create a record, return its ID."""
        url = f"{self.config.api_url}/{entity_set}"
        response = httpx.post(url, headers=self._headers(), json=data, timeout=30.0)
        
        # Capture error details before raising
        if response.status_code >= 400:
            try:
                error_body = response.json()
                error_msg = error_body.get("error", {}).get("message", response.text[:500])
            except Exception:
                error_msg = response.text[:500]
            raise RuntimeError(f"HTTP {response.status_code}: {error_msg}")
        
        response.raise_for_status()

        # Extract ID from OData-EntityId header
        entity_id = response.headers.get("OData-EntityId", "")
        match = re.search(r"\(([a-f0-9-]+)\)", entity_id)
        if match:
            return match.group(1)

        # Fallback to response body
        if response.status_code != 204 and response.content:
            body = response.json()
            for key in body:
                if key.endswith("id") and isinstance(body[key], str):
                    return body[key]

        raise RuntimeError(f"Failed to extract ID from create response for {entity_set}")


# Work Order definitions - 5 Printer Installations and 5 Network Cable Trunking
WORK_ORDERS = [
    # Printer Installation work orders
    {
        "type": "Printer Installation",
        "incident_type": "Printer Installation",
        "title": "Admin Block - New Printer for Visitor Registration",
        "description": (
            "Install HP LaserJet M507 network printer in the visitor registration area of "
            "the Admin Block. This printer will be used for printing visitor passes and "
            "registration documents. Must ensure secure network configuration - printer "
            "should only be accessible from registration terminals. Contact Officer Sarah "
            "Thompson on arrival for security escort."
        ),
        "priority": 2,  # Normal
        "days_offset": 1,
    },
    {
        "type": "Printer Installation",
        "incident_type": "Printer Installation",
        "title": "Healthcare Wing - Medical Records Printer",
        "description": (
            "Install new secure printer in the Healthcare Wing for printing medical records "
            "and prescription labels. Strict confidentiality requirements - printer must be "
            "configured with PIN-protected printing for sensitive documents. Coordinate with "
            "the Healthcare Manager and ensure compliance with NHS data handling requirements."
        ),
        "priority": 1,  # High
        "days_offset": 0,
    },
    {
        "type": "Printer Installation",
        "incident_type": "Printer Installation",
        "title": "Education Department - Classroom Printer Replacement",
        "description": (
            "Replace failed printer in Education Block, Classroom 3. The existing HP 400 series "
            "has recurring paper jam issues. Install new HP LaserJet M507 with duplex printing "
            "capability for course materials. Must be completed before morning classes - earliest "
            "access is 07:30. Ask for Paul from Education on arrival."
        ),
        "priority": 2,  # Normal
        "days_offset": 2,
    },
    {
        "type": "Printer Installation",
        "incident_type": "Printer Installation",
        "title": "Reception - Gate Entry Pass Printer",
        "description": (
            "Install dedicated thermal/laser printer at Reception Gate 1 for printing temporary "
            "pass badges. High reliability requirement as this is a critical entry point. Printer "
            "must integrate with existing visitor management software. Security clearance confirmed "
            "for entry - report to Main Gate with photo ID."
        ),
        "priority": 1,  # High
        "days_offset": 3,
    },
    {
        "type": "Printer Installation",
        "incident_type": "Printer Installation",
        "title": "Workshops - Industrial Training Centre Printer",
        "description": (
            "Install network printer in the Industrial Training Centre workshop area. This will "
            "be used for printing health and safety documentation, work instructions, and training "
            "certificates. Dusty environment - consider protective cover for the unit. Liaise with "
            "Workshop Supervisor Mr. Davies for site access."
        ),
        "priority": 3,  # Low
        "days_offset": 5,
    },
    # Network Cable Trunking work orders
    {
        "type": "Network Cable Trunking",
        "incident_type": "Network Cable Trunking Installation",
        "title": "C-Wing - CCTV System Network Extension",
        "description": (
            "Install 40 metres of cable trunking along C-Wing corridor to support new CCTV camera "
            "positions. Run CAT6 cabling from the central communications room to 4 new camera "
            "locations. Ensure trunking is securely mounted and tamper-resistant. All work must "
            "be completed during association period (10:00-11:30) when wing is clear."
        ),
        "priority": 1,  # High
        "days_offset": 1,
    },
    {
        "type": "Network Cable Trunking",
        "incident_type": "Network Cable Trunking Installation",
        "title": "Control Room - Redundant Network Link",
        "description": (
            "Install cable trunking and CAT6 network cables for a redundant network link to the "
            "Control Room. Critical infrastructure project - provides backup connectivity for "
            "security monitoring systems. Route from Server Room B via secure corridor. Work "
            "in coordination with IT Security team - contact Mike Reynolds prior to starting."
        ),
        "priority": 1,  # High
        "days_offset": 4,
    },
    {
        "type": "Network Cable Trunking",
        "incident_type": "Network Cable Trunking Installation",
        "title": "Staff Training Room - Conference System Setup",
        "description": (
            "Install network cabling infrastructure for the new video conferencing system in "
            "Staff Training Room 2. Run 25 metres of trunking from the nearest network point "
            "to ceiling-mount and desk locations. Must accommodate 2x CAT6 drops for display "
            "and camera/microphone system. Work permitted during weekdays 09:00-16:00 only."
        ),
        "priority": 2,  # Normal
        "days_offset": 6,
    },
    {
        "type": "Network Cable Trunking",
        "incident_type": "Network Cable Trunking Installation",
        "title": "Gymnasium - Access Control System Cabling",
        "description": (
            "Install network cabling to support new electronic door access control system at "
            "the Gymnasium entrance and emergency exits. Requires 3 cable runs from D-Wing "
            "communications room. Trunking must be vandal-resistant specification. Site survey "
            "completed - refer to attached diagrams. Contact Facilities on extension 4421."
        ),
        "priority": 2,  # Normal
        "days_offset": 7,
    },
    {
        "type": "Network Cable Trunking",
        "incident_type": "Network Cable Trunking Installation",
        "title": "Kitchen Block - Stockroom Inventory Terminal",
        "description": (
            "Run network cabling to new inventory terminal location in Kitchen Block stockroom. "
            "Food preparation area - trunking must be hygiene-grade white PVC specification. "
            "15 metres from nearest network point in adjacent corridor. Coordinate timing with "
            "Catering Manager to avoid meal preparation periods. Best window: 14:00-16:30."
        ),
        "priority": 3,  # Low
        "days_offset": 10,
    },
]


def main():
    config = DataverseConfig.from_env()

    if not config.base_url:
        print("ERROR: DATAVERSE_BASE_URL not set")
        sys.exit(1)

    print(f"Connecting to: {config.base_url}")
    client = DataverseClient(config)

    # Look up required references
    print("\n[1/4] Looking up Work Order Types and Incident Types...")

    # Get Work Order Types
    wot_printer = client.get("msdyn_workordertypes", filter_expr="msdyn_name eq 'Printer Installation'")
    wot_network = client.get("msdyn_workordertypes", filter_expr="msdyn_name eq 'Network Cable Trunking'")

    if not wot_printer:
        print("ERROR: Work Order Type 'Printer Installation' not found. Run setup_prison_demo.py first.")
        sys.exit(1)
    if not wot_network:
        print("ERROR: Work Order Type 'Network Cable Trunking' not found. Run setup_prison_demo.py first.")
        sys.exit(1)

    wot_ids = {
        "Printer Installation": wot_printer[0]["msdyn_workordertypeid"],
        "Network Cable Trunking": wot_network[0]["msdyn_workordertypeid"],
    }
    print(f"  ✓ Printer Installation: {wot_ids['Printer Installation']}")
    print(f"  ✓ Network Cable Trunking: {wot_ids['Network Cable Trunking']}")

    # Get Incident Types
    inc_printer = client.get("msdyn_incidenttypes", filter_expr="msdyn_name eq 'Printer Installation'")
    inc_network = client.get("msdyn_incidenttypes", filter_expr="msdyn_name eq 'Network Cable Trunking Installation'")

    if not inc_printer:
        print("WARNING: Incident Type 'Printer Installation' not found. Work orders will be created without primary incident.")
        inc_ids = {}
    else:
        inc_ids = {
            "Printer Installation": inc_printer[0]["msdyn_incidenttypeid"] if inc_printer else None,
            "Network Cable Trunking Installation": inc_network[0]["msdyn_incidenttypeid"] if inc_network else None,
        }
        print(f"  ✓ Printer Installation Incident: {inc_ids.get('Printer Installation', 'N/A')}")
        print(f"  ✓ Network Cable Trunking Incident: {inc_ids.get('Network Cable Trunking Installation', 'N/A')}")

    # Get HM Prison Service account
    print("\n[2/4] Looking up Service Account...")
    accounts = client.get("accounts", filter_expr="name eq 'HM Prison Service'")
    if not accounts:
        print("ERROR: Account 'HM Prison Service' not found. Run setup_prison_demo.py first.")
        sys.exit(1)
    account_id = accounts[0]["accountid"]
    print(f"  ✓ HM Prison Service: {account_id}")

    # Get Priority records
    print("\n[3/4] Looking up Priority values...")
    priorities = client.get("msdyn_priorities", select=["msdyn_priorityid", "msdyn_name"])
    priority_map = {p["msdyn_name"]: p["msdyn_priorityid"] for p in priorities}
    
    # Map our simple priority values to actual priority names
    # Field Service typically has: Critical, High, Medium, Low priorities
    priority_name_map = {
        1: "High",     # Map our priority 1 to "High"
        2: "Medium",   # Map our priority 2 to "Medium" or "Normal"
        3: "Low",      # Map our priority 3 to "Low"
    }
    
    # Try to find matching priorities
    for num, name in priority_name_map.items():
        if name in priority_map:
            print(f"  ✓ Priority {num} ({name}): {priority_map[name]}")
        else:
            # Try alternative names
            for alt_name in [name, name.lower(), name.upper()]:
                if alt_name in priority_map:
                    priority_name_map[num] = alt_name
                    print(f"  ✓ Priority {num} ({alt_name}): {priority_map[alt_name]}")
                    break
    
    if not priority_map:
        print("  ⚠ No priority records found - work orders will be created without priority")

    # Create Work Orders
    print("\n[4/4] Creating Work Orders...")
    print("=" * 60)

    created_count = 0

    for i, wo_def in enumerate(WORK_ORDERS, 1):
        # Build work order data
        wo_data: dict[str, Any] = {
            "msdyn_name": wo_def["title"],
            "msdyn_workordersummary": wo_def["description"],
            "msdyn_serviceaccount@odata.bind": f"/accounts({account_id})",
            "msdyn_workordertype@odata.bind": f"/msdyn_workordertypes({wot_ids[wo_def['type']]})",
            "msdyn_systemstatus": 690970000,  # Unscheduled
        }
        
        # Add primary incident type if available
        if wo_def["incident_type"] in inc_ids and inc_ids[wo_def["incident_type"]]:
            wo_data["msdyn_primaryincidenttype@odata.bind"] = f"/msdyn_incidenttypes({inc_ids[wo_def['incident_type']]})"
        
        # Add priority if we have the mapping
        priority_num = wo_def["priority"]
        priority_name = priority_name_map.get(priority_num)
        if priority_name and priority_name in priority_map:
            wo_data["msdyn_priority@odata.bind"] = f"/msdyn_priorities({priority_map[priority_name]})"

        # Remove None bindings
        wo_data = {k: v for k, v in wo_data.items() if v is not None}

        try:
            wo_id = client.create("msdyn_workorders", wo_data)
            created_count += 1
            priority_labels = {1: "High", 2: "Medium", 3: "Low"}
            priority_display = priority_labels.get(wo_def["priority"], "Medium")
            print(f"{i:2}. ✓ {wo_def['title']}")
            print(f"       Type: {wo_def['type']} | Priority: {priority_display}")
            print(f"       ID: {wo_id}")
        except Exception as e:
            print(f"{i:2}. ✗ {wo_def['title']}")
            print(f"       ERROR: {e}")

    print("=" * 60)
    print(f"\n✅ Created {created_count} of {len(WORK_ORDERS)} work orders")

    print("\nNext Steps:")
    print("  1. Open Dynamics 365 Field Service")
    print("  2. Navigate to Work Orders")
    print("  3. Use the Schedule Board to assign work orders to David So")
    print("  4. View work orders on the mobile app")


if __name__ == "__main__":
    main()
