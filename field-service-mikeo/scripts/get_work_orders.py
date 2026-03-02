"""Fetch the last 5 work orders from Field Service."""
import os
import httpx
from dotenv import load_dotenv

# Load credentials
load_dotenv("mcp-dataverse-server/.env")

base_url = os.getenv("DATAVERSE_BASE_URL")
tenant_id = os.getenv("DATAVERSE_TENANT_ID")
client_id = os.getenv("DATAVERSE_CLIENT_ID")
client_secret = os.getenv("DATAVERSE_CLIENT_SECRET")

# Authenticate
token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
token_resp = httpx.post(token_url, data={
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": f"{base_url}/.default"
})
token = token_resp.json().get("access_token")

if not token:
    print("Auth failed:", token_resp.json())
    exit(1)

# Query last 5 work orders
api_url = f"{base_url}/api/data/v9.2/msdyn_workorders"
params = {
    "$select": "msdyn_name,msdyn_workorderid,createdon,msdyn_systemstatus",
    "$orderby": "createdon desc",
    "$top": "5"
}
headers = {
    "Authorization": f"Bearer {token}",
    "OData-MaxVersion": "4.0",
    "OData-Version": "4.0"
}

resp = httpx.get(api_url, headers=headers, params=params)
data = resp.json()

if "value" in data:
    print("Last 5 Work Orders:")
    for wo in data["value"]:
        name = wo.get("msdyn_name", "N/A")
        created = wo.get("createdon", "N/A")
        status = wo.get("msdyn_systemstatus", "N/A")
        print(f"  - {name} | Created: {created} | Status: {status}")
else:
    print("Error:", data)
