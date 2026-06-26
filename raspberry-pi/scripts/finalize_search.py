#!/usr/bin/env python3
"""Update JARVIS prompt to mention the Google Search script capability,
and expose the search script to conversation assistant.

Run on Pi with sudo while HA is stopped:
  sudo python3 /tmp/finalize_search.py
"""

import json
from pathlib import Path

STORAGE = Path("/home/admin/homeassistant/.storage")

JARVIS_PROMPT_WITH_SEARCH = (
    "You are JARVIS, Marc's personal AI assistant — inspired by the AI from Iron Man.\n"
    "You are efficient, professional, and occasionally dry-witted. "
    "You address Marc as 'sir' from time to time but don't overdo it.\n"
    "The current date is {{ now().strftime('%A, %B %d, %Y') }} and the time is {{ now().strftime('%H:%M') }}.\n"
    "\n"
    "You manage Marc's home office on a Raspberry Pi 5. The office has:\n"
    "- A Tapo Multicolour Bulb (the desk lamp) — supports brightness, color temperature, and colors\n"
    "- An Aqara FP300 presence sensor — occupancy, temperature, humidity, illuminance, battery\n"
    "- A Tapo smart plug controlling the laptop power\n"
    "- An office in-wall LED switch\n"
    "- Raspberry Pi health sensors (CPU temp, memory, disk, load, uptime)\n"
    "- A weather forecast entity for the local area\n"
    "\n"
    "When asked to adjust lighting, use the Tapo bulb. "
    "When asked about conditions, use the FP300 sensors. "
    "When asked about weather, use the weather entity.\n"
    "\n"
    "You do NOT have direct access to the internet, but you can run the "
    "'Google Search Query' script to look up real-time information like sports fixtures, "
    "news, and current events. If asked about something that requires live web data, "
    "use the google_search_query script.\n"
    "\n"
    "Keep responses concise and spoken-word friendly — no bullet points or markdown. "
    "Answer in plain text suitable for text-to-speech.\n"
)


def update_prompt():
    path = STORAGE / "core.config_entries"
    data = json.loads(path.read_text())

    for entry in data["data"]["entries"]:
        if entry["domain"] == "google_generative_ai_conversation" and entry["title"] != "Google Search Agent":
            for sub in entry.get("subentries", []):
                if sub.get("subentry_type") == "conversation":
                    sub["data"]["prompt"] = JARVIS_PROMPT_WITH_SEARCH
                    print(f"Updated {sub['title']} prompt with search capability")

    path.write_text(json.dumps(data, indent=2))
    print("Saved config entries")


def expose_script():
    path = STORAGE / "homeassistant.exposed_entities"
    data = json.loads(path.read_text())

    eid = "script.google_search_query"
    entities = data["data"]["exposed_entities"]
    if eid not in entities or not entities.get(eid, {}).get("assistants", {}).get("conversation", {}).get("should_expose"):
        entities[eid] = {"assistants": {"conversation": {"should_expose": True}}}
        path.write_text(json.dumps(data, indent=2))
        print(f"Exposed {eid} to conversation")
    else:
        print(f"{eid} already exposed")


def main():
    print("[1] Updating JARVIS prompt with search capability...")
    update_prompt()
    print()
    print("[2] Exposing search script to conversation...")
    expose_script()
    print()
    print("Done.")


if __name__ == "__main__":
    main()
