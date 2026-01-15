from __future__ import annotations

import base64
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

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # schedule board bundle
    wid = "8eaabd82-fac2-59f9-93fe-112946b29e38"
    url = f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/webresourceset({wid})?$select=name,content"
    resp = httpx.get(url, headers=headers, timeout=120.0)
    resp.raise_for_status()
    data = resp.json()

    raw = base64.b64decode(data["content"])
    text = raw.decode("utf-8", errors="replace")

    names = [
        "ScheduleAssistant_LoadAndGetResources",
        "Ufx_RetrieveConstraints",
        "Ufx_RetrieveResourceAvailability_v2",
        "Ufx_RetrieveResources",
    ]

    for name in names:
        # try a few patterns; bundle is minified
        patterns = [
            rf"{re.escape(name)}=([0-9]+)",
            rf"\[{re.escape(name)}=([0-9]+)\]",
            rf"{re.escape(name)}\s*[:=]\s*([0-9]+)",
        ]
        found = set()
        for pat in patterns:
            for m in re.finditer(pat, text):
                found.add(m.group(1))
        print(name, "->", ", ".join(sorted(found)) if found else "(not found)")


if __name__ == "__main__":
    main()
