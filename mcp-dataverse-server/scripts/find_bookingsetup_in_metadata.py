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
    xml = httpx.get(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/xml"}, timeout=120.0).text

    # Grab entity type block for msdyn_resourcerequirement
    m = re.search(r"<EntityType\s+Name=\"msdyn_resourcerequirement\"[\s\S]*?</EntityType>", xml)
    if not m:
        print("entity type not found")
        return

    block = m.group(0)

    # Find property/nav property names containing BookingSetup/booking
    names = set()
    for pat in [r"<Property\s+Name=\"([^\"]+)\"", r"<NavigationProperty\s+Name=\"([^\"]+)\""]:
        for name in re.findall(pat, block):
            if "booking" in name.lower() and "setup" in name.lower():
                names.add(name)

    print("matches:")
    for n in sorted(names):
        print(n)


if __name__ == "__main__":
    main()
