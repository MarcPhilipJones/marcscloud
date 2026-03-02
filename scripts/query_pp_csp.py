"""Query Power Platform API for Code App CSP settings."""

import json

import httpx

token = open("scripts/pp_token.txt").read().strip()
env_id = "08690526-047d-ed9d-ab35-4528a98c0f4f"

# Query with $select for the Code App CSP fields
url = (
    f"https://api.powerplatform.com/environmentmanagement/environments/{env_id}/settings"
    f"?api-version=2022-03-01-preview"
    f"&$select=PowerApps_CSPReportingEndpoint,PowerApps_CSPEnabledCodeApps,PowerApps_CSPConfigCodeApps"
)

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json",
}

with httpx.Client(timeout=30.0) as client:
    resp = client.get(url, headers=headers)
    print(f"Status: {resp.status_code}")
    data = resp.json()

    # Pretty print all settings
    result = data.get("objectResult", [{}])
    if isinstance(result, list) and len(result) > 0:
        settings = result[0]
    else:
        settings = result

    # Filter for CSP-related settings
    print("\n=== ALL CSP-RELATED SETTINGS ===")
    csp_keys = [
        k
        for k in settings.keys()
        if "csp" in k.lower()
        or "contentsecurity" in k.lower()
        or "security" in k.lower()
    ]

    if csp_keys:
        for k in sorted(csp_keys):
            v = settings[k]
            print(f"  {k}: {v}")
            if v and isinstance(v, str):
                try:
                    parsed = json.loads(v)
                    print(f"    -> {json.dumps(parsed, indent=6)}")
                except json.JSONDecodeError:
                    pass
    else:
        print("  No CSP-specific keys found")

    # Also show all keys for reference
    print(f"\n=== ALL SETTING KEYS ({len(settings)} total) ===")
    for k in sorted(settings.keys()):
        v = settings[k]
        # Truncate long values
        v_str = str(v)
        if len(v_str) > 100:
            v_str = v_str[:100] + "..."
        print(f"  {k}: {v_str}")
