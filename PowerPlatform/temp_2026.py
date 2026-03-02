import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from powerplatform.client import DataverseClient

with DataverseClient() as client:
    print("=== DVLA Vehicle Check 2026 ===\n")
    
    # Check connectors
    r = client._request("GET", "connectors", params={
        "$filter": "contains(name,'2026') or contains(displayname,'2026')"
    })
    if r.get("value"):
        for c in r["value"]:
            print(f"Connector: {c.get('displayname') or c.get('name')}")
            print(f"  ID: {c.get('connectorid')}")
            print(f"  State: {'Active' if c.get('statecode') == 0 else 'Inactive'}")
    
    # Check AI plugins
    r = client._request("GET", "aiplugins", params={
        "$filter": "contains(name,'2026') or contains(name,'DVLA') or contains(name,'Vehicle')"
    })
    if r.get("value"):
        for p in r["value"]:
            print(f"AI Plugin: {p.get('name')}")
            print(f"  ID: {p.get('aipluginid')}")
            print(f"  State: {'Active' if p.get('statecode') == 0 else 'Inactive'}")
    
    if not r.get("value"):
        print("Not yet synced to Dataverse - but if it works in UI, you're good!")
