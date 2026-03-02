"""
Search for ALL CSP-related fields on the organization entity,
including any code-app specific ones.
"""

import json
import os
import sys

os.chdir(
    r"c:\VSCODE_Developement\logicappsdevelopment\logicappsdevelopment\mcp-dataverse-server"
)
sys.path.insert(0, "src")

import httpx
from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings

settings = load_settings()
tp = TokenProvider(
    tenant_id=settings.dataverse_tenant_id,
    client_id=settings.dataverse_client_id,
    client_secret=settings.dataverse_client_secret,
    resource=settings.dataverse_base_url,
)
token = tp.get_access_token()
base = settings.dataverse_base_url
ver = settings.dataverse_api_version
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json",
    "OData-MaxVersion": "4.0",
    "OData-Version": "4.0",
}

org_id = "f2d6ac98-f65e-ef11-bfdf-000d3ab5d940"

# Try to get ALL organization columns that contain 'security' or 'csp' in name
# Use metadata API without filter (just get all attributes)
metadata_url = f"{base}/api/data/{ver}/EntityDefinitions(LogicalName='organization')/Attributes?$select=LogicalName"

with httpx.Client(timeout=60.0) as client:
    resp = client.get(metadata_url, headers=headers)
    resp.raise_for_status()
    all_attrs = resp.json()["value"]

# Filter locally for CSP/security related
csp_attrs = [
    a["LogicalName"]
    for a in all_attrs
    if any(
        kw in a["LogicalName"].lower()
        for kw in ["contentsecurity", "csp", "codeapp", "frameancestor"]
    )
]

print(f"Total organization attributes: {len(all_attrs)}")
print(f"\nCSP/Code-app related attributes ({len(csp_attrs)}):")
for attr in sorted(csp_attrs):
    print(f"  {attr}")

# Now query the org for ALL these fields
if csp_attrs:
    select = ",".join(csp_attrs)
    url = f"{base}/api/data/{ver}/organizations({org_id})?$select={select}"

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        org = resp.json()

    print("\nCurrent values:")
    print(f"{'=' * 70}")
    for attr in sorted(csp_attrs):
        val = org.get(attr)
        print(f"  {attr}: {val}")
        if val and isinstance(val, str):
            try:
                parsed = json.loads(val)
                print(f"    → Parsed JSON: {json.dumps(parsed, indent=6)}")
            except (json.JSONDecodeError, TypeError):
                pass
