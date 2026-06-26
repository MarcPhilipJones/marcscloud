"""Watch script.prepare_the_tesla.last_triggered. Prints when it changes.

Usage:
    python scripts/watch_prepare_tesla.py            # poll forever
    python scripts/watch_prepare_tesla.py --once     # single snapshot
"""
import argparse
import re
import sys
import time
from pathlib import Path

import requests  # type: ignore

ENV_PATH = Path(r"C:\VSCODE_Developement\logicappsdevelopment\logicappsdevelopment\raspberry-pi\.env")
BASE = "http://192.168.0.111:8123"
ENTITY = "script.prepare_the_tesla"


def token() -> str:
    text = ENV_PATH.read_text()
    m = re.search(r"^HA_TOKEN=(.+)$", text, re.MULTILINE)
    if not m:
        raise RuntimeError("HA_TOKEN missing")
    return m.group(1).strip()


def fetch(headers: dict) -> tuple[str, str]:
    r = requests.get(f"{BASE}/api/states/{ENTITY}", headers=headers, timeout=5)
    r.raise_for_status()
    j = r.json()
    return j.get("state", "?"), j.get("attributes", {}).get("last_triggered", "never")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true")
    p.add_argument("--interval", type=float, default=2.0)
    args = p.parse_args()

    h = {"Authorization": f"Bearer {token()}"}
    state, last = fetch(h)
    print(f"[start] state={state} last_triggered={last}")
    print("Speak: 'Alexa, turn on Prepare Tesla'  (Ctrl+C to stop)")
    if args.once:
        return

    baseline = last
    try:
        while True:
            time.sleep(args.interval)
            state, last = fetch(h)
            ts = time.strftime("%H:%M:%S")
            if last != baseline:
                print(f"[{ts}] >>> FIRED <<<  last_triggered: {baseline} -> {last}")
                baseline = last
            else:
                sys.stdout.write(f"\r[{ts}] state={state} last_triggered={last}    ")
                sys.stdout.flush()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
