#!/usr/bin/env python3
"""Apply all voice assistant improvements in one go.

1. Add entity aliases for natural voice commands
2. Update Gemini prompt to Jarvis personality
3. Expose weather entity to conversation
4. Create Google Search grounding script in scripts.yaml

Run on Pi with sudo while HA is stopped:
  sudo python3 /tmp/apply_all_improvements.py
"""

import json
from pathlib import Path
from datetime import datetime, timezone

STORAGE = Path("/home/admin/homeassistant/.storage")
CONFIG = Path("/home/admin/homeassistant")

# ============================================================
# 1. ENTITY ALIASES
# ============================================================

ALIASES = {
    "light.smart_multicolor_bulb": [
        "desk lamp", "office light", "office lamp", "the light", "bulb"
    ],
    "switch.smart_wi_fi_plug": [
        "the plug", "office plug", "laptop power", "office power"
    ],
    "binary_sensor.presence_multi_sensor_fp300_occupancy": [
        "presence sensor", "occupancy sensor", "motion sensor"
    ],
    "sensor.presence_multi_sensor_fp300_temperature": [
        "office temperature", "temperature", "office temp"
    ],
    "sensor.presence_multi_sensor_fp300_humidity": [
        "office humidity", "humidity"
    ],
    "sensor.presence_multi_sensor_fp300_illuminance": [
        "office brightness", "light level", "lux", "illuminance"
    ],
    "sensor.presence_multi_sensor_fp300_battery": [
        "sensor battery"
    ],
    "media_player.home_assistant_voice_nabu_media_player": [
        "voice speaker", "nabu", "office speaker"
    ],
    "light.office_in_wall_led": [
        "wall light", "in wall light", "switch light"
    ],
    "weather.forecast_home": [
        "weather", "weather forecast", "forecast"
    ],
}


def add_aliases():
    path = STORAGE / "core.entity_registry"
    data = json.loads(path.read_text())

    count = 0
    for entity in data["data"]["entities"]:
        eid = entity["entity_id"]
        if eid in ALIASES:
            existing = set(entity.get("aliases", []))
            new_aliases = set(ALIASES[eid])
            merged = sorted(existing | new_aliases)
            if merged != sorted(existing):
                entity["aliases"] = merged
                count += 1
                added = new_aliases - existing
                print(f"  {eid}: +{len(added)} aliases ({', '.join(added)})")

    if count:
        path.write_text(json.dumps(data, indent=2))
        print(f"  Saved ({count} entities updated)")
    else:
        print("  All aliases already set")


# ============================================================
# 2. JARVIS PERSONALITY PROMPT
# ============================================================

JARVIS_PROMPT = (
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
    "IMPORTANT: You do NOT have access to the internet or live data beyond what Home Assistant provides.\n"
    "If asked about current events, sports fixtures, news, or anything requiring real-time web information, "
    "honestly say you don't have access to live web data and suggest Marc checks his phone or browser.\n"
    "Do not guess or fabricate answers about current events — your training data may be outdated.\n"
    "\n"
    "Keep responses concise and spoken-word friendly — no bullet points or markdown. "
    "Answer in plain text suitable for text-to-speech.\n"
)


def update_prompt():
    path = STORAGE / "core.config_entries"
    data = json.loads(path.read_text())

    count = 0
    for entry in data["data"]["entries"]:
        if entry["domain"] == "google_generative_ai_conversation":
            for sub in entry.get("subentries", []):
                if sub.get("subentry_type") == "conversation":
                    sub["data"]["prompt"] = JARVIS_PROMPT
                    count += 1
                    print(f"  Updated {sub['title']} -> JARVIS personality")

    if count:
        path.write_text(json.dumps(data, indent=2))
        print(f"  Saved ({count} prompts)")
    else:
        print("  No changes needed")


# ============================================================
# 3. EXPOSE WEATHER TO CONVERSATION
# ============================================================

EXTRA_EXPOSE = [
    "weather.forecast_home",
]


def expose_weather():
    path = STORAGE / "homeassistant.exposed_entities"
    data = json.loads(path.read_text())

    entities = data["data"]["exposed_entities"]
    count = 0
    for eid in EXTRA_EXPOSE:
        if eid not in entities:
            entities[eid] = {"assistants": {"conversation": {"should_expose": True}}}
            count += 1
            print(f"  Exposed {eid}")
        elif not entities[eid].get("assistants", {}).get("conversation", {}).get("should_expose"):
            entities.setdefault(eid, {}).setdefault("assistants", {})["conversation"] = {"should_expose": True}
            count += 1
            print(f"  Exposed {eid}")
        else:
            print(f"  {eid} already exposed")

    if count:
        path.write_text(json.dumps(data, indent=2))
        print(f"  Saved ({count} new exposures)")


# ============================================================
# 4. ADD GOOGLE SEARCH SCRIPT TO scripts.yaml
# ============================================================

SEARCH_SCRIPT_YAML = """
google_search_query:
  alias: Google Search Query
  description: >-
    Ask a question using Google Search grounding via a second Gemini conversation
    agent. Call this when you need real-time web information.
  fields:
    question:
      description: The question to search for
      required: true
      selector:
        text:
  sequence:
    - action: conversation.process
      data:
        agent_id: conversation.google_search_agent
        text: "{{ question }}"
      response_variable: search_result
    - stop: ""
      response_variable: search_result
  mode: single
"""


def add_search_script():
    path = CONFIG / "scripts.yaml"
    content = path.read_text() if path.exists() else ""

    if "google_search_query" in content:
        print("  Google Search script already exists in scripts.yaml")
        return

    # Append the script
    path.write_text(content.rstrip() + "\n" + SEARCH_SCRIPT_YAML)
    print("  Added google_search_query script to scripts.yaml")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=== Applying all voice assistant improvements ===\n")

    print("[1] Adding entity aliases...")
    add_aliases()
    print()

    print("[2] Setting JARVIS personality prompt...")
    update_prompt()
    print()

    print("[3] Exposing weather to conversation...")
    expose_weather()
    print()

    print("[4] Adding Google Search script...")
    add_search_script()
    print()

    print("All improvements applied. Start HA to activate.")


if __name__ == "__main__":
    main()
