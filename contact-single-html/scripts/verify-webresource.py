"""Verify the deployed web resource content in Dataverse."""

import base64
import re
import sys
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

# Get token
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

# Fetch web resource content
wr_id = "a665e256-0f17-f111-8341-7c1e52fc4a22"
with httpx.Client(timeout=30.0) as client:
    resp = client.get(
        f"{base_url}/api/data/v9.2/webresourceset({wr_id})?$select=name,displayname,content",
        headers=headers,
    )
    resp.raise_for_status()
    data = resp.json()
    content = base64.b64decode(data["content"]).decode("utf-8")

    # Check for version strings
    versions = re.findall(r"v\d+\.\d+\.\d+", content)
    print(f"Web resource: {data['name']}")
    print(f"Display name: {data['displayname']}")
    print(f"Content size: {len(content):,} chars")
    print(f"Version strings found: {versions}")

    # Check for save button vs auto-save
    has_save_btn = "btn-save" in content or "handleSave" in content
    has_autosave = "autoSaveField" in content and "setFieldAndSave" in content
    has_old_dirty = "isDirty" in content or "updateDirtyState" in content
    has_top_bar = 'class="top-bar"' in content
    has_parent_refresh = "refreshParentForm" in content
    print(f"Has save button: {has_save_btn}")
    print(f"Has auto-save:   {has_autosave}")
    print(f"Has old dirty:   {has_old_dirty}")
    print(f"Has top bar:     {has_top_bar}")
    print(f"Has parent refresh: {has_parent_refresh}")

    if (
        "v1.3.0" in versions
        and has_autosave
        and not has_save_btn
        and not has_old_dirty
        and not has_top_bar
        and has_parent_refresh
    ):
        print(
            "\n✓ Deployment verified — v1.3.0 with auto-save, parent form refresh, no top bar."
        )
    else:
        print("\n✗ Deployment issue detected!")
        sys.exit(1)
