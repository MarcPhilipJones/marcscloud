import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from powerplatform.client import DataverseClient

with DataverseClient() as client:
    print("=== CHECKING AI PLUGINS ===\n")
    r = client._request("GET", "aiplugins", params={
        "$select": "aipluginid,name,plugintype,statecode,createdon",
        "$orderby": "createdon desc",
        "$top": "10"
    })
    
    for p in r.get("value", []):
        print(f"- {p.get('name')}")
        print(f"  ID: {p.get('aipluginid')}")
        print(f"  Type: {p.get('plugintype')}")
        print(f"  State: {'Active' if p.get('statecode') == 0 else 'Inactive'}")
        print(f"  Created: {p.get('createdon','N/A')}")
        print()
