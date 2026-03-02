"""List all fields on the 'Summary' tab of the Contact for Utilities (Interactive) form."""

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

filt = "objecttypecode eq 'contact' and contains(name, 'Utilities (Interactive')"
url = f"{base}/api/data/{ver}/systemforms?$filter={filt}&$select=formid,name,formxml"

with httpx.Client(timeout=30.0) as client:
    resp = client.get(url, headers=headers)
    resp.raise_for_status()
    forms = resp.json().get("value", [])

for form in forms:
    root = ET.fromstring(form["formxml"])

    for tab in root.findall(".//tab"):
        tab_name = tab.get("name", "")
        if tab_name != "SUMMARY_TAB":
            continue

        labels_el = tab.find("labels")
        label_text = ""
        if labels_el is not None:
            for lbl in labels_el.findall("label"):
                if lbl.get("languagecode") == "1033":
                    label_text = lbl.get("description", "")
                    break

        print(f"Tab: {label_text!r} (name={tab_name})")
        print("-" * 60)

        for section in tab.findall(".//section"):
            sec_labels = section.find("labels")
            sec_label = ""
            if sec_labels is not None:
                for lbl in sec_labels.findall("label"):
                    if lbl.get("languagecode") == "1033":
                        sec_label = lbl.get("description", "")
                        break
            sec_name = section.get("name", "")
            print(f"\n  Section: {sec_label!r} (name={sec_name})")

            for row in section.findall(".//row"):
                for cell in row.findall("cell"):
                    ctrl = cell.find("control")
                    if ctrl is None:
                        continue
                    datafieldname = ctrl.get("datafieldname", "")
                    ctrl_id = ctrl.get("id", "")
                    classid = ctrl.get("classid", "")

                    cell_labels = cell.find("labels")
                    cell_label = ""
                    if cell_labels is not None:
                        for lbl in cell_labels.findall("label"):
                            if lbl.get("languagecode") == "1033":
                                cell_label = lbl.get("description", "")
                                break

                    if datafieldname:
                        display = cell_label if cell_label else datafieldname
                        print(f"    Field: {datafieldname:<45} Label: {display}")
                    elif ctrl_id:
                        print(f"    Control: {ctrl_id:<43} ClassID: {classid[:40]}")
