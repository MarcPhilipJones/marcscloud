#!/usr/bin/env python3
"""Fix the voice web search automation to use set_conversation_response.

The correct pattern for returning a response from a sentence-triggered automation:
1. Call conversation.process on the search agent -> response_variable
2. Use set_conversation_response to pass the speech text back

Run on Pi with sudo while HA is stopped:
  sudo python3 /tmp/fix_search_response.py
"""

import yaml
from pathlib import Path

CONFIG = Path("/home/admin/homeassistant")


def main():
    path = CONFIG / "automations.yaml"
    content = path.read_text()
    automations = yaml.safe_load(content) or []

    for auto in automations:
        if auto.get("id") == "voice_web_search":
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
                    "set_conversation_response": "{{ search_result.response.speech.plain.speech }}",
                },
            ]
            print("Fixed: using set_conversation_response")
            break

    path.write_text(yaml.dump(automations, default_flow_style=False, allow_unicode=True, sort_keys=False))
    print("Saved.")


if __name__ == "__main__":
    main()
