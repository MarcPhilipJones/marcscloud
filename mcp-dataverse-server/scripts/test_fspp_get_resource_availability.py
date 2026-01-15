from __future__ import annotations

import json

import httpx

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings


def call(inbag: dict) -> None:
    s = load_settings()
    tp = TokenProvider(
        tenant_id=s.dataverse_tenant_id,
        client_id=s.dataverse_client_id,
        client_secret=s.dataverse_client_secret,
        resource=s.dataverse_base_url,
    )
    token = tp.get_access_token()

    url = f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/msdyn_fspp_GetResourceAvailability"
    payload = {"InBag": json.dumps(inbag)}

    resp = httpx.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120.0,
    )

    print("status", resp.status_code)
    try:
        data = resp.json()
    except Exception:
        print(resp.text[:4000])
        return

    if resp.status_code >= 400:
        print(json.dumps(data, indent=2)[:4000])
        return

    outbag = data.get("OutBag")
    print("OutBag type", type(outbag), "len", (len(outbag) if isinstance(outbag, str) else None))
    if isinstance(outbag, str):
        print(outbag[:4000])
        # Try parse as JSON
        try:
            obj = json.loads(outbag)
            print("OutBag JSON keys:", list(obj.keys()) if isinstance(obj, dict) else type(obj))
            print(json.dumps(obj, indent=2)[:4000])
        except Exception as e:
            print("OutBag not JSON:", e)


if __name__ == "__main__":
    call({})
