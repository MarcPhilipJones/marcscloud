---
name: teslamate-home-lab
description: >-
  TeslaMate + Home Assistant Tesla integration for THIS home lab (self-hosted,
  free, replaces paid TeslaFi). Use when the user asks to add/list/delete a
  TeslaMate GEOFENCE, work on the "drive started" notification, edit the
  prepare_the_tesla script, query TeslaMate drives/positions, or decide between
  TeslaMate vs Tesla Fleet for a Tesla feature. Encodes the DB schema, MQTT
  topics, key entities, the drive-alert design, and the deploy gotchas.
---

# TeslaMate Home-Lab Skill

Goal (hard constraint): **cancel paid TeslaFi, stay FREE + FULLY LOCAL.** Do NOT
propose paid subscriptions (Teslemetry / Tessie are ruled out). Default stack =
self-hosted TeslaMate (data) + HA `tesla_fleet` (control) + HA automations.

## Infrastructure
- Pi 5 `192.168.0.111`, SSH alias `pi5` (passwordless sudo). HA at `:8123`.
- TeslaMate stack in `~/docker-compose.yml`: `teslamate` (:4000), `teslamate-db`
  (postgres, internal), `teslamate/grafana` (:3000), `mosquitto` (:1883).
- DB creds: user/db `teslamate`, password `$TM_DB_PASS` in Pi `~/.env`.
- HA REST token: `HA_TOKEN` in the workspace `.env`.

## Use the repo helpers (don't hand-roll)
- **Geofences:** `python scripts/geofence.py list | add "Name" [--radius m] [--lat --lon] | find "q" | delete <id|name>`.
  Resolves names via Nominatim, escapes apostrophes, prevents the quoting pain.
- **HA REST/diagnostics:** `from _ha import HA, pi_ssh` (token, states, services,
  template render, `reload_all`, `check_config`).
- **Remote cmds / root-owned file deploys:** `scripts/pi-exec.ps1`
  (`-Command`, `-Python`, `-Root`, or `-DeployFile -Dest`). Pipes over stdin so
  PowerShell never mangles quotes.
- **Drive-alert deploy:** `python scripts/deploy_tesla_drive_alert.py`.
- **Git save-point:** `scripts/checkpoint.ps1 "msg"` (local commit only).

## Geofences (TeslaMate Postgres `geofences`)
Columns: id, name varchar(255), latitude numeric(8,6), longitude numeric(9,6),
radius **smallint METRES** (default 25), inserted_at, updated_at, cost_per_unit,
session_fee, billing_type. `sensor.tesla_geofence` mirrors the matched name; it
has a value_template => shows **"Away"** outside all fences. Effective on the
car's next location publish (no restart/wake). When picking a place, choose the
`type=supermarket/convenience` Nominatim hit, not a distribution centre.

## Drive-started notification
- Automation `tesla_drive_started_destination` (entity
  `automation.tesla_drive_started_destination_alert` — HA slugs the alias).
- **Trigger = `sensor.tesla_state` -> `driving`** (fires ONCE per trip, immune to
  the P/R/N/D gear shuffle). Do NOT use `sensor.tesla_shift_state -> D` with a
  P/N guard — it misses Reverse->Drive departures off the driveway.
- Waits up to 25s for `sensor.tesla_active_route_destination`; nav set => rich
  card; no nav => "new drive started" + origin in words (geofence name, else
  Nominatim reverse-geocode via `rest_command.reverse_geocode`).
- **Mandatory top 3 lines (BOTH branches, with emoji):**
  `🚗 Drive Started: <HH:MM>` / `⬅️ From: <origin>` / `📍 Destination: <dest|Not set>`,
  then the rest (ETA, miles, battery now->arrival, cabin, traffic).
- `start_clock` + `start_lat/lon` captured as the FIRST action (before the wait) so
  the time = real departure and the Start map link = real start point. `origin`
  resolved ONCE up front and reused by both branches.
- **Destination override:** Marc works from home, so the dest template maps
  `Work` -> `Home`: `{{ 'Home' if d == 'Work' else d }}`.
- **Google Maps links (tappable, `html=1`):** end line `🔗 Start | Destination`,
  URL `https://www.google.com/maps/search/?api=1&query=LAT,LON` (opens the Google
  Maps app on iPhone via universal link). Start = captured start GPS; Destination =
  `sensor.tesla_active_route_location` lat/lon attrs (new sensor; availability-gated,
  reads `unavailable` with no active route). No-nav branch has only the Start link.
  - ⚠️ `html` MUST be nested under the notify `data` key (`data: { data: { html: 1 } }`);
    a top-level `html` field returns HTTP 400.
- **Thumbnail static map (attached image):** drive-start calls
  `shell_command.build_drive_map` (start+dest "lat,lon"; dest "None,None" => start-only
  A marker) which runs Pi-only `/config/drive_map.sh` (repo `scripts/drive_map.sh`).
  The script reads the Google Static Maps key from `/config/.google_maps_key`
  (mode 600, NOT in git) and curls a 600x320@2x PNG (A green / B red / blue route)
  to `/config/www/drive_maps/last_drive.png`. Attach via pushover nested data
  `attachment: /config/www/drive_maps/last_drive.png` (LOCAL FILE PATH only).
  - ⚠️ HA pushover `attachment` only accepts a whitelisted local file path; a URL
    fails with "Path is not whitelisted" and the push sends WITHOUT the image (still
    HTTP 200). `/config/www` MUST be in `homeassistant: allowlist_external_dirs:`
    (configuration.yaml, needs a restart). Key never reaches the phone (HA uploads bytes).
  - ⚠️ HA `shell_command` runs WITHOUT a shell: no `$(...)`, pipes or `&&` (returns
    200 but does nothing). Put logic in a script and call `/bin/sh /config/x.sh ...`.
  - ⚠️ Changing the shell_command DEFINITION needs an HA restart; editing the SCRIPT
    body does not. Strip CRLF on deploy (`sed -i 's/\r$//'`) + `chmod 0755`.
  - Google key: IP-restricted to the WAN IP + restricted to Maps Static API; free
    tier 10k/mo (≈$0). `python scripts/...` curl test from the Pi originates from the
    allowed WAN IP.
- Reverse-geocode lat/lon from
  `state_attr('device_tracker.tesla_location','latitude'/'longitude')`.

## Deploy gotchas
- `~/homeassistant/packages/*.yaml` + config are **root-owned** => use
  `pi-exec.ps1 -DeployFile`/`sudo cp`; plain scp/`>>` = Permission denied.
- A BRAND-NEW `rest_command` (or other new YAML domain) is NOT picked up by
  `reload_all` — needs a one-time `homeassistant.restart` (does not wake car).
- `reload_all` re-publishes retained MQTT, so reloading WHILE driving re-fires
  the drive automation once (harmless).
- **ALWAYS** `HA().check_config()` before a reload/restart.
- Automations: add via REST `POST /api/config/automation/config/<id>` (leaves
  UI-made automations intact), then `scp pi5:.../automations.yaml` DOWN to
  reconcile the repo backup. Pi has 2 UI-only automations not in older backups.

## Fleet vs TeslaMate (researched, verified on the car)
- Native HA `tesla_fleet` is POLLING-ONLY and exposes NO shift/driving entity.
- Car (Model Y, fw 2026.20.0, telemetry client 1.2.0, key paired) DOES support
  Fleet Telemetry streaming, but that needs a self-hosted public telemetry server
  (FQDN+mTLS) or a paid service — out of scope per the free/local constraint.
- => For "drive started", TeslaMate `state=driving` is the right source.

## Verify commands
- MQTT live: `ssh pi5 'docker exec mosquitto mosquitto_sub -h localhost -t "teslamate/cars/1/#" -v -W 4'`
- Drives: `geofence.py`-style psql, table `drives` (end_date NULL = in progress).
