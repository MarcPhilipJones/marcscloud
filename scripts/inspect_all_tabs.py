"""Inspect ALL tabs on the 'Contact for Utilities (Interactive)' form."""

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

filt = "objecttypecode eq 'contact' and contains(name, 'Utilities')"
url = (
    f"{base}/api/data/{ver}/systemforms?$filter={filt}&$select=formid,name,type,formxml"
)

with httpx.Client(timeout=30.0) as client:
    resp = client.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()

forms = data.get("value", [])
print(f"Found {len(forms)} form(s)")

for form in forms:
    print(f"\nForm: {form['name']}  ID: {form['formid']}  Type: {form['type']}")
    formxml = form.get("formxml", "")
    if not formxml:
        continue

    root = ET.fromstring(formxml)
    tabs = root.findall(".//tab")
    print(f"  Tabs ({len(tabs)}):")

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
        tab_id = tab.get("id", "?")
        print(f"    [{i}] id={tab_id!r} name={tab_name!r} label={label_text!r}")

        # For "App" tab, dump full structure
        if "app" in label_text.lower() or "app" in tab_name.lower():
            print("\n    >>> INSPECTING 'APP' TAB <<<")
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
                sec_id = sec.get("id", "?")
                print(
                    f"      Section [{si}] id={sec_id!r} name={sec_name!r} label={sec_label!r}"
                )

                rows = sec.findall(".//row")
                for ri, row in enumerate(rows):
                    cells = row.findall("cell")
                    for ci, cell in enumerate(cells):
                        ctrl = cell.find("control")
                        if ctrl is not None:
                            ctrl_id = ctrl.get("id", "?")
                            ctrl_classid = ctrl.get("classid", "")
                            ctrl_datafieldname = ctrl.get("datafieldname", "")
                            print(
                                f"        Row {ri} Cell {ci}: id={ctrl_id!r} classid={ctrl_classid!r} field={ctrl_datafieldname!r}"
                            )
                            # Dump params for iframe controls
                            if (
                                ctrl_classid.upper()
                                == "{FD2A7985-3187-444E-908D-6624B21F69C0}"
                            ):
                                print("          ^ IFRAME control")
                                params_el = ctrl.find("parameters")
                                if params_el is not None:
                                    for p in params_el:
                                        print(f"          {p.tag} = {p.text}")
                        else:
                            print(f"        Row {ri} Cell {ci}: (empty cell)")

            # Also dump raw XML snippet for the tab
            tab_xml = ET.tostring(tab, encoding="unicode")
            if len(tab_xml) < 3000:
                print(f"\n    RAW XML:\n{tab_xml}")
            else:
                print(f"\n    RAW XML (truncated):\n{tab_xml[:3000]}...")

print("\nDone.")
