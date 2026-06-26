"""Deploy Pi Health dashboard and fix Energy view in Tesla dashboard via HA WebSocket API."""
import asyncio
import json
import os
import sys

import websockets

BASE_URL = "192.168.0.111:8123"
TOKEN = os.environ.get("HA_TOKEN", "")

# ─── Pi Health + Automation Observability Dashboard ───

PI_HEALTH_URL = "pi-health"
PI_HEALTH_TITLE = "Pi Health"

PI_HEALTH_CONFIG = {
    "views": [
        {
            "title": "Pi Health",
            "path": "pi-health",
            "icon": "mdi:raspberry-pi",
            "type": "sections",
            "max_columns": 4,
            "sections": [
                {
                    "type": "grid",
                    "cards": [
                        {"type": "heading", "heading": "CPU & Memory", "heading_style": "title"},
                        {
                            "type": "tile",
                            "entity": "sensor.pi_cpu_temperature",
                            "name": "CPU Temperature",
                        },
                        {
                            "type": "tile",
                            "entity": "sensor.pi_cpu_load",
                            "name": "CPU Load (1m)",
                        },
                        {
                            "type": "tile",
                            "entity": "sensor.pi_memory_used_percent",
                            "name": "Memory Usage",
                        },
                        {
                            "type": "tile",
                            "entity": "sensor.pi_disk_used_percent",
                            "name": "Disk Usage",
                        },
                        {
                            "type": "tile",
                            "entity": "sensor.pi_uptime",
                            "name": "Uptime",
                        },
                    ],
                },
                {
                    "type": "grid",
                    "cards": [
                        {"type": "heading", "heading": "Trends (24h)", "heading_style": "title"},
                        {
                            "type": "history-graph",
                            "hours_to_show": 24,
                            "entities": [
                                {"entity": "sensor.pi_cpu_temperature", "name": "CPU Temp"},
                            ],
                        },
                        {
                            "type": "history-graph",
                            "hours_to_show": 24,
                            "entities": [
                                {"entity": "sensor.pi_cpu_load", "name": "CPU Load"},
                                {"entity": "sensor.pi_memory_used_percent", "name": "Memory %"},
                            ],
                        },
                    ],
                },
            ],
        },
        {
            "title": "Automation Activity",
            "path": "automation-activity",
            "icon": "mdi:robot",
            "type": "sections",
            "max_columns": 4,
            "sections": [
                {
                    "type": "grid",
                    "cards": [
                        {"type": "heading", "heading": "All Automations (7 days)", "heading_style": "title"},
                    ],
                },
            ],
        },
    ],
}


# ─── Fixed Energy View for Tesla Dashboard ───
# Uses correct entities: sensor.smart_wi_fi_plug_power (W),
# sensor.smart_wi_fi_plug_energy (kWh cumulative),
# and cost sensors for monetary tracking.

ENERGY_VIEW = {
    "type": "sections",
    "max_columns": 4,
    "title": "Energy",
    "path": "energy",
    "icon": "mdi:lightning-bolt",
    "sections": [
        {
            "type": "grid",
            "cards": [
                {"type": "heading", "heading": "Live Power", "heading_style": "title"},
                {
                    "type": "gauge",
                    "entity": "sensor.smart_wi_fi_plug_power",
                    "name": "Office Plug — Live Power",
                    "min": 0,
                    "max": 500,
                    "unit": "W",
                    "severity": {"green": 0, "yellow": 200, "red": 400},
                },
                {
                    "type": "sensor",
                    "entity": "sensor.smart_wi_fi_plug_effective_voltage",
                    "name": "Voltage",
                    "graph": "line",
                    "detail": 2,
                },
                {
                    "type": "sensor",
                    "entity": "sensor.smart_wi_fi_plug_effective_current",
                    "name": "Current",
                    "graph": "line",
                    "detail": 2,
                },
            ],
        },
        {
            "type": "grid",
            "cards": [
                {"type": "heading", "heading": "Energy Usage", "heading_style": "title"},
                {
                    "type": "sensor",
                    "entity": "sensor.smart_wi_fi_plug_energy",
                    "name": "Total Energy",
                    "graph": "line",
                    "detail": 2,
                },
                {
                    "type": "history-graph",
                    "title": "Power Draw (24h)",
                    "hours_to_show": 24,
                    "entities": [
                        {"entity": "sensor.smart_wi_fi_plug_power", "name": "Power (W)"},
                    ],
                },
                {
                    "type": "statistics-graph",
                    "title": "Daily Energy (last 7 days)",
                    "entities": ["sensor.smart_wi_fi_plug_energy"],
                    "period": "day",
                    "days_to_show": 7,
                    "stat_types": ["change"],
                    "chart_type": "bar",
                },
            ],
        },
        {
            "type": "grid",
            "cards": [
                {"type": "heading", "heading": "Cost Tracking", "heading_style": "title"},
                {
                    "type": "entities",
                    "title": "Energy Costs",
                    "entities": [
                        {"entity": "sensor.living_room_plug_cost_rate", "name": "Current Rate"},
                        {"entity": "sensor.living_room_plug_cost_daily", "name": "Today"},
                        {"entity": "sensor.living_room_plug_cost_weekly", "name": "This Week"},
                        {"entity": "sensor.living_room_plug_cost_monthly", "name": "This Month"},
                        {"entity": "sensor.living_room_plug_cost_yearly", "name": "This Year"},
                        {"entity": "sensor.living_room_plug_cost_total", "name": "Total"},
                    ],
                },
            ],
        },
    ],
}


async def main():
    if not TOKEN:
        print("Error: Set HA_TOKEN environment variable")
        sys.exit(1)

    uri = f"ws://{BASE_URL}/api/websocket"
    msg_id = 0

    def next_id():
        nonlocal msg_id
        msg_id += 1
        return msg_id

    async with websockets.connect(uri) as ws:
        # 1. Auth
        resp = json.loads(await ws.recv())
        print(f"1. {resp['type']}")

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

        # 4. Fetch automation list for the logbook
        mid = next_id()
        await ws.send(json.dumps({"id": mid, "type": "get_states"}))
        resp = json.loads(await ws.recv())
        auto_entities = sorted([
            s["entity_id"]
            for s in resp.get("result", [])
            if s["entity_id"].startswith("automation.")
        ])
        print(f"4. Found {len(auto_entities)} automations")

        # Add logbook card with all automations
        auto_cards = [
            {"type": "heading", "heading": "All Automations (7 days)", "heading_style": "title"},
            {
                "type": "logbook",
                "entities": auto_entities,
                "hours_to_show": 168,
            },
        ]
        # Add per-automation logbook cards
        per_auto_cards = [
            {"type": "heading", "heading": "Per Automation (7 days)", "heading_style": "title"},
        ]
        for eid in auto_entities:
            name = eid.replace("automation.", "").replace("_", " ").title()
            per_auto_cards.append({
                "type": "logbook",
                "entities": [eid],
                "hours_to_show": 168,
                "title": name,
            })

        PI_HEALTH_CONFIG["views"][1]["sections"] = [
            {"type": "grid", "cards": auto_cards},
            {"type": "grid", "cards": per_auto_cards},
        ]

        # ═══ Deploy Pi Health Dashboard ═══
        print("\n─── Pi Health Dashboard ───")

        if PI_HEALTH_URL in existing:
            print(f"5. Dashboard '{PI_HEALTH_URL}' already exists — updating config")
        else:
            mid = next_id()
            await ws.send(json.dumps({
                "id": mid,
                "type": "lovelace/dashboards/create",
                "url_path": PI_HEALTH_URL,
                "title": PI_HEALTH_TITLE,
                "icon": "mdi:raspberry-pi",
                "mode": "storage",
                "require_admin": False,
                "show_in_sidebar": True,
            }))
            resp = json.loads(await ws.recv())
            if resp.get("success"):
                print(f"5. Dashboard '{PI_HEALTH_URL}' created")
            else:
                print(f"5. Create failed: {resp}")
                return

        mid = next_id()
        await ws.send(json.dumps({
            "id": mid,
            "type": "lovelace/config/save",
            "url_path": PI_HEALTH_URL,
            "config": PI_HEALTH_CONFIG,
        }))
        resp = json.loads(await ws.recv())
        if resp.get("success"):
            print(f"6. Pi Health config saved!")
            print(f"   → http://{BASE_URL}/{PI_HEALTH_URL}/0")
        else:
            print(f"6. Save failed: {resp}")

        # ═══ Fix Energy View in Tesla Dashboard ═══
        print("\n─── Tesla Dashboard (Energy Fix) ───")

        tesla_url = "dashboard-tesla"
        if tesla_url not in existing:
            print(f"7. Dashboard '{tesla_url}' not found! Skipping.")
        else:
            # Fetch current Tesla dashboard config
            mid = next_id()
            await ws.send(json.dumps({
                "id": mid,
                "type": "lovelace/config",
                "url_path": tesla_url,
            }))
            resp = json.loads(await ws.recv())
            if not resp.get("success"):
                print(f"7. Failed to fetch Tesla dashboard: {resp}")
            else:
                tesla_config = resp["result"]
                views = tesla_config.get("views", [])

                # Find and replace the Energy view
                energy_idx = None
                for i, view in enumerate(views):
                    if view.get("path") == "energy" or view.get("title") == "Energy":
                        energy_idx = i
                        break

                if energy_idx is not None:
                    views[energy_idx] = ENERGY_VIEW
                    print(f"7. Replacing Energy view at index {energy_idx}")
                else:
                    views.append(ENERGY_VIEW)
                    print(f"7. Energy view not found — appending as new view")

                tesla_config["views"] = views

                # Save updated Tesla dashboard
                mid = next_id()
                await ws.send(json.dumps({
                    "id": mid,
                    "type": "lovelace/config/save",
                    "url_path": tesla_url,
                    "config": tesla_config,
                }))
                resp = json.loads(await ws.recv())
                if resp.get("success"):
                    print(f"8. Tesla dashboard updated with fixed Energy view!")
                    print(f"   → http://{BASE_URL}/{tesla_url}/energy")
                else:
                    print(f"8. Save failed: {resp}")

        print("\n✓ Done!")


if __name__ == "__main__":
    asyncio.run(main())
