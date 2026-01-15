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

    start_utc, end_utc = compute_day_window_utc("today")

    start_iso = start_utc.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    end_iso = end_utc.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    settings = {
        "ConsiderTravelTime": True,
        "ConsiderResourceCalendar": True,
        "ConsiderBookings": True,
        "ReturnBestSlots": True,
        "MaxNumberOfResources": 5,
        "MaxNumberOfTimeSlots": 10,
    }
    requirement = {
        "StartTime": start_iso,
        "EndTime": end_iso,
        "Duration": 120,
        "Latitude": 52.41882,
        "Longitude": -1.78605,
        "WorkLocation": 690970000,
    }

    action_variants = [
        "msdyn_SearchResourceAvailability",
        "Microsoft.Dynamics.CRM.msdyn_SearchResourceAvailability",
        "msdyn_RetrieveResourceAvailability",
        "Microsoft.Dynamics.CRM.msdyn_RetrieveResourceAvailability",
    ]

    for action in action_variants:
        print("\n--- trying", action)
        try:
            payload = {"Requirements": [requirement], "Settings": settings}
            raw = dv.execute_unbound_action(action, payload)
            print("OK; raw keys", sorted(list(raw.keys()))[:50])
            print("raw sample", json.dumps(raw, indent=2)[:1200])
            break
        except httpx.HTTPStatusError as e:
            print("FAIL", e.response.status_code)
            print(e.response.text[:2000])
        except Exception as e:
            print("FAIL", str(e)[:500])


if __name__ == "__main__":
    main()
