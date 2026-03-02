"""Setup script for Prison Service Field Service Demo.

Creates:
- 2 Work Order Types (Printer Installation, Network Cable Trunking)
- 2 Incident Types with Service Tasks
- Characteristics for the technician
- Assigns characteristics to David So
- Customer Account (HM Prison Service)
- Products for installations
"""

import os
import sys
from uuid import UUID

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from field_service_mikeo.dataverse_client import DataverseClient
from rich.console import Console
from rich.table import Table

console = Console()


def find_or_create(client: DataverseClient, entity_set: str, name_field: str, name_value: str, data: dict) -> str:
    """Find existing record by name or create new one. Returns GUID."""
    # Search for existing
    params = {"$filter": f"{name_field} eq '{name_value}'", "$select": f"{entity_set.rstrip('s')}id,{name_field}"}
    try:
        result = client.get(entity_set, params)
        records = result.get("value", [])
        if records:
            # Extract ID from first record
            for key in records[0]:
                if key.endswith("id") and key != "@odata.etag":
                    existing_id = records[0][key]
                    console.print(f"  [yellow]Found existing:[/yellow] {name_value} ({existing_id})")
                    return existing_id
    except Exception:
        pass
    
    # Create new
    data[name_field] = name_value
    result = client.post(entity_set, data)
    if result and "@odata.id" in result:
        guid = result["@odata.id"].split("(")[-1].rstrip(")")
        console.print(f"  [green]Created:[/green] {name_value} ({guid})")
        return guid
    raise RuntimeError(f"Failed to create {name_value}")


def setup_work_order_types(client: DataverseClient) -> dict[str, str]:
    """Create Work Order Types."""
    console.print("\n[bold cyan]Creating Work Order Types...[/bold cyan]")
    
    types = {}
    
    # Printer Installation
    types["printer"] = find_or_create(
        client, "msdyn_workordertypes", "msdyn_name", "Printer Installation",
        {"msdyn_incidentrequired": True, "msdyn_taxable": False}
    )
    
    # Network Cable Trunking
    types["cable"] = find_or_create(
        client, "msdyn_workordertypes", "msdyn_name", "Network Cable Trunking",
        {"msdyn_incidentrequired": True, "msdyn_taxable": False}
    )
    
    return types


def setup_service_task_types(client: DataverseClient) -> dict[str, str]:
    """Create Service Task Types."""
    console.print("\n[bold cyan]Creating Service Task Types...[/bold cyan]")
    
    tasks = {}
    task_definitions = [
        ("Security Check-in", 5, "Prison visitor registration, ID verification"),
        ("Unpack & Inspect Equipment", 3, "Verify equipment, check for damage"),
        ("Connect to Network", 8, "Cable connection, IP configuration"),
        ("Install Drivers & Configure", 7, "Set up drivers, configure settings"),
        ("Test Print & Validation", 4, "Print test page, verify quality"),
        ("End User Handover", 3, "Brief demonstration to staff"),
        ("Survey Installation Route", 10, "Verify cable path, identify obstacles"),
        ("Mount Trunking Brackets", 15, "Secure mounting points to wall"),
        ("Run & Secure Cables", 15, "Pull CAT6 through trunking, secure covers"),
        ("Terminate & Test", 10, "Crimp RJ45 connectors, test connectivity"),
        ("Clean Up & Sign Off", 5, "Remove debris, obtain completion signature"),
    ]
    
    for name, duration, description in task_definitions:
        task_id = find_or_create(
            client, "msdyn_servicetasktypes", "msdyn_name", name,
            {
                "msdyn_estimatedduration": duration,
                "msdyn_description": description,
            }
        )
        tasks[name] = task_id
    
    return tasks


def setup_incident_types(client: DataverseClient, work_order_types: dict, service_tasks: dict) -> dict[str, str]:
    """Create Incident Types with linked service tasks."""
    console.print("\n[bold cyan]Creating Incident Types...[/bold cyan]")
    
    incidents = {}
    
    # Printer Installation Incident Type
    incidents["printer"] = find_or_create(
        client, "msdyn_incidenttypes", "msdyn_name", "Printer Installation",
        {
            "msdyn_estimatedduration": 30,
            "msdyn_description": "Install and configure network printer in secure facility",
            "msdyn_defaultworkordertype@odata.bind": f"/msdyn_workordertypes({work_order_types['printer']})",
        }
    )
    
    # Network Cable Trunking Incident Type
    incidents["cable"] = find_or_create(
        client, "msdyn_incidenttypes", "msdyn_name", "Network Cable Trunking Installation",
        {
            "msdyn_estimatedduration": 60,
            "msdyn_description": "Install surface-mounted cable trunking and run network cables",
            "msdyn_defaultworkordertype@odata.bind": f"/msdyn_workordertypes({work_order_types['cable']})",
        }
    )
    
    # Link Service Tasks to Incident Types
    console.print("\n[bold cyan]Linking Service Tasks to Incident Types...[/bold cyan]")
    
    # Printer Installation Tasks
    printer_tasks = [
        ("Security Check-in", 1),
        ("Unpack & Inspect Equipment", 2),
        ("Connect to Network", 3),
        ("Install Drivers & Configure", 4),
        ("Test Print & Validation", 5),
        ("End User Handover", 6),
    ]
    
    for task_name, order in printer_tasks:
        find_or_create(
            client, "msdyn_incidenttypeservicetasks", "msdyn_name", f"Printer - {task_name}",
            {
                "msdyn_incidenttype@odata.bind": f"/msdyn_incidenttypes({incidents['printer']})",
                "msdyn_tasktype@odata.bind": f"/msdyn_servicetasktypes({service_tasks[task_name]})",
                "msdyn_lineorder": order,
            }
        )
    
    # Cable Trunking Tasks
    cable_tasks = [
        ("Security Check-in", 1),
        ("Survey Installation Route", 2),
        ("Mount Trunking Brackets", 3),
        ("Run & Secure Cables", 4),
        ("Terminate & Test", 5),
        ("Clean Up & Sign Off", 6),
    ]
    
    for task_name, order in cable_tasks:
        find_or_create(
            client, "msdyn_incidenttypeservicetasks", "msdyn_name", f"Cable - {task_name}",
            {
                "msdyn_incidenttype@odata.bind": f"/msdyn_incidenttypes({incidents['cable']})",
                "msdyn_tasktype@odata.bind": f"/msdyn_servicetasktypes({service_tasks[task_name]})",
                "msdyn_lineorder": order,
            }
        )
    
    return incidents


def setup_characteristics(client: DataverseClient) -> dict[str, str]:
    """Create Characteristics for technician skills."""
    console.print("\n[bold cyan]Creating Characteristics...[/bold cyan]")
    
    chars = {}
    char_definitions = [
        ("IT Hardware Installation", 1),  # 1 = Skill
        ("Network Cabling & Termination", 1),
        ("Printer Configuration", 1),
        ("Working at Height", 2),  # 2 = Certification
        ("Enhanced Security Clearance (DBS)", 2),
    ]
    
    for name, char_type in char_definitions:
        char_id = find_or_create(
            client, "characteristics", "name", name,
            {"characteristictype": char_type}
        )
        chars[name] = char_id
    
    return chars


def find_david_so(client: DataverseClient) -> str | None:
    """Find David So's bookable resource."""
    console.print("\n[bold cyan]Finding David So's Bookable Resource...[/bold cyan]")
    
    # Search for David So in systemusers first
    params = {
        "$filter": "contains(fullname, 'David So') or contains(fullname, 'David')",
        "$select": "systemuserid,fullname",
    }
    
    try:
        result = client.get("systemusers", params)
        users = result.get("value", [])
        
        david_user = None
        for user in users:
            if "david" in user.get("fullname", "").lower():
                console.print(f"  Found user: {user['fullname']} ({user['systemuserid']})")
                david_user = user["systemuserid"]
                break
        
        if not david_user:
            console.print("  [yellow]David So user not found, searching all bookable resources...[/yellow]")
        
        # Find bookable resource
        resource_params = {
            "$select": "bookableresourceid,name",
            "$expand": "UserId($select=fullname)",
        }
        
        if david_user:
            resource_params["$filter"] = f"_userid_value eq {david_user}"
        
        result = client.get("bookableresources", resource_params)
        resources = result.get("value", [])
        
        for res in resources:
            name = res.get("name", "")
            if "david" in name.lower() or (res.get("UserId") and "david" in res["UserId"].get("fullname", "").lower()):
                console.print(f"  [green]Found bookable resource:[/green] {name} ({res['bookableresourceid']})")
                return res["bookableresourceid"]
        
        # List all resources if David not found
        console.print("  [yellow]David So not found. Available resources:[/yellow]")
        for res in resources[:10]:
            console.print(f"    - {res.get('name', 'Unknown')}")
        
        return None
        
    except Exception as e:
        console.print(f"  [red]Error finding David So: {e}[/red]")
        return None


def assign_characteristics_to_resource(client: DataverseClient, resource_id: str, characteristics: dict) -> None:
    """Assign characteristics to a bookable resource."""
    console.print("\n[bold cyan]Assigning Characteristics to David So...[/bold cyan]")
    
    # Rating values: 1=Familiar, 2=Good, 3=Proficient, 4=Expert
    assignments = [
        ("IT Hardware Installation", 3),  # Proficient
        ("Network Cabling & Termination", 4),  # Expert
        ("Printer Configuration", 3),  # Proficient
        ("Working at Height", 3),  # Certified (Proficient)
        ("Enhanced Security Clearance (DBS)", 4),  # Yes (Expert)
    ]
    
    for char_name, rating in assignments:
        if char_name not in characteristics:
            console.print(f"  [yellow]Characteristic not found: {char_name}[/yellow]")
            continue
        
        char_id = characteristics[char_name]
        
        try:
            # Create assignment (skip duplicate check - Dataverse will reject duplicates)
            data = {
                "Resource@odata.bind": f"/bookableresources({resource_id})",
                "Characteristic@odata.bind": f"/characteristics({char_id})",
            }
            
            client.post("bookableresourcecharacteristics", data)
            rating_labels = {1: "Familiar", 2: "Good", 3: "Proficient", 4: "Expert"}
            console.print(f"  [green]Assigned:[/green] {char_name} ({rating_labels.get(rating, rating)})")
            
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                console.print(f"  [yellow]Already assigned:[/yellow] {char_name}")
            else:
                console.print(f"  [red]Error assigning {char_name}: {e}[/red]")


def get_gbp_currency_id(client: DataverseClient) -> str:
    """Get the GBP (Pound Sterling) transaction currency ID."""
    result = client.get("transactioncurrencies", {"$filter": "isocurrencycode eq 'GBP'", "$select": "transactioncurrencyid"})
    currencies = result.get("value", [])
    if currencies:
        return currencies[0]["transactioncurrencyid"]
    raise RuntimeError("GBP currency not found in Dataverse")


def setup_customer_account(client: DataverseClient) -> dict[str, str]:
    """Create HM Prison Service customer account and service account."""
    console.print("\n[bold cyan]Creating Customer Account...[/bold cyan]")
    
    # Get GBP currency for UK accounts
    gbp_id = get_gbp_currency_id(client)
    console.print(f"  [dim]Using GBP currency: {gbp_id}[/dim]")
    
    account_id = find_or_create(
        client, "accounts", "name", "HM Prison Service",
        {
            "description": "His Majesty's Prison and Probation Service",
            "address1_line1": "102 Petty France",
            "address1_city": "London",
            "address1_postalcode": "SW1H 9AJ",
            "address1_country": "United Kingdom",
            "telephone1": "0300 047 6325",
            "websiteurl": "https://www.gov.uk/government/organisations/hm-prison-and-probation-service",
            "transactioncurrencyid@odata.bind": f"/transactioncurrencies({gbp_id})",
        }
    )
    
    # Create Service Account (linked to parent account)
    console.print("\n[bold cyan]Creating Service Account...[/bold cyan]")
    service_account_id = find_or_create(
        client, "accounts", "name", "HMP Demonstration",
        {
            "description": "Demonstration Prison Facility for Field Service demos",
            "address1_line1": "HMP Demo Site",
            "address1_line2": "123 Prison Lane",
            "address1_city": "Birmingham",
            "address1_postalcode": "B1 1AA",
            "address1_country": "United Kingdom",
            "telephone1": "0121 555 0100",
            "parentaccountid@odata.bind": f"/accounts({account_id})",
            "transactioncurrencyid@odata.bind": f"/transactioncurrencies({gbp_id})",
        }
    )
    
    return {"customer": account_id, "service_account": service_account_id}


def setup_products(client: DataverseClient) -> dict[str, str]:
    """Create products for Field Service."""
    console.print("\n[bold cyan]Creating Products...[/bold cyan]")
    
    # Get GBP currency
    gbp_id = get_gbp_currency_id(client)
    
    products = {}
    product_definitions = [
        ("HP LaserJet Enterprise M507", "Equipment - Network Printer", 899.00),
        ("Cable Trunking 50mm x 3m", "Materials - Surface mount trunking", 12.50),
        ("CAT6 Cable 100m", "Materials - Network cable", 45.00),
        ("RJ45 Connectors Pack (10)", "Materials - Cable termination", 8.99),
        ("Mounting Brackets Pack (20)", "Materials - Trunking fixings", 15.00),
    ]
    
    # First, find or create a unit group and unit
    try:
        # Find default unit group
        result = client.get("uomschedules", {"$filter": "name eq 'Default Unit'", "$select": "uomscheduleid"})
        unit_groups = result.get("value", [])
        
        if unit_groups:
            unit_group_id = unit_groups[0]["uomscheduleid"]
        else:
            # Create unit group
            result = client.post("uomschedules", {"name": "Default Unit"})
            unit_group_id = result["@odata.id"].split("(")[-1].rstrip(")")
        
        # Find or create "Each" unit
        result = client.get("uoms", {"$filter": "name eq 'Each'", "$select": "uomid"})
        units = result.get("value", [])
        
        if units:
            unit_id = units[0]["uomid"]
        else:
            result = client.post("uoms", {
                "name": "Each",
                "uomscheduleid@odata.bind": f"/uomschedules({unit_group_id})",
                "quantity": 1,
            })
            unit_id = result["@odata.id"].split("(")[-1].rstrip(")")
        
        for name, description, price in product_definitions:
            product_id = find_or_create(
                client, "products", "name", name,
                {
                    "description": description,
                    "price": price,
                    "productnumber": name.replace(" ", "_")[:20],
                    "quantitydecimal": 0,
                    "defaultuomscheduleid@odata.bind": f"/uomschedules({unit_group_id})",
                    "defaultuomid@odata.bind": f"/uoms({unit_id})",
                    "transactioncurrencyid@odata.bind": f"/transactioncurrencies({gbp_id})",
                }
            )
            products[name] = product_id
            
    except Exception as e:
        console.print(f"  [yellow]Note: Product creation may require additional configuration: {e}[/yellow]")
    
    return products


def main():
    """Main setup function."""
    console.print("[bold magenta]═══════════════════════════════════════════════════════[/bold magenta]")
    console.print("[bold magenta]  Prison Service Field Service Demo Setup[/bold magenta]")
    console.print("[bold magenta]═══════════════════════════════════════════════════════[/bold magenta]")
    
    # Initialize client
    client = DataverseClient()
    console.print(f"\n[dim]Connecting to: {client.dataverse_url}[/dim]")
    
    try:
        # Test connection
        client.get("WhoAmI")
        console.print("[green]✓ Connected to Dataverse[/green]")
    except Exception as e:
        console.print(f"[red]✗ Failed to connect: {e}[/red]")
        sys.exit(1)
    
    # Create all the data
    work_order_types = setup_work_order_types(client)
    service_tasks = setup_service_task_types(client)
    incidents = setup_incident_types(client, work_order_types, service_tasks)
    characteristics = setup_characteristics(client)
    
    # Find David So and assign characteristics
    david_resource_id = find_david_so(client)
    if david_resource_id:
        assign_characteristics_to_resource(client, david_resource_id, characteristics)
    else:
        console.print("[yellow]⚠ David So not found - characteristics created but not assigned[/yellow]")
    
    # Create customer and products
    accounts = setup_customer_account(client)
    products = setup_products(client)
    
    # Summary
    console.print("\n[bold magenta]═══════════════════════════════════════════════════════[/bold magenta]")
    console.print("[bold green]✓ Demo Setup Complete![/bold green]")
    console.print("[bold magenta]═══════════════════════════════════════════════════════[/bold magenta]")
    
    table = Table(title="Summary")
    table.add_column("Item", style="cyan")
    table.add_column("Count", justify="right")
    
    table.add_row("Work Order Types", str(len(work_order_types)))
    table.add_row("Service Task Types", str(len(service_tasks)))
    table.add_row("Incident Types", str(len(incidents)))
    table.add_row("Characteristics", str(len(characteristics)))
    table.add_row("Products", str(len(products)))
    table.add_row("Accounts (Customer + Service)", str(len(accounts)))
    
    console.print(table)
    
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("1. Open Dynamics 365 Field Service")
    console.print("2. Create a Work Order using 'Printer Installation' or 'Network Cable Trunking'")
    console.print("3. Set customer to 'HM Prison Service' or Service Account 'HMP Demonstration'")
    console.print("4. Book David Mallory as the technician")
    console.print("\n[dim]Currency: All UK accounts set to GBP (Pound Sterling)[/dim]")


if __name__ == "__main__":
    main()
