#!/usr/bin/env python3
"""Fix the voice web search automation to properly return the search response.

The action sequence should be:
1. Call conversation.process on the search agent
2. Use 'stop' with response_variable to return the result

Run on Pi with sudo while HA is stopped:
  sudo python3 /tmp/fix_search_automation.py
"""

import yaml
from pathlib import Path

CONFIG = Path("/home/admin/homeassistant")

def main():
    path = CONFIG / "automations.yaml"
    content = path.read_text()
    automations = yaml.safe_load(content) or []

    found = False
    for auto in automations:
        if auto.get("id") == "voice_web_search":
            found = True
            # Fix the actions - replace with correct sequence
            auto["actions"] = [
                {
                    "action": "conversation.process",
                    "data": {
                        "agent_id": "conversation.google_search_agent",
                        "text": "{{ trigger.slots.query }}",
                    },
                    "response_variable": "search_result",
                },
                {
                    "stop": "Returning search result",
                    "response_variable": "search_result",
                },
            ]

            # Also make sure trigger sentences are broad enough
            auto["triggers"] = [
                {
                    "trigger": "conversation",
                    "command": [
                        "search for {query}",
                        "search the web for {query}",
                        "look up {query}",
                        "google {query}",
                        "web search {query}",
                        "find out {query}",
                    ],
                }
            ]
            print("Fixed voice_web_search automation actions")
            break

    if not found:
        print("ERROR: voice_web_search automation not found")
        return

    path.write_text(yaml.dump(automations, default_flow_style=False, allow_unicode=True, sort_keys=False))
    print("Saved automations.yaml")


if __name__ == "__main__":
    main()
