"""
Update the IFrame URL on the 'App' tab of the 'Contact for Utilities (Interactive)' form
to point to the Power Apps Code App (Energy Dashboard).

Old URL: https://mj-webapps-demo-2026.azurewebsites.net/ContactDemo
New URL: https://apps.powerapps.com/play/e/08690526-047d-ed9d-ab35-4528a98c0f4f/app/69d080da-4ad0-4719-8698-d475b552fee2
  (with ?hideNavBar=true — D365 will append &typename=contact&type=2&id={guid})

Also update the IFrame Scrolling from 'auto' to 'no' since the dashboard is designed
to fit the viewport without scrolling.
"""

import os
import sys
import xml.etree.ElementTree as ET

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
    "Content-Type": "application/json",
    "OData-MaxVersion": "4.0",
    "OData-Version": "4.0",
}

# ── Config ────────────────────────────────────────────────────────
FORM_ID = "b45b0a55-3d74-f011-b4cc-002248a0aee6"
FORM_NAME = "Contact for Utilities (Interactive)"
IFRAME_ID = "IFRAME_MJWebPage"
NEW_URL = "https://apps.powerapps.com/play/e/08690526-047d-ed9d-ab35-4528a98c0f4f/app/69d080da-4ad0-4719-8698-d475b552fee2?hideNavBar=true"

# ── Step 1: Fetch current formxml ─────────────────────────────────
print(f"Fetching form: {FORM_NAME} ({FORM_ID})")
url = f"{base}/api/data/{ver}/systemforms({FORM_ID})?$select=formxml"

with httpx.Client(timeout=30.0) as client:
    resp = client.get(url, headers=headers)
    resp.raise_for_status()
    formxml = resp.json()["formxml"]

# ── Step 2: Parse and update the IFrame URL ───────────────────────
root = ET.fromstring(formxml)

# Find the IFrame control by its id
iframe_ctrl = None
for ctrl in root.iter("control"):
    if ctrl.get("id") == IFRAME_ID:
        iframe_ctrl = ctrl
        break

if iframe_ctrl is None:
    print(f"ERROR: Could not find IFrame control with id={IFRAME_ID!r}")
    sys.exit(1)

params = iframe_ctrl.find("parameters")
if params is None:
    print("ERROR: IFrame control has no <parameters> element")
    sys.exit(1)

# Update URL
url_el = params.find("Url")
old_url = url_el.text if url_el is not None else "(none)"
print(f"Old URL: {old_url}")

if url_el is None:
    url_el = ET.SubElement(params, "Url")
url_el.text = NEW_URL
print(f"New URL: {NEW_URL}")

# Update Scrolling to 'no'
scroll_el = params.find("Scrolling")
if scroll_el is not None:
    print(f"Scrolling: {scroll_el.text} → no")
    scroll_el.text = "no"

# Ensure PassParameters is true
pass_el = params.find("PassParameters")
if pass_el is not None:
    print(f"PassParameters: {pass_el.text}")
else:
    pass_el = ET.SubElement(params, "PassParameters")
    pass_el.text = "true"
    print("PassParameters: added (true)")

# Ensure Security is false (no cross-frame restriction)
sec_el = params.find("Security")
if sec_el is not None:
    print(f"Security: {sec_el.text}")
    sec_el.text = "false"

print(
    f"Border: {params.find('Border').text if params.find('Border') is not None else '?'}"
)

# ── Step 3: Serialize and PATCH back ──────────────────────────────
new_formxml = ET.tostring(root, encoding="unicode", xml_declaration=False)

print("\nUpdating form in Dataverse...")
patch_url = f"{base}/api/data/{ver}/systemforms({FORM_ID})"

with httpx.Client(timeout=30.0) as client:
    resp = client.patch(
        patch_url,
        headers=headers,
        json={"formxml": new_formxml},
    )
    resp.raise_for_status()
    print(f"PATCH response: {resp.status_code}")

# ── Step 4: Publish the form ──────────────────────────────────────
print("\nPublishing form...")
publish_url = f"{base}/api/data/{ver}/PublishXml"
publish_xml = (
    "<importexportxml><entities><entity>contact</entity></entities></importexportxml>"
)

with httpx.Client(timeout=60.0) as client:
    resp = client.post(
        publish_url,
        headers=headers,
        json={"ParameterXml": publish_xml},
    )
    resp.raise_for_status()
    print(f"Publish response: {resp.status_code}")

print("\n✅ Done! The 'App' tab IFrame now points to the Energy Dashboard Code App.")
print("   D365 will auto-append the contact ID when the tab loads.")
