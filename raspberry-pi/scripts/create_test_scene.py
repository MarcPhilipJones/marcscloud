"""Create a unique-named test script and force-push it to Alexa.

The script just fires a Pushover notification so we can verify it ran end-to-end.
Safe to re-run: PUT is idempotent on the same script id.
"""
import asyncio
import json
import re
from pathlib import Path

import requests  # type: ignore
import websockets  # type: ignore

ENV_PATH = Path(r"C:\VSCODE_Developement\logicappsdevelopment\logicappsdevelopment\raspberry-pi\.env")
BASE = "http://192.168.0.111:8123"

SCRIPT_ID = "tesla_tesla_tesla"
SCRIPT_ALIAS = "Tesla Tesla Tesla"

SCRIPT_BODY = {
    "alias": SCRIPT_ALIAS,
    "mode": "single",
    "sequence": [
        {
            "action": "notify.pushover",
            "data": {
                "title": "Tesla Tesla Tesla",
                "message": "🟢 Test scene fired from Alexa.",
            },
        }
    ],
}


def token() -> str:
    text = ENV_PATH.read_text()
    m = re.search(r"^HA_TOKEN=(.+)$", text, re.MULTILINE)
    if not m:
        raise RuntimeError("HA_TOKEN missing")
    return m.group(1).strip()


async def main() -> None:
    tok = token()
    h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}

    # 1. Create / overwrite the test script via REST
    url = f"{BASE}/api/config/script/config/{SCRIPT_ID}"
    print(f"PUT {url}")
    r = requests.post(url, headers=h, json=SCRIPT_BODY, timeout=10)
    print(f"  -> {r.status_code} {r.text[:200]}")
    r.raise_for_status()

    # 2. Confirm it landed as an entity
    state = requests.get(f"{BASE}/api/states/script.{SCRIPT_ID}", headers=h, timeout=5)
    print(f"\nstate check: {state.status_code}")
    if state.ok:
        s = state.json()
        print(f"  entity_id: {s['entity_id']}")
        print(f"  friendly_name: {s['attributes'].get('friendly_name')}")

    # 3. Force a push to Alexa via websocket cloud/alexa/sync
    ws_url = "ws://192.168.0.111:8123/api/websocket"
    async with websockets.connect(ws_url, max_size=10_000_000) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": tok}))
        auth = json.loads(await ws.recv())
        assert auth["type"] == "auth_ok"

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

        sync = await call({"type": "cloud/alexa/sync"})
        print(f"\ncloud/alexa/sync: success={sync.get('success')} result={sync.get('result')}")

        ents = await call({"type": "cloud/alexa/entities"})
        target = f"script.{SCRIPT_ID}"
        hit = next((e for e in ents.get("result", []) if e.get("entity_id") == target), None)
        print(f"\n{target} advertised to Alexa: {json.dumps(hit, indent=2) if hit else 'NOT FOUND'}")


if __name__ == "__main__":
    asyncio.run(main())
