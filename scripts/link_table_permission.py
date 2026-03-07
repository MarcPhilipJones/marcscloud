"""Associate table permission with web role via M:N relationship."""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "mcp-dataverse-server", "src")
)
os.chdir(os.path.join(os.path.dirname(__file__), "..", "mcp-dataverse-server"))

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings

settings = load_settings()
tp = TokenProvider(
    settings.dataverse_tenant_id,
    settings.dataverse_client_id,
    settings.dataverse_client_secret,
    settings.dataverse_base_url,
)
token = tp.get_access_token()

import httpx

base = settings.dataverse_base_url + "/api/data/v9.2"
perm_id = "f5725b44-2c1a-f111-8341-7c1e52fb0b79"
role_id = "54a42c1a-0c71-4d28-9e97-a17dfeff3591"

url = (
    f"{base}/powerpagecomponents({perm_id})/powerpagecomponent_powerpagecomponent/$ref"
)
body = {"@odata.id": f"{base}/powerpagecomponents({role_id})"}
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}

r = httpx.post(url, json=body, headers=headers)
print(f"Status: {r.status_code}")
if r.status_code >= 400:
    print(r.text[:500])
else:
    print("Association created successfully!")
