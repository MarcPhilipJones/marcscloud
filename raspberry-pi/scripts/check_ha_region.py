"""Check HA region/country + Cloud Alexa region for region-mismatch debug."""
import asyncio
import json
import re
from pathlib import Path

import websockets  # type: ignore

ENV_PATH = Path(r"C:\VSCODE_Developement\logicappsdevelopment\logicappsdevelopment\raspberry-pi\.env")


def load_token() -> str:
    text = ENV_PATH.read_text()
    m = re.search(r"^HA_TOKEN=(.+)$", text, re.MULTILINE)
    if not m:
        raise RuntimeError("HA_TOKEN missing")
    return m.group(1).strip()


async def main() -> None:
    token = load_token()
    url = "ws://192.168.0.111:8123/api/websocket"
    async with websockets.connect(url, max_size=10_000_000) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        auth = json.loads(await ws.recv())
        assert auth["type"] == "auth_ok", auth

        msg_id = 1

        async def call(payload: dict) -> dict:
            nonlocal msg_id
            payload = {"id": msg_id, **payload}
            msg_id += 1
            await ws.send(json.dumps(payload))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get("id") == payload["id"]:
                    return resp

        # 1. HA core config (country, timezone, currency, language)
        cfg = await call({"type": "get_config"})
        r = cfg.get("result", {})
        print("=== Home Assistant core config ===")
        for k in ("country", "language", "currency", "time_zone", "location_name",
                  "latitude", "longitude", "elevation", "unit_system"):
            print(f"  {k}: {r.get(k)}")
        print(f"  version: {r.get('version')}")

        # 2. Cloud status — region-relevant fields
        cs = await call({"type": "cloud/status"})
        cr = cs.get("result", {})
        print("\n=== HA Cloud (Nabu Casa) account ===")
        for k in ("email", "cloud", "alexa_registered", "google_registered",
                  "remote_domain", "active_subscription"):
            print(f"  {k}: {cr.get(k)}")
        prefs = cr.get("prefs", {}) or {}
        print(f"  prefs.alexa_enabled: {prefs.get('alexa_enabled')}")
        print(f"  prefs.alexa_report_state: {prefs.get('alexa_report_state')}")

        # 3. Cloud cert/remote info gives us region hints in the remote URL
        try:
            remote = await call({"type": "cloud/remote/get_certificate_info"})
            print("\n=== Cloud remote certificate ===")
            print(json.dumps(remote.get("result"), indent=2))
        except Exception as e:
            print(f"\nremote info: {e}")

        # 4. Cloudhook URLs — the hostname encodes the region (eu-* vs us-*)
        hooks = prefs.get("cloudhooks", {}) or {}
        print("\n=== Cloudhook hostnames (region hint) ===")
        for hid, h in hooks.items():
            url_h = h.get("cloudhook_url", "")
            print(f"  {url_h}")


if __name__ == "__main__":
    asyncio.run(main())
