"""Debug: check incident type service tasks and work order service tasks."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from helpers import get_client, load_state

client = get_client()
inc_ids = load_state("phase5_incident_types")
wo_ids = load_state("phase8_work_orders")

print("\n=== Incident Type Service Tasks ===")
for name, iid in inc_ids.items():
    tasks = client.get("msdyn_incidenttypeservicetasks", {
        "$filter": f"_msdyn_incidenttype_value eq {iid}",
        "$select": "msdyn_name,msdyn_lineorder",
        "$orderby": "msdyn_lineorder asc",
    })
    records = tasks.get("value", [])
    print(f"\n{name} ({iid}): {len(records)} tasks")
    for t in records:
        print(f"  #{t.get('msdyn_lineorder')}: {t.get('msdyn_name')}")

print("\n=== Work Order Service Tasks ===")
for name, wid in wo_ids.items():
    tasks = client.get("msdyn_workorderservicetasks", {
        "$filter": f"_msdyn_workorder_value eq {wid}",
        "$select": "msdyn_name",
    })
    records = tasks.get("value", [])
    print(f"\n{name} ({wid}): {len(records)} tasks")
    for t in records:
        print(f"  - {t.get('msdyn_name')}")

print("\n=== Work Order Incident Details ===")
for name, wid in wo_ids.items():
    wo = client.get(f"msdyn_workorders({wid})", {
        "$select": "msdyn_name,_msdyn_primaryincidenttype_value,msdyn_systemstatus",
    })
    print(f"\n{name}")
    print(f"  Incident type: {wo.get('_msdyn_primaryincidenttype_value')}")
    print(f"  Status: {wo.get('msdyn_systemstatus')}")
    
    # Check work order incidents (child records)
    incidents = client.get("msdyn_workorderincidents", {
        "$filter": f"_msdyn_workorder_value eq {wid}",
        "$select": "msdyn_name,_msdyn_incidenttype_value",
    })
    inc_records = incidents.get("value", [])
    print(f"  Work order incidents: {len(inc_records)}")
    for inc in inc_records:
        print(f"    - {inc.get('msdyn_name')} (type: {inc.get('_msdyn_incidenttype_value')})")
