"""Update the 'Summary' tab labels on 'Contact for Utilities (Interactive)' form with emoji prefixes."""

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

# Emoji mapping: (datafieldname, current_label) -> new_label
# Using tuple key because parentcustomerid appears twice with different labels
EMOJI_LABELS = {
    ("parentcustomerid", "Company Name"): "🏛️ Company Name",
    ("firstname", "First Name"): "🅰️ First Name",
    ("lastname", "Last Name"): "🅱️ Last Name",
    ("mj_priorityregister", "Priority Register"): "⭐ Priority Register",
    ("mj_smartmeter", "Smart Meter"): "📊 Smart Meter",
    ("parentcustomerid", "Account Name"): "🏢 Account Name",
    ("mobilephone", "Mobile Phone"): "📱 Mobile Phone",
    ("fax", "Fax"): "📠 Fax",
    ("preferredcontactmethodcode", "Contact Method"): "💬 Contact Method",
    ("address1_composite", "Address"): "📍 Address",
    ("emailaddress1", "Email"): "📧 Email",
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
    if tab_name != "SUMMARY_TAB":
        continue

    print("\nProcessing SUMMARY_TAB...")

    for cell in tab.findall(".//cell"):
        ctrl = cell.find("control")
        if ctrl is None:
            continue
        datafieldname = ctrl.get("datafieldname", "")
        if not datafieldname:
            continue

        # Get current label
        labels_el = cell.find("labels")
        current_label = ""
        if labels_el is not None:
            for lbl in labels_el.findall("label"):
                if lbl.get("languagecode") == "1033":
                    current_label = lbl.get("description", "")
                    break

        lookup_key = (datafieldname, current_label)
        if lookup_key not in EMOJI_LABELS:
            continue

        new_label = EMOJI_LABELS[lookup_key]

        if labels_el is None:
            labels_el = ET.SubElement(cell, "labels")

        found = False
        for lbl in labels_el.findall("label"):
            if lbl.get("languagecode") == "1033":
                lbl.set("description", new_label)
                found = True
                break

        if not found:
            new_lbl = ET.SubElement(labels_el, "label")
            new_lbl.set("description", new_label)
            new_lbl.set("languagecode", "1033")

        print(f"  {datafieldname}: '{current_label}' -> '{new_label}'")
        changes += 1

print(f"\n{changes} label(s) updated in XML.")

if changes == 0:
    print("No changes to apply.")
    sys.exit(0)

# Step 3: Serialize and PATCH
updated_xml = ET.tostring(root, encoding="unicode", xml_declaration=False)

print(f"\nPATCHing form {form_id}...")
with httpx.Client(timeout=30.0) as client:
    resp = client.patch(
        f"{base}/api/data/{ver}/systemforms({form_id})",
        headers=headers,
        json={"formxml": updated_xml},
    )
    if resp.status_code == 204:
        print("Form updated successfully!")
    else:
        print(f"PATCH failed: {resp.status_code}")
        print(resp.text[:500])
        sys.exit(1)

# Step 4: Publish
print("\nPublishing contact entity...")
with httpx.Client(timeout=60.0) as client:
    resp = client.post(
        f"{base}/api/data/{ver}/PublishXml",
        headers=headers,
        json={
            "ParameterXml": "<importexportxml><entities><entity>contact</entity></entities></importexportxml>"
        },
    )
    if resp.status_code in (200, 204):
        print("Published successfully!")
    else:
        print(f"Publish failed: {resp.status_code}")
        print(resp.text[:500])

print("\nDone! Refresh the form in D365 to see the emoji labels.")
