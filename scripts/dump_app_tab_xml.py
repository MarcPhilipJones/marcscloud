"""Dump the full XML of the 'App' tab (tab_4) from the Contact form."""

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

FORM_ID = "b45b0a55-3d74-f011-b4cc-002248a0aee6"
url = f"{base}/api/data/{ver}/systemforms({FORM_ID})?$select=formxml"

with httpx.Client(timeout=30.0) as client:
    resp = client.get(url, headers=headers)
    resp.raise_for_status()
    formxml = resp.json()["formxml"]

root = ET.fromstring(formxml)

for tab in root.findall(".//tab"):
    if tab.get("name") == "tab_4":
        print(ET.tostring(tab, encoding="unicode"))
        break
