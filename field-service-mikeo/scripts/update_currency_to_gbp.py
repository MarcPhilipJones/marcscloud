"""Update existing records to use GBP currency."""
import sys
import os

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, "src")

from field_service_mikeo.dataverse_client import DataverseClient
from rich.console import Console

console = Console()

def main():
    client = DataverseClient()
    console.print("[bold cyan]Updating currency to GBP (Pound Sterling)...[/bold cyan]\n")
    
    # Get GBP currency ID
    result = client.get("transactioncurrencies", {"$filter": "isocurrencycode eq 'GBP'", "$select": "transactioncurrencyid"})
    gbp_id = result["value"][0]["transactioncurrencyid"]
    console.print(f"GBP Currency ID: {gbp_id}")
    
    # Update HM Prison Service account
    result = client.get("accounts", {"$filter": "name eq 'HM Prison Service'", "$select": "accountid"})
    if result["value"]:
        account_id = result["value"][0]["accountid"]
        client.patch(f"accounts({account_id})", {
            "transactioncurrencyid@odata.bind": f"/transactioncurrencies({gbp_id})"
        })
        console.print(f"  [green]✓[/green] HM Prison Service - updated to GBP")
    
    # Update HMP Demonstration account  
    result = client.get("accounts", {"$filter": "name eq 'HMP Demonstration'", "$select": "accountid"})
    if result["value"]:
        account_id = result["value"][0]["accountid"]
        client.patch(f"accounts({account_id})", {
            "transactioncurrencyid@odata.bind": f"/transactioncurrencies({gbp_id})"
        })
        console.print(f"  [green]✓[/green] HMP Demonstration - updated to GBP")
    
    # Update products
    products = [
        "HP LaserJet Enterprise M507",
        "Cable Trunking 50mm x 3m",
        "CAT6 Cable 100m",
        "RJ45 Connectors Pack (10)",
        "Mounting Brackets Pack (20)",
    ]
    
    for product_name in products:
        result = client.get("products", {"$filter": f"name eq '{product_name}'", "$select": "productid"})
        if result["value"]:
            product_id = result["value"][0]["productid"]
            try:
                client.patch(f"products({product_id})", {
                    "transactioncurrencyid@odata.bind": f"/transactioncurrencies({gbp_id})"
                })
                console.print(f"  [green]✓[/green] {product_name} - updated to GBP")
            except Exception as e:
                console.print(f"  [yellow]⚠[/yellow] {product_name} - {e}")
    
    console.print("\n[bold green]Currency update complete![/bold green]")

if __name__ == "__main__":
    main()
