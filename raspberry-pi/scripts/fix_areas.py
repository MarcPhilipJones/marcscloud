#!/usr/bin/env python3
"""Create Office area and assign office devices to it.

Run on Pi with sudo while HA is stopped:
  sudo python3 /tmp/fix_areas.py
"""

import json
from pathlib import Path
from datetime import datetime, timezone

STORAGE = Path("/home/admin/homeassistant/.storage")

# Device IDs for office devices
OFFICE_DEVICES = {
    "50e1ba02f72b6c9d9417e2c6b3aa9deb": "Presence Multi-Sensor FP300",
    "72d1fbb311d16713795cecbfc29588ec": "Smart Multicolor Bulb",
    "511a22c45f648e55556df3bbb4a746ad": "Home Assistant Voice NABU",
    "7fb66228dc90f50a0ac0d80a569a717e": "Smart Wi-Fi Plug",
    "674b350f7e755f9e807ca5666a0ee926": "Office In Wall",
}

OFFICE_AREA_ID = "office"


def fix_area_registry():
    path = STORAGE / "core.area_registry"
    data = json.loads(path.read_text())

    area_ids = [a["id"] for a in data["data"]["areas"]]
    if OFFICE_AREA_ID not in area_ids:
        now = datetime.now(timezone.utc).isoformat()
        data["data"]["areas"].append({
            "aliases": [],
            "floor_id": None,
            "humidity_entity_id": "sensor.presence_multi_sensor_fp300_humidity",
            "icon": "mdi:desk",
            "id": OFFICE_AREA_ID,
            "labels": [],
            "name": "Office",
            "picture": None,
            "temperature_entity_id": "sensor.presence_multi_sensor_fp300_temperature",
            "created_at": now,
            "modified_at": now,
        })
        path.write_text(json.dumps(data, indent=2))
        print("  Created 'Office' area with temp/humidity sensors")
    else:
        print("  'Office' area already exists")


def fix_device_registry():
    path = STORAGE / "core.device_registry"
    data = json.loads(path.read_text())

    count = 0
    for device in data["data"]["devices"]:
        if device["id"] in OFFICE_DEVICES:
            old_area = device.get("area_id", "")
            if old_area != OFFICE_AREA_ID:
                device["area_id"] = OFFICE_AREA_ID
                count += 1
                print(f"  {OFFICE_DEVICES[device['id']]}: {old_area or '(none)'} -> office")

    if count:
        path.write_text(json.dumps(data, indent=2))
        print(f"  Saved ({count} devices reassigned)")
    else:
        print("  All devices already in Office")


def main():
    print("[Areas] Creating Office area...")
    fix_area_registry()
    print()
    print("[Devices] Assigning devices to Office...")
    fix_device_registry()
    print()
    print("Done. Start HA to activate.")


if __name__ == "__main__":
    main()
