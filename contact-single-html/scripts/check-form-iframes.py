"""Check what IFrame URLs are on the contact form."""

import re
from pathlib import Path

import httpx
import msal

# Load env
env_path = (
    Path(__file__).resolve().parent.parent.parent / "mcp-dataverse-server" / ".env"
)
env = {}
for line in env_path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"').strip("'")

base_url = env["DATAVERSE_BASE_URL"].rstrip("/")
app = msal.ConfidentialClientApplication(
    client_id=env["DATAVERSE_CLIENT_ID"],
    client_credential=env["DATAVERSE_CLIENT_SECRET"],
    authority=f"https://login.microsoftonline.com/{env['DATAVERSE_TENANT_ID']}",
)
result = app.acquire_token_for_client(scopes=[f"{base_url}/.default"])
token = result["access_token"]
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json",
    "OData-MaxVersion": "4.0",
    "OData-Version": "4.0",
}

form_id = "b45b0a55-3d74-f011-b4cc-002248a0aee6"
with httpx.Client(timeout=30.0) as client:
    resp = client.get(
        f"{base_url}/api/data/v9.2/systemforms({form_id})?$select=name,formxml",
        headers=headers,
    )
    resp.raise_for_status()
    data = resp.json()
    print(f"Form: {data['name']}")
    formxml = data["formxml"]

    # Find IFrame controls with their URLs
    # Pattern: <control id="IFRAME_xxx" ... classid="{FD2A7985-...}"> ... <Url>...</Url>
    iframes = re.findall(
        r'<control\s+id="([^"]*IFRAME[^"]*)"[^>]*>.*?<Url>([^<]*)</Url>',
        formxml,
        re.DOTALL | re.IGNORECASE,
    )
    print(f"\nIFrame controls found: {len(iframes)}")
    for iframe_id, url in iframes:
        print(f"  {iframe_id}")
        print(f"    URL: {url}")

    # Also find web resource controls
    # classid for web resource = {9FDF5F91-88B1-47f4-AD53-C11EFC01A01D}
    webres = re.findall(
        r'<control\s+id="([^"]*)"[^>]*classid="\{9FDF5F91[^}]*\}"[^>]*>.*?<Url>([^<]*)</Url>',
        formxml,
        re.DOTALL | re.IGNORECASE,
    )
    if webres:
        print(f"\nWeb Resource controls found: {len(webres)}")
        for wr_id, url in webres:
            print(f"  {wr_id}")
            print(f"    URL: {url}")
