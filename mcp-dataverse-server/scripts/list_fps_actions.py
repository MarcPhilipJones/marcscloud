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

    blocks = re.findall(r"(<Action\s+Name=\"[^\"]*(?:Fps|fps|Ufx|ufx)[^\"]*\"[\s\S]*?</Action>)", xml)
    out = []
    for block in blocks:
        name = re.search(r"<Action\s+Name=\"([^\"]+)\"", block).group(1)
        ret_m = re.search(r"<ReturnType\s+Type=\"([^\"]+)\"", block)
        ret = ret_m.group(1) if ret_m else "(none)"
        out.append((name, ret))

    out.sort(key=lambda t: t[0].lower())
    for name, ret in out[:300]:
        print(f"{name} -> {ret}")
    print("\ncount", len(out))


if __name__ == "__main__":
    main()
