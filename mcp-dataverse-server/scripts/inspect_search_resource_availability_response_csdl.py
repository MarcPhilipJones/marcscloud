from __future__ import annotations

import re

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

    url = f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/$metadata"
    resp = httpx.get(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/xml"}, timeout=120.0)
    resp.raise_for_status()
    xml = resp.text

    # Extract the complex type definition for msdyn_SearchResourceAvailabilityResponse
    name = "msdyn_SearchResourceAvailabilityResponse"
    pattern = re.compile(rf"<ComplexType\s+Name=\"{re.escape(name)}\"[\s\S]*?</ComplexType>")
    m = pattern.search(xml)
    if not m:
        raise RuntimeError(f"Could not find ComplexType {name}")

    block = m.group(0)
    # Print a trimmed block
    print(block[:8000])


if __name__ == "__main__":
    main()
