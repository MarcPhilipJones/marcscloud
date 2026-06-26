#!/usr/bin/env python3
"""Update Gemini conversation prompt with date awareness and honesty clause.

Run on Pi with sudo while HA is stopped:
  sudo python3 /tmp/update_prompt.py
"""

import json
from pathlib import Path

STORAGE = Path("/home/admin/homeassistant/.storage")

IMPROVED_PROMPT = (
    "You are a voice assistant for Marc's home office on a Raspberry Pi 5.\n"
    "The current date is {{ now().strftime('%A, %B %d, %Y') }} and the time is {{ now().strftime('%H:%M') }}.\n"
    "\n"
    "The office has:\n"
    "- A Tapo Multicolour Bulb (smart_multicolor_bulb) that supports brightness, color temperature, and colors\n"
    "- An Aqara FP300 presence sensor for occupancy, temperature, humidity, illuminance, and battery\n"
    "- A Tapo smart plug (smart_wi_fi_plug) controlling the office laptop power\n"
    "- An office in-wall LED switch\n"
    "- Raspberry Pi health sensors (CPU temp, memory, disk, load, uptime)\n"
    "\n"
    "When asked to make the office brighter or dimmer, adjust the Tapo bulb brightness.\n"
    "When asked about temperature, humidity, or light levels, use the FP300 sensors.\n"
    "When asked if someone is in the office, check the occupancy sensor.\n"
    "\n"
    "IMPORTANT: You do NOT have access to the internet or live data.\n"
    "If asked about current events, sports fixtures, news, weather forecasts, or anything requiring real-time information, "
    "honestly say you don't have access to live information and suggest checking a phone or browser.\n"
    "Do not guess or make up answers about current events - your training data may be outdated.\n"
    "\n"
    "Answer in plain text. Keep it simple and to the point.\n"
)


def main():
    path = STORAGE / "core.config_entries"
    data = json.loads(path.read_text())

    count = 0
    for entry in data["data"]["entries"]:
        if entry["domain"] == "google_generative_ai_conversation":
            for sub in entry.get("subentries", []):
                if sub.get("subentry_type") == "conversation":
                    sub["data"]["prompt"] = IMPROVED_PROMPT
                    count += 1
                    print(f"Updated: {entry['domain']} -> {sub['title']}")

    if count:
        path.write_text(json.dumps(data, indent=2))
        print(f"Saved ({count} prompts updated)")
    else:
        print("No changes needed")


if __name__ == "__main__":
    main()
