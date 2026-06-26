#!/usr/bin/env python3
"""Check and fix the Google Search Agent config to use the correct HA format.

Also check the main Gemini config for comparison.
"""
import json
from pathlib import Path

STORAGE = Path("/home/admin/homeassistant/.storage")

path = STORAGE / "core.config_entries"
data = json.loads(path.read_text())

for entry in data["data"]["entries"]:
    if entry["domain"] == "google_generative_ai_conversation":
        print(f"=== {entry['title']} (entry_id: {entry['entry_id']}) ===")
        for sub in entry.get("subentries", []):
            print(f"  [{sub['subentry_type']}] {sub['title']}")
            print(f"    data: {json.dumps(sub['data'], indent=6)}")
        print()
