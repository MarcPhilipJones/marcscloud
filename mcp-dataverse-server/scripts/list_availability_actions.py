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

    # Very lightweight CSDL scrape: find Actions with 'Availability' and print Name + return type.
    # Example:
    # <Action Name="msdyn_SearchResourceAvailability"><Parameter .../>...<ReturnType Type="Microsoft.Dynamics.CRM.foo"/></Action>
    action_blocks = re.findall(r"<Action\s+Name=\"([^\"]*Availability[^\"]*)\"[\s\S]*?</Action>", xml)
    # Unfortunately the above only gives the name; do another pass that captures block.
    blocks = re.findall(r"(<Action\s+Name=\"[^\"]*Availability[^\"]*\"[\s\S]*?</Action>)", xml)

    out = []
    for block in blocks:
        name_m = re.search(r"<Action\s+Name=\"([^\"]+)\"", block)
        if not name_m:
            continue
        name = name_m.group(1)
        ret_m = re.search(r"<ReturnType\s+Type=\"([^\"]+)\"", block)
        ret = ret_m.group(1) if ret_m else "(none)"
        out.append((name, ret))

    # Sort for readability
    out.sort(key=lambda t: t[0].lower())

    for name, ret in out:
        print(f"{name} -> {ret}")


if __name__ == "__main__":
    main()
