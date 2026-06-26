#!/usr/bin/env python3
"""Enable prefer_local_intents on the Gemini Voice pipeline.

This ensures sentence triggers (like 'search for ...') are processed
BEFORE the LLM agent, so the web search automation fires correctly.

Run on Pi with sudo while HA is stopped:
  sudo python3 /tmp/fix_prefer_local.py
"""

import json
from pathlib import Path

STORAGE = Path("/home/admin/homeassistant/.storage")

path = STORAGE / "assist_pipeline.pipelines"
data = json.loads(path.read_text())

for item in data["data"]["items"]:
    old = item.get("prefer_local_intents", False)
    print(f"  {item['name']}: prefer_local_intents = {old}")
    if item["name"] == "Gemini Voice" and not old:
        item["prefer_local_intents"] = True
        print(f"    -> Changed to True")

path.write_text(json.dumps(data, indent=2))
print("Saved.")
