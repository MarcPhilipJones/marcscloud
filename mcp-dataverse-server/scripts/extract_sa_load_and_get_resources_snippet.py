from __future__ import annotations

import base64

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

    wid = "d571c882-fc5c-e711-8119-00155db92d27"  # msdyn_/fps/ExtensibleScheduleBoard/ESB.js
    url = f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/webresourceset({wid})?$select=name,content"
    resp = httpx.get(url, headers=headers, timeout=120.0)
    resp.raise_for_status()
    raw = base64.b64decode(resp.json()["content"])
    text = raw.decode("utf-8", errors="replace")

    needle = "ScheduleAssistant_LoadAndGetResources"
    idx = text.find(needle)
    if idx == -1:
        print("needle not found")
        return

    start = max(0, idx - 2000)
    end = min(len(text), idx + 2000)
    snippet = text[start:end]
    print(snippet)


if __name__ == "__main__":
    main()
