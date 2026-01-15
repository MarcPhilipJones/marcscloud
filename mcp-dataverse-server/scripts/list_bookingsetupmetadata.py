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

    url = (
        f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/msdyn_bookingsetupmetadatas"
        "?$select=msdyn_bookingsetupmetadataid,msdyn_entitylogicalname,_msdyn_retrieveconstraintsquery_value,_msdyn_retrieveresourcesquery_value,msdyn_enablequickbook"
        "&$top=100"
    )

    resp = httpx.get(url, headers=headers, timeout=120.0)
    resp.raise_for_status()
    items = resp.json().get("value", [])

    # Group by entity logical name
    grouped = {}
    for it in items:
        ln = it.get("msdyn_entitylogicalname")
        grouped.setdefault(ln, []).append(it)

    for ln in sorted(grouped.keys()):
        rows = grouped[ln]
        print("\n==", ln, "count", len(rows), "==")
        for r in rows[:5]:
            print(
                r.get("msdyn_bookingsetupmetadataid"),
                "constraints", r.get("_msdyn_retrieveconstraintsquery_value"),
                "resources", r.get("_msdyn_retrieveresourcesquery_value"),
                "quickbook", r.get("msdyn_enablequickbook"),
            )


if __name__ == "__main__":
    main()
