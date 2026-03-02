"""Attach Knowledge Articles to Work Orders.

Links the published knowledge articles to the relevant work orders:
- Printer Installation article -> Printer work orders
- Cable Trunking article -> Cable work orders
"""

import sys
import os

os.chdir(r"c:\VSCODE_Developement\logicappsdevelopment\logicappsdevelopment\mcp-dataverse-server")
sys.path.insert(0, "src")

from dotenv import load_dotenv
load_dotenv(".env")

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings
import httpx
from rich.console import Console

console = Console()

# Knowledge Article IDs (created earlier)
PRINTER_ARTICLE_ID = "5b09a5c7-e60c-f111-8406-6045bde1bdbc"
CABLE_ARTICLE_ID = "6a09a5c7-e60c-f111-8406-6045bde1bdbc"


def main():
    settings = load_settings()
    tp = TokenProvider(
        settings.dataverse_tenant_id,
        settings.dataverse_client_id,
        settings.dataverse_client_secret,
        settings.dataverse_base_url
    )
    token = tp.get_access_token()
    base = settings.dataverse_base_url
    ver = settings.dataverse_api_version
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
    }
    
    with httpx.Client(timeout=60.0) as client:
        # Get all prison work orders (linked to HM Prison Service account)
        console.print("\n[bold cyan]Fetching Prison Work Orders...[/bold cyan]\n")
        
        # First find the HM Prison Service account
        acct_url = f"{base}/api/data/{ver}/accounts?$filter=contains(name,'Prison')&$select=accountid,name"
        response = client.get(acct_url, headers=headers)
        
        if response.status_code != 200:
            console.print(f"[red]Error fetching account: {response.status_code}[/red]")
            return
        
        accounts = response.json().get("value", [])
        if not accounts:
            console.print("[red]HM Prison Service account not found[/red]")
            return
        
        account_id = accounts[0]["accountid"]
        console.print(f"Found account: {accounts[0]['name']} ({account_id})")
        
        # Get work orders for this account
        url = f"{base}/api/data/{ver}/msdyn_workorders?$filter=_msdyn_serviceaccount_value eq {account_id}&$select=msdyn_workorderid,msdyn_name&$orderby=createdon desc"
        response = client.get(url, headers=headers)
        
        if response.status_code != 200:
            console.print(f"[red]Error fetching work orders: {response.status_code}[/red]")
            console.print(response.text[:500])
            return
        
        work_orders = response.json().get("value", [])
        console.print(f"Found {len(work_orders)} work orders\n")
        
        # Categorize work orders
        printer_wos = []
        cable_wos = []
        
        for wo in work_orders:
            name = wo["msdyn_name"]
            wo_id = wo["msdyn_workorderid"]
            
            if "Printer" in name:
                printer_wos.append((wo_id, name))
            elif "Network" in name or "Cable" in name or "Cabling" in name or "CCTV" in name or "Redundant" in name or "Conference" in name or "Access Control" in name or "Terminal" in name:
                cable_wos.append((wo_id, name))
        
        console.print(f"[cyan]Printer work orders:[/cyan] {len(printer_wos)}")
        console.print(f"[cyan]Cable work orders:[/cyan] {len(cable_wos)}")
        
        # Check the entity for linking knowledge articles to work orders
        # In Dataverse, we use knowledgearticle_msdyn_workorder association
        # or we can set msdyn_workorder_knowledgearticle_knowledgearticleid
        
        # First, let's check what relationship exists
        console.print("\n[bold cyan]Linking Knowledge Articles to Work Orders...[/bold cyan]\n")
        
        # Link Printer article to printer work orders
        for wo_id, wo_name in printer_wos:
            # Use the many-to-many relationship: msdyn_msdyn_workorder_knowledgearticle
            assoc_url = f"{base}/api/data/{ver}/knowledgearticles({PRINTER_ARTICLE_ID})/msdyn_msdyn_workorder_knowledgearticle/$ref"
            payload = {
                "@odata.id": f"{base}/api/data/{ver}/msdyn_workorders({wo_id})"
            }
            
            response = client.post(assoc_url, headers=headers, json=payload)
            
            if response.status_code in (200, 201, 204):
                console.print(f"[green]✓[/green] Linked Printer article to: {wo_name}")
            else:
                # Try alternative relationship name
                console.print(f"[yellow]Trying alternative relationship...[/yellow]")
                console.print(f"  Status: {response.status_code}, Error: {response.text[:200]}")
        
        # Link Cable article to cable work orders  
        for wo_id, wo_name in cable_wos:
            assoc_url = f"{base}/api/data/{ver}/knowledgearticles({CABLE_ARTICLE_ID})/msdyn_msdyn_workorder_knowledgearticle/$ref"
            payload = {
                "@odata.id": f"{base}/api/data/{ver}/msdyn_workorders({wo_id})"
            }
            
            response = client.post(assoc_url, headers=headers, json=payload)
            
            if response.status_code in (200, 201, 204):
                console.print(f"[green]✓[/green] Linked Cable article to: {wo_name}")
            else:
                console.print(f"[yellow]Status {response.status_code}[/yellow] for {wo_name}")
                console.print(f"  [dim]{response.text[:200]}[/dim]")
        
        console.print("\n[bold green]Done![/bold green]\n")


if __name__ == "__main__":
    main()
