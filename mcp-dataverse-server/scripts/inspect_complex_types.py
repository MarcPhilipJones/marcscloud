from __future__ import annotations

import re

import httpx

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings


def extract_complex_type(xml: str, name: str) -> str | None:
    pattern = re.compile(rf"<ComplexType\s+Name=\"{re.escape(name)}\"[\s\S]*?</ComplexType>")
    m = pattern.search(xml)
    return m.group(0) if m else None


def main() -> None:
    s = load_settings()
    tp = TokenProvider(
        tenant_id=s.dataverse_tenant_id,
        client_id=s.dataverse_client_id,
        client_secret=s.dataverse_client_secret,
        resource=s.dataverse_base_url,
    )
    token = tp.get_access_token()

    url = f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/$metadata"
    resp = httpx.get(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/xml"}, timeout=120.0)
    resp.raise_for_status()
    xml = resp.text

    names = [
        "msdyn_SearchResourceAvailabilityResponse",
        "msdyn_RetrieveResourceAvailabilityResponse",
        "msdyn_GetAvailabilitySummaryFromDemandResponse",
        "msdyn_fspp_GetResourceAvailabilityResponse",
        "msdyn_SearchResourceAvailabilityForRequirementGroupResponse",
        "msdyn_FpsActionResponse",
    ]

    for name in names:
        print("\n===", name, "===")
        block = extract_complex_type(xml, name)
        if not block:
            print("(not found)")
            continue
        print(block)


if __name__ == "__main__":
    main()
