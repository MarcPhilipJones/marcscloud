#!/usr/bin/env python3
"""Merge office_back_garden into office area and remove the old area.

Run on Pi with sudo while HA is stopped:
  sudo python3 /tmp/merge_areas.py
"""

import json
from pathlib import Path

STORAGE = Path("/home/admin/homeassistant/.storage")
OLD_AREA = "office_back_garden"
NEW_AREA = "office"


def migrate_devices():
    path = STORAGE / "core.device_registry"
    data = json.loads(path.read_text())
    count = 0
    for d in data["data"]["devices"]:
        if d.get("area_id") == OLD_AREA:
            d["area_id"] = NEW_AREA
            count += 1
            print(f"  Device: {d.get('name', d['id'])} -> office")
    if count:
        path.write_text(json.dumps(data, indent=2))
    print(f"  {count} devices moved")


def migrate_entities():
    path = STORAGE / "core.entity_registry"
    data = json.loads(path.read_text())
    count = 0
    for e in data["data"]["entities"]:
        if e.get("area_id") == OLD_AREA:
            e["area_id"] = NEW_AREA
            count += 1
            print(f"  Entity: {e['entity_id']} -> office")
    if count:
        path.write_text(json.dumps(data, indent=2))
    print(f"  {count} entities moved")


def remove_old_area():
    path = STORAGE / "core.area_registry"
    data = json.loads(path.read_text())
    before = len(data["data"]["areas"])
    data["data"]["areas"] = [a for a in data["data"]["areas"] if a["id"] != OLD_AREA]
    after = len(data["data"]["areas"])
    if before != after:
        path.write_text(json.dumps(data, indent=2))
        print(f"  Removed '{OLD_AREA}' area")
    else:
        print(f"  '{OLD_AREA}' area not found")


def main():
    print("[1] Moving devices...")
    migrate_devices()
    print("[2] Moving entities...")
    migrate_entities()
    print("[3] Removing old area...")
    remove_old_area()
    print("Done.")


if __name__ == "__main__":
    main()
