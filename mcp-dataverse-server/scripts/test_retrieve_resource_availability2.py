from __future__ import annotations

import datetime as dt
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

    # Sample WO 01149
    work_order_id = "47d0988f-6cf3-4b7b-a5f1-a62f2717b73e"

    # Window: today (UTC) 00:00-23:59
    now = dt.datetime.now(dt.timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + dt.timedelta(days=1)

    payload = {
        "WorkOrder": {
            "@odata.type": "Microsoft.Dynamics.CRM.msdyn_workorder",
            "msdyn_workorderid": work_order_id,
        },
        "RealTimeMode": True,
        "Duration": 120,
        "ForceDateRange": True,
        "IgnoreDuration": False,
        "IgnoreTravelTime": True,
        "AllowOverlapping": False,
        "Radius": 0,
        "StartTime": start.isoformat(),
        "EndTime": end.isoformat(),
    }

    url = f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/msdyn_RetrieveResourceAvailability"
    resp = httpx.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Prefer": 'odata.include-annotations="*"',
        },
        json=payload,
        timeout=120.0,
    )

    print("status", resp.status_code)
    try:
        data = resp.json()
    except Exception:
        print(resp.text[:4000])
        return

    if resp.status_code >= 400:
        print(json.dumps(data, indent=2)[:4000])
        return

    print("keys", list(data.keys()))
    if "ExceptionMessage" in data and data["ExceptionMessage"]:
        print("ExceptionMessage", data["ExceptionMessage"])

    result = data.get("Result")
    if isinstance(result, list):
        print("Result len", len(result))
        if result:
            print("Result[0] keys", list(result[0].keys()))
            print(json.dumps(result[:3], indent=2)[:8000])


if __name__ == "__main__":
    main()
