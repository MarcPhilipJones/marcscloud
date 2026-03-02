"""
Query and display all Content Security Policy settings from the Dataverse
organization entity, as per:
https://learn.microsoft.com/en-gb/power-platform/admin/content-security-policy
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

# ── Query organization entity for ALL CSP-related fields ──────────
# The doc mentions these fields on the organization entity:
#   iscontentsecuritypolicyenabled             (model-driven)
#   contentsecuritypolicyconfiguration         (model-driven frame-ancestors)
#   iscontentsecuritypolicyenabledforcanvas    (canvas)
#   contentsecuritypolicyconfigurationforcanvas(canvas frame-ancestors)
#   contentsecuritypolicyreporturi             (shared reporting endpoint)
#
# There may also be code-app-specific fields — let's grab everything.

csp_fields = [
    "organizationid",
    "iscontentsecuritypolicyenabled",
    "contentsecuritypolicyconfiguration",
    "iscontentsecuritypolicyenabledforcanvas",
    "contentsecuritypolicyconfigurationforcanvas",
    "contentsecuritypolicyreporturi",
]

select = ",".join(csp_fields)
url = f"{base}/api/data/{ver}/organizations?$select={select}"

with httpx.Client(timeout=30.0) as client:
    resp = client.get(url, headers=headers)
    resp.raise_for_status()
    orgs = resp.json()["value"]

print(f"Found {len(orgs)} organization(s)\n")

for org in orgs:
    print(f"Organization ID: {org.get('organizationid')}")
    print(f"{'=' * 60}")

    # Model-driven CSP
    enabled = org.get("iscontentsecuritypolicyenabled")
    config = org.get("contentsecuritypolicyconfiguration")
    print("\n[Model-Driven Apps]")
    print(f"  CSP Enabled (enforced):  {enabled}")
    print(f"  CSP Configuration:       {config}")
    if config:
        try:
            parsed = json.loads(config)
            print(f"  Parsed config:           {json.dumps(parsed, indent=4)}")
        except json.JSONDecodeError:
            print("  (not valid JSON)")

    # Canvas CSP
    canvas_enabled = org.get("iscontentsecuritypolicyenabledforcanvas")
    canvas_config = org.get("contentsecuritypolicyconfigurationforcanvas")
    print("\n[Canvas Apps]")
    print(f"  CSP Enabled (enforced):  {canvas_enabled}")
    print(f"  CSP Configuration:       {canvas_config}")
    if canvas_config:
        try:
            parsed = json.loads(canvas_config)
            print(f"  Parsed config:           {json.dumps(parsed, indent=4)}")
        except json.JSONDecodeError:
            print("  (not valid JSON)")

    # Reporting
    report_uri = org.get("contentsecuritypolicyreporturi")
    print("\n[Reporting]")
    print(f"  Report URI:              {report_uri or '(not set)'}")

# ── Also check for any code-app-specific CSP fields ───────────────
print(f"\n{'=' * 60}")
print("Searching for code-app CSP fields on organization entity...\n")

# Query ALL organization fields to find any with 'csp' or 'contentsecurity' in name
metadata_url = f"{base}/api/data/{ver}/EntityDefinitions(LogicalName='organization')/Attributes?$select=LogicalName,DisplayName&$filter=contains(LogicalName,'contentsecuritypolicy')"

with httpx.Client(timeout=30.0) as client:
    resp = client.get(metadata_url, headers=headers)
    resp.raise_for_status()
    attrs = resp.json()["value"]

print(f"Organization entity attributes matching 'contentsecuritypolicy': {len(attrs)}")
for attr in attrs:
    ln = attr.get("LogicalName", "?")
    dn = attr.get("DisplayName", {}).get("UserLocalizedLabel", {})
    dn_text = dn.get("Label", "") if isinstance(dn, dict) else ""
    print(f"  {ln}  ({dn_text})")

# Now check if any field has 'codeapp' or 'codeapps' in name
print()
metadata_url2 = f"{base}/api/data/{ver}/EntityDefinitions(LogicalName='organization')/Attributes?$select=LogicalName&$filter=contains(LogicalName,'codeapp')"

with httpx.Client(timeout=30.0) as client:
    resp2 = client.get(metadata_url2, headers=headers)
    resp2.raise_for_status()
    attrs2 = resp2.json()["value"]

if attrs2:
    print(f"Organization entity attributes matching 'codeapp': {len(attrs2)}")
    for attr in attrs2:
        print(f"  {attr.get('LogicalName', '?')}")
else:
    print("No 'codeapp' fields found on organization entity.")

# Also search for 'app' combined with 'security'
metadata_url3 = f"{base}/api/data/{ver}/EntityDefinitions(LogicalName='organization')/Attributes?$select=LogicalName&$filter=contains(LogicalName,'contentsecuritypolicyoptions')"
with httpx.Client(timeout=30.0) as client:
    resp3 = client.get(metadata_url3, headers=headers)
    resp3.raise_for_status()
    attrs3 = resp3.json()["value"]

if attrs3:
    print(
        f"\nOrganization entity attributes matching 'contentsecuritypolicyoptions': {len(attrs3)}"
    )
    for attr in attrs3:
        print(f"  {attr.get('LogicalName', '?')}")
