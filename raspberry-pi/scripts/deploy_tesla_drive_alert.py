"""One-off: deploy the Tesla drive-started automation via HA REST API and reload.

Reads HA_TOKEN from the workspace .env. Adds/updates the automation by id
(leaves all other automations on the Pi untouched), then reloads manually
configured MQTT entities + automations so the geofence "Away" default and the
new automation take effect. Does NOT touch the car (no wake, no polling).
"""
import json
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

BASE = "http://192.168.0.111:8123"
AUTO_ID = "tesla_drive_started_destination"


def ha_token() -> str:
    env = Path(__file__).resolve().parents[1] / ".env"
    m = re.search(r"^HA_TOKEN=(.+)$", env.read_text(encoding="utf-8"), re.MULTILINE)
    if not m:
        sys.exit("HA_TOKEN missing from .env")
    return m.group(1).strip()


def call(method: str, path: str, token: str, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read().decode()


AUTOMATION = {
    "alias": "Tesla Drive Started - Destination Alert",
    "description": (
        "Fires once per drive (passive TeslaMate MQTT - never wakes/polls the "
        "car). Trigger = sensor.tesla_state -> 'driving' (stable for the whole "
        "trip, immune to the P/R/N/D gear shuffle on the driveway). With a nav "
        "destination set it sends the full ETA/distance/etc card; without one it "
        "says 'new drive started' and reports the origin in words (geofence name, "
        "else reverse-geocoded street via Nominatim)."
    ),
    "triggers": [
        {"trigger": "state", "entity_id": "sensor.tesla_state", "to": "driving"}
    ],
    "conditions": [],
    "actions": [
        # Capture the drive-start clock + GPS BEFORE the up-to-25s destination wait
        # so the "Drive Started" header shows the real departure time and the Start
        # Google Maps link points at where the car actually set off (it has moved by
        # the time the notification fires).
        {
            "variables": {
                "start_clock": "{{ now().strftime('%H:%M') }}",
                "start_lat": "{{ state_attr('device_tracker.tesla_location', 'latitude') }}",
                "start_lon": "{{ state_attr('device_tracker.tesla_location', 'longitude') }}",
            }
        },
        {
            "wait_template": (
                "{{ states('sensor.tesla_active_route_destination') not in "
                "['unknown', 'unavailable', ''] }}"
            ),
            "timeout": {"seconds": 25},
            "continue_on_timeout": True,
        },
        # Resolve the origin in WORDS once, up front, so BOTH branches can put it
        # on the mandatory "From:" header line: geofence name if inside one, else
        # reverse-geocode the start GPS via Nominatim.
        {"variables": {"origin": "{{ states('sensor.tesla_geofence') }}"}},
        {
            "if": [
                {
                    "condition": "template",
                    "value_template": (
                        "{{ origin in ['Away', 'unknown', 'unavailable', ''] }}"
                    ),
                }
            ],
            "then": [
                {
                    "action": "rest_command.reverse_geocode",
                    "continue_on_error": True,
                    "data": {
                        "lat": "{{ state_attr('device_tracker.tesla_location', 'latitude') }}",
                        "lon": "{{ state_attr('device_tracker.tesla_location', 'longitude') }}",
                    },
                    "response_variable": "rev",
                },
                {
                    "variables": {
                        "origin": (
                            "{% set a = rev.content.address if rev is defined "
                            "and rev.content is defined and rev.content is mapping "
                            "else {} %}"
                            "{% set road = a.road or a.pedestrian or a.footway "
                            "or a.neighbourhood %}"
                            "{% set place = a.town or a.village or a.suburb "
                            "or a.city or a.hamlet or a.county %}"
                            "{% set parts = [road, place] | select('string') "
                            "| reject('equalto', '') | list %}"
                            "{{ parts | join(', ') if parts else 'an unknown location' }}"
                        )
                    }
                },
            ],
        },
        {
            "choose": [
                {
                    "conditions": [
                        {
                            "condition": "template",
                            "value_template": (
                                "{{ states('sensor.tesla_active_route_destination') "
                                "not in ['unknown', 'unavailable', ''] }}"
                            ),
                        }
                    ],
                    "sequence": [
                        {
                            # Build the A->B static map first (HA awaits it). The
                            # key is read from a Pi-only file, never in git.
                            "action": "shell_command.build_drive_map",
                            "data": {
                                "start": "{{ start_lat }},{{ start_lon }}",
                                "dest": (
                                    "{{ state_attr('sensor.tesla_active_route_location','latitude') }},"
                                    "{{ state_attr('sensor.tesla_active_route_location','longitude') }}"
                                ),
                            },
                        },
                        {
                            "action": "notify.pushover",
                            "data": {
                                "title": "\U0001F697 Drive started",
                                # html=1 + the map attachment go under the notify
                                # service `data` key (top-level html -> 400).
                                "data": {
                                    "html": 1,
                                    "attachment": "/config/www/drive_maps/last_drive.png",
                                },
                                "message": (
                                    # Mandatory top three lines (always, with emoji).
                                    "\U0001F697 Drive Started: {{ start_clock }}\n"
                                    "\u2B05\uFE0F From: {{ origin }}\n"
                                    # Marc works from home -> Home and Work are the
                                    # same address, so the Tesla "Work" favourite is
                                    # reported as "Home".
                                    "\U0001F4CD Destination: "
                                    "{% set d = states('sensor.tesla_active_route_destination') | trim %}"
                                    "{{ 'Home' if d == 'Work' else d }}\n"
                                    # ...followed by the rest.
                                    "\U0001F552 ETA: {{ (now() + timedelta(minutes="
                                    "states('sensor.tesla_active_route_minutes_to_arrival')|int(0)))"
                                    ".strftime('%H:%M') }} "
                                    "({{ states('sensor.tesla_active_route_minutes_to_arrival')|int(0) }} min)\n"
                                    "\U0001F6E3\uFE0F Distance: {{ ("
                                    "states('sensor.tesla_active_route_distance_to_arrival')|float(0)"
                                    " / 1.60934)|round(0)|int }} miles\n"
                                    "\U0001F50B Battery: {{ states('sensor.tesla_battery_level') }}% "
                                    "({{ (states('sensor.tesla_rated_battery_range')|float(0) / 1.60934)"
                                    "|round(0)|int }} mi) "
                                    "\u2192 {{ states('sensor.tesla_active_route_energy_at_arrival') }}% "
                                    "({% set bl = states('sensor.tesla_battery_level')|float(0) %}"
                                    "{% set rng = states('sensor.tesla_rated_battery_range')|float(0) %}"
                                    "{% set arr = states('sensor.tesla_active_route_energy_at_arrival')|float(0) %}"
                                    "{{ ((rng / bl * arr) / 1.60934)|round(0)|int if bl > 0 else 0 }} mi) "
                                    "on arrival\n"
                                    "\U0001F321\uFE0F Climate: "
                                    "{{ states('sensor.tesla_inside_temp')|float(0)|round(0)|int }}"
                                    "\u00B0C cabin\n"
                                    "\U0001F6A6 Traffic: "
                                    "{% set d = states('sensor.tesla_active_route_traffic_minutes_delay')"
                                    "|float(0) %}"
                                    "{% if d <= 0 %}None{% elif d < 5 %}Light"
                                    "{% elif d < 15 %}Moderate{% else %}Heavy{% endif %}"
                                    "{% if d > 0 %} (+{{ d|round(0)|int }} min){% endif %}"
                                    # Tappable Google Maps links (HTML). On iPhone the
                                    # api=1 maps URL opens the Google Maps app via a
                                    # universal link when it is installed.
                                    "\n\U0001F517 "
                                    "<a href=\"https://www.google.com/maps/search/?api=1&query="
                                    "{{ start_lat }},{{ start_lon }}\">Start</a> | "
                                    "<a href=\"https://www.google.com/maps/search/?api=1&query="
                                    "{{ state_attr('sensor.tesla_active_route_location', 'latitude') }},"
                                    "{{ state_attr('sensor.tesla_active_route_location', 'longitude') }}\">"
                                    "Destination</a>"
                                ),
                            },
                        }
                    ],
                }
            ],
            "default": [
                {
                    # Start-only static map for a no-destination drive (the script
                    # falls back to a single A marker when dest is "None,None").
                    "action": "shell_command.build_drive_map",
                    "data": {
                        "start": "{{ start_lat }},{{ start_lon }}",
                        "dest": "None,None",
                    },
                },
                {
                    "action": "notify.pushover",
                    "data": {
                        "title": "\U0001F697 New drive started",
                        # html=1 + the map attachment go under the notify `data`
                        # key (top-level html is rejected -> 400).
                        "data": {
                            "html": 1,
                            "attachment": "/config/www/drive_maps/last_drive.png",
                        },
                        "message": (
                            # Mandatory top three lines (always, with emoji).
                            "\U0001F697 Drive Started: {{ start_clock }}\n"
                            "\u2B05\uFE0F From: {{ origin }}\n"
                            "\U0001F4CD Destination: Not set\n"
                            # ...followed by the rest.
                            "\U0001F50B Battery: {{ states('sensor.tesla_battery_level') }}% "
                            "({{ (states('sensor.tesla_rated_battery_range')|float(0) / 1.60934)"
                            "|round(0)|int }} mi range)\n"
                            "\U0001F321\uFE0F Climate: "
                            "{{ states('sensor.tesla_inside_temp')|float(0)|round(0)|int }}"
                            "\u00B0C cabin"
                            # Tappable Google Maps link to where the drive started.
                            "\n\U0001F517 "
                            "<a href=\"https://www.google.com/maps/search/?api=1&query="
                            "{{ start_lat }},{{ start_lon }}\">Start</a>"
                        ),
                    },
                },
            ],
        },
    ],
    "mode": "single",
}


def main():
    token = ha_token()
    s, b = call(
        "POST", f"/api/config/automation/config/{AUTO_ID}", token, AUTOMATION
    )
    print("POST automation:", s, b)
    s, b = call("POST", "/api/services/homeassistant/reload_all", token, {})
    print("reload_all:", s)
    # Confirm the automation now exists and is on. NOTE: HA derives the entity_id
    # from the alias slug, not the config id, so it is
    # automation.tesla_drive_started_destination_alert.
    s, b = call(
        "GET", "/api/states/automation.tesla_drive_started_destination_alert", token
    )
    print("automation state:", s, b)
    s, b = call("GET", "/api/states/sensor.tesla_geofence", token)
    print("geofence sensor:", s, b)


if __name__ == "__main__":
    main()
