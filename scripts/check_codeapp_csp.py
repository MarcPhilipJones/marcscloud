"""
Check and optionally update Code App CSP settings via Power Platform API.
Uses MSAL device code flow with the Power Platform CLI client ID.

API: https://api.powerplatform.com/environmentmanagement/environments/{envId}/settings
Docs: https://learn.microsoft.com/en-us/power-apps/developer/code-apps/how-to/content-security-policy
"""

import json
import os
import sys

# Use workspace venv's msal
os.chdir(r"c:\VSCODE_Developement\logicappsdevelopment\logicappsdevelopment")

import httpx
import msal

# ── Config ────────────────────────────────────────────────────────
TENANT_ID = "996f568a-cc69-450a-b684-ae784069e679"
PAC_CLI_CLIENT_ID = "9cee029c-6210-4654-90bb-17e6e9d36617"  # Power Platform CLI
POWER_PLATFORM_RESOURCE = "https://api.powerplatform.com/"
ENV_ID = "08690526-047d-ed9d-ab35-4528a98c0f4f"  # MJCC2024

# ── Step 1: Authenticate via device code flow ─────────────────────
authority = f"https://login.microsoftonline.com/{TENANT_ID}"
app = msal.PublicClientApplication(PAC_CLI_CLIENT_ID, authority=authority)

# Try cache first
accounts = app.get_accounts()
if accounts:
    result = app.acquire_token_silent(
        scopes=[f"{POWER_PLATFORM_RESOURCE}.default"], account=accounts[0]
    )
else:
    result = None

if not result or "access_token" not in result:
    # Device code flow
    flow = app.initiate_device_flow(scopes=[f"{POWER_PLATFORM_RESOURCE}.default"])
    if "user_code" not in flow:
        print(f"ERROR: Could not initiate device code flow: {flow}")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"To authenticate, visit: {flow['verification_uri']}")
    print(f"Enter code: {flow['user_code']}")
    print(f"{'=' * 60}\n")
    print("Waiting for authentication...")

    result = app.acquire_token_by_device_flow(flow)

if "access_token" not in result:
    print(f"ERROR: Authentication failed: {result.get('error_description', result)}")
    sys.exit(1)

token = result["access_token"]
print("Authenticated successfully!\n")

# ── Step 2: Query current Code App CSP settings ──────────────────
base_url = "https://api.powerplatform.com"
settings_url = (
    f"{base_url}/environmentmanagement/environments/{ENV_ID}/settings"
    f"?api-version=2022-03-01-preview"
    f"&$select=PowerApps_CSPReportingEndpoint,PowerApps_CSPEnabledCodeApps,PowerApps_CSPConfigCodeApps"
)

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

with httpx.Client(timeout=30.0) as client:
    resp = client.get(settings_url, headers=headers)
    if resp.status_code != 200:
        print(f"ERROR ({resp.status_code}): {resp.text}")
        sys.exit(1)

    data = resp.json()

settings_list = data.get("objectResult", data.get("value", [data]))
if isinstance(settings_list, list) and len(settings_list) > 0:
    settings_data = settings_list[0]
else:
    settings_data = settings_list

print("=" * 60)
print("Code App CSP Settings (MJCC2024)")
print("=" * 60)

csp_enabled = settings_data.get("PowerApps_CSPEnabledCodeApps")
csp_config = settings_data.get("PowerApps_CSPConfigCodeApps")
csp_report = settings_data.get("PowerApps_CSPReportingEndpoint")

print(f"CSP Enabled (enforced):  {csp_enabled}")
print(f"Reporting Endpoint:      {csp_report or '(not set)'}")
print(f"CSP Config (raw):        {csp_config or '(not set - using defaults)'}")

if csp_config:
    try:
        parsed = json.loads(csp_config)
        print("\nParsed directives:")
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        pass

print("\nDefault frame-ancestors: 'self' https://*.powerapps.com")
print("\nTo embed in D365, need: https://*.dynamics.com")
print("=" * 60)

# ── Step 3: Ask to update ─────────────────────────────────────────
if "--update" in sys.argv:
    print("\n>>> UPDATING frame-ancestors to allow D365 embedding...")

    # Build the config: add *.dynamics.com to frame-ancestors
    # Get existing directives first
    existing_config = {}
    if csp_config:
        try:
            existing_config = json.loads(csp_config)
        except json.JSONDecodeError:
            pass

    # Add frame-ancestors with D365 origin
    existing_config["Frame-Ancestors"] = {
        "sources": [
            {"source": "https://*.dynamics.com"},
            {"source": "https://*.crm4.dynamics.com"},
        ]
    }

    patch_payload = {"PowerApps_CSPConfigCodeApps": json.dumps(existing_config)}

    patch_url = (
        f"{base_url}/environmentmanagement/environments/{ENV_ID}/settings"
        f"?api-version=2022-03-01-preview"
    )

    with httpx.Client(timeout=30.0) as client:
        resp = client.patch(patch_url, headers=headers, json=patch_payload)
        if resp.status_code in (200, 204):
            print(f"PATCH response: {resp.status_code} - SUCCESS!")
            print("\nframe-ancestors now includes:")
            print(
                "  'self' https://*.powerapps.com https://*.dynamics.com https://*.crm4.dynamics.com"
            )
        else:
            print(f"PATCH FAILED ({resp.status_code}): {resp.text}")

    # Verify
    print("\nVerifying updated settings...")
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(settings_url, headers=headers)
        if resp.status_code == 200:
            verify_data = resp.json()
            verify_settings = verify_data.get("objectResult", [verify_data])
            if isinstance(verify_settings, list) and len(verify_settings) > 0:
                verify_settings = verify_settings[0]
            new_config = verify_settings.get("PowerApps_CSPConfigCodeApps")
            print(f"Updated config: {new_config}")
else:
    print("\nRun with --update flag to add *.dynamics.com to frame-ancestors:")
    print(f"  python {sys.argv[0]} --update")
