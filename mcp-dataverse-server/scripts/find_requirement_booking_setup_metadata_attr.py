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

    url = (
        f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/"
        "EntityDefinitions(LogicalName='msdyn_resourcerequirement')/Attributes"
        "?$select=LogicalName,SchemaName,AttributeType"
        "&$filter=contains(LogicalName,'bookingsetup') or contains(SchemaName,'BookingSetup')"
    )

    resp = httpx.get(url, headers=headers, timeout=120.0)
    print("status", resp.status_code)
    if resp.status_code >= 400:
        print(resp.text[:2000])
        return

    items = resp.json().get("value", [])
    print("count", len(items))
    for it in items[:50]:
        print(it.get("LogicalName"), it.get("SchemaName"), it.get("AttributeType"))


if __name__ == "__main__":
    main()
