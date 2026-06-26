"""Query Alexa exposure for a specific entity via HA WebSocket API."""
import asyncio
import json
import os
import re
import sys
from pathlib import Path

import websockets  # type: ignore

ENV_PATH = Path(r"C:\VSCODE_Developement\logicappsdevelopment\logicappsdevelopment\raspberry-pi\.env")


def load_token() -> str:
    text = ENV_PATH.read_text()
    m = re.search(r"^HA_TOKEN=(.+)$", text, re.MULTILINE)
    if not m:
        raise RuntimeError("HA_TOKEN missing from .env")
    return m.group(1).strip()


async def main(entity_id: str) -> None:
    token = load_token()
    url = "ws://192.168.0.111:8123/api/websocket"
    async with websockets.connect(url, max_size=10_000_000) as ws:
        hello = json.loads(await ws.recv())
        assert hello["type"] == "auth_required", hello
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

        # Cloud status
        cloud = await call({"type": "cloud/status"})
        print("=== cloud/status ===")
        print(json.dumps(cloud.get("result", cloud), indent=2)[:2000])

        # Exposed entities for assistants
        exposed = await call({"type": "homeassistant/expose_entity/list"})
        print("\n=== homeassistant/expose_entity/list (excerpt) ===")
        if "result" in exposed:
            entities = exposed["result"].get("exposed_entities", {})
            target = entities.get(entity_id)
            print(f"{entity_id} -> {json.dumps(target, indent=2)}")
            # Show all script.* exposures
            print("\n--- All script.* exposures ---")
            for k, v in entities.items():
                if k.startswith("script."):
                    print(f"{k}: {v}")
        else:
            print(json.dumps(exposed, indent=2))

        # Cloud-specific Alexa entities config
        alexa_cfg = await call({"type": "cloud/alexa/entities"})
        print("\n=== cloud/alexa/entities (target) ===")
        if "result" in alexa_cfg:
            for ent in alexa_cfg["result"]:
                if ent.get("entity_id") == entity_id:
                    print(json.dumps(ent, indent=2))
                    break
            else:
                print(f"{entity_id} NOT FOUND in cloud/alexa/entities")
        else:
            print(json.dumps(alexa_cfg, indent=2)[:800])


if __name__ == "__main__":
    entity = sys.argv[1] if len(sys.argv) > 1 else "script.prepare_the_tesla"
    asyncio.run(main(entity))
