"""
Add a new 'App2' tab to the 'Contact for Utilities (Interactive)' form.
This tab embeds the Contact Code App via IFrame, testing whether the
CSP toggle in Power Platform Admin Centre allows D365 embedding.

Code App URL: https://apps.powerapps.com/play/e/08690526-047d-ed9d-ab35-4528a98c0f4f/app/69d080da-4ad0-4719-8698-d475b552fee2?hideNavBar=true
"""

import os
import sys
import uuid
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
CODE_APP_URL = "https://apps.powerapps.com/play/e/08690526-047d-ed9d-ab35-4528a98c0f4f/app/69d080da-4ad0-4719-8698-d475b552fee2?hideNavBar=true"

# IFrame classid for D365 forms
IFRAME_CLASSID = "{FD2A7985-3187-444E-908D-6624B21F69C0}"

# ── Step 1: Fetch current formxml ─────────────────────────────────
print(f"Fetching form: {FORM_NAME} ({FORM_ID})")
url = f"{base}/api/data/{ver}/systemforms({FORM_ID})?$select=formxml"

with httpx.Client(timeout=30.0) as client:
    resp = client.get(url, headers=headers)
    resp.raise_for_status()
    formxml = resp.json()["formxml"]

root = ET.fromstring(formxml)

# ── Step 2: Check if App2 tab already exists ──────────────────────
tabs_parent = root.find(".//tabs")
if tabs_parent is None:
    # tabs might be direct children
    tabs_parent = root

existing_tabs = root.findall(".//tab")
print(f"\nExisting tabs ({len(existing_tabs)}):")
for tab in existing_tabs:
    name = tab.get("name", "?")
    labels = tab.find("labels")
    label_text = ""
    if labels is not None:
        lbl = labels.find("label")
        if lbl is not None:
            label_text = lbl.get("description", "")
    print(f"  {name} = '{label_text}'")
    if name == "tab_5" or label_text == "App2":
        print("\n⚠️  'App2' tab already exists! Removing it to recreate...")
        tabs_parent.remove(tab)

# ── Step 3: Build the new App2 tab XML ────────────────────────────
tab_id = str(uuid.uuid4())
section_id = str(uuid.uuid4())
cell_id = str(uuid.uuid4())

# Build the tab XML structure matching the existing App tab pattern
tab_xml = f"""<tab name="tab_5" id="{tab_id}" IsUserDefined="0" locklevel="0" showlabel="true" expanded="false" visible="true">
  <labels>
    <label description="App2" languagecode="1033" />
  </labels>
  <columns>
    <column width="100%">
      <sections>
        <section name="tab_5_section_1" id="{section_id}" IsUserDefined="0" locklevel="0" showlabel="false" showbar="false" layout="varwidth" celllabelalignment="Left" celllabelposition="Left" columns="1" labelwidth="115">
          <labels>
            <label description="Code App Section" languagecode="1033" />
          </labels>
          <rows>
            <row />
            <row>
              <cell locklevel="0" id="{{{cell_id}}}" showlabel="false" rowspan="40" colspan="1" auto="true">
                <labels>
                  <label description="Code App IFrame" languagecode="1033" />
                </labels>
                <control id="IFRAME_CodeApp" classid="{IFRAME_CLASSID}">
                  <parameters>
                    <PassParameters>true</PassParameters>
                    <Security>false</Security>
                    <Scrolling>auto</Scrolling>
                    <Border>false</Border>
                    <Url>{CODE_APP_URL}</Url>
                  </parameters>
                </control>
                <events>
                  <event name="onload" application="false" active="false" />
                </events>
              </cell>
            </row>
            <row /><row /><row /><row /><row /><row /><row /><row />
            <row /><row /><row /><row /><row /><row /><row /><row />
            <row /><row /><row /><row /><row /><row /><row /><row />
            <row /><row /><row /><row /><row /><row /><row /><row />
            <row /><row /><row /><row /><row />
          </rows>
        </section>
      </sections>
    </column>
  </columns>
</tab>"""

new_tab = ET.fromstring(tab_xml)

# ── Step 4: Insert after the App tab (tab_4) ─────────────────────
# Find the parent that contains tab elements
tabs_container = None
for parent in root.iter():
    for child in parent:
        if child.tag == "tab":
            tabs_container = parent
            break
    if tabs_container is not None:
        break

if tabs_container is None:
    print("ERROR: Could not find tabs container in formxml")
    sys.exit(1)

# Find index of tab_4 and insert after it
tab_list = list(tabs_container)
insert_idx = None
for i, child in enumerate(tab_list):
    if child.tag == "tab" and child.get("name") == "tab_4":
        insert_idx = i + 1
        break

if insert_idx is not None:
    tabs_container.insert(insert_idx, new_tab)
    print(f"\nInserted 'App2' tab after 'App' tab (position {insert_idx})")
else:
    tabs_container.append(new_tab)
    print("\nAppended 'App2' tab at end (couldn't find tab_4)")

# Verify
all_tabs = root.findall(".//tab")
print(f"\nUpdated form now has {len(all_tabs)} tabs:")
for tab in all_tabs:
    name = tab.get("name", "?")
    labels = tab.find("labels")
    lbl_text = ""
    if labels is not None:
        lbl = labels.find("label")
        if lbl is not None:
            lbl_text = lbl.get("description", "")
    print(f"  {name} = '{lbl_text}'")

# ── Step 5: Serialize and PATCH back ──────────────────────────────
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

# ── Step 6: Publish the form ──────────────────────────────────────
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

print("\n✅ Done! New 'App2' tab added with Code App IFrame.")
print(f"   URL: {CODE_APP_URL}")
print(
    "   D365 will auto-append &typename=contact&type=2&id={{guid}} when the tab loads."
)
print("\n   Open a contact record and click the 'App2' tab to test embedding.")
