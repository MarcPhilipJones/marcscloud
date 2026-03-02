"""Update the 'Details' tab labels on 'Contact for Utilities (Interactive)' form with emoji prefixes."""

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

# Emoji mapping: datafieldname -> new label
EMOJI_LABELS = {
    "gendercode": "⚧️ Gender",
    "familystatuscode": "💑 Marital Status",
    "spousesname": "❤️ Spouse/Partner Name",
    "birthdate": "🎂 Birthday",
    "anniversary": "💍 Anniversary",
    "mj_initiateoutboundcall": "📞 Initiate Outbound Call",
    "description": "📝 Description",
    "originatingleadid": "🎯 Originating Lead",
    "lastusedincampaign": "📅 Last Campaign Date",
    "donotsendmm": "📰 Marketing Materials",
    "preferredcontactmethodcode": "💬 Contact Method",
    "donotemail": "🚫 Email",
    "followemail": "📨 Follow Email",
    "donotbulkemail": "🚫 Bulk Email",
    "donotphone": "🚫 Phone",
    "donotfax": "🚫 Fax",
    "donotpostalmail": "🚫 Mail",
    "transactioncurrencyid": "💷 Currency",
    "creditlimit": "💳 Credit Limit",
    "creditonhold": "⛔ Credit Hold",
    "paymenttermscode": "📋 Payment Terms",
    "address1_shippingmethodcode": "🚚 Shipping Method",
    "address1_freighttermscode": "📦 Freight Terms",
}

# Step 1: Get the form
print("Fetching form...")
filt = "objecttypecode eq 'contact' and contains(name, 'Utilities (Interactive')"
url = f"{base}/api/data/{ver}/systemforms?$filter={filt}&$select=formid,name,formxml"

with httpx.Client(timeout=30.0) as client:
    resp = client.get(url, headers=headers)
    resp.raise_for_status()
    forms = resp.json().get("value", [])

if not forms:
    print("ERROR: Form not found!")
    sys.exit(1)

form = forms[0]
form_id = form["formid"]
print(f"Form: {form['name']} (ID: {form_id})")

# Step 2: Parse and update the formxml
root = ET.fromstring(form["formxml"])
changes = 0

for tab in root.findall(".//tab"):
    tab_name = tab.get("name", "")
    if tab_name != "DETAILS_TAB":
        continue

    print("\nProcessing DETAILS_TAB...")

    for cell in tab.findall(".//cell"):
        ctrl = cell.find("control")
        if ctrl is None:
            continue
        datafieldname = ctrl.get("datafieldname", "")
        if datafieldname not in EMOJI_LABELS:
            continue

        new_label = EMOJI_LABELS[datafieldname]

        # Find or create labels element
        labels_el = cell.find("labels")
        if labels_el is None:
            labels_el = ET.SubElement(cell, "labels")

        # Find English label (1033)
        found = False
        for lbl in labels_el.findall("label"):
            if lbl.get("languagecode") == "1033":
                old = lbl.get("description", "")
                lbl.set("description", new_label)
                print(f"  {datafieldname}: '{old}' -> '{new_label}'")
                found = True
                changes += 1
                break

        if not found:
            # Create a new label element
            new_lbl = ET.SubElement(labels_el, "label")
            new_lbl.set("description", new_label)
            new_lbl.set("languagecode", "1033")
            print(f"  {datafieldname}: (no label) -> '{new_label}'")
            changes += 1

print(f"\n{changes} label(s) updated in XML.")

if changes == 0:
    print("No changes to apply.")
    sys.exit(0)

# Step 3: Serialize updated formxml
updated_xml = ET.tostring(root, encoding="unicode", xml_declaration=False)

# Step 4: PATCH the form
print(f"\nPATCHing form {form_id}...")
patch_url = f"{base}/api/data/{ver}/systemforms({form_id})"
patch_body = {"formxml": updated_xml}

with httpx.Client(timeout=30.0) as client:
    resp = client.patch(patch_url, headers=headers, json=patch_body)
    if resp.status_code == 204:
        print("Form updated successfully!")
    else:
        print(f"PATCH failed: {resp.status_code}")
        print(resp.text[:500])
        sys.exit(1)

# Step 5: Publish the entity so changes appear in the UI
print("\nPublishing contact entity...")
publish_url = f"{base}/api/data/{ver}/PublishXml"
publish_body = {
    "ParameterXml": "<importexportxml><entities><entity>contact</entity></entities></importexportxml>"
}
with httpx.Client(timeout=60.0) as client:
    resp = client.post(publish_url, headers=headers, json=publish_body)
    if resp.status_code in (200, 204):
        print("Published successfully!")
    else:
        print(f"Publish failed: {resp.status_code}")
        print(resp.text[:500])

print("\nDone! Refresh the form in D365 to see the emoji labels.")
