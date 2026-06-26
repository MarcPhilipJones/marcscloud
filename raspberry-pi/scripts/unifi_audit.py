"""UniFi Network — read-only audit helper.

Logs into the local UniFi OS console (UCK G2 Plus) using a View Only local
account and reports basic health, connected clients, and recent admin-login
events (the data needed to investigate "admin accessed UniFi" alerts).

READ-ONLY: performs only GET requests after authenticating. Never changes config.

Credentials are read from the git-ignored .env file:
    UNIFI_HOST, UNIFI_PORT, UNIFI_USERNAME, UNIFI_PASSWORD, UNIFI_SITE, UNIFI_VERIFY_SSL

Usage:
    python scripts/unifi_audit.py            # summary + recent admin logins
    python scripts/unifi_audit.py --events 50
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import urllib3
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

console = Console()

# Load .env from the repo root (parent of this scripts/ dir)
REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")


def _env(name: str, default: str | None = None, required: bool = False) -> str | None:
    val = os.getenv(name, default)
    if required and not val:
        console.print(f"[red]Missing required env var:[/red] {name} (set it in .env)")
        sys.exit(2)
    return val


HOST = _env("UNIFI_HOST", required=True)
PORT = _env("UNIFI_PORT", "443")
USERNAME = _env("UNIFI_USERNAME", required=True)
PASSWORD = _env("UNIFI_PASSWORD", required=True)
SITE = _env("UNIFI_SITE", "default")
VERIFY_SSL = (_env("UNIFI_VERIFY_SSL", "false") or "false").lower() in ("1", "true", "yes")

BASE = f"https://{HOST}:{PORT}"

if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class UniFiClient:
    """Minimal UniFi OS REST client (read-only beyond the login POST)."""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.verify = VERIFY_SSL
        self.is_unifi_os = True  # UCK G2 Plus runs UniFi OS
        self._csrf: str | None = None

    def login(self) -> None:
        url = f"{BASE}/api/auth/login"
        resp = self.session.post(
            url,
            json={"username": USERNAME, "password": PASSWORD, "rememberMe": False},
            timeout=15,
        )
        if resp.status_code == 200:
            self._csrf = resp.headers.get("x-csrf-token") or resp.headers.get("X-CSRF-Token")
            return
        if resp.status_code in (401, 403):
            console.print("[red]Login failed (401/403):[/red] check UNIFI_USERNAME/UNIFI_PASSWORD "
                          "and that the account is a local admin.")
            sys.exit(1)
        resp.raise_for_status()

    def _net_get(self, path: str) -> dict:
        # UniFi OS proxies the Network application under /proxy/network
        url = f"{BASE}/proxy/network{path}"
        headers = {}
        if self._csrf:
            headers["x-csrf-token"] = self._csrf
        resp = self.session.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def _net_post(self, path: str, body: dict) -> dict:
        url = f"{BASE}/proxy/network{path}"
        headers = {}
        if self._csrf:
            headers["x-csrf-token"] = self._csrf
        resp = self.session.post(url, headers=headers, json=body, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def health(self) -> list[dict]:
        return self._net_get(f"/api/s/{SITE}/stat/health").get("data", [])

    def sysinfo(self) -> list[dict]:
        return self._net_get(f"/api/s/{SITE}/stat/sysinfo").get("data", [])

    def clients(self) -> list[dict]:
        return self._net_get(f"/api/s/{SITE}/stat/sta").get("data", [])

    def devices(self) -> list[dict]:
        # Adopted infrastructure: gateway, switches, UAPs, Cloud Key, etc.
        return self._net_get(f"/api/s/{SITE}/stat/device").get("data", [])

    def _try_get(self, path: str) -> list[dict] | None:
        try:
            return self._net_get(path).get("data", [])
        except requests.HTTPError:
            return None

    def _try_post(self, path: str, body: dict) -> list[dict] | None:
        try:
            return self._net_post(path, body).get("data", [])
        except requests.HTTPError:
            return None

    def events(self, limit: int = 30, within_hours: int = 720) -> tuple[list[dict], str]:
        """Fetch recent events/alarms, trying endpoints that vary across Network versions.

        Returns (events, endpoint_used). Admin logins appear as EVT_AD_Login.
        """
        body = {"_limit": limit, "within": within_hours, "_sort": "-time"}
        candidates = [
            ("POST", f"/api/s/{SITE}/stat/event", body),
            ("GET", f"/api/s/{SITE}/stat/event", None),
            ("POST", f"/api/s/{SITE}/stat/alarm", {"_limit": limit, "within": within_hours}),
            ("GET", f"/api/s/{SITE}/list/alarm", None),
            ("GET", f"/api/s/{SITE}/rest/event", None),
        ]
        for method, path, b in candidates:
            data = self._try_get(path) if method == "GET" else self._try_post(path, b or {})
            if data is not None:
                return data, f"{method} {path}"
        return [], "(none worked)"

    def logout(self) -> None:
        try:
            headers = {"x-csrf-token": self._csrf} if self._csrf else {}
            self.session.post(f"{BASE}/api/auth/logout", headers=headers, timeout=10)
        except requests.RequestException:
            pass


def _fmt_ts(ms: float | int | None) -> str:
    if not ms:
        return "-"
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, OSError):
        return str(ms)


def _human_bytes(n: float | int | None) -> str:
    n = float(n or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _client_bytes(c: dict) -> tuple[int, int]:
    """Return (rx_bytes, tx_bytes) handling wired vs wireless field names."""
    if c.get("is_wired"):
        return int(c.get("wired-rx_bytes", 0) or 0), int(c.get("wired-tx_bytes", 0) or 0)
    return int(c.get("rx_bytes", 0) or 0), int(c.get("tx_bytes", 0) or 0)


def _client_name(c: dict) -> str:
    return (c.get("name") or c.get("hostname") or c.get("oui")
            or c.get("ip") or c.get("mac") or "?")


def show_top_talkers(client: "UniFiClient", n: int) -> None:
    clients = client.clients()
    ranked = sorted(clients, key=lambda c: sum(_client_bytes(c)), reverse=True)[:n]
    table = Table(title=f"Top {len(ranked)} clients by data (this session, since connect)")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Client", style="cyan")
    table.add_column("IP")
    table.add_column("Link")
    table.add_column("Down (rx)", justify="right", style="green")
    table.add_column("Up (tx)", justify="right", style="yellow")
    table.add_column("Total", justify="right", style="bold")
    for i, c in enumerate(ranked, 1):
        rx, tx = _client_bytes(c)
        link = "wired" if c.get("is_wired") else f"wifi {c.get('radio_proto', '')}".strip()
        table.add_row(str(i), _client_name(c), c.get("ip", "-"), link,
                      _human_bytes(rx), _human_bytes(tx), _human_bytes(rx + tx))
    console.print(table)
    console.print("[dim]Note: byte counters are per current session (since each client connected), "
                  "not an all-time/monthly total.[/dim]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only UniFi audit helper")
    parser.add_argument("--events", type=int, default=30, help="number of recent events to fetch")
    parser.add_argument("--top", type=int, metavar="N",
                        help="show the top N clients by data usage and exit")
    parser.add_argument("--json", action="store_true",
                        help="dump a machine-readable inventory (sysinfo, devices, clients) as JSON and exit")
    args = parser.parse_args()

    # In --json mode, route status lines to stderr so stdout stays pure JSON.
    out = Console(stderr=True) if args.json else console

    out.print(f"[bold]Connecting[/bold] to UniFi OS at {BASE} as [cyan]{USERNAME}[/cyan] "
              f"(verify_ssl={VERIFY_SSL})…")

    client = UniFiClient()
    try:
        client.login()
        out.print("[green]✓ Authenticated[/green] (read-only)\n")

        if args.top:
            show_top_talkers(client, args.top)
            return

        # System info
        info = client.sysinfo()
        devices = client.devices()

        if args.json:
            import json
            payload = {
                "sysinfo": info,
                "devices": devices,
                "clients": client.clients(),
            }
            # print to stdout for capture (no rich formatting)
            print(json.dumps(payload, indent=2, default=str))
            return

        if info:
            si = info[0]
            console.print(f"[bold]Console:[/bold] {si.get('name', '?')} ({si.get('hostname','?')})  "
                          f"Network app v{si.get('version', '?')}  "
                          f"UniFi OS v{si.get('console_display_version', '?')}")

        # Infrastructure devices with firmware versions
        if devices:
            dtable = Table(title=f"Adopted devices ({len(devices)})")
            dtable.add_column("Name", style="cyan")
            dtable.add_column("Model")
            dtable.add_column("Type")
            dtable.add_column("Firmware", style="green")
            dtable.add_column("IP")
            dtable.add_column("State")
            for d in devices:
                dtable.add_row(
                    d.get("name") or d.get("model") or "-",
                    d.get("model", "-"),
                    d.get("type", "-"),
                    d.get("version", "-"),
                    d.get("ip", "-"),
                    str(d.get("state", "-")),
                )
            console.print(dtable)

        # Connected clients
        clients = client.clients()
        console.print(f"\n[bold]Connected clients:[/bold] {len(clients)}\n")

        # Recent admin-login events (the security-relevant ones)
        events, endpoint = client.events(args.events)
        console.print(f"[dim]events endpoint:[/dim] {endpoint}")
        login_events = [e for e in events if "Login" in e.get("key", "") or e.get("key", "").startswith("EVT_AD")]

        table = Table(title=f"Recent admin/login events (of {len(events)} fetched)")
        table.add_column("Time (UTC)", style="cyan", no_wrap=True)
        table.add_column("Key")
        table.add_column("Admin / Msg")
        table.add_column("Source IP", style="yellow")

        rows = login_events or events  # fall back to all events if no login events found
        for e in rows[:args.events]:
            table.add_row(
                _fmt_ts(e.get("time")),
                e.get("key", "-"),
                (e.get("admin") or e.get("msg") or "-")[:60],
                e.get("ip") or e.get("src_ip") or "-",
            )
        console.print(table)

        if login_events:
            console.print(f"\n[bold]{len(login_events)}[/bold] login-related event(s). "
                          "Check the [yellow]Source IP[/yellow] column: 192.168.0.x = local (your Pi/HA "
                          "or you); an unfamiliar public IP would be a concern.")
        else:
            console.print("\n[dim]No explicit login events in the fetched window — "
                          "increase --events to look further back.[/dim]")

    finally:
        client.logout()


if __name__ == "__main__":
    main()
