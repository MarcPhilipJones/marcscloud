"""
Update Code App CSP settings to allow embedding in D365 (*.dynamics.com).

Current state:
  PowerApps_CSPEnabledCodeApps: False
  PowerApps_CSPConfigCodeApps: None (using defaults)
  PowerApps_CSPReportingEndpoint: None

Default frame-ancestors: 'self' https://*.powerapps.com

After update:
  frame-ancestors: 'self' https://*.powerapps.com https://*.dynamics.com

API: https://api.powerplatform.com/environmentmanagement/environments/{envId}/settings
Docs: https://learn.microsoft.com/en-us/power-apps/developer/code-apps/how-to/content-security-policy
"""

import json

import httpx

token = open("scripts/pp_token.txt").read().strip()
env_id = "08690526-047d-ed9d-ab35-4528a98c0f4f"

base_url = "https://api.powerplatform.com"
settings_url = (
    f"{base_url}/environmentmanagement/environments/{env_id}/settings"
    f"?api-version=2022-03-01-preview"
)

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# ── Step 1: Show current state ────────────────────────────────────
select_url = (
    settings_url
    + "&$select=PowerApps_CSPReportingEndpoint,PowerApps_CSPEnabledCodeApps,PowerApps_CSPConfigCodeApps"
)

with httpx.Client(timeout=30.0) as client:
    resp = client.get(select_url, headers=headers)
    resp.raise_for_status()
    current = resp.json()["objectResult"][0]

print("=== CURRENT CODE APP CSP SETTINGS ===")
print(f"  Enabled:    {current.get('PowerApps_CSPEnabledCodeApps')}")
print(f"  Config:     {current.get('PowerApps_CSPConfigCodeApps')}")
print(f"  Report URI: {current.get('PowerApps_CSPReportingEndpoint')}")

# ── Step 2: Build the updated config ─────────────────────────────
# Add *.dynamics.com to frame-ancestors
# Custom values are MERGED with defaults, so we only need to add the new origins
config = {
    "Frame-Ancestors": {
        "sources": [
            {"source": "https://*.dynamics.com"},
        ]
    }
}

payload = {
    "PowerApps_CSPConfigCodeApps": json.dumps(config),
    # Enable CSP enforcement so the custom frame-ancestors takes effect
    "PowerApps_CSPEnabledCodeApps": True,
}

print("\n=== UPDATING CSP ===")
print(f"  Payload: {json.dumps(payload, indent=2)}")
print("\n  This will set frame-ancestors to:")
print("    'self' https://*.powerapps.com https://*.dynamics.com")
print("  (custom values are merged with defaults)")

# ── Step 3: PATCH the settings ────────────────────────────────────
with httpx.Client(timeout=30.0) as client:
    resp = client.patch(settings_url, headers=headers, json=payload)
    print(f"\n  PATCH status: {resp.status_code}")
    if resp.status_code not in (200, 204):
        print(f"  Response: {resp.text}")
    else:
        print("  SUCCESS!")

# ── Step 4: Verify ────────────────────────────────────────────────
print("\n=== VERIFYING UPDATED SETTINGS ===")
with httpx.Client(timeout=30.0) as client:
    resp = client.get(select_url, headers=headers)
    resp.raise_for_status()
    updated = resp.json()["objectResult"][0]

print(f"  Enabled:    {updated.get('PowerApps_CSPEnabledCodeApps')}")
print(f"  Config:     {updated.get('PowerApps_CSPConfigCodeApps')}")
print(f"  Report URI: {updated.get('PowerApps_CSPReportingEndpoint')}")

if updated.get("PowerApps_CSPConfigCodeApps"):
    parsed = json.loads(updated["PowerApps_CSPConfigCodeApps"])
    print("\n  Parsed directives:")
    print(f"  {json.dumps(parsed, indent=4)}")

print("\n✅ Done! Code Apps should now allow embedding in D365 (*.dynamics.com)")
print("   The App2 tab on the Contact form should now load the Code App.")
print("   Note: Changes may take a few minutes to propagate.")
