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

    # Existing Work Order from your example
    work_order_id = "47d0988f-6cf3-4b7b-a5f1-a62f2717b73e"

    start_utc, end_utc = compute_day_window_utc("today")
    start_iso = start_utc.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    end_iso = end_utc.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    payload = {
        # crmbaseentity
        "WorkOrder": {
            "@odata.type": "Microsoft.Dynamics.CRM.msdyn_workorder",
            "msdyn_workorderid": work_order_id,
        },
        "RealTimeMode": False,
        "Duration": 120,
        "IgnoreDuration": False,
        "IgnoreTravelTime": False,
        "AllowOverlapping": False,
        "Radius": 100,
        "StartTime": start_iso,
        "EndTime": end_iso,
        "Latitude": 52.41882,
        "Longitude": -1.78605,
    }

    try:
        raw = dv.execute_unbound_action("msdyn_RetrieveResourceAvailability", payload)
        print("OK; keys:", sorted(list(raw.keys()))[:60])
        print(json.dumps(raw, indent=2)[:3000])
    except httpx.HTTPStatusError as e:
        print("FAIL", e.response.status_code)
        print(e.response.text[:4000])


if __name__ == "__main__":
    main()
