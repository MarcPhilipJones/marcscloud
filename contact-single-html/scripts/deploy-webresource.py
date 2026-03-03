r"""
Deploy Contact Energy Dashboard as a D365 Web Resource
=======================================================
Creates or updates the HTML web resource in Dataverse, then publishes it.

Uses MSAL client-credentials flow (same app reg as other Dataverse scripts).

Usage:
    cd contact-single-html
    ..\.venv\Scripts\python.exe scripts\deploy-webresource.py
"""

import base64
import sys
from pathlib import Path

import httpx
import msal

# ── Configuration ─────────────────────────────────────────────────
WEB_RESOURCE_NAME = "mj_contact_energy_dashboard"
WEB_RESOURCE_DISPLAY_NAME = "Contact Energy Dashboard"
WEB_RESOURCE_DESCRIPTION = (
    "Single-file HTML web resource — contact details with editable "
    "energy/boiler fields and Chart.js usage charts. "
    "Replaces the Contact Code App."
)
# Web resource type: 1=HTML, 2=CSS, 3=JS, 4=XML, 5=PNG, 6=JPG, 7=GIF, 8=XAP, 9=XSL, 10=ICO, 11=SVG, 12=RESX
WEB_RESOURCE_TYPE = 1  # HTML

HTML_FILE = Path(__file__).resolve().parent.parent / "contact-energy-dashboard.html"


# ── Load settings from mcp-dataverse-server .env ──────────────────
def load_env():
    """Load Dataverse credentials from the workspace .env file."""
    env_path = (
        Path(__file__).resolve().parent.parent.parent / "mcp-dataverse-server" / ".env"
    )
    if not env_path.exists():
        print(f"ERROR: .env file not found at {env_path}")
        sys.exit(1)

    env = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def get_token(env: dict) -> str:
    """Acquire a Dataverse access token via MSAL client credentials."""
    base_url = env["DATAVERSE_BASE_URL"].rstrip("/")
    app = msal.ConfidentialClientApplication(
        client_id=env["DATAVERSE_CLIENT_ID"],
        client_credential=env["DATAVERSE_CLIENT_SECRET"],
        authority=f"https://login.microsoftonline.com/{env['DATAVERSE_TENANT_ID']}",
    )
    result = app.acquire_token_for_client(scopes=[f"{base_url}/.default"])
    if "access_token" not in result:
        print(
            f"ERROR: Token acquisition failed: {result.get('error_description', result)}"
        )
        sys.exit(1)
    return result["access_token"]


def main():
    print("=" * 60)
    print("Deploy Contact Energy Dashboard as D365 Web Resource")
    print("=" * 60)

    # 1. Load HTML content
    if not HTML_FILE.exists():
        print(f"ERROR: HTML file not found: {HTML_FILE}")
        sys.exit(1)

    html_bytes = HTML_FILE.read_bytes()
    content_b64 = base64.b64encode(html_bytes).decode("ascii")
    print(f"  HTML file: {HTML_FILE.name} ({len(html_bytes):,} bytes)")

    # 2. Authenticate
    env = load_env()
    token = get_token(env)
    base_url = env["DATAVERSE_BASE_URL"].rstrip("/")
    api_url = f"{base_url}/api/data/v9.2"

    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    print(f"  Dataverse: {base_url}")
    print(f"  Web Resource: {WEB_RESOURCE_NAME}")
    print()

    with httpx.Client(timeout=60.0) as client:
        # 3. Check if web resource already exists
        search_url = (
            f"{api_url}/webresourceset"
            f"?$filter=name eq '{WEB_RESOURCE_NAME}'"
            f"&$select=webresourceid,name,displayname"
        )
        resp = client.get(search_url, headers=headers)
        resp.raise_for_status()
        existing = resp.json().get("value", [])

        if existing:
            # Update existing
            wr_id = existing[0]["webresourceid"]
            print(f"  Found existing web resource: {wr_id}")
            print("  Updating content...")

            update_url = f"{api_url}/webresourceset({wr_id})"
            payload = {
                "content": content_b64,
                "displayname": WEB_RESOURCE_DISPLAY_NAME,
                "description": WEB_RESOURCE_DESCRIPTION,
            }
            resp = client.patch(update_url, headers=headers, json=payload)
            resp.raise_for_status()
            print("  Updated successfully.")
        else:
            # Create new
            print("  Web resource not found — creating new...")
            create_url = f"{api_url}/webresourceset"
            payload = {
                "name": WEB_RESOURCE_NAME,
                "displayname": WEB_RESOURCE_DISPLAY_NAME,
                "description": WEB_RESOURCE_DESCRIPTION,
                "webresourcetype": WEB_RESOURCE_TYPE,
                "content": content_b64,
            }
            resp = client.post(create_url, headers=headers, json=payload)
            resp.raise_for_status()

            # Extract ID from response (POST may return 204 with no body)
            wr_id = None
            if resp.content:
                try:
                    wr_id = resp.json().get("webresourceid")
                except Exception:
                    pass
            if not wr_id:
                loc = resp.headers.get("OData-EntityId", "")
                wr_id = loc.split("(")[-1].rstrip(")") if "(" in loc else "unknown"
            print(f"  Created: {wr_id}")

        # 4. Publish the web resource
        print("\n  Publishing...")
        publish_url = f"{api_url}/PublishXml"
        publish_payload = {
            "ParameterXml": (
                f"<importexportxml><webresources>"
                f"<webresource>{wr_id}</webresource>"
                f"</webresources></importexportxml>"
            )
        }
        resp = client.post(publish_url, headers=headers, json=publish_payload)
        resp.raise_for_status()
        print("  Published successfully.")

    print()
    print("Done! The web resource is now available in D365:")
    print(f"  Name: {WEB_RESOURCE_NAME}")
    print(f"  ID:   {wr_id}")
    print()
    print("To embed on a form, add a Web Resource control pointing to:")
    print(f"  {WEB_RESOURCE_NAME}")


if __name__ == "__main__":
    main()
