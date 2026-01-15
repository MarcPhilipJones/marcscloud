from __future__ import annotations

import datetime as dt
import json

import httpx

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings


def find_booking_setup_metadata(headers: dict[str, str], base_url: str, api_version: str) -> dict:
    # Grab the record that actually has query IDs (entitylogicalname == 'none')
    url = (
        f"{base_url}/api/data/{api_version}/msdyn_bookingsetupmetadatas"
        "?$select=msdyn_bookingsetupmetadataid,msdyn_entitylogicalname,_msdyn_retrieveconstraintsquery_value,_msdyn_retrieveresourcesquery_value"
        "&$filter=msdyn_entitylogicalname eq 'none'"
        "&$top=1"
    )
    resp = httpx.get(url, headers=headers, timeout=60.0)
    resp.raise_for_status()
    items = resp.json().get("value", [])
    if not items:
        raise RuntimeError("No msdyn_bookingsetupmetadata with entitylogicalname == 'none'")
    return items[0]


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

    # Sample WO 01149 + its requirement
    work_order_id = "47d0988f-6cf3-4b7b-a5f1-a62f2717b73e"
    requirement_id = "47e6503a-25f1-f011-8406-0022489e611f"

    bsm = find_booking_setup_metadata(headers, s.dataverse_base_url, s.dataverse_api_version)
    constraints_q = bsm.get("_msdyn_retrieveconstraintsquery_value")
    resources_q = bsm.get("_msdyn_retrieveresourcesquery_value")
    print("constraints_q", constraints_q)
    print("resources_q", resources_q)

    # Step 1: Ufx_RetrieveConstraints (402)
    # Approximate the Schedule Board bag shape (Id + LogicalName + BookingSetupMetadata lookup)
    bsm_id = bsm.get("msdyn_bookingsetupmetadataid")
    input_bag = {
        "Id": work_order_id,
        "LogicalName": "msdyn_workorder",
        "msdyn_BookingSetupMetadataId": {
            "Id": bsm_id,
            "LogicalName": "msdyn_bookingsetupmetadata",
            "EntityLogicalName": bsm.get("msdyn_entitylogicalname"),
        },
    }
    input_param_402 = json.dumps({"QueryId": constraints_q, "Bag": json.dumps(input_bag)})

    fps_url = f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/msdyn_FpsAction"

    resp_402 = httpx.post(
        fps_url,
        headers={**headers, "Content-Type": "application/json"},
        json={"Type": 402, "InputParameter": input_param_402},
        timeout=120.0,
    )

    print("402 status", resp_402.status_code)
    data_402 = resp_402.json()
    if resp_402.status_code >= 400:
        print(json.dumps(data_402, indent=2)[:4000])
        return

    out_402 = data_402.get("OutputParameter")
    print("402 OutputParameter len", len(out_402) if isinstance(out_402, str) else None)
    req_info = json.loads(out_402) if isinstance(out_402, str) else None
    print("req_info type", type(req_info))
    if isinstance(req_info, dict):
        print("req_info top keys", list(req_info.keys())[:50])
        print(json.dumps(req_info, indent=2)[:4000])

    # Pull a few requirement fields that are useful for availability
    req_selects = [
        "msdyn_duration",
        "msdyn_worklocation",
        "timezonecode",
        # Some orgs don't expose these fields on the requirement row
        "msdyn_latitude",
        "msdyn_longitude",
    ]
    req_row = {}
    for i in range(len(req_selects), 0, -1):
        req_url = (
            f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/msdyn_resourcerequirements({requirement_id})"
            f"?$select={','.join(req_selects[:i])}"
        )
        req_resp = httpx.get(req_url, headers=headers, timeout=60.0)
        if req_resp.status_code >= 400:
            # try with fewer columns
            if i == 1:
                print("requirement fetch failed", req_resp.status_code)
                try:
                    print(json.dumps(req_resp.json(), indent=2)[:2000])
                except Exception:
                    print(req_resp.text[:2000])
            continue
        req_row = req_resp.json()
        break
    print("requirement msdyn_duration", req_row.get("msdyn_duration"))
    print("requirement msdyn_worklocation", req_row.get("msdyn_worklocation"))
    print("requirement timezonecode", req_row.get("timezonecode"))

    # Step 2: Ufx_RetrieveResourceAvailability_v2 (403)
    # Build a schedule-board-like requestInfo bag.
    start = dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + dt.timedelta(days=1)

    start_s = start.isoformat().replace("+00:00", "Z")
    end_s = end.isoformat().replace("+00:00", "Z")

    request_info = {
        "ResourceTypes": req_info.get("ResourceTypes") if isinstance(req_info, dict) else None,
        "Duration": int(req_row.get("msdyn_duration") or 120),
        "Requirement": {
            "msdyn_resourcerequirementid": requirement_id,
            "msdyn_fromdate": start_s,
            # EndDate key mapping isn't printed in snippet, but msdyn_todate is the natural pair.
            "msdyn_todate": end_s,
            "msdyn_duration": int(req_row.get("msdyn_duration") or 120),
            "RealTimeMode": True,
            "IgnoreTravelTime": True,
            "IgnoreDuration": False,
            "ForceDateRange": True,
            "Radius": 0,
        },
    }

    # Remove nulls (server-side code can be picky)
    def prune(obj):
        if isinstance(obj, dict):
            return {k: prune(v) for k, v in obj.items() if v is not None}
        if isinstance(obj, list):
            return [prune(v) for v in obj]
        return obj

    request_info = prune(request_info)

    input_param_403 = json.dumps({"RetrieveResourcesQueryId": resources_q, "Bag": json.dumps(request_info)})

    resp_403 = httpx.post(
        fps_url,
        headers={**headers, "Content-Type": "application/json"},
        json={"Type": 403, "InputParameter": input_param_403},
        timeout=180.0,
    )

    print("403 status", resp_403.status_code)
    data_403 = resp_403.json()
    if resp_403.status_code >= 400:
        print(json.dumps(data_403, indent=2)[:4000])
        return

    out_403 = data_403.get("OutputParameter")
    print("403 OutputParameter len", len(out_403) if isinstance(out_403, str) else None)

    if isinstance(out_403, str):
        # OutputParameter is JSON
        try:
            availability = json.loads(out_403)
        except Exception as e:
            print("Failed to parse OutputParameter", e)
            print(out_403[:4000])
            return

        if isinstance(availability, dict):
            print("availability keys", list(availability.keys())[:50])
            # Print a sample of likely result arrays
            for k in ["Results", "results", "Resources", "resources", "TimeSlots", "timeslots", "Slots", "slots", "ResourceAvailability"]:
                if k in availability:
                    v = availability[k]
                    if isinstance(v, list):
                        print(k, "len", len(v))
                        print(json.dumps(v[:2], indent=2)[:6000])
                    else:
                        print(k, type(v), str(v)[:2000])
        else:
            print("availability type", type(availability))
            print(str(availability)[:2000])


if __name__ == "__main__":
    main()
