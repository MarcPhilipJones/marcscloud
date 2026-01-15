from __future__ import annotations

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings

import httpx


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
    resp = httpx.get(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/xml"}, timeout=60.0)
    resp.raise_for_status()
    text = resp.text

    needles = [
        "SearchResourceAvailabilitySettings",
        "msdyn_searchresourceavailability",
        "msdyn_SearchResourceAvailability",
        "ResourceSpecification",
        "MaxNumberOfTimeSlots",
        "MaxNumberOfResources",
        "ConsiderTravelTime",
        "SchedulerSettings",
        "msdyn_schedulersetting",
        "msdyn_ScheduleBoardSetting",
        "scheduleassistant",
    ]

    for n in needles:
        idx = text.find(n)
        print("\n====", n, "found" if idx != -1 else "NOT FOUND")
        if idx != -1:
            start = max(0, idx - 500)
            end = min(len(text), idx + 1500)
            snippet = text[start:end]
            print(snippet.replace("\r", "").replace("\n", "")[:2000])


if __name__ == "__main__":
    main()
