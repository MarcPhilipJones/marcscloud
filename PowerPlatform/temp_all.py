import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from powerplatform.client import DataverseClient

with DataverseClient() as client:
    print("=== ALL CUSTOM CONNECTORS ===\n")
    r = client._request("GET", "connectors", params={
        "$select": "connectorid,name,displayname,statecode,createdon"
    })
    
    for c in r.get("value", []):
        print(f"- {c.get('displayname') or c.get('name')} (ID: {c.get('connectorid')[:8]}...) Created: {c.get('createdon','N/A')[:10] if c.get('createdon') else 'N/A'}")
    
    if not r.get("value"):
        print("No connectors found at all.")
