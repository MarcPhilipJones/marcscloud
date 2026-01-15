from __future__ import annotations

import json

import httpx

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings
from mcp_dataverse_server.dataverse import DataverseClient


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

    work_order_id = "47d0988f-6cf3-4b7b-a5f1-a62f2717b73e"

    paths = [
        f"msdyn_resourcerequirements?$select=msdyn_resourcerequirementid,msdyn_name,msdyn_fromdate,msdyn_todate,msdyn_duration,_msdyn_workorder_value&$filter=_msdyn_workorder_value eq {work_order_id}",
        f"resourcerequirements?$select=resourcerequirementid,name&$top=1",
    ]

    for p in paths:
        print("\n---", p)
        try:
            data = dv._get(p, include_annotations=True)  # type: ignore[attr-defined]
            print("keys", list(data.keys()))
            print("count", len(data.get("value", [])))
            print(json.dumps(data.get("value", [])[:5], indent=2)[:2000])
        except httpx.HTTPStatusError as e:
            print("FAIL", e.response.status_code)
            print(e.response.text[:1000])


if __name__ == "__main__":
    main()
