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

    logical_names = [
        "msdyn_scheduleboardsetting",
        "msdyn_bookingsetupmetadata",
        "msdyn_timeoffset",
        "msdyn_resourcerequirement",
        "bookableresource",
        "bookableresourcebooking",
    ]

    for ln in logical_names:
        url = f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/EntityDefinitions(LogicalName='{ln}')?$select=LogicalName,EntitySetName"
        resp = httpx.get(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}, timeout=60.0)
        try:
            resp.raise_for_status()
            data = resp.json()
            print("\n", ln, "->", data.get("EntitySetName"))
        except httpx.HTTPStatusError:
            print("\n", ln, "FAILED", resp.status_code)
            print(resp.text[:500])


if __name__ == "__main__":
    main()
