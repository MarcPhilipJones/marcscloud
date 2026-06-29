#!/usr/bin/env python3
"""TeslaMate geofence manager (free, local).

One-liners for the recurring "add a geofence for X" request. Talks to the
TeslaMate Postgres on the Pi over SSH (sourcing ~/.env for the DB password) and
resolves place names via OpenStreetMap Nominatim — the same geocoder TeslaMate
itself uses.

Usage:
    python scripts/geofence.py list
    python scripts/geofence.py add "Lidl Wednesbury" --radius 100
    python scripts/geofence.py add "Home" --lat 52.539620 --lon -2.006674 --radius 30
    python scripts/geofence.py find "Tesco Express Stone Cross"   # lookup only
    python scripts/geofence.py delete 14            # by id
    python scripts/geofence.py delete "Lyng Jon"    # by name

Notes:
- Geofence radius is in METRES. Effective on the car's next location publish
  (no restart, no wake).
- Names with apostrophes are handled (e.g. "Nan and Grandad's").
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _ha import pi_ssh  # noqa: E402

UA = {"User-Agent": "ha-teslamate-geofence/1.0 (raspberry-pi home lab)"}
PSQL = (
    "set -a; . ~/.env; "
    "docker exec -i -e PGPASSWORD=$TM_DB_PASS teslamate-db "
    "psql -U teslamate -d teslamate"
)


def sql(statement: str) -> str:
    rc, out = pi_ssh(PSQL, stdin_text=statement)
    if rc != 0:
        print(out, file=sys.stderr)
        sys.exit(f"psql failed (rc={rc})")
    return out


def q(text: str) -> str:
    """SQL single-quote escape."""
    return text.replace("'", "''")


def geocode(query: str):
    url = "https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&q=" + \
        urllib.parse.quote(query)
    req = urllib.request.Request(url, headers=UA)
    results = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
    # Prefer a real retail/place hit over distribution centres / warehouses.
    pref = ("supermarket", "convenience", "department_store", "mall",
            "retail", "station", "house", "residential")
    results.sort(key=lambda r: (r.get("type") not in pref))
    return results


def cmd_list(_args):
    print(sql(
        "SELECT id, name, latitude, longitude, radius FROM geofences ORDER BY id;"
    ))


def cmd_find(args):
    res = geocode(args.query)
    if not res:
        sys.exit("No Nominatim results.")
    for r in res:
        print(f"{r['lat']:>12}, {r['lon']:>12}  [{r.get('type')}]  "
              f"{r['display_name'][:90]}")


def cmd_add(args):
    lat, lon = args.lat, args.lon
    if lat is None or lon is None:
        res = geocode(args.name if args.query is None else args.query)
        if not res:
            sys.exit("No Nominatim results; pass --lat/--lon explicitly.")
        top = res[0]
        lat, lon = float(top["lat"]), float(top["lon"])
        print(f"Resolved '{args.name}' -> {lat:.6f}, {lon:.6f}  "
              f"[{top.get('type')}] {top['display_name'][:80]}")
    out = sql(
        "INSERT INTO geofences (name, latitude, longitude, radius, "
        "inserted_at, updated_at) VALUES "
        f"('{q(args.name)}', {lat:.6f}, {lon:.6f}, {args.radius}, NOW(), NOW());\n"
        "SELECT id, name, latitude, longitude, radius FROM geofences ORDER BY id;"
    )
    print(out)


def cmd_delete(args):
    target = args.id_or_name
    if target.isdigit():
        where = f"id = {int(target)}"
    else:
        where = f"name = '{q(target)}'"
    out = sql(
        f"DELETE FROM geofences WHERE {where};\n"
        "SELECT id, name, latitude, longitude, radius FROM geofences ORDER BY id;"
    )
    print(out)


def main():
    p = argparse.ArgumentParser(description="TeslaMate geofence manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list").set_defaults(func=cmd_list)

    pf = sub.add_parser("find", help="Nominatim lookup only (no DB write)")
    pf.add_argument("query")
    pf.set_defaults(func=cmd_find)

    pa = sub.add_parser("add")
    pa.add_argument("name")
    pa.add_argument("--radius", type=int, default=40, help="metres (default 40)")
    pa.add_argument("--lat", type=float)
    pa.add_argument("--lon", type=float)
    pa.add_argument("--query", help="override the geocode search text")
    pa.set_defaults(func=cmd_add)

    pd = sub.add_parser("delete")
    pd.add_argument("id_or_name")
    pd.set_defaults(func=cmd_delete)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
