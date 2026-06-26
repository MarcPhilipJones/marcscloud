#!/usr/bin/env python3
"""Fix the Google Search Agent config to use the correct option key.

The correct key is 'enable_google_search_tool', not 'google_search_tool'.
Also ensure llm_hass_api is empty (no HA control) as required.

Run on Pi with sudo while HA is stopped:
  sudo python3 /tmp/fix_search_key.py
"""

import json
from pathlib import Path

STORAGE = Path("/home/admin/homeassistant/.storage")

path = STORAGE / "core.config_entries"
data = json.loads(path.read_text())

for entry in data["data"]["entries"]:
    if entry["title"] == "Google Search Agent":
        for sub in entry.get("subentries", []):
            if sub.get("subentry_type") == "conversation":
                d = sub["data"]
                # Remove wrong key
                if "google_search_tool" in d:
                    del d["google_search_tool"]
                    print("Removed incorrect key 'google_search_tool'")
                # Set correct key
                d["enable_google_search_tool"] = True
                # Ensure no HA control
                d["llm_hass_api"] = []
                # Ensure recommended is False so our settings are used
                d["recommended"] = False
                print(f"Set 'enable_google_search_tool': True")
                print(f"Data: {json.dumps(d, indent=2)}")

path.write_text(json.dumps(data, indent=2))
print("Saved.")
