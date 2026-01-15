from __future__ import annotations

import datetime as dt
import json

import httpx

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings


def get_default_scheduleboardsetting_id(headers: dict[str, str], base_url: str, api_version: str) -> str:
    url = f"{base_url}/api/data/{api_version}/msdyn_scheduleboardsettinges?$select=msdyn_scheduleboardsettingid&$top=1"
    resp = httpx.get(url, headers=headers, timeout=60.0)
    resp.raise_for_status()
    return resp.json()["value"][0]["msdyn_scheduleboardsettingid"]


def main() -> None:
    s = load_settings()
    tp = TokenProvider(
        tenant_id=s.dataverse_tenant_id,
        client_id=s.dataverse_client_id,
        client_secret=s.dataverse_client_secret,
        resource=s.dataverse_base_url,
    )
    token = tp.get_access_token()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    requirement_id = "47e6503a-25f1-f011-8406-0022489e611f"
    sbid = get_default_scheduleboardsetting_id(headers, s.dataverse_base_url, s.dataverse_api_version)

    start = dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + dt.timedelta(days=1)

    # Best-guess minimal input bag. Add schedule board setting id explicitly.
    input_obj = {
        "Id": requirement_id,
        "LogicalName": "msdyn_resourcerequirement",
        "ScheduleBoardSettingId": sbid,
        "StartDate": start.isoformat().replace("+00:00", "Z"),
        "EndDate": end.isoformat().replace("+00:00", "Z"),
    }

    fps_url = f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/msdyn_FpsAction"
    resp = httpx.post(
        fps_url,
        headers={**headers, "Content-Type": "application/json"},
        json={"Type": 153, "InputParameter": json.dumps(input_obj)},
        timeout=180.0,
    )

    print("status", resp.status_code)
    data = resp.json()
    if resp.status_code >= 400:
        print(json.dumps(data, indent=2)[:4000])
        return

    outp = data.get("OutputParameter")
    print("OutputParameter len", len(outp) if isinstance(outp, str) else None)

    if isinstance(outp, str):
        try:
            obj = json.loads(outp)
        except Exception as e:
            print("not json", e)
            print(outp[:4000])
            return

        if isinstance(obj, dict):
            print("keys", list(obj.keys())[:50])
            # show a few nested keys if present
            for k in ["Load", "Availability", "LastRequest", "LastResponse", "SABookingSetupMetadataId"]:
                if k in obj:
                    v = obj[k]
                    if isinstance(v, dict):
                        print(k, "dict keys", list(v.keys())[:50])
                    elif isinstance(v, list):
                        print(k, "list len", len(v))
                    else:
                        print(k, type(v), str(v)[:2000])
        else:
            print("type", type(obj))
            print(str(obj)[:2000])


if __name__ == "__main__":
    main()
