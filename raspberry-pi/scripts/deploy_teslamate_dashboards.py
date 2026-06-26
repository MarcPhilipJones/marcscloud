"""Deploy two Home Assistant dashboards for TeslaMate:

  1. "Tesla" (url: tesla-live)        — polished NATIVE dashboard (HA entities).
  2. "Tesla Analytics" (tesla-grafana) — embeds the TeslaMate Grafana dashboards.

Idempotent: re-running updates the configs. Reads HA_TOKEN from .env.
Run:  python scripts/deploy_teslamate_dashboards.py
"""
import asyncio
import json
import re
import sys
from pathlib import Path

import websockets

BASE_URL = "192.168.0.111:8123"
GRAFANA = "http://192.168.0.111:3000"


def load_token():
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^HA_TOKEN=(.+)$", line.strip())
        if m:
            return m.group(1)
    return None


def gframe(uid, slug, frm="now-30d"):
    return {
        "type": "iframe",
        "url": f"{GRAFANA}/d/{uid}/{slug}?orgId=1&kiosk&theme=dark&from={frm}&to=now",
        "aspect_ratio": "90%",
    }


# ── Native dashboard ──────────────────────────────────────────────────────────
NATIVE = {
    "title": "Tesla",
    "views": [
        {
            "title": "Overview",
            "path": "overview",
            "icon": "mdi:car-electric",
            "type": "sections",
            "max_columns": 3,
            "sections": [
                {"type": "grid", "cards": [
                    {"type": "heading", "heading": "Status", "icon": "mdi:car-connected"},
                    {"type": "tile", "entity": "sensor.tesla_charging_status_summary", "name": "Charging Status"},
                    {"type": "tile", "entity": "sensor.tesla_state", "name": "Car State"},
                    {"type": "tile", "entity": "binary_sensor.octopus_cheap_rate_active", "name": "Cheap Rate Now", "color": "green"},
                    {"type": "tile", "entity": "binary_sensor.tesla_charging_on_cheap_rate", "name": "Charging on Cheap Rate", "color": "green"},
                    {"type": "tile", "entity": "sensor.octopus_intelligent_go_price", "name": "Current Rate"},
                ]},
                {"type": "grid", "cards": [
                    {"type": "heading", "heading": "Battery & Range", "icon": "mdi:battery-high"},
                    {"type": "gauge", "entity": "sensor.tesla_battery_level", "name": "Battery", "min": 0, "max": 100,
                     "needle": True, "severity": {"green": 60, "yellow": 30, "red": 0}},
                    {"type": "tile", "entity": "sensor.tesla_usable_battery_level", "name": "Usable"},
                    {"type": "tile", "entity": "sensor.tesla_rated_battery_range", "name": "Rated Range"},
                    {"type": "tile", "entity": "sensor.tesla_charge_limit_soc", "name": "Charge Limit"},
                    {"type": "custom:mini-graph-card", "entities": [{"entity": "sensor.tesla_battery_level"}],
                     "name": "Battery (24h)", "hours_to_show": 24, "points_per_hour": 2, "line_color": "#03a9f4", "line_width": 3},
                ]},
                {"type": "grid", "cards": [
                    {"type": "heading", "heading": "Charging", "icon": "mdi:ev-station"},
                    {"type": "tile", "entity": "binary_sensor.tesla_plugged_in", "name": "Plugged In"},
                    {"type": "tile", "entity": "binary_sensor.tesla_charge_port_door_open", "name": "Charge Port"},
                    {"type": "gauge", "entity": "sensor.tesla_charger_power", "name": "Charge Power", "min": 0, "max": 11, "unit": "kW",
                     "severity": {"green": 0, "yellow": 0, "red": 0}},
                    {"type": "tile", "entity": "sensor.tesla_charger_voltage", "name": "Voltage"},
                    {"type": "tile", "entity": "sensor.tesla_charger_actual_current", "name": "Current"},
                    {"type": "tile", "entity": "sensor.tesla_charge_energy_added", "name": "Energy Added"},
                    {"type": "tile", "entity": "sensor.tesla_time_to_full_charge", "name": "Time to Full"},
                    {"type": "tile", "entity": "sensor.tesla_scheduled_charging_start_time", "name": "Scheduled Start"},
                ]},
                {"type": "grid", "cards": [
                    {"type": "heading", "heading": "Climate & Security", "icon": "mdi:shield-car"},
                    {"type": "tile", "entity": "sensor.tesla_inside_temp", "name": "Inside Temp"},
                    {"type": "tile", "entity": "sensor.tesla_outside_temp", "name": "Outside Temp"},
                    {"type": "tile", "entity": "binary_sensor.tesla_is_climate_on", "name": "Climate"},
                    {"type": "tile", "entity": "binary_sensor.tesla_locked", "name": "Locked"},
                    {"type": "tile", "entity": "binary_sensor.tesla_sentry_mode", "name": "Sentry"},
                    {"type": "tile", "entity": "binary_sensor.tesla_windows_open", "name": "Windows"},
                    {"type": "tile", "entity": "binary_sensor.tesla_doors_open", "name": "Doors"},
                ]},
                {"type": "grid", "cards": [
                    {"type": "heading", "heading": "Location", "icon": "mdi:map-marker"},
                    {"type": "map", "entities": ["device_tracker.tesla_location"], "default_zoom": 13,
                     "dark_mode": True, "aspect_ratio": "16:9"},
                    {"type": "tile", "entity": "sensor.tesla_geofence", "name": "Geofence"},
                    {"type": "tile", "entity": "sensor.tesla_odometer", "name": "Odometer"},
                ]},
                {"type": "grid", "cards": [
                    {"type": "heading", "heading": "Vehicle", "icon": "mdi:information-outline"},
                    {"type": "tile", "entity": "sensor.tesla_display_name", "name": "Name"},
                    {"type": "tile", "entity": "sensor.tesla_model", "name": "Model"},
                    {"type": "tile", "entity": "sensor.tesla_version", "name": "Software"},
                    {"type": "tile", "entity": "binary_sensor.tesla_update_available", "name": "Update Available"},
                    {"type": "tile", "entity": "binary_sensor.tesla_healthy", "name": "Logger Healthy"},
                ]},
            ],
        }
    ],
}

# ── Grafana embed dashboard ───────────────────────────────────────────────────
GRAFANA_DASH = {
    "title": "Tesla Analytics",
    "views": [
        {"title": "Overview", "path": "overview", "icon": "mdi:view-dashboard", "panel": True,
         "cards": [gframe("kOuP_Fggz", "overview", "now-7d")]},
        {"title": "Battery Health", "path": "battery", "icon": "mdi:battery-heart-variant", "panel": True,
         "cards": [gframe("jchmRiqUfXgTM", "battery-health", "now-1y")]},
        {"title": "Charging", "path": "charging", "icon": "mdi:ev-station", "panel": True,
         "cards": [gframe("-pkIkhmRz", "charging-stats", "now-90d")]},
        {"title": "Charge Level", "path": "charge-level", "icon": "mdi:battery-charging", "panel": True,
         "cards": [gframe("WopVO_mgz", "charge-level", "now-30d")]},
        {"title": "Drives", "path": "drives", "icon": "mdi:map-marker-path", "panel": True,
         "cards": [gframe("Y8upc6ZRk", "drives", "now-90d")]},
        {"title": "Efficiency", "path": "efficiency", "icon": "mdi:leaf", "panel": True,
         "cards": [gframe("fu4SiQgWz", "efficiency", "now-90d")]},
        {"title": "Statistics", "path": "statistics", "icon": "mdi:chart-box", "panel": True,
         "cards": [gframe("1EZnXszMk", "statistics", "now-1y")]},
        {"title": "Vampire Drain", "path": "vampire", "icon": "mdi:sleep", "panel": True,
         "cards": [gframe("zhHx2Fggk", "vampire-drain", "now-30d")]},
    ],
}

DASHBOARDS = [
    ("tesla-live", "Tesla", "mdi:car-electric", NATIVE),
    ("tesla-grafana", "Tesla Analytics", "mdi:chart-areaspline", GRAFANA_DASH),
]


async def main():
    token = load_token()
    if not token:
        print("ERROR: HA_TOKEN missing from .env")
        return 1
    uri = f"ws://{BASE_URL}/api/websocket"
    mid = 0

    def nid():
        nonlocal mid
        mid += 1
        return mid

    async with websockets.connect(uri, max_size=8_000_000) as ws:
        await ws.recv()  # auth_required
        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        if json.loads(await ws.recv()).get("type") != "auth_ok":
            print("Auth failed")
            return 1

        await ws.send(json.dumps({"id": nid(), "type": "lovelace/dashboards/list"}))
        existing = {d["url_path"] for d in json.loads(await ws.recv()).get("result", []) if d.get("url_path")}

        for url_path, title, icon, config in DASHBOARDS:
            if url_path not in existing:
                await ws.send(json.dumps({
                    "id": nid(), "type": "lovelace/dashboards/create",
                    "url_path": url_path, "title": title, "icon": icon,
                    "mode": "storage", "require_admin": False, "show_in_sidebar": True,
                }))
                r = json.loads(await ws.recv())
                print(f"create {url_path}: {'ok' if r.get('success') else r}")
            else:
                print(f"{url_path} exists — updating config")
            await ws.send(json.dumps({
                "id": nid(), "type": "lovelace/config/save",
                "url_path": url_path, "config": config,
            }))
            r = json.loads(await ws.recv())
            print(f"save {url_path}: {'ok' if r.get('success') else r}")
            print(f"   -> http://{BASE_URL}/{url_path}/0")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
