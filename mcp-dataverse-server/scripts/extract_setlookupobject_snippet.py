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

    wid = "d571c882-fc5c-e711-8119-00155db92d27"  # ESB.js
    url = f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/webresourceset({wid})?$select=content"
    resp = httpx.get(url, headers=headers, timeout=120.0)
    resp.raise_for_status()
    raw = base64.b64decode(resp.json()["content"])
    text = raw.decode("utf-8", errors="replace")

    m = re.search(r"setLookupObject\s*:\s*function\s*\(", text)
    if not m:
        m = re.search(r"setLookupObject\s*=\s*function\s*\(", text)
    if not m:
        print("setLookupObject definition not found")
        return

    idx = m.start()

    start = max(0, idx - 800)
    end = min(len(text), idx + 1200)
    print(text[start:end])


if __name__ == "__main__":
    main()
