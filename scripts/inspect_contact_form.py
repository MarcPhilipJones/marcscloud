"""Inspect the 'Contact for Utilities (Interactive)' form and its 'Contact Details' tab."""

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
headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

# Step 1: Find the form
filt = "objecttypecode eq 'contact' and contains(name, 'Utilities')"
url = (
    f"{base}/api/data/{ver}/systemforms?$filter={filt}&$select=formid,name,type,formxml"
)

with httpx.Client(timeout=30.0) as client:
    resp = client.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()

forms = data.get("value", [])
print(f"Found {len(forms)} form(s) matching 'Utilities'")

for form in forms:
    print(f"\n{'=' * 60}")
    print(f"Form: {form['name']}")
    print(f"ID:   {form['formid']}")
    print(f"Type: {form['type']}")

    formxml = form.get("formxml", "")
    if not formxml:
        print("  No formxml")
        continue

    root = ET.fromstring(formxml)

    # List all tabs
    tabs = root.findall(".//tab")
    print(f"\nTabs ({len(tabs)}):")
    for i, tab in enumerate(tabs):
        labels = tab.find("labels")
        label_text = ""
        if labels is not None:
            for lbl in labels.findall("label"):
                if lbl.get("languagecode") == "1033":
                    label_text = lbl.get("description", "")
                    break
            if not label_text:
                first = labels.find("label")
                if first is not None:
                    label_text = first.get("description", "")
        tab_name = tab.get("name", f"tab_{i}")
        print(f"  [{i}] name={tab_name!r}  label={label_text!r}")

        # If this is the Contact Details tab, dump its full structure
        if "Contact Details" in label_text or "contact details" in label_text.lower():
            print(f"\n  >>> INSPECTING TAB: {label_text}")
            sections = tab.findall(".//section")
            for si, sec in enumerate(sections):
                sec_labels = sec.find("labels")
                sec_label = ""
                if sec_labels is not None:
                    for lbl in sec_labels.findall("label"):
                        if lbl.get("languagecode") == "1033":
                            sec_label = lbl.get("description", "")
                            break
                sec_name = sec.get("name", f"section_{si}")
                print(f"\n    Section [{si}] name={sec_name!r} label={sec_label!r}")

                # Check for iframes
                iframes = sec.findall(".//iframe")
                for iframe in iframes:
                    iframe_name = iframe.get("name", "?")
                    iframe_url = iframe.get("url", "")
                    iframe_security = iframe.get("security", "")
                    iframe_scrolling = iframe.get("scrolling", "")
                    iframe_border = iframe.get("border", "")
                    pass_params = iframe.get("passparameters", "")
                    print(f"      IFRAME: name={iframe_name!r}")
                    print(f"        url={iframe_url!r}")
                    print(f"        passparameters={pass_params!r}")
                    print(f"        security={iframe_security!r}")
                    print(f"        scrolling={iframe_scrolling!r}")
                    print(f"        border={iframe_border!r}")

                # Check for web resources
                webresources = sec.findall(".//WebResource")
                for wr in webresources:
                    print(
                        f"      WebResource: {ET.tostring(wr, encoding='unicode')[:200]}"
                    )

                # Check for regular controls/fields
                rows = sec.findall(".//row")
                for row in rows:
                    cells = row.findall("cell")
                    for cell in cells:
                        ctrl = cell.find("control")
                        if ctrl is not None:
                            ctrl_id = ctrl.get("id", "?")
                            ctrl_classid = ctrl.get("classid", "")
                            ctrl_datafieldname = ctrl.get("datafieldname", "")
                            # Check if it's an iframe control
                            if (
                                "iframe" in ctrl_classid.lower()
                                or "iframe" in ctrl_id.lower()
                            ):
                                print(
                                    f"      IFRAME CONTROL: id={ctrl_id!r} classid={ctrl_classid!r}"
                                )
                                params = ctrl.findall(".//parameter")
                                for p in params:
                                    print(f"        param: {p.tag} = {p.text}")
                                # dump full control XML
                                print(
                                    f"        XML: {ET.tostring(ctrl, encoding='unicode')[:500]}"
                                )
                            elif ctrl_datafieldname:
                                print(f"      Field: {ctrl_datafieldname}")
                            else:
                                print(
                                    f"      Control: id={ctrl_id!r} classid={ctrl_classid!r}"
                                )
                                # Might be an iframe by classid
                                if (
                                    ctrl_classid
                                    == "{FD2A7985-3187-4571-85A1-ED7B72A4F31D}"
                                ):
                                    print("        ^ This is an IFRAME control classid")
                                    for child in ctrl:
                                        print(
                                            f"        child: {ET.tostring(child, encoding='unicode')[:300]}"
                                        )

print("\nDone.")
