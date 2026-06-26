#!/usr/bin/env python3
"""Add a voice web search automation to automations.yaml.

This creates sentence triggers that catch search-related voice commands
and route them to the Google Search Agent, then return the response.

Run on Pi with sudo while HA is stopped:
  sudo python3 /tmp/add_search_automation.py
"""

import yaml
from pathlib import Path

CONFIG = Path("/home/admin/homeassistant")

SEARCH_AUTOMATION = {
    "id": "voice_web_search",
    "alias": "Voice Web Search",
    "description": (
        "When user asks a question requiring web search, route it to the "
        "Google Search Agent and return the answer as a conversation response."
    ),
    "triggers": [
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
    ],
    "actions": [
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
    ],
    "mode": "single",
}


def main():
    path = CONFIG / "automations.yaml"
    content = path.read_text()

    # Check if already exists
    if "voice_web_search" in content:
        print("voice_web_search automation already exists, skipping")
        return

    # Load existing automations
    automations = yaml.safe_load(content) or []

    # Add the search automation
    automations.append(SEARCH_AUTOMATION)

    # Write back
    path.write_text(yaml.dump(automations, default_flow_style=False, allow_unicode=True, sort_keys=False))
    print("Added voice_web_search automation")
    print("Sentence triggers: 'search for ...', 'look up ...', 'google ...', etc.")


if __name__ == "__main__":
    main()
