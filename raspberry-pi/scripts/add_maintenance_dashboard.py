"""Configure HA: list dashboards, ensure Maintenance dashboard is in sidebar."""
import asyncio
import json
import os
import re
import sys
from pathlib import Path

import websockets

REPO = Path(__file__).resolve().parents[1]


def _get_token() -> str:
    env = (REPO / ".env").read_text()
    m = re.search(r"^HA_TOKEN=(.+)$", env, re.MULTILINE)
    return m.group(1).strip()


async def main() -> int:
    token = _get_token()
    uri = "ws://192.168.0.111:8123/api/websocket"
    async with websockets.connect(uri) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        await ws.recv()
        mid = 1

        async def call(p):
            nonlocal mid
            p["id"] = mid
            mid += 1
            await ws.send(json.dumps(p))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == p["id"]:
                    return r

        dashes = await call({"type": "lovelace/dashboards/list"})
        print("=== Dashboards ===")
        for d in dashes.get("result", []):
            print(
                f"  url_path={d.get('url_path')!r}  title={d.get('title')!r}  "
                f"mode={d.get('mode')!r}  sidebar={d.get('show_in_sidebar')}  "
                f"id={d.get('id')!r}"
            )

        # Maintenance dashboard is a built-in strategy dashboard. It only
        # appears in the sidebar when added via lovelace/dashboards/create
        # with a `strategy` reference, OR via the default panel selector.
        # Check if it already exists.
        # Built-in (strategy) dashboards like Maintenance live in panels,
        # not the lovelace storage list. Inspect panels.
        cfg = await call({"type": "get_config"})
        # frontend panels are exposed via 'frontend/get_panels' (older) or
        # are surfaced in get_states... use direct frontend API instead.
        panels = await call({"type": "frontend/get_panels"})
        print("\n=== ALL panels (raw) ===")
        for url_path, p in (panels.get("result") or {}).items():
            print(f"  {url_path!r:35} component={p.get('component_name')!r:15} title={p.get('title')!r}")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
