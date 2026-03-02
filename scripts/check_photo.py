"""Find Alan Steiner's contact ID and check if photo exists."""

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
headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

url = f"{base}/api/data/{ver}/contacts?$filter=contains(fullname,'Alan Steiner')&$select=contactid,fullname,entityimage_url"
with httpx.Client(timeout=30.0) as client:
    resp = client.get(url, headers=headers)
    for c in resp.json().get("value", []):
        print(json.dumps(c, indent=2))
        cid = c["contactid"]
        # Try fetching the entity image
        img_url = f"{base}/api/data/{ver}/contacts({cid})/entityimage/$value"
        img_resp = client.get(
            img_url, headers={"Authorization": f"Bearer {token}", "Accept": "image/*"}
        )
        print(
            f"Photo status: {img_resp.status_code}, Content-Type: {img_resp.headers.get('content-type', '?')}, Size: {len(img_resp.content)} bytes"
        )
