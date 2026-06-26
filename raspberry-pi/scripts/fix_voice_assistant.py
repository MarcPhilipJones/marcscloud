#!/usr/bin/env python3
"""Apply all voice assistant improvements to Home Assistant storage files.

Fixes:
1. Fix Gemini Voice pipeline: change conversation engine to Google AI
2. Create a full Google AI pipeline (Google STT + Gemini + Google TTS)
3. Expose key entities to the conversation assistant
4. Improve AI prompts for OpenAI and Google agents

Run on the Pi while HA is stopped:
  python3 /tmp/fix_voice_assistant.py
"""

import json
import sys
from pathlib import Path

STORAGE_DIR = Path("/home/admin/homeassistant/.storage")

# ---------- Fix 2: Fix Gemini Voice pipeline ----------

def fix_pipelines():
    path = STORAGE_DIR / "assist_pipeline.pipelines"
    data = json.loads(path.read_text())

    changed = False
    for item in data["data"]["items"]:
        # Fix Gemini Voice: wrong conversation engine
        if item["name"] == "Gemini Voice":
            if item["conversation_engine"] == "conversation.home_assistant":
                item["conversation_engine"] = "conversation.google_ai_conversation"
                item["conversation_language"] = "*"
                item["prefer_local_intents"] = True
                print("  Fixed Gemini Voice pipeline -> Google AI Conversation")
                changed = True

    # ---------- Fix 5: Create full Google AI pipeline ----------
    names = [i["name"] for i in data["data"]["items"]]
    if "Google AI Full" not in names:
        new_pipeline = {
            "conversation_engine": "conversation.google_ai_conversation",
            "conversation_language": "*",
            "id": "01kdjgoogle_full_pipeline01",
            "language": "en",
            "name": "Google AI Full",
            "stt_engine": "stt.google_ai_stt",
            "stt_language": "en",
            "tts_engine": "tts.google_ai_tts",
            "tts_language": "en-GB",
            "tts_voice": None,
            "wake_word_entity": None,
            "wake_word_id": None,
            "prefer_local_intents": True,
        }
        data["data"]["items"].append(new_pipeline)
        print("  Created 'Google AI Full' pipeline (Google STT + Gemini + Google TTS)")
        changed = True

    if changed:
        path.write_text(json.dumps(data, indent=2))
        print("  Pipeline file saved")
    else:
        print("  Pipelines already correct")


# ---------- Fix 3: Expose key entities ----------

ENTITIES_TO_EXPOSE = [
    "light.smart_multicolor_bulb",
    "binary_sensor.presence_multi_sensor_fp300_occupancy",
    "sensor.presence_multi_sensor_fp300_temperature",
    "sensor.presence_multi_sensor_fp300_humidity",
    "sensor.presence_multi_sensor_fp300_illuminance",
    "sensor.presence_multi_sensor_fp300_battery",
    "switch.smart_wi_fi_plug",
    "sensor.pi_cpu_temperature",
    "sensor.pi_memory_used_percent",
    "sensor.pi_disk_used_percent",
    "sensor.pi_cpu_load",
    "sensor.pi_uptime",
    "sensor.office_overnight_low_temperature",
    "media_player.home_assistant_voice_nabu_media_player",
    "light.office_in_wall_led",
]


def fix_exposed_entities():
    path = STORAGE_DIR / "homeassistant.exposed_entities"
    data = json.loads(path.read_text())

    entities = data["data"]["exposed_entities"]
    count = 0

    for entity_id in ENTITIES_TO_EXPOSE:
        if entity_id in entities:
            entry = entities[entity_id]
            if "conversation" not in entry.get("assistants", {}):
                entry.setdefault("assistants", {})["conversation"] = {"should_expose": True}
                count += 1
            elif not entry["assistants"]["conversation"].get("should_expose"):
                entry["assistants"]["conversation"]["should_expose"] = True
                count += 1
        else:
            entities[entity_id] = {
                "assistants": {
                    "conversation": {"should_expose": True}
                }
            }
            count += 1

    if count > 0:
        path.write_text(json.dumps(data, indent=2))
        print(f"  Exposed {count} entities to conversation assistant")
    else:
        print("  All entities already exposed")


# ---------- Fix 4: Improve AI prompts ----------

IMPROVED_PROMPT = (
    "You are a voice assistant for Marc's home office on a Raspberry Pi 5.\n"
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
    "Answer questions about the world truthfully.\n"
    "Answer in plain text. Keep it simple and to the point.\n"
)


def fix_prompts():
    path = STORAGE_DIR / "core.config_entries"
    data = json.loads(path.read_text())

    count = 0
    for entry in data["data"]["entries"]:
        if entry["domain"] in ("openai_conversation", "google_generative_ai_conversation"):
            for sub in entry.get("subentries", []):
                if sub.get("subentry_type") == "conversation":
                    old_prompt = sub["data"].get("prompt", "")
                    if old_prompt != IMPROVED_PROMPT:
                        sub["data"]["prompt"] = IMPROVED_PROMPT
                        count += 1
                        print(f"  Updated prompt for {entry['domain']} -> {sub['title']}")

    if count > 0:
        path.write_text(json.dumps(data, indent=2))
        print(f"  Config entries saved ({count} prompts updated)")
    else:
        print("  Prompts already up to date")


def main():
    print("Applying voice assistant fixes...")
    print()

    print("[Fix 2] Fixing pipelines...")
    fix_pipelines()
    print()

    print("[Fix 3] Exposing entities...")
    fix_exposed_entities()
    print()

    print("[Fix 4] Improving AI prompts...")
    fix_prompts()
    print()

    print("All fixes applied. Start HA to activate changes.")


if __name__ == "__main__":
    main()
