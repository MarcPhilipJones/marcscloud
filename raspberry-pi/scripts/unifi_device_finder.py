"""UniFi Device Finder — read-only "where is X?" lookups.

Answers questions like:
    - "Which AP is the iPad connected to?"
    - "Which switch port is the Hikvision DVR on?"
    - "What IP / signal does the Raspberry Pi have right now?"

Reuses the read-only UniFiClient from unifi_audit.py (same View-Only login).
READ-ONLY: only GET requests after the auth POST. Never changes config.

Usage:
    python scripts/unifi_device_finder.py                 # list LIVE clients with location
    python scripts/unifi_device_finder.py pi              # match name/host/IP/MAC substring
    python scripts/unifi_device_finder.py 192.168.0.144   # match by IP
    python scripts/unifi_device_finder.py dvr --json      # machine-readable
    python scripts/unifi_device_finder.py ipad --offline  # search KNOWN clients incl. offline
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

from rich.console import Console
from rich.table import Table

# Import the existing read-only client (script dir is on sys.path when run directly).
from unifi_audit import SITE, UniFiClient

console = Console()


def _name(c: dict) -> str:
    return (c.get("name") or c.get("hostname") or c.get("oui")
            or c.get("ip") or c.get("mac") or "?")


def _uptime(c: dict) -> str:
    secs = int(c.get("uptime", 0) or 0)
    if secs <= 0:
        return "-"
    return str(timedelta(seconds=secs))


def _build_device_index(devices: list[dict]) -> dict[str, dict]:
    """Map lowercased device MAC -> {name, model, port_names{idx:name}}."""
    idx: dict[str, dict] = {}
    for d in devices:
        mac = (d.get("mac") or "").lower()
        if not mac:
            continue
        port_names = {}
        for p in d.get("port_table", []) or []:
            pi = p.get("port_idx")
            if pi is not None:
                port_names[int(pi)] = p.get("name") or f"Port {pi}"
        idx[mac] = {
            "name": d.get("name") or d.get("model") or mac,
            "model": d.get("model", "-"),
            "port_names": port_names,
        }
    return idx


def _location(c: dict, dev_idx: dict[str, dict]) -> str:
    """Human 'where is this client' string."""
    if c.get("is_wired"):
        sw = dev_idx.get((c.get("sw_mac") or "").lower())
        port = c.get("sw_port")
        if sw and port is not None:
            pname = sw["port_names"].get(int(port), "")
            label = f"{sw['name']} · port {port}"
            return f"{label} ({pname})" if pname and pname != f"Port {port}" else label
        return "wired (uplink unknown)"
    ap = dev_idx.get((c.get("ap_mac") or "").lower())
    ap_name = ap["name"] if ap else (c.get("ap_mac") or "?")
    band = c.get("radio_proto") or c.get("radio") or ""
    ch = c.get("channel")
    extra = f" · ch{ch}" if ch else ""
    return f"{ap_name} ({band}{extra})".strip()


def _matches(c: dict, q: str) -> bool:
    q = q.lower()
    for field in ("name", "hostname", "oui", "ip", "last_ip", "mac"):
        if q in str(c.get(field, "")).lower():
            return True
    return False


def _last_seen_str(epoch_s: int | None) -> str:
    if not epoch_s:
        return "-"
    when = datetime.fromtimestamp(int(epoch_s), tz=timezone.utc)
    age = datetime.now(tz=timezone.utc) - when
    days = age.days
    if days >= 1:
        ago = f"{days}d ago"
    elif age.seconds >= 3600:
        ago = f"{age.seconds // 3600}h ago"
    else:
        ago = f"{max(age.seconds // 60, 1)}m ago"
    return f"{when:%Y-%m-%d %H:%M} ({ago})"


def _offline_location(u: dict, dev_idx: dict[str, dict]) -> str:
    """Where a KNOWN client was last seen (from rest/user)."""
    name = u.get("last_uplink_name")
    if not name:
        dev = dev_idx.get((u.get("last_uplink_mac") or "").lower())
        name = dev["name"] if dev else None
    if not name:
        return "unknown"
    if u.get("is_wired"):
        port = u.get("last_uplink_remote_port")
        return f"{name} · port {port}" if port else name
    radio = u.get("last_radio") or ""
    net = u.get("last_connection_network_name") or ""
    tail = " · ".join(x for x in (radio, net) if x)
    return f"{name} ({tail})" if tail else name


def _run_offline(client: "UniFiClient", query: str | None, dev_idx: dict[str, dict],
                 as_json: bool) -> None:
    users = client._net_get(f"/api/s/{SITE}/rest/user").get("data", [])
    matched = [u for u in users if not query or _matches(u, query)]
    matched.sort(key=lambda u: int(u.get("last_seen", 0) or 0), reverse=True)

    if as_json:
        print(json.dumps([
            {
                "name": _name(u),
                "last_ip": u.get("last_ip"),
                "mac": u.get("mac"),
                "connection": "wired" if u.get("is_wired") else "wifi",
                "last_location": _offline_location(u, dev_idx),
                "last_seen_utc": (datetime.fromtimestamp(int(u["last_seen"]), tz=timezone.utc)
                                  .isoformat() if u.get("last_seen") else None),
            }
            for u in matched
        ], indent=2, default=str))
        return

    title = (f"Known clients matching '{query}'" if query
             else "All known clients") + f" ({len(matched)}, incl. offline)"
    table = Table(title=title)
    table.add_column("Name", style="cyan")
    table.add_column("Last IP")
    table.add_column("Conn")
    table.add_column("Last seen at (AP / switch · port)", style="green")
    table.add_column("Last seen", style="dim")
    for u in matched:
        table.add_row(
            _name(u),
            u.get("last_ip") or "-",
            "wired" if u.get("is_wired") else "wifi",
            _offline_location(u, dev_idx),
            _last_seen_str(u.get("last_seen")),
        )
    console.print(table)
    if query and not matched:
        console.print(f"[yellow]No known client matched '{query}'.[/yellow] Try a shorter substring.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only UniFi 'where is X?' device finder")
    parser.add_argument("query", nargs="?", help="name/hostname/IP/MAC substring to match")
    parser.add_argument("--offline", action="store_true",
                        help="search the KNOWN-client DB (rest/user), incl. currently-offline devices, "
                             "showing where each was last seen")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    out = Console(stderr=True) if args.json else console
    client = UniFiClient()
    try:
        client.login()
        out.print("[green]\u2713 Authenticated[/green] (read-only)")
        devices = client.devices()
        dev_idx = _build_device_index(devices)

        if args.offline:
            _run_offline(client, args.query, dev_idx, args.json)
            return

        clients = client.clients()
        matched = [c for c in clients if not args.query or _matches(c, args.query)]
        matched.sort(key=_name)

        if args.json:
            print(json.dumps([
                {
                    "name": _name(c),
                    "ip": c.get("ip"),
                    "mac": c.get("mac"),
                    "connection": "wired" if c.get("is_wired") else "wifi",
                    "location": _location(c, dev_idx),
                    "signal_dbm": None if c.get("is_wired") else c.get("signal"),
                    "network": c.get("network"),
                    "uptime": _uptime(c),
                }
                for c in matched
            ], indent=2, default=str))
            return

        title = (f"Devices matching '{args.query}'" if args.query
                 else "All connected clients") + f" ({len(matched)})"
        table = Table(title=title)
        table.add_column("Name", style="cyan")
        table.add_column("IP")
        table.add_column("Conn")
        table.add_column("Where (AP / switch · port)", style="green")
        table.add_column("Signal", justify="right")
        table.add_column("Network")
        table.add_column("Uptime", justify="right", style="dim")
        for c in matched:
            wired = c.get("is_wired")
            sig = "-" if wired else f"{c.get('signal', '?')} dBm"
            table.add_row(
                _name(c),
                c.get("ip", "-"),
                "wired" if wired else "wifi",
                _location(c, dev_idx),
                sig,
                c.get("network", "-"),
                _uptime(c),
            )
        console.print(table)
        if args.query and not matched:
            console.print(f"[yellow]No connected client matched '{args.query}'.[/yellow] "
                          "It may be offline, or try a shorter substring (name/IP/MAC).")
    finally:
        client.logout()


if __name__ == "__main__":
    main()
