#!/usr/bin/env python3
"""Query a specific work order from Dataverse."""
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Credentials — loaded from environment / .env file
tenant_id = os.getenv('DATAVERSE_TENANT_ID', '996f568a-cc69-450a-b684-ae784069e679')
client_id = os.getenv('DATAVERSE_CLIENT_ID', 'beb6cb7d-3328-4c2f-be9a-aab746be614a')
client_secret = os.getenv('DATAVERSE_CLIENT_SECRET', '')
resource = os.getenv('DATAVERSE_BASE_URL', 'https://org6cb3e9fb.crm4.dynamics.com')

# Get OAuth token
token_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
token_data = {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
    'scope': f'{resource}/.default'
}

print("Getting access token...")
resp = httpx.post(token_url, data=token_data)
token = resp.json().get('access_token')
if not token:
    print('Token error:', resp.text)
    exit(1)
print("Token acquired successfully!")

headers = {'Authorization': f'Bearer {token}', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0', 'Accept': 'application/json'}

# Search for work order 01209
print("\n=== SEARCHING FOR WORK ORDER 01209 ===")
search_url = f"{resource}/api/data/v9.2/msdyn_workorders?$filter=contains(msdyn_name,'01209')&$top=5"
wo_resp = httpx.get(search_url, headers=headers)
work_orders = wo_resp.json().get('value', [])

if not work_orders:
    print("No work orders found matching '01209'. Trying broader search...")
    search_url = f"{resource}/api/data/v9.2/msdyn_workorders?$orderby=createdon desc&$top=10"
    wo_resp = httpx.get(search_url, headers=headers)
    work_orders = wo_resp.json().get('value', [])
    print(f"Found {len(work_orders)} recent work orders")
    for wo in work_orders:
        print(f"  - {wo.get('msdyn_name')}: {wo.get('msdyn_workorderid')}")
else:
    print(f"Found {len(work_orders)} work orders")
    for wo in work_orders:
        print(f"  - {wo.get('msdyn_name')}: {wo.get('msdyn_workorderid')}")

# If we found the work order, get full details
if work_orders:
    wo = work_orders[0]
    wo_id = wo.get('msdyn_workorderid')
    wo_name = wo.get('msdyn_name')
    
    print(f"\n=== FULL WORK ORDER DETAILS: {wo_name} ===")
    detail_url = f"{resource}/api/data/v9.2/msdyn_workorders({wo_id})"
    detail_resp = httpx.get(detail_url, headers=headers)
    wo_detail = detail_resp.json()
    
    # Key fields to display
    key_fields = [
        'msdyn_name', 'msdyn_workorderid', 'statecode', 'statuscode',
        '_msdyn_primaryincidenttype_value', '_msdyn_serviceaccount_value',
        '_msdyn_billingaccount_value', '_msdyn_pricelist_value',
        '_msdyn_serviceterritory_value', '_msdyn_workordertype_value',
        'msdyn_systemstatus', 'msdyn_substatus', 'msdyn_datewindowstart',
        'msdyn_datewindowend', 'msdyn_timefrompromisd', 'msdyn_timetopromised',
        'msdyn_address1', 'msdyn_city', 'msdyn_postalcode', 'msdyn_country',
        'msdyn_latitude', 'msdyn_longitude', 'msdyn_instructions',
        '_msdyn_priority_value', 'createdon', 'modifiedon'
    ]
    
    print("\nKey Fields:")
    for field in key_fields:
        value = wo_detail.get(field)
        if value is not None:
            print(f"  {field}: {value}")
    
    # Get the incident type details
    incident_type_id = wo_detail.get('_msdyn_primaryincidenttype_value')
    if incident_type_id:
        print(f"\n=== INCIDENT TYPE DETAILS ===")
        inc_url = f"{resource}/api/data/v9.2/msdyn_incidenttypes({incident_type_id})"
        inc_resp = httpx.get(inc_url, headers=headers)
        incident_type = inc_resp.json()
        print(json.dumps(incident_type, indent=2, default=str))
        
        # Get incident type products
        print(f"\n=== INCIDENT TYPE PRODUCTS ===")
        itp_url = f"{resource}/api/data/v9.2/msdyn_incidenttypeproducts?$filter=_msdyn_incidenttype_value eq {incident_type_id}"
        itp_resp = httpx.get(itp_url, headers=headers)
        print(json.dumps(itp_resp.json(), indent=2, default=str))
        
        # Get incident type services
        print(f"\n=== INCIDENT TYPE SERVICES ===")
        its_url = f"{resource}/api/data/v9.2/msdyn_incidenttypeservices?$filter=_msdyn_incidenttype_value eq {incident_type_id}"
        its_resp = httpx.get(its_url, headers=headers)
        print(json.dumps(its_resp.json(), indent=2, default=str))
        
        # Get incident type service tasks
        print(f"\n=== INCIDENT TYPE SERVICE TASKS ===")
        itst_url = f"{resource}/api/data/v9.2/msdyn_incidenttypeservicetasks?$filter=_msdyn_incidenttype_value eq {incident_type_id}"
        itst_resp = httpx.get(itst_url, headers=headers)
        print(json.dumps(itst_resp.json(), indent=2, default=str))
        
        # Get incident type characteristics (skills required)
        print(f"\n=== INCIDENT TYPE CHARACTERISTICS (SKILLS) ===")
        itc_url = f"{resource}/api/data/v9.2/msdyn_incidenttypecharacteristics?$filter=_msdyn_incidenttype_value eq {incident_type_id}"
        itc_resp = httpx.get(itc_url, headers=headers)
        print(json.dumps(itc_resp.json(), indent=2, default=str))
    
    # Get the work order type details
    wo_type_id = wo_detail.get('_msdyn_workordertype_value')
    if wo_type_id:
        print(f"\n=== WORK ORDER TYPE DETAILS ===")
        wot_url = f"{resource}/api/data/v9.2/msdyn_workordertypes({wo_type_id})"
        wot_resp = httpx.get(wot_url, headers=headers)
        print(json.dumps(wot_resp.json(), indent=2, default=str))
    
    # Get work order products
    print(f"\n=== WORK ORDER PRODUCTS ===")
    wop_url = f"{resource}/api/data/v9.2/msdyn_workorderproducts?$filter=_msdyn_workorder_value eq {wo_id}"
    wop_resp = httpx.get(wop_url, headers=headers)
    print(json.dumps(wop_resp.json(), indent=2, default=str))
    
    # Get work order services
    print(f"\n=== WORK ORDER SERVICES ===")
    wos_url = f"{resource}/api/data/v9.2/msdyn_workorderservices?$filter=_msdyn_workorder_value eq {wo_id}"
    wos_resp = httpx.get(wos_url, headers=headers)
    print(json.dumps(wos_resp.json(), indent=2, default=str))
    
    # Get work order service tasks
    print(f"\n=== WORK ORDER SERVICE TASKS ===")
    wost_url = f"{resource}/api/data/v9.2/msdyn_workorderservicetasks?$filter=_msdyn_workorder_value eq {wo_id}"
    wost_resp = httpx.get(wost_url, headers=headers)
    print(json.dumps(wost_resp.json(), indent=2, default=str))
    
    # Get bookings for this work order
    print(f"\n=== BOOKINGS FOR THIS WORK ORDER ===")
    book_url = f"{resource}/api/data/v9.2/bookableresourcebookings?$filter=_msdyn_workorder_value eq {wo_id}"
    book_resp = httpx.get(book_url, headers=headers)
    print(json.dumps(book_resp.json(), indent=2, default=str))
    
    print("\n=== COMPLETE WORK ORDER JSON ===")
    print(json.dumps(wo_detail, indent=2, default=str))
