"""Force HA Cloud → Alexa sync, then verify entity is still advertised."""
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
        raise RuntimeError("HA_TOKEN missing from .env")
    return m.group(1).strip()


async def main() -> None:
    token = load_token()
    url = "ws://192.168.0.111:8123/api/websocket"
    async with websockets.connect(url, max_size=10_000_000) as ws:
        await ws.recv()  # auth_required
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

        # 1. Cloud status before
        before = await call({"type": "cloud/status"})
        r = before.get("result", {})
        print("BEFORE — cloud:", r.get("cloud"), "alexa_registered:", r.get("alexa_registered"),
              "alexa_enabled:", r.get("prefs", {}).get("alexa_enabled"),
              "alexa_report_state:", r.get("prefs", {}).get("alexa_report_state"))

        # 2. Force a push of the full entity catalogue to Alexa
        print("\nForcing cloud/alexa/sync ...")
        sync = await call({"type": "cloud/alexa/sync"})
        print(json.dumps(sync, indent=2))

        # 3. Re-check that the Tesla script is still in the Alexa-advertised list
        alexa_cfg = await call({"type": "cloud/alexa/entities"})
        target = "script.prepare_the_tesla"
        found = None
        if "result" in alexa_cfg:
            for ent in alexa_cfg["result"]:
                if ent.get("entity_id") == target:
                    found = ent
                    break
        print(f"\n{target} after sync:")
        print(json.dumps(found, indent=2) if found else "NOT FOUND")

        # 4. Show a small sample of other scripts/scenes so we can see catalogue size
        scripts = [e["entity_id"] for e in alexa_cfg.get("result", []) if e.get("entity_id", "").startswith("script.")]
        scenes = [e["entity_id"] for e in alexa_cfg.get("result", []) if e.get("entity_id", "").startswith("scene.")]
        print(f"\nTotal advertised: scripts={len(scripts)} scenes={len(scenes)}")
        print("First 5 scripts:", scripts[:5])


if __name__ == "__main__":
    asyncio.run(main())
