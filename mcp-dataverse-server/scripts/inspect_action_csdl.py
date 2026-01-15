from __future__ import annotations

import re
import sys

import httpx

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: inspect_action_csdl.py <ActionName>")
        raise SystemExit(2)

    action_name = sys.argv[1]

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

    pattern = re.compile(rf"<Action\s+Name=\"{re.escape(action_name)}\"[\s\S]*?</Action>")
    m = pattern.search(xml)
    if not m:
        raise RuntimeError(f"Action not found: {action_name}")

    print(m.group(0))


if __name__ == "__main__":
    main()
