from __future__ import annotations

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

    list_url = f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/msdyn_bookingsetupmetadatas?$top=1"
    lst = httpx.get(list_url, headers=headers, timeout=60.0)
    print("list status", lst.status_code)
    if lst.status_code >= 400:
        print(lst.text[:2000])
        lst.raise_for_status()
    items = lst.json().get("value", [])
    if not items:
        raise RuntimeError("No bookingsetupmetadata records")

    item = items[0]
    mid = item.get("msdyn_bookingsetupmetadataid")
    print("id", mid)

    url = f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/msdyn_bookingsetupmetadatas({mid})"
    resp = httpx.get(url, headers=headers, timeout=60.0)
    print("get status", resp.status_code)
    resp.raise_for_status()
    data = resp.json()

    keys = sorted([k for k in data.keys() if not k.startswith("@")])
    print("keys count", len(keys))
    print("\n".join(keys))


if __name__ == "__main__":
    main()
