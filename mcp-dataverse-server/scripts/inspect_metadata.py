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

    resp = httpx.get(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/xml"},
        timeout=60.0,
    )
    resp.raise_for_status()

    text = resp.text
    pattern = r'Name="([^"]*(Availability|ResourceAvailability|Schedule|Book|Booking)[^"]*)"'
    names = sorted({m[0] for m in re.findall(pattern, text)})

    print(f"matches: {len(names)}")
    for name in names:
        print(name)

    # Print parameter blocks for likely availability actions.
    targets = [
        "msdyn_SearchResourceAvailability",
        "msdyn_RetrieveResourceAvailability",
        "msdyn_CreateScheduleAssistantSuggestions",
        "msdyn_BookResourceSchedulingSuggestions",
        "msdyn_GetBookableResources",
        "msdyn_GetAvailabilitySummaryFromDemand",
    ]
    for t in targets:
        print("\n==== ACTION", t)
        m = re.search(rf"<Action Name=\"{re.escape(t)}\"[^>]*>(.*?)</Action>", text, flags=re.DOTALL)
        if not m:
            print("(not found)")
            continue
        block = m.group(0)
        # Keep output reasonable.
        print(block[:4000])


if __name__ == "__main__":
    main()
