#!/usr/bin/env python3
"""Add (or verify) the Home Assistant MQTT integration pointed at the local
Mosquitto broker created for TeslaMate.

- Reads HA_TOKEN (and optional PI_HOST) from the workspace .env.
- Idempotent: if an MQTT config entry already exists, it does nothing.
- HA runs in host-network mode, so the broker is reachable at 127.0.0.1:1883.

Run:  python scripts/setup_mqtt_integration.py
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

BROKER = "127.0.0.1"
PORT = 1883


def load_env():
    env = {}
    p = Path(".env")
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^([A-Z_]+)=(.*)$", line.strip())
            if m:
                env[m.group(1)] = m.group(2)
    return env


def api(base, token, method, path, payload=None):
    url = f"{base}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return resp.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            body = json.loads(body)
        except Exception:
            pass
        return e.code, body


def main():
    env = load_env()
    token = env.get("HA_TOKEN")
    host = env.get("PI_HOST", "192.168.0.111")
    base = f"http://{host}:8123"
    if not token:
        print("ERROR: HA_TOKEN missing from .env")
        return 1

    # 1. Already configured?
    status, entries = api(base, token, "GET", "/api/config/config_entries/entry")
    if status == 200 and isinstance(entries, list):
        mqtt = [e for e in entries if e.get("domain") == "mqtt"]
        if mqtt:
            print(f"MQTT already configured: {mqtt[0].get('title')} (entry_id={mqtt[0].get('entry_id')})")
            return 0
    else:
        print(f"WARN: could not list config entries (status {status}): {entries}")

    # 2. Start the MQTT config flow.
    status, flow = api(
        base, token, "POST", "/api/config/config_entries/flow",
        {"handler": "mqtt", "show_advanced_options": False},
    )
    print(f"flow start -> {status}: {json.dumps(flow)[:300]}")
    if status not in (200, 201) or not isinstance(flow, dict):
        print("ERROR: could not start MQTT config flow")
        return 1
    if flow.get("type") == "create_entry":
        print("MQTT entry created immediately.")
        return 0
    flow_id = flow.get("flow_id")
    step = flow.get("step_id")
    print(f"flow_id={flow_id} step={step}")

    # 3. Submit broker details (anonymous broker -> no username/password).
    status, result = api(
        base, token, "POST", f"/api/config/config_entries/flow/{flow_id}",
        {"broker": BROKER, "port": PORT},
    )
    print(f"submit -> {status}: {json.dumps(result)[:400]}")
    if isinstance(result, dict) and result.get("type") == "create_entry":
        print(f"SUCCESS: MQTT integration created (title={result.get('title')}).")
        return 0
    print("ERROR: MQTT flow did not complete. See output above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
