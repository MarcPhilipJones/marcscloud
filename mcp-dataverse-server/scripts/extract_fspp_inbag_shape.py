from __future__ import annotations

import base64
import re

import httpx

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings


def fetch_webresource_text(base_url: str, api_version: str, token: str, webresourceid: str) -> tuple[str, str]:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    get_url = f"{base_url}/api/data/{api_version}/webresourceset({webresourceid})?$select=name,content"
    resp = httpx.get(get_url, headers=headers, timeout=120.0)
    resp.raise_for_status()
    data = resp.json()
    name = data.get("name")
    content_b64 = data.get("content")
    raw = base64.b64decode(content_b64)

    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return name, raw.decode(enc)
        except Exception:
            continue
    return name, raw.decode("latin-1", errors="replace")


def main() -> None:
    s = load_settings()
    tp = TokenProvider(
        tenant_id=s.dataverse_tenant_id,
        client_id=s.dataverse_client_id,
        client_secret=s.dataverse_client_secret,
        resource=s.dataverse_base_url,
    )
    token = tp.get_access_token()

    targets = {
        "msdyn_/fps/ExtensibleScheduleBoard/ESB.js": "d571c882-fc5c-e711-8119-00155db92d27",
        "msdyn_/ScheduleBoard/bundle.js": "8eaabd82-fac2-59f9-93fe-112946b29e38",
    }

    for expected_name, wid in targets.items():
        name, text = fetch_webresource_text(s.dataverse_base_url, s.dataverse_api_version, token, wid)
        print("\n====", name, "====")
        needles = [
            "msdyn_fspp_GetResourceAvailability",
            "fspp_GetResourceAvailability",
            "msdyn_RetrieveResourceAvailability",
            "RetrieveResourceAvailability",
            "msdyn_SearchResourceAvailability",
            "SearchResourceAvailability",
        ]
        for needle in needles:
            found = False
            for m in re.finditer(re.escape(needle), text):
                found = True
                start = max(0, m.start() - 400)
                end = min(len(text), m.end() + 400)
                snippet = text[start:end]
                snippet = snippet.replace("\r", " ").replace("\n", " ")
                print("\nneedle:", needle)
                print("...", snippet, "...")
            if not found:
                continue

        # Also look for InBag / OutBag usage
        for kw in ["InBag", "OutBag", "GetResourceAvailability", "ResourceAvailability"]:
            if kw in text:
                print("contains", kw)

        # Key implementation hooks
        hooks = [
            "getRequestInputParameter",
            "appendRequestParameters",
            "ExecuteJobSync",
            "ExecuteJobAsync",
            "FpsAction",
            "SystemJobType",
            "Ufx_RetrieveConstraints",
            "Ufx_RetrieveResourceAvailability_v2",
            "msdyn_FpsAction",
            "msdyn_fspp_",
            "msdyn_",
        ]
        for hook in hooks:
            if hook not in text:
                continue
            # Print first occurrence context
            idx = text.find(hook)
            if hook in ("getRequestInputParameter", "appendRequestParameters"):
                start = max(0, idx - 200)
                end = min(len(text), idx + 2200)
            else:
                start = max(0, idx - 400)
                end = min(len(text), idx + 400)
            snippet = text[start:end].replace("\r", " ").replace("\n", " ")
            print("\nfirst hook:", hook)
            print("...", snippet, "...")


if __name__ == "__main__":
    main()
