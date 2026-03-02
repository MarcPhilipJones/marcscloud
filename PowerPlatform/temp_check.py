import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from powerplatform.client import DataverseClient

with DataverseClient() as client:
    print("=== NEW DVLA CONNECTOR CHECK ===\n")
    
    # Find all connectors - look for DVLA or vehicle related
    r = client._request("GET", "connectors", params={
        "$select": "connectorid,name,displayname,description,openapidefinition,connectionparameters,statecode",
        "$filter": "contains(name,'DVLA') or contains(name,'Vehicle') or contains(displayname,'DVLA') or contains(displayname,'Vehicle')"
    })
    
    if not r.get("value"):
        print("No DVLA/Vehicle connectors found. Checking all recent connectors...")
        r = client._request("GET", "connectors", params={
            "$select": "connectorid,name,displayname,description,statecode,createdon",
            "$orderby": "createdon desc",
            "$top": "5"
        })
    
    for c in r.get("value", []):
        print(f"Name: {c.get('displayname') or c.get('name')}")
        print(f"ID: {c.get('connectorid')}")
        print(f"State: {'Active' if c.get('statecode') == 0 else 'Inactive'}")
        if c.get('description'):
            print(f"Description: {c.get('description')[:100]}...")
        if c.get('createdon'):
            print(f"Created: {c.get('createdon')}")
        print()
