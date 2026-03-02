import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from powerplatform.client import DataverseClient

with DataverseClient() as client:
    print("=== CHECKING ALL DVLA COMPONENTS ===\n")
    
    # Connectors
    print("1. Custom Connectors with 'DVLA':")
    r = client._request("GET", "connectors", params={"$filter": "contains(name,'DVLA')"})
    if r.get("value"):
        for c in r["value"]:
            print(f"   FOUND: {c.get('name')} ({c.get('connectorid')})")
    else:
        print("   None found - CLEAN")
    
    # AI Plugins
    print("\n2. AI Plugins with 'DVLA':")
    r = client._request("GET", "aiplugins", params={"$filter": "contains(name,'DVLA')"})
    if r.get("value"):
        for p in r["value"]:
            print(f"   FOUND: {p.get('name')} ({p.get('aipluginid')})")
    else:
        print("   None found - CLEAN")
    
    # Connection References
    print("\n3. Connection References with 'DVLA':")
    r = client._request("GET", "connectionreferences", params={"$filter": "contains(connectionreferencedisplayname,'DVLA')"})
    if r.get("value"):
        for c in r["value"]:
            print(f"   FOUND: {c.get('connectionreferencedisplayname')} ({c.get('connectionreferenceid')})")
    else:
        print("   None found - CLEAN")
    
    # Workflows
    print("\n4. Workflows with 'DVLA':")
    r = client._request("GET", "workflows", params={"$filter": "contains(name,'DVLA')"})
    if r.get("value"):
        for w in r["value"]:
            print(f"   FOUND: {w.get('name')} ({w.get('workflowid')})")
    else:
        print("   None found - CLEAN")
    
    print("\n=== VERIFICATION COMPLETE ===")
