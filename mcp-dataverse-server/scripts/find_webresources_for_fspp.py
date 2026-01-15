from __future__ import annotations

import base64
import json

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

    # webresourceset is the legacy entity set name in Dataverse Web API
    terms = ["fspp", "fsp", "availability", "schedule", "assistant"]
    items: list[dict] = []
    for term in terms:
        url = (
            f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/webresourceset"
            "?$select=webresourceid,name,webresourcetype"
            f"&$filter=contains(name,'msdyn_') and contains(name,'{term}')"
            "&$top=200"
        )
        resp = httpx.get(url, headers=headers, timeout=120.0)
        print("list term", term, "status", resp.status_code)
        resp.raise_for_status()
        items.extend(resp.json().get("value", []))

    # Dedup by id
    seen = set()
    deduped = []
    for it in items:
        wid = it.get("webresourceid")
        if not wid or wid in seen:
            continue
        seen.add(wid)
        deduped.append(it)
    items = deduped
    print("candidates", len(items))

    hits: list[tuple[str, str]] = []

    for it in items:
        wid = it.get("webresourceid")
        name = it.get("name")
        if not wid or not name:
            continue

        # Only look at JS/CSS/HTML types likely to contain strings
        wtype = it.get("webresourcetype")
        if wtype not in (1, 2, 3, 11):
            continue

        get_url = (
            f"{s.dataverse_base_url}/api/data/{s.dataverse_api_version}/webresourceset({wid})"
            "?$select=name,content"
        )
        r = httpx.get(get_url, headers=headers, timeout=120.0)
        if r.status_code >= 400:
            continue
        data = r.json()
        content_b64 = data.get("content")
        if not isinstance(content_b64, str):
            continue

        try:
            raw = base64.b64decode(content_b64)
        except Exception:
            continue

        # Some webresources are binary; best-effort decode
        text = None
        for enc in ("utf-8", "utf-16", "latin-1"):
            try:
                text = raw.decode(enc)
                break
            except Exception:
                continue
        if text is None:
            continue

        if "msdyn_fspp_GetResourceAvailability" in text or "GetResourceAvailability" in text:
            hits.append((name, wid))
            print("HIT", name)

    print("\nTotal hits:", len(hits))
    for name, wid in hits:
        print(name, wid)


if __name__ == "__main__":
    main()
