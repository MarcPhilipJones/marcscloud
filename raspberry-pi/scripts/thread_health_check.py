"""Thread / Matter-over-Thread health check (read-only).

Three vantage points, no changes made to anything:

  1. Home Assistant WebSocket API  (ws://<pi>:8123)
       - which integrations are loaded (thread / otbr / matter / apple_tv)
       - Thread datasets HA itself stores
  2. python-matter-server on the Pi (ws://<pi>:5580/ws)
       - every Matter node in HA's fabric, online/offline, Thread vs Wi-Fi
  3. LAN mDNS scan
       - `_meshcop._udp`  -> every Thread Border Router (Apple TV, HomePod,
         tado bridge, Amazon Echo, OpenThread/OTBR ...) grouped by network
       - `_matter._tcp`   -> operational Matter nodes advertising on the LAN

Reads HA_TOKEN / PI_HOST from .env.

Usage:  python scripts/thread_health_check.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import websockets
from dotenv import load_dotenv

try:  # make Windows consoles print Unicode TXT records safely
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PI_HOST = os.getenv("PI_HOST", "192.168.0.111")
HA_TOKEN = os.getenv("HA_TOKEN")
HA_WS_URL = f"ws://{PI_HOST}:8123/api/websocket"
MATTER_WS_URL = f"ws://{PI_HOST}:5580/ws"

# Matter ThreadNetworkDiagnostics RoutingRole enum (cluster 0x35 / attr 1)
ROUTING_ROLE = {
    0: "Unspecified",
    1: "Unassigned",
    2: "SleepyEndDevice",
    3: "EndDevice",
    4: "REED",
    5: "Router",
    6: "Leader",
}

_id = 0


def _next() -> int:
    global _id
    _id += 1
    return _id


async def ha_send(ws, payload: dict) -> dict:
    payload["id"] = _next()
    await ws.send(json.dumps(payload))
    while True:
        msg = json.loads(await ws.recv())
        if msg.get("id") == payload["id"] and msg.get("type") == "result":
            return msg


async def query_ha(report: dict) -> None:
    print("=" * 72)
    print("1. HOME ASSISTANT  -  integrations + Thread datasets")
    print("=" * 72)
    if not HA_TOKEN:
        print("  HA_TOKEN missing; skipping HA queries")
        return
    async with websockets.connect(HA_WS_URL, max_size=None) as ws:
        assert json.loads(await ws.recv())["type"] == "auth_required"
        await ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
        if json.loads(await ws.recv())["type"] != "auth_ok":
            print("  auth failed")
            return

        entries = await ha_send(ws, {"type": "config_entries/get"})
        wanted = {"thread", "otbr", "matter", "apple_tv", "homekit_controller"}
        print("  Loaded integrations of interest:")
        for e in entries.get("result", []):
            if e.get("domain") in wanted:
                print(f"    - {e['domain']:<18} title={e.get('title')!r:<28} state={e.get('state')}")

        ds = await ha_send(ws, {"type": "thread/list_datasets"})
        sets = ds.get("result", {}).get("datasets", [])
        report["ha_datasets"] = len(sets)
        print(f"\n  Thread datasets stored by HA: {len(sets)}")
        for d in sets:
            print(
                f"    - network={d.get('network_name')!r} pan_id={d.get('pan_id')} "
                f"preferred={d.get('preferred')} source={d.get('source')}"
            )


async def query_matter(report: dict) -> None:
    print("\n" + "=" * 72)
    print("2. MATTER SERVER (HA fabric)  -  node reachability + radio")
    print("=" * 72)
    try:
        async with websockets.connect(MATTER_WS_URL, max_size=None) as ws:
            info = json.loads(await ws.recv())
            print(
                f"  thread_credentials_set={info.get('thread_credentials_set')}  "
                f"wifi_credentials_set={info.get('wifi_credentials_set')}  "
                f"sdk={info.get('sdk_version')}"
            )
            await ws.send(json.dumps({"message_id": "nodes", "command": "get_nodes"}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("message_id") == "nodes":
                    break
            nodes = msg.get("result", [])
            online = offline = 0
            for n in nodes:
                nid = n.get("node_id")
                avail = bool(n.get("available"))
                attrs = n.get("attributes", {})
                is_thread = any(k.startswith("0/53/") for k in attrs)
                is_wifi = any(k.startswith("0/54/") for k in attrs)
                net = "Thread" if is_thread else ("Wi-Fi" if is_wifi else "?")
                vendor = (attrs.get("0/40/1") or "").replace("\u00b0", "")
                product = attrs.get("0/40/3")
                role = ROUTING_ROLE.get(attrs.get("0/53/1"), attrs.get("0/53/1"))
                flag = "OK " if avail else "DOWN"
                online += avail
                offline += not avail
                extra = f"  role={role}" if is_thread else ""
                print(f"    [{flag}] node {nid:<2} {net:<6} {vendor} {product}{extra}")
                if not avail:
                    report.setdefault("offline_nodes", []).append(
                        f"node {nid} ({vendor} {product}, {net})"
                    )
            report["matter_online"] = online
            report["matter_offline"] = offline
            print(f"\n  Online: {online}   Offline: {offline}")
    except Exception as exc:  # noqa: BLE001
        print(f"  Could not reach matter-server at {MATTER_WS_URL}: {exc}")


def _txt(props) -> dict:
    out = {}
    for k, v in (props or {}).items():
        key = k.decode(errors="replace") if isinstance(k, bytes) else str(k)
        if isinstance(v, bytes):
            try:
                out[key] = v.decode("ascii")
            except UnicodeDecodeError:
                out[key] = "0x" + v.hex()
        else:
            out[key] = v
    return out


async def scan_mdns(report: dict) -> None:
    print("\n" + "=" * 72)
    print("3. LAN mDNS  -  Thread Border Routers grouped by network")
    print("=" * 72)
    try:
        from zeroconf import ServiceBrowser, Zeroconf
    except ImportError:
        print("  zeroconf not installed (pip install zeroconf) - skipping")
        return

    routers: list[dict] = []
    matter_count = {"n": 0}

    class _Listener:
        def __init__(self, kind):
            self.kind = kind

        def add_service(self, zc, type_, name):
            info = zc.get_service_info(type_, name, timeout=3000)
            if not info:
                return
            addrs = list(info.parsed_addresses())
            if self.kind == "br":
                txt = _txt(info.properties)
                routers.append(
                    {
                        "name": name.split("._meshcop")[0],
                        "addr": next((a for a in addrs if ":" not in a), addrs[0] if addrs else "?"),
                        "vendor": txt.get("vn", "?"),
                        "network": txt.get("nn", "?"),
                        "xpan": txt.get("xp", "?"),
                        "ver": txt.get("tv", "?"),
                    }
                )
            else:
                matter_count["n"] += 1

        def update_service(self, *a):
            pass

        def remove_service(self, *a):
            pass

    zc = Zeroconf()
    ServiceBrowser(zc, "_meshcop._udp.local.", _Listener("br"))
    ServiceBrowser(zc, "_matter._tcp.local.", _Listener("m"))
    await asyncio.sleep(6)
    try:
        zc.close()
    except Exception:  # noqa: BLE001
        pass

    networks: dict[str, list[dict]] = {}
    for r in routers:
        networks.setdefault(r["network"], []).append(r)

    report["thread_networks"] = len(networks)
    report["border_routers"] = len(routers)
    report["operational_matter_services"] = matter_count["n"]

    for net, brs in networks.items():
        print(f"\n  Thread network: {net!r}   (xpan={brs[0]['xpan']})")
        for r in brs:
            print(
                f"    - {r['name']:<22} {r['addr']:<15} vendor={r['vendor']:<10} thread v{r['ver']}"
            )
    print(f"\n  Operational Matter (_matter._tcp) services advertised: {matter_count['n']}")


def verdict(report: dict) -> None:
    print("\n" + "=" * 72)
    print("HEALTH SUMMARY")
    print("=" * 72)
    nets = report.get("thread_networks", 0)
    brs = report.get("border_routers", 0)
    print(f"  Thread networks on LAN : {nets}")
    print(f"  Thread border routers  : {brs}")
    print(
        f"  HA Matter fabric       : {report.get('matter_online', '?')} online / "
        f"{report.get('matter_offline', '?')} offline"
    )
    offline = report.get("offline_nodes", [])
    if offline:
        print("  Offline Matter nodes:")
        for o in offline:
            print(f"    ! {o}")
    if report.get("ha_datasets", 0) == 0:
        print(
            "  NOTE: HA stores 0 Thread datasets of its own - its Thread devices "
            "ride on the\n        Apple border routers using imported credentials "
            "(no HA-owned OTBR)."
        )
    if nets > 1:
        print(
            f"  NOTE: {nets} SEPARATE Thread networks exist. Devices on different "
            "networks cannot\n        route for each other - consolidate where possible."
        )


async def main() -> None:
    report: dict = {}
    await query_ha(report)
    await query_matter(report)
    await scan_mdns(report)
    verdict(report)


if __name__ == "__main__":
    asyncio.run(main())
