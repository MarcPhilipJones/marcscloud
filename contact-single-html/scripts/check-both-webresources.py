"""Check the web resource the form is actually using."""

import base64
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

# Search for both web resources
names = ["mj_contact_energy_dashboard", "mj_/html/contactenergydashboard.html"]

with httpx.Client(timeout=30.0) as client:
    for name in names:
        print(f"--- Searching for: {name} ---")
        resp = client.get(
            f"{base_url}/api/data/v9.2/webresourceset"
            f"?$filter=name eq '{name}'"
            f"&$select=webresourceid,name,displayname,content",
            headers=headers,
        )
        resp.raise_for_status()
        results = resp.json().get("value", [])
        if not results:
            print("  NOT FOUND\n")
            continue

        wr = results[0]
        content = base64.b64decode(wr["content"]).decode("utf-8")
        versions = re.findall(r"v\d+\.\d+\.\d+", content)
        has_save_btn = "btn-save" in content
        has_autosave = "autoSaveField" in content

        print(f"  ID: {wr['webresourceid']}")
        print(f"  Display: {wr.get('displayname', 'N/A')}")
        print(f"  Size: {len(content):,} chars")
        print(f"  Versions: {versions}")
        print(f"  Has save button: {has_save_btn}")
        print(f"  Has auto-save: {has_autosave}")
        print()
