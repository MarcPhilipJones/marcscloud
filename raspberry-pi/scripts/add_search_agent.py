#!/usr/bin/env python3
"""Add a second Google Generative AI config entry with Google Search enabled.

This creates a conversation agent that can use Google Search grounding
but has NO Home Assistant control (required API limitation).

Run on Pi with sudo while HA is stopped:
  sudo python3 /tmp/add_search_agent.py
"""

import json
from pathlib import Path
from datetime import datetime, timezone

STORAGE = Path("/home/admin/homeassistant/.storage")


def main():
    path = STORAGE / "core.config_entries"
    data = json.loads(path.read_text())

    # Check if search agent already exists
    for entry in data["data"]["entries"]:
        if entry["domain"] == "google_generative_ai_conversation" and entry["title"] == "Google Search Agent":
            print("Google Search Agent already exists, skipping")
            return

    # Get the API key from existing Gemini entry
    api_key = None
    for entry in data["data"]["entries"]:
        if entry["domain"] == "google_generative_ai_conversation":
            api_key = entry["data"]["api_key"]
            break

    if not api_key:
        print("ERROR: No existing Gemini entry found to copy API key from")
        return

    now = datetime.now(timezone.utc).isoformat()

    new_entry = {
        "created_at": now,
        "data": {
            "api_key": api_key,
        },
        "disabled_by": None,
        "discovery_keys": {},
        "domain": "google_generative_ai_conversation",
        "entry_id": "01KDJGSEARCH_AGENT_001",
        "minor_version": 4,
        "modified_at": now,
        "options": {},
        "pref_disable_new_entities": False,
        "pref_disable_polling": False,
        "source": "user",
        "subentries": [
            {
                "data": {
                    "llm_hass_api": [],
                    "prompt": (
                        "You are a web search assistant. "
                        "Answer the user's question using information from Google Search. "
                        "Be concise and factual. Include dates when relevant. "
                        "Keep answers short and suitable for spoken responses."
                    ),
                    "recommended": False,
                    "google_search_tool": True,
                },
                "subentry_id": "01KDJGSEARCH_CONV_001",
                "subentry_type": "conversation",
                "title": "Google Search Agent",
                "unique_id": None,
            },
            {
                "data": {
                    "recommended": True,
                },
                "subentry_id": "01KDJGSEARCH_TASK_001",
                "subentry_type": "ai_task_data",
                "title": "Google Search AI Task",
                "unique_id": None,
            },
        ],
        "title": "Google Search Agent",
        "unique_id": None,
        "version": 2,
    }

    data["data"]["entries"].append(new_entry)
    path.write_text(json.dumps(data, indent=2))
    print("Added 'Google Search Agent' config entry")
    print("  - Google Search grounding: enabled")
    print("  - HA control (Assist): disabled (API limitation)")
    print("  - Entity: conversation.google_search_agent")


if __name__ == "__main__":
    main()
