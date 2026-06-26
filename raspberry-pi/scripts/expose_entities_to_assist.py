"""Expose a curated set of entities to the Assist LLM API (used by mcp_server).

Reads HASS_TOKEN from .vscode/mcp.json. Idempotent — safe to re-run.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import websockets

REPO = Path(__file__).resolve().parents[1]
MCP_JSON = REPO / ".vscode" / "mcp.json"
HA_HOST = "192.168.0.111"
HA_PORT = 8123
ASSISTANT = "conversation"  # exposure scope used by mcp_server / Assist API

ENTITIES = [
    # Office
    "light.smart_multicolor_bulb",
    "light.office_in_wall_led",
    "binary_sensor.presence_multi_sensor_fp300_occupancy",
    "sensor.presence_multi_sensor_fp300_illuminance",
    "sensor.presence_multi_sensor_fp300_temperature",
    "sensor.presence_multi_sensor_fp300_humidity",
    "sensor.presence_multi_sensor_fp300_battery",
    "number.presence_multi_sensor_fp300_hold_time",
    "select.presence_multi_sensor_fp300_sensitivity",
    # Other lights
    "light.gateway_lite_led",
    "light.garage_led",
    "light.living_room_wifi_6_led",
    "light.switch_led",
]


def _strip_jsonc(text: str) -> str:
    out = []
    in_str = False
    esc = False
    i = 0
    while i < len(text):
        c = text[i]
        if in_str:
            out.append(c)
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < len(text):
            n = text[i + 1]
            if n == "/":
                while i < len(text) and text[i] != "\n":
                    i += 1
                continue
            if n == "*":
                i += 2
                while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                    i += 1
                i += 2
                continue
        out.append(c)
        i += 1
    return "".join(out)


def get_token() -> str:
    raw = MCP_JSON.read_text(encoding="utf-8")
    cfg = json.loads(_strip_jsonc(raw))
    return cfg["servers"]["homeassistant"]["env"]["HASS_TOKEN"]


async def main() -> int:
    token = get_token()
    uri = f"ws://{HA_HOST}:{HA_PORT}/api/websocket"
    msg_id = 1
    async with websockets.connect(uri) as ws:
        # auth handshake
        hello = json.loads(await ws.recv())
        assert hello["type"] == "auth_required", hello
        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        ok = json.loads(await ws.recv())
        assert ok["type"] == "auth_ok", ok

        async def call(payload: dict) -> dict:
            nonlocal msg_id
            payload["id"] = msg_id
            msg_id += 1
            await ws.send(json.dumps(payload))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get("id") == payload["id"]:
                    return resp

        results = []
        for entity_id in ENTITIES:
            r = await call({
                "type": "homeassistant/expose_entity",
                "assistants": [ASSISTANT],
                "entity_ids": [entity_id],
                "should_expose": True,
            })
            results.append((entity_id, r.get("success", False), r.get("error")))

        # list current exposed for verification
        listing = await call({"type": "homeassistant/expose_entity/list"})

    print("=== Exposure results ===")
    for eid, ok, err in results:
        flag = "OK" if ok else "FAIL"
        extra = f" -- {err}" if err else ""
        print(f"  [{flag}] {eid}{extra}")

    exposed = [
        eid for eid, info in (listing.get("result", {}).get("exposed_entities", {}) or {}).items()
        if info.get(ASSISTANT)
    ]
    print(f"\n=== Total entities exposed to '{ASSISTANT}': {len(exposed)} ===")
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
