"""Phase 6: Create 8 Products for water utility field service.

Usage:
    cd field-service-wessex
    python scripts/phase6_products.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from helpers import (
    console,
    extract_guid,
    find_or_create,
    get_client,
    save_state,
    validate_count,
)

PRODUCTS = [
    {
        "name": "MDPE Pipe 25mm (per metre)",
        "description": "Medium density polyethylene pipe for supply repairs",
        "price": 3.50,
    },
    {
        "name": "Pipe Repair Clamp 25mm",
        "description": "Stainless steel clamp for mains/supply pipe repair",
        "price": 28.00,
    },
    {
        "name": "Smart Water Meter Unit",
        "description": "Smart meter with integrated AMI transmitter",
        "price": 145.00,
    },
    {
        "name": "Meter Box Lid",
        "description": "Replacement meter chamber cover",
        "price": 12.50,
    },
    {
        "name": "CCTV Survey Report",
        "description": "Completed drain survey report with footage",
        "price": 0.00,
    },
    {
        "name": "High-Pressure Jetting (per hour)",
        "description": "Jetting equipment and operator time",
        "price": 85.00,
    },
    {
        "name": "Water Sample Kit",
        "description": "Sterile sample bottles and testing reagents",
        "price": 15.00,
    },
    {
        "name": "Chlorine Test Strips (pack)",
        "description": "Pack of 50 on-site chlorine residual test strips",
        "price": 8.00,
    },
]


def main():
    console.print("\n[bold magenta]═══ Phase 6: Products ═══[/bold magenta]")
    client = get_client()

    # Find GBP currency
    console.print("  Looking up GBP currency...")
    result = client.get(
        "transactioncurrencies",
        {"$filter": "isocurrencycode eq 'GBP'", "$select": "transactioncurrencyid"},
    )
    currencies = result.get("value", [])
    if not currencies:
        console.print("  [red]✗ GBP currency not found[/red]")
        sys.exit(1)
    gbp_id = currencies[0]["transactioncurrencyid"]
    console.print(f"  [green]✓ GBP currency: {gbp_id}[/green]")

    # Find or create Default Unit group
    console.print("  Looking up Default Unit group...")
    result = client.get(
        "uomschedules",
        {"$filter": "name eq 'Default Unit'", "$select": "uomscheduleid"},
    )
    unit_groups = result.get("value", [])
    if unit_groups:
        unit_group_id = unit_groups[0]["uomscheduleid"]
    else:
        ug_result = client.post("uomschedules", {"name": "Default Unit"})
        unit_group_id = extract_guid(ug_result["@odata.id"])
    console.print(f"  [green]✓ Unit group: {unit_group_id}[/green]")

    # Find or create "Each" unit
    console.print("  Looking up 'Each' unit of measure...")
    result = client.get("uoms", {"$filter": "name eq 'Each'", "$select": "uomid"})
    units = result.get("value", [])
    if units:
        unit_id = units[0]["uomid"]
    else:
        u_result = client.post(
            "uoms",
            {
                "name": "Each",
                "uomscheduleid@odata.bind": f"/uomschedules({unit_group_id})",
                "quantity": 1,
            },
        )
        unit_id = extract_guid(u_result["@odata.id"])
    console.print(f"  [green]✓ UoM 'Each': {unit_id}[/green]")

    # Create products
    product_ids: dict[str, str] = {}
    for prod in PRODUCTS:
        name = prod["name"]
        product_number = name.replace(" ", "_").replace("(", "").replace(")", "")[:25]
        pid = find_or_create(
            client,
            "products",
            "name",
            name,
            {
                "description": prod["description"],
                "price": prod["price"],
                "productnumber": product_number,
                "quantitydecimal": 0,
                "defaultuomscheduleid@odata.bind": f"/uomschedules({unit_group_id})",
                "defaultuomid@odata.bind": f"/uoms({unit_id})",
                "transactioncurrencyid@odata.bind": f"/transactioncurrencies({gbp_id})",
            },
        )
        product_ids[name] = pid

    # Validate
    console.print("\n  Validating Phase 6...")
    all_names = [p["name"] for p in PRODUCTS]
    ok = validate_count(client, "products", "name", all_names, "Products")
    if not ok:
        sys.exit(1)

    console.print(f"\n  [green]✓ Phase 6 complete: {len(product_ids)} products[/green]")
    save_state("phase6_products", product_ids)


if __name__ == "__main__":
    main()
