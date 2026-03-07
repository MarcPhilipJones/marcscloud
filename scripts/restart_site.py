"""Restart a Power Pages site via the Power Platform Admin API."""

import os
import sys

import httpx

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "mcp-dataverse-server", "src")
)
os.chdir(os.path.join(os.path.dirname(__file__), "..", "mcp-dataverse-server"))

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings

settings = load_settings()

# Get token for Dataverse (Power Pages lifecycle API is on the org endpoint)
tp = TokenProvider(
    settings.dataverse_tenant_id,
    settings.dataverse_client_id,
    settings.dataverse_client_secret,
    settings.dataverse_base_url,
)
token = tp.get_access_token()

base = settings.dataverse_base_url + "/api/data/v9.2"
site_id = "f902ddf0-3990-4cd0-9014-07e9d4c6910a"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}

# Power Pages restart is done via the Restart action on powerpagesite
# Try the custom action approach
url = f"{base}/powerpagesites({site_id})/Microsoft.Dynamics.CRM.adx_RestartPortal"
r = httpx.post(url, headers=headers, json={})
print(f"adx_RestartPortal: {r.status_code}")
if r.status_code >= 400:
    print(r.text[:300])

    # Fallback: try updating the site to trigger a cache clear
    print("\nTrying cache invalidation via site update...")
    patch_url = f"{base}/powerpagesites({site_id})"
    # Touch the record to invalidate cache
    r2 = httpx.patch(
        patch_url,
        headers=headers,
        json={
            "adx_headerwebtemplateid@odata.bind": "/powerpagecomponents(c3ccd895-e128-46af-9ce8-1f124863b590)"
        },
    )
    print(f"Site touch: {r2.status_code}")
    if r2.status_code < 400:
        print("Site record touched — cache should invalidate shortly.")
    else:
        print(r2.text[:300])
