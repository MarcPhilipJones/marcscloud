"""
Prison Service Field Service Demo Setup Script

Creates all required data for a Field Service demo:
- Work Order Types (Printer Installation, Network Cable Trunking)
- Incident Types with Service Tasks
- Characteristics for David So
- Customer Account (HM Prison Service)
- Products (Printer, Cable Trunking, CAT6 Cable, Connectors)

Usage:
    cd field-service-mikeo
    python scripts/setup_prison_demo.py
"""

import os
import re
import sys
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import httpx
from dotenv import load_dotenv


# Load environment from parent PowerPlatform folder
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.dirname(PROJECT_ROOT)
POWERPLATFORM_ENV = os.path.join(WORKSPACE_ROOT, "PowerPlatform", ".env")

if os.path.exists(POWERPLATFORM_ENV):
    load_dotenv(POWERPLATFORM_ENV)
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
    """Simple Dataverse client for demo setup."""

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

    def get_by_id(self, entity_set: str, entity_id: str) -> dict[str, Any]:
        """Get single record by ID."""
        url = f"{self.config.api_url}/{entity_set}({entity_id})"
        response = httpx.get(url, headers=self._headers(), timeout=30.0)
        response.raise_for_status()
        return response.json()

    def create(self, entity_set: str, data: dict[str, Any]) -> str:
        """Create a record, return its ID."""
        url = f"{self.config.api_url}/{entity_set}"
        response = httpx.post(url, headers=self._headers(), json=data, timeout=30.0)
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

    def update(self, entity_set: str, entity_id: str, data: dict[str, Any]) -> None:
        """Update a record."""
        url = f"{self.config.api_url}/{entity_set}({entity_id})"
        response = httpx.patch(url, headers=self._headers(), json=data, timeout=30.0)
        response.raise_for_status()

    def find_or_create(self, entity_set: str, filter_expr: str, data: dict[str, Any], id_field: str) -> tuple[str, bool]:
        """Find existing record or create new one. Returns (id, was_created)."""
        existing = self.get(entity_set, filter_expr=filter_expr)
        if existing:
            return existing[0][id_field], False
        new_id = self.create(entity_set, data)
        return new_id, True


def duration_minutes_to_iso8601(minutes: int) -> str:
    """Convert minutes to ISO 8601 duration string (PT30M format)."""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0 and mins > 0:
        return f"PT{hours}H{mins}M"
    elif hours > 0:
        return f"PT{hours}H"
    else:
        return f"PT{mins}M"


class PrisonDemoSetup:
    """Sets up all Field Service demo data for Prison Service scenario."""

    def __init__(self, client: DataverseClient):
        self.client = client
        self.created_ids: dict[str, str] = {}

    def run(self) -> None:
        """Execute full demo setup."""
        print("\n" + "=" * 60)
        print("Prison Service Field Service Demo Setup")
        print("=" * 60)

        # 1. Create Work Order Types
        print("\n[1/7] Creating Work Order Types...")
        self.create_work_order_types()

        # 2. Create Customer Account
        print("\n[2/7] Creating Customer Account...")
        self.create_customer_account()

        # 3. Create Products
        print("\n[3/7] Creating Products...")
        self.create_products()

        # 4. Create Characteristics
        print("\n[4/7] Creating Characteristics...")
        self.create_characteristics()

        # 5. Find David So and assign characteristics
        print("\n[5/7] Finding David So and assigning Characteristics...")
        self.assign_characteristics_to_david()

        # 6. Create Incident Types
        print("\n[6/7] Creating Incident Types...")
        self.create_incident_types()

        # 7. Create Service Tasks for each Incident Type
        print("\n[7/7] Creating Service Tasks...")
        self.create_service_tasks()

        print("\n" + "=" * 60)
        print("Demo setup complete!")
        print("=" * 60)
        self.print_summary()

    def create_work_order_types(self) -> None:
        """Create the two work order types."""
        work_order_types = [
            {
                "msdyn_name": "Printer Installation",
                "msdyn_incidentrequired": True,
                "msdyn_taxable": False,
            },
            {
                "msdyn_name": "Network Cable Trunking",
                "msdyn_incidentrequired": True,
                "msdyn_taxable": False,
            },
        ]

        for wot in work_order_types:
            name = wot["msdyn_name"]
            wot_id, created = self.client.find_or_create(
                "msdyn_workordertypes",
                f"msdyn_name eq '{name}'",
                wot,
                "msdyn_workordertypeid",
            )
            self.created_ids[f"wot_{name}"] = wot_id
            status = "Created" if created else "Already exists"
            print(f"  ✓ {name}: {wot_id} ({status})")

    def create_customer_account(self) -> None:
        """Create HM Prison Service account."""
        account_data = {
            "name": "HM Prison Service",
            "description": "Her Majesty's Prison and Probation Service - Demo Account",
            "address1_line1": "HMP Demonstration",
            "address1_line2": "Prison Lane",
            "address1_city": "Birmingham",
            "address1_stateorprovince": "West Midlands",
            "address1_postalcode": "B18 4AS",
            "address1_country": "United Kingdom",
            "telephone1": "+44 121 555 0100",
            "websiteurl": "https://www.gov.uk/government/organisations/hm-prison-service",
        }

        account_id, created = self.client.find_or_create(
            "accounts",
            "name eq 'HM Prison Service'",
            account_data,
            "accountid",
        )
        self.created_ids["account_hm_prison"] = account_id
        status = "Created" if created else "Already exists"
        print(f"  ✓ HM Prison Service: {account_id} ({status})")

        # Also create as a Service Account (in Field Service, accounts can be service accounts)
        # This is done by associating it with Field Service if needed

    def create_products(self) -> None:
        """Create products for the demo."""
        # First, get or create a Unit (required for products)
        unit_id = self._ensure_unit()

        # Get or create a Unit Group
        unit_group_id = self._ensure_unit_group(unit_id)

        products = [
            {
                "name": "HP LaserJet Enterprise M507",
                "productnumber": "HP-LJ-M507",
                "description": "HP LaserJet Enterprise M507 Network Printer",
                "msdyn_fieldserviceproducttype": 690970000,  # Inventory
                "quantitydecimal": 0,
                "defaultuomid@odata.bind": f"/uoms({unit_id})",
            },
            {
                "name": "Cable Trunking 50mm x 3m",
                "productnumber": "TRUNK-50-3M",
                "description": "PVC cable trunking, 50mm x 25mm, 3 meter lengths",
                "msdyn_fieldserviceproducttype": 690970000,  # Inventory
                "quantitydecimal": 0,
                "defaultuomid@odata.bind": f"/uoms({unit_id})",
            },
            {
                "name": "CAT6 Cable 100m",
                "productnumber": "CAT6-100M",
                "description": "Category 6 Ethernet cable, 100 meter drum",
                "msdyn_fieldserviceproducttype": 690970000,  # Inventory
                "quantitydecimal": 0,
                "defaultuomid@odata.bind": f"/uoms({unit_id})",
            },
            {
                "name": "RJ45 Connectors (Pack of 10)",
                "productnumber": "RJ45-10PK",
                "description": "RJ45 connectors for CAT6 cable termination",
                "msdyn_fieldserviceproducttype": 690970000,  # Inventory
                "quantitydecimal": 0,
                "defaultuomid@odata.bind": f"/uoms({unit_id})",
            },
        ]

        for product in products:
            prod_name = product["name"]
            prod_number = product["productnumber"]
            prod_id, created = self.client.find_or_create(
                "products",
                f"productnumber eq '{prod_number}'",
                product,
                "productid",
            )
            self.created_ids[f"product_{prod_number}"] = prod_id
            status = "Created" if created else "Already exists"
            print(f"  ✓ {prod_name}: {prod_id} ({status})")

    def _ensure_unit(self) -> str:
        """Ensure a 'Each' unit exists and return its ID."""
        units = self.client.get("uoms", filter_expr="name eq 'Each'", select=["uomid", "name"])
        if units:
            return units[0]["uomid"]

        # Try 'Primary Unit' or other common names
        units = self.client.get("uoms", select=["uomid", "name"])
        if units:
            return units[0]["uomid"]

        raise RuntimeError("No units found in the system. Please create a unit first.")

    def _ensure_unit_group(self, unit_id: str) -> str:
        """Get the unit group for a unit."""
        unit = self.client.get_by_id("uoms", unit_id)
        return unit.get("_uomscheduleid_value", "")

    def create_characteristics(self) -> None:
        """Create characteristics (skills/certifications) for David So."""
        characteristics = [
            {
                "msdyn_name": "IT Hardware Installation",
                "msdyn_type": 690970000,  # Skill
                "msdyn_description": "Ability to install and configure IT hardware including printers, monitors, workstations",
            },
            {
                "msdyn_name": "Network Cabling & Termination",
                "msdyn_type": 690970000,  # Skill
                "msdyn_description": "Expert in running network cables, terminating RJ45 connectors, testing connectivity",
            },
            {
                "msdyn_name": "Enhanced Security Clearance (DBS)",
                "msdyn_type": 690970001,  # Certification
                "msdyn_description": "Enhanced DBS check clearance for working in secure environments including prisons",
            },
            {
                "msdyn_name": "Printer Configuration",
                "msdyn_type": 690970000,  # Skill
                "msdyn_description": "Configuration of network printers including drivers, queues, and settings",
            },
            {
                "msdyn_name": "Working at Height",
                "msdyn_type": 690970001,  # Certification
                "msdyn_description": "Certified for working at height - ladder and scaffold work",
            },
        ]

        for char in characteristics:
            char_name = char["msdyn_name"]
            char_id, created = self.client.find_or_create(
                "msdyn_characteristics",
                f"msdyn_name eq '{char_name}'",
                char,
                "msdyn_characteristicid",
            )
            self.created_ids[f"char_{char_name}"] = char_id
            status = "Created" if created else "Already exists"
            print(f"  ✓ {char_name}: {char_id} ({status})")

    def assign_characteristics_to_david(self) -> None:
        """Find David So and assign all characteristics to him."""
        # Find David So as a Bookable Resource
        resources = self.client.get(
            "bookableresources",
            filter_expr="contains(msdyn_name,'David So') or contains(name,'David So')",
            select=["bookableresourceid", "name"],
        )

        if not resources:
            # Try searching by partial name
            resources = self.client.get(
                "bookableresources",
                filter_expr="contains(msdyn_name,'David') or contains(name,'David')",
                select=["bookableresourceid", "name"],
            )

        if not resources:
            print("  ⚠ WARNING: Could not find David So as a Bookable Resource")
            print("    Please ensure David So is set up as a Bookable Resource in Field Service")
            return

        resource = resources[0]
        resource_id = resource["bookableresourceid"]
        resource_name = resource.get("name", resource.get("msdyn_name", "Unknown"))
        print(f"  Found: {resource_name} ({resource_id})")

        self.created_ids["resource_david"] = resource_id

        # Get rating value for 'Proficient' and 'Expert'
        rating_values = self._get_rating_values()

        # Assign each characteristic
        char_ratings = {
            "IT Hardware Installation": "Proficient",
            "Network Cabling & Termination": "Expert",
            "Enhanced Security Clearance (DBS)": None,  # Certification - no rating
            "Printer Configuration": "Proficient",
            "Working at Height": None,  # Certification - no rating
        }

        for char_name, rating_name in char_ratings.items():
            char_key = f"char_{char_name}"
            if char_key not in self.created_ids:
                continue

            char_id = self.created_ids[char_key]

            # Check if already assigned
            existing = self.client.get(
                "bookableresourcecharacteristics",
                filter_expr=f"_bookableresource_value eq '{resource_id}' and _characteristic_value eq '{char_id}'",
            )

            if existing:
                print(f"    ✓ {char_name}: Already assigned")
                continue

            # Create the association
            assoc_data: dict[str, Any] = {
                "bookableresource@odata.bind": f"/bookableresources({resource_id})",
                "characteristic@odata.bind": f"/msdyn_characteristics({char_id})",
            }

            # Add rating if applicable
            if rating_name and rating_name in rating_values:
                assoc_data["ratingvalue@odata.bind"] = f"/ratingvalues({rating_values[rating_name]})"

            try:
                self.client.create("bookableresourcecharacteristics", assoc_data)
                print(f"    ✓ {char_name}: Assigned" + (f" ({rating_name})" if rating_name else ""))
            except Exception as e:
                print(f"    ⚠ {char_name}: Failed to assign - {e}")

    def _get_rating_values(self) -> dict[str, str]:
        """Get rating values (e.g., Proficient, Expert) from the system."""
        ratings = self.client.get("ratingvalues", select=["ratingvalueid", "name", "value"])
        return {r["name"]: r["ratingvalueid"] for r in ratings}

    def create_incident_types(self) -> None:
        """Create incident types linked to work order types."""
        incident_types = [
            {
                "msdyn_name": "Printer Installation",
                "msdyn_description": "Install and configure network printer at customer site",
                "msdyn_estimatedduration": 30,  # minutes
                "msdyn_defaultworkordertype@odata.bind": f"/msdyn_workordertypes({self.created_ids.get('wot_Printer Installation', '')})",
            },
            {
                "msdyn_name": "Network Cable Trunking Installation",
                "msdyn_description": "Install surface-mounted cable trunking and run network cables",
                "msdyn_estimatedduration": 60,  # minutes
                "msdyn_defaultworkordertype@odata.bind": f"/msdyn_workordertypes({self.created_ids.get('wot_Network Cable Trunking', '')})",
            },
        ]

        for inc in incident_types:
            inc_name = inc["msdyn_name"]

            # Prepare data without odata.bind if the work order type wasn't created
            inc_data = {
                "msdyn_name": inc["msdyn_name"],
                "msdyn_description": inc["msdyn_description"],
                "msdyn_estimatedduration": inc["msdyn_estimatedduration"],
            }

            # Add work order type binding if we have it
            if "msdyn_defaultworkordertype@odata.bind" in inc and "()" not in inc["msdyn_defaultworkordertype@odata.bind"]:
                inc_data["msdyn_defaultworkordertype@odata.bind"] = inc["msdyn_defaultworkordertype@odata.bind"]

            inc_id, created = self.client.find_or_create(
                "msdyn_incidenttypes",
                f"msdyn_name eq '{inc_name}'",
                inc_data,
                "msdyn_incidenttypeid",
            )
            self.created_ids[f"incident_{inc_name}"] = inc_id
            status = "Created" if created else "Already exists"
            print(f"  ✓ {inc_name}: {inc_id} ({status})")

    def create_service_tasks(self) -> None:
        """Create service task types and link to incident types."""
        # Service Task Types (these are the templates)
        service_task_types = [
            # For Printer Installation (30 mins total)
            {"name": "Security Check-in", "duration": 5, "incident": "Printer Installation"},
            {"name": "Unpack & Inspect Equipment", "duration": 3, "incident": "Printer Installation"},
            {"name": "Connect Printer to Network", "duration": 8, "incident": "Printer Installation"},
            {"name": "Install Drivers & Configure", "duration": 7, "incident": "Printer Installation"},
            {"name": "Test Print & Validation", "duration": 4, "incident": "Printer Installation"},
            {"name": "End User Handover", "duration": 3, "incident": "Printer Installation"},
            # For Network Cable Trunking (60 mins total)
            {"name": "Security Check-in", "duration": 5, "incident": "Network Cable Trunking Installation"},
            {"name": "Survey Installation Route", "duration": 10, "incident": "Network Cable Trunking Installation"},
            {"name": "Mount Trunking Brackets", "duration": 15, "incident": "Network Cable Trunking Installation"},
            {"name": "Run & Secure Cables", "duration": 15, "incident": "Network Cable Trunking Installation"},
            {"name": "Terminate & Test Connections", "duration": 10, "incident": "Network Cable Trunking Installation"},
            {"name": "Clean Up & Sign Off", "duration": 5, "incident": "Network Cable Trunking Installation"},
        ]

        # First, create Service Task Types
        print("  Creating Service Task Types...")
        for task in service_task_types:
            task_name = task["name"]
            duration_iso = duration_minutes_to_iso8601(task["duration"])

            task_data = {
                "msdyn_name": task_name,
                "msdyn_estimatedduration": task["duration"],
            }

            task_id, created = self.client.find_or_create(
                "msdyn_servicetasktypes",
                f"msdyn_name eq '{task_name}'",
                task_data,
                "msdyn_servicetasktypeid",
            )
            self.created_ids[f"tasktype_{task_name}"] = task_id

        # Now link Service Task Types to Incident Types via msdyn_incidenttypeservicetask
        print("  Linking Service Tasks to Incident Types...")

        line_order = {}  # Track order per incident type

        for task in service_task_types:
            incident_name = task["incident"]
            task_name = task["name"]
            incident_key = f"incident_{incident_name}"

            if incident_key not in self.created_ids:
                continue

            incident_id = self.created_ids[incident_key]
            task_type_id = self.created_ids.get(f"tasktype_{task_name}", "")

            if not task_type_id:
                continue

            # Track line order per incident
            if incident_name not in line_order:
                line_order[incident_name] = 0
            line_order[incident_name] += 1

            # Check if already linked
            existing = self.client.get(
                "msdyn_incidenttypeservicetasks",
                filter_expr=f"_msdyn_incidenttype_value eq '{incident_id}' and _msdyn_tasktype_value eq '{task_type_id}'",
            )

            if existing:
                print(f"    ✓ {incident_name} → {task_name}: Already linked")
                continue

            link_data = {
                "msdyn_incidenttype@odata.bind": f"/msdyn_incidenttypes({incident_id})",
                "msdyn_tasktype@odata.bind": f"/msdyn_servicetasktypes({task_type_id})",
                "msdyn_name": f"{task_name}",
                "msdyn_lineorder": line_order[incident_name],
                "msdyn_estimatedduration": task["duration"],
            }

            try:
                self.client.create("msdyn_incidenttypeservicetasks", link_data)
                print(f"    ✓ {incident_name} → {task_name}: Linked")
            except Exception as e:
                print(f"    ⚠ {incident_name} → {task_name}: Failed - {e}")

    def print_summary(self) -> None:
        """Print summary of created data."""
        print("\n📋 Summary of Demo Data")
        print("-" * 40)

        categories = {
            "Work Order Types": [k for k in self.created_ids if k.startswith("wot_")],
            "Account": [k for k in self.created_ids if k.startswith("account_")],
            "Products": [k for k in self.created_ids if k.startswith("product_")],
            "Characteristics": [k for k in self.created_ids if k.startswith("char_")],
            "Incident Types": [k for k in self.created_ids if k.startswith("incident_")],
            "Service Task Types": [k for k in self.created_ids if k.startswith("tasktype_")],
            "Resource": [k for k in self.created_ids if k.startswith("resource_")],
        }

        for category, keys in categories.items():
            if keys:
                print(f"\n{category}:")
                for key in keys:
                    display_name = key.split("_", 1)[1] if "_" in key else key
                    print(f"  • {display_name}")

        print("\n" + "=" * 60)
        print("Next Steps:")
        print("  1. Create a Work Order using 'Printer Installation' type")
        print("  2. Set Service Account to 'HM Prison Service'")
        print("  3. Add the Primary Incident Type")
        print("  4. Schedule to David So via the Schedule Board")
        print("=" * 60)


def main():
    config = DataverseConfig.from_env()

    if not config.base_url:
        print("ERROR: DATAVERSE_BASE_URL not set")
        print("Please set the following environment variables or create a .env file:")
        print("  DATAVERSE_BASE_URL=https://your-org.crm.dynamics.com")
        print("  DATAVERSE_TENANT_ID=your-tenant-id")
        print("  DATAVERSE_CLIENT_ID=your-client-id")
        print("  DATAVERSE_CLIENT_SECRET=your-client-secret")
        sys.exit(1)

    print(f"Connecting to: {config.base_url}")

    client = DataverseClient(config)
    setup = PrisonDemoSetup(client)
    setup.run()


if __name__ == "__main__":
    main()
