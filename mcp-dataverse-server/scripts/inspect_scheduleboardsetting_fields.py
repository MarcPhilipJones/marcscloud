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

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # get top 1 schedule board setting id
    list_url = f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/msdyn_scheduleboardsettinges?$select=msdyn_scheduleboardsettingid&$top=1"
    lst = httpx.get(list_url, headers=headers, timeout=60.0)
    lst.raise_for_status()
    sid = lst.json()["value"][0]["msdyn_scheduleboardsettingid"]

    url = f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/msdyn_scheduleboardsettinges({sid})"
    resp = httpx.get(url, headers=headers, timeout=60.0)
    resp.raise_for_status()
    data = resp.json()

    keys = sorted([k for k in data.keys() if not k.startswith("@")])
    print("keys count", len(keys))
    print("first 80 keys:")
    print("\n".join(keys[:80]))

    # print likely interesting GUID lookup fields
    likely = [k for k in keys if k.endswith("id") or k.endswith("_value") or "Query" in k or "query" in k or "Metadata" in k or "metadata" in k]
    print("\nlikely interesting:")
    print("\n".join(likely[:200]))

    for field in ["msdyn_settings", "msdyn_filtervalues", "msdyn_bookbasedon"]:
        if field in data:
            val = data[field]
            if isinstance(val, str):
                print(f"\n{field} len {len(val)}")
                print(val[:2000])
            else:
                print(f"\n{field} = {val!r}")


if __name__ == "__main__":
    main()
