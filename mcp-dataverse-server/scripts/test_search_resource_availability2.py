from __future__ import annotations

import json

import httpx

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings


def main() -> None:
    s = load_settings()
    tp = TokenProvider(
        tenant_id=s.dataverse_tenant_id,
        client_id=s.dataverse_client_id,
        client_secret=s.dataverse_client_secret,
        resource=s.dataverse_base_url,
    )
    token = tp.get_access_token()

    # From earlier discovery (WO 01149)
    requirement_id = "47e6503a-25f1-f011-8406-0022489e611f"

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # Get a schedule board setting record to use as Settings
    sb_url = f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/msdyn_scheduleboardsettinges?$select=msdyn_scheduleboardsettingid&$top=1"
    sb = httpx.get(sb_url, headers=headers, timeout=60.0)
    if sb.status_code >= 400:
        print("scheduleboardsetting status", sb.status_code)
        try:
            print(json.dumps(sb.json(), indent=2)[:4000])
        except Exception:
            print(sb.text[:4000])
        sb.raise_for_status()
    sb_json = sb.json()
    if not sb_json.get("value"):
        raise RuntimeError("No schedule board settings found")

    sb_setting_id = sb_json["value"][0]["msdyn_scheduleboardsettingid"]

    payload = {
        "Version": "1.0",
        "IsWebApi": False,
        "Requirement": {
            "@odata.type": "Microsoft.Dynamics.CRM.msdyn_resourcerequirement",
            "msdyn_resourcerequirementid": requirement_id,
        },
        "Settings": {
            "@odata.type": "Microsoft.Dynamics.CRM.msdyn_scheduleboardsetting",
            "msdyn_scheduleboardsettingid": sb_setting_id,
        },
    }

    action_url = (
        f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/msdyn_SearchResourceAvailability"
        "?$expand=TimeSlots,Resources,Related,Exceptions"
    )
    resp = httpx.post(
        action_url,
        headers={
            **headers,
            "Content-Type": "application/json",
            "Prefer": 'odata.include-annotations="*"',
        },
        json=payload,
        timeout=120.0,
    )
    print("status", resp.status_code)

    # Raw preview (helps spot @odata.id / annotations)
    print("raw preview:", resp.text[:1500].replace("\n", " "))

    try:
        data = resp.json()
    except Exception:
        print(resp.text[:2000])
        raise

    if resp.status_code >= 400:
        print(json.dumps(data, indent=2)[:4000])
        return

    print("@odata.context:", data.get("@odata.context"))
    print("keys:", list(data.keys()))
    # Heuristic prints
    for k in ["TimeSlots", "Resources", "Related", "Exceptions", "Response", "Result", "ResourceAvailability", "Availability"]:
        if k in data:
            v = data[k]
            if isinstance(v, list):
                print(k, "list len", len(v))
                if v:
                    print(k, "[0] keys", list(v[0].keys()))
                    # Print a few entries verbatim (but keep it bounded)
                    print(json.dumps(v[:3], indent=2)[:8000])
            else:
                print(k, "type", type(v))
                print(json.dumps(v, indent=2)[:4000])


if __name__ == "__main__":
    main()
