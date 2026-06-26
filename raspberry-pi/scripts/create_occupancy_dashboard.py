"""Create an Occupancy dashboard in Home Assistant via WebSocket API."""
import asyncio
import json
import os

import websockets

BASE_URL = "192.168.0.111:8123"
TOKEN = os.environ.get("HA_TOKEN", "")
DASHBOARD_URL = "office-occupancy"
DASHBOARD_TITLE = "Occupancy"

DASHBOARD_CONFIG = {
    "views": [
        {
            "title": "Occupancy",
            "path": "occupancy",
            "icon": "mdi:account-eye",
            "cards": [
                # ── Current Status ──
                {
                    "type": "heading",
                    "heading": "Current Status",
                    "heading_style": "title",
                },
                {
                    "type": "entities",
                    "title": "FP300 Presence Sensor",
                    "show_header_toggle": False,
                    "entities": [
                        {
                            "entity": "binary_sensor.presence_multi_sensor_fp300_occupancy",
                            "name": "Office Occupancy",
                        },
                        {
                            "entity": "sensor.presence_multi_sensor_fp300_illuminance",
                            "name": "Light Level",
                        },
                        {
                            "entity": "sensor.presence_multi_sensor_fp300_temperature",
                            "name": "Temperature",
                        },
                        {
                            "entity": "sensor.presence_multi_sensor_fp300_humidity",
                            "name": "Humidity",
                        },
                    ],
                },
                # ── Today ──
                {
                    "type": "heading",
                    "heading": "Today",
                    "heading_style": "title",
                },
                {
                    "type": "history-graph",
                    "title": "Occupancy Today",
                    "hours_to_show": 24,
                    "entities": [
                        {
                            "entity": "binary_sensor.presence_multi_sensor_fp300_occupancy",
                            "name": "Occupancy",
                        },
                    ],
                },
                {
                    "type": "history-graph",
                    "title": "Light Level Today",
                    "hours_to_show": 24,
                    "entities": [
                        {
                            "entity": "sensor.presence_multi_sensor_fp300_illuminance",
                            "name": "Illuminance (lux)",
                        },
                    ],
                },
                # ── This Week ──
                {
                    "type": "heading",
                    "heading": "This Week",
                    "heading_style": "title",
                },
                {
                    "type": "history-graph",
                    "title": "Occupancy — Last 7 Days",
                    "hours_to_show": 168,
                    "entities": [
                        {
                            "entity": "binary_sensor.presence_multi_sensor_fp300_occupancy",
                            "name": "Occupancy",
                        },
                    ],
                },
                {
                    "type": "statistics-graph",
                    "title": "Daily Illuminance — This Week",
                    "period": "day",
                    "days_to_show": 7,
                    "stat_types": ["mean", "max", "min"],
                    "entities": [
                        "sensor.presence_multi_sensor_fp300_illuminance",
                    ],
                },
                {
                    "type": "statistics-graph",
                    "title": "Daily Temperature — This Week",
                    "period": "day",
                    "days_to_show": 7,
                    "stat_types": ["mean", "max", "min"],
                    "entities": [
                        "sensor.presence_multi_sensor_fp300_temperature",
                    ],
                },
                # ── This Month ──
                {
                    "type": "heading",
                    "heading": "This Month",
                    "heading_style": "title",
                },
                {
                    "type": "history-graph",
                    "title": "Occupancy — Last 30 Days",
                    "hours_to_show": 720,
                    "entities": [
                        {
                            "entity": "binary_sensor.presence_multi_sensor_fp300_occupancy",
                            "name": "Occupancy",
                        },
                    ],
                },
                {
                    "type": "statistics-graph",
                    "title": "Daily Illuminance — This Month",
                    "period": "day",
                    "days_to_show": 30,
                    "stat_types": ["mean", "max"],
                    "entities": [
                        "sensor.presence_multi_sensor_fp300_illuminance",
                    ],
                },
                {
                    "type": "statistics-graph",
                    "title": "Daily Temperature & Humidity — This Month",
                    "period": "day",
                    "days_to_show": 30,
                    "stat_types": ["mean"],
                    "entities": [
                        "sensor.presence_multi_sensor_fp300_temperature",
                        "sensor.presence_multi_sensor_fp300_humidity",
                    ],
                },
            ],
        }
    ]
}


async def main():
    uri = f"ws://{BASE_URL}/api/websocket"
    msg_id = 0

    def next_id():
        nonlocal msg_id
        msg_id += 1
        return msg_id

    async with websockets.connect(uri) as ws:
        # 1. Receive auth_required
        resp = json.loads(await ws.recv())
        print(f"1. {resp['type']}")

        # 2. Authenticate
        await ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
        resp = json.loads(await ws.recv())
        print(f"2. Auth: {resp['type']}")
        if resp["type"] != "auth_ok":
            print(f"   Auth failed: {resp}")
            return

        # 3. List existing dashboards
        mid = next_id()
        await ws.send(json.dumps({"id": mid, "type": "lovelace/dashboards/list"}))
        resp = json.loads(await ws.recv())
        dashboards = resp.get("result", [])
        existing = [d["url_path"] for d in dashboards if d.get("url_path")]
        print(f"3. Existing dashboards: {existing}")

        # 4. Create dashboard if it doesn't exist
        if DASHBOARD_URL in existing:
            print(f"4. Dashboard '{DASHBOARD_URL}' already exists — will update config")
        else:
            mid = next_id()
            await ws.send(json.dumps({
                "id": mid,
                "type": "lovelace/dashboards/create",
                "url_path": DASHBOARD_URL,
                "title": DASHBOARD_TITLE,
                "icon": "mdi:account-eye",
                "mode": "storage",
                "require_admin": False,
                "show_in_sidebar": True,
            }))
            resp = json.loads(await ws.recv())
            if resp.get("success"):
                print(f"4. Dashboard '{DASHBOARD_URL}' created successfully")
            else:
                print(f"4. Create failed: {resp}")
                return

        # 5. Set dashboard Lovelace config
        mid = next_id()
        await ws.send(json.dumps({
            "id": mid,
            "type": "lovelace/config/save",
            "url_path": DASHBOARD_URL,
            "config": DASHBOARD_CONFIG,
        }))
        resp = json.loads(await ws.recv())
        if resp.get("success"):
            print(f"5. Dashboard config saved successfully!")
            print(f"\n   View at: http://{BASE_URL}/{DASHBOARD_URL}/0")
        else:
            print(f"5. Config save failed: {resp}")


if __name__ == "__main__":
    asyncio.run(main())
