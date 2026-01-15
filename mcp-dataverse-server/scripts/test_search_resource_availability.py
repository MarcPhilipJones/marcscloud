from __future__ import annotations

import json
from datetime import timezone

import httpx

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings
from mcp_dataverse_server.dataverse import DataverseClient, compute_day_window_utc


def main() -> None:
    s = load_settings()
    dv = DataverseClient(
        base_url=s.dataverse_base_url,
        api_version=s.dataverse_api_version,
        token_provider=TokenProvider(
            tenant_id=s.dataverse_tenant_id,
            client_id=s.dataverse_client_id,
            client_secret=s.dataverse_client_secret,
            resource=s.dataverse_base_url,
        ),
    )

    start_utc, end_utc = compute_day_window_utc("today_or_tomorrow")
    start_iso = start_utc.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    end_iso = end_utc.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    # Requirement record linked to work order 01149 (from earlier query)
    req_id = "47e6503a-25f1-f011-8406-0022489e611f"

    # Pick a schedule board setting as Settings context
    sb = dv._get("msdyn_scheduleboardsettings?$select=msdyn_scheduleboardsettingid,msdyn_name&$top=1", include_annotations=True)  # type: ignore[attr-defined]
    sb_items = list(sb.get("value", []))
    if not sb_items:
        raise RuntimeError("No msdyn_scheduleboardsettings found")
    sb_id = sb_items[0]["msdyn_scheduleboardsettingid"]
    print("Using scheduleboardsetting", sb_items[0].get("msdyn_name"), sb_id)

    payload = {
        "Version": "1.0",
        "IsWebApi": True,
        "Requirement": {
            "@odata.type": "Microsoft.Dynamics.CRM.msdyn_resourcerequirement",
            "msdyn_resourcerequirementid": req_id,
            "msdyn_fromdate": start_iso,
            "msdyn_todate": end_iso,
            "msdyn_duration": 120,
        },
        "Settings": {
            "@odata.type": "Microsoft.Dynamics.CRM.msdyn_scheduleboardsetting",
            "msdyn_scheduleboardsettingid": sb_id,
        },
    }

    try:
        raw = dv.execute_unbound_action("msdyn_SearchResourceAvailability", payload)
        print("OK; keys:", sorted(list(raw.keys()))[:40])
        print(json.dumps(raw, indent=2)[:3500])
    except httpx.HTTPStatusError as e:
        print("FAIL", e.response.status_code)
        print(e.response.text[:4000])


if __name__ == "__main__":
    main()
