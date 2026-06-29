"""Shared Home Assistant + Pi helper for this repo's scripts.

Centralises the things every ad-hoc script kept re-implementing:
- reading HA_TOKEN from the workspace .env
- calling the HA REST API (states, services, template render)
- reloading config without a restart
- validating HA config BEFORE a reload/restart (check_config)
- running a remote command on the Pi over SSH via stdin (quote-safe)

Usage:
    from _ha import HA, pi_ssh
    ha = HA()
    print(ha.state("sensor.tesla_state"))
    ha.reload_all()
    ok, out = ha.check_config()
"""
from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://192.168.0.111:8123"
PI = "pi5"  # SSH alias (also: admin@192.168.0.111)
_ENV = Path(__file__).resolve().parents[1] / ".env"


def _token() -> str:
    m = re.search(r"^HA_TOKEN=(.+)$", _ENV.read_text(encoding="utf-8"), re.MULTILINE)
    if not m:
        raise RuntimeError("HA_TOKEN missing from .env")
    return m.group(1).strip()


def pi_ssh(remote_cmd: str, stdin_text: str | None = None) -> tuple[int, str]:
    """Run a command on the Pi. Pipe scripts via stdin_text to stay quote-safe.

    Example (run python as root on the Pi):
        pi_ssh("sudo python3 -", stdin_text=my_script)
    """
    p = subprocess.run(
        ["ssh", PI, remote_cmd],
        input=stdin_text,
        capture_output=True,
        text=True,
    )
    return p.returncode, (p.stdout + p.stderr)


class HA:
    def __init__(self, token: str | None = None, base: str = BASE):
        self.base = base
        self.token = token or _token()

    def call(self, method: str, path: str, body=None) -> tuple[int, str]:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read().decode()
        except urllib.error.HTTPError as ex:
            return ex.code, ex.read().decode()

    def state(self, entity_id: str):
        s, b = self.call("GET", f"/api/states/{entity_id}")
        return json.loads(b) if s == 200 else None

    def states(self) -> list:
        s, b = self.call("GET", "/api/states")
        return json.loads(b) if s == 200 else []

    def service(self, domain: str, service: str, data: dict | None = None):
        return self.call("POST", f"/api/services/{domain}/{service}", data or {})

    def render(self, template: str) -> str:
        s, b = self.call("POST", "/api/template", {"template": template})
        return b

    def reload_all(self):
        return self.service("homeassistant", "reload_all")

    def reload(self, what: str):
        """Reload one domain, e.g. 'automation', 'script', 'rest_command'."""
        return self.service(what, "reload")

    def check_config(self) -> tuple[bool, str]:
        """Validate the live HA config in the container. ALWAYS run before reload."""
        rc, out = pi_ssh(
            "docker exec homeassistant python -m homeassistant "
            "--script check_config -c /config"
        )
        ok = rc == 0 and "Failed config" not in out
        return ok, out


if __name__ == "__main__":  # tiny smoke test
    ha = HA()
    v = ha.state("sensor.tesla_state")
    print("tesla_state:", v["state"] if v else "n/a")
