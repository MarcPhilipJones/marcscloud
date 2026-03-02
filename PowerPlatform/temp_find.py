import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from powerplatform.client import DataverseClient

with DataverseClient() as client:
    # Check ai plugins for "MJ DVLA"
    print("AI Plugins with DVLA:")
    plugins = client._request("GET", "aiplugins", params={"$filter": "contains(name,'DVLA')"})
    for p in plugins.get("value", []):
        print(f"  {p.get('name')} - ID: {p.get('aipluginid')}")
    
    # Check workflows with exact name
    print("\nWorkflows with exact 'MJ DVLA':")
    wfs = client._request("GET", "workflows", params={"$filter": "name eq 'MJ DVLA'"})
    for w in wfs.get("value", []):
        print(f"  {w.get('name')} - ID: {w.get('workflowid')}")
