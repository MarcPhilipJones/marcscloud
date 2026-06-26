# TODO — TeslaFi → TeslaMate Migration

Replace the paid TeslaFi subscription with a self-hosted TeslaMate stack on the
Pi 5, integrated into Home Assistant with Grafana + a native HA dashboard.

Decisions (2026-06-26): run on SD card for now (USB SSD later); Marc does the
Tesla web sign-in; LAN-only (no internet exposure); Grafana dashboard + new
best-effort native HA dashboard (old Tesla dashboard deleted later).

## Tasks

1. **DONE** — Append TeslaMate stack (teslamate, postgres, grafana, mosquitto) to `docker-compose.yml`
2. **DONE** — Create `.env.teslamate.example` template + generate real `.env` on the Pi (git-ignored secrets)
3. **DONE** — Deploy compose to Pi, create `/mnt/data/teslamate/*` dirs, `docker compose up -d`
4. **DONE** — Marc: Tesla web sign-in at `http://192.168.0.111:4000` (Auth-app token); TeslaMate logging
5. **DONE** — HA MQTT integration + TeslaMate→HA package (44 entities). Hardened mosquitto healthcheck to fix the first-boot MQTT publisher race.
6. **DONE** — Grafana anonymous LAN embedding + "Tesla Analytics" HA dashboard (8 iframe views)
7. **DONE** — "Tesla" native HA dashboard (status/battery/charging/climate/location/info)
8. **DONE** — Octopus cheap-rate badge (live price < £0.10 logic; no Echo per Marc)

## Notes / Constraints

- Disk: 29G SD, ~7.8G free (72% used). `/mnt/data` is the SAME SD card. Monitor growth.
- No MQTT broker existed before — Mosquitto is NEW and shared (HA will use it too).
- TeslaMate (June 2026 release) already fixed the Owner-API auth-host 403 that
  currently breaks `tesla_custom`, so TeslaMate logs data the HACS integration cannot.
- `tesla_custom` stays installed for command/control once its 403 fix lands.
- Watchtower stays OFF for these services (pinned, manual updates) — repo convention.
- Security: Tesla token encrypted at rest (ENCRYPTION_KEY); Postgres/Grafana/MQTT
  passwords live only in the Pi `.env`, never committed.

---

## Archived — Bilresa Button Fix (completed)

1. **DONE** — Fix bilresa button 1 automation to ignore unavailable→available transitions (phantom press)
2. **DONE** — Fix bilresa button 2 automation to ignore unavailable→available transitions (phantom press)
3. **DONE** — Investigate Zigbee connectivity flapping & battery anomaly (100% battery, 0.0V voltage) — see findings below
4. **BLOCKED** — Clean up stale Device 1 — requires manual action in HA UI (see instructions below)
5. **DONE** — Check Eve Smart Plugs, Apple Home network, and Thread mesh topology — see findings below
6. **DONE** — Removed both Bilresa automations from HA entirely (phantom presses persisted despite prior fixes)

## Findings — Eve Smart Plugs & Thread Mesh (Task 5)

**Eve Smart Plugs: NOT visible in Home Assistant.**
Searched all 335 entities — zero Eve devices found. Neither as available nor unavailable entities.

**Apple Home network: NOT integrated with Home Assistant.**
- The `homekit` / `homekit_controller` integration is NOT loaded
- There is an Apple TV (`media_player.living_room_apple_tv`) via the `apple_tv` integration, but this doesn't bridge Apple Home devices into HA

**Thread integration: Loaded but isolated.**
- The `thread` integration is present in HA
- The HA Voice NABU device is the likely Thread border router
- However, the Eve plugs are **not** part of HA's Matter/Thread fabric

### Why the Eve plugs aren't visible

Eve Smart Plugs with Thread support are likely paired to your **Apple Home** ecosystem, not to Home Assistant's Matter fabric. This is the key issue:

- **Apple Home has its own Thread network** with its own Thread border routers (Apple TV, HomePod)
- **Home Assistant has a separate Thread network** managed by its own border router (NABU voice)
- These are **two separate Thread networks** unless you explicitly share credentials between them
- The Eve plugs extending your Apple Home Thread mesh do **nothing** for HA's Thread mesh — the BILRESA button is on HA's Thread network, not Apple's

### What needs to happen for this to work

**Option A — Add Eve plugs to HA's Matter fabric (recommended):**
1. In the Eve app, enable "Matter" for each Eve plug (Eve app → device → settings → enable Matter/Thread)
2. Generate a Matter pairing code from the Eve app
3. In HA, go to **Settings → Devices & Services → Add Integration → Matter** and pair the Eve plug using that code
4. The Eve plug will then be on BOTH Apple Home AND HA's Thread networks, acting as a Thread router for both

**Option B — Share Thread credentials:**
1. In HA, go to **Settings → Devices & Services → Thread**
2. Check if there's an option to import/share Thread network credentials with Apple Home
3. This would merge the two Thread networks so devices from both can talk to each other

**Option A is simpler and more reliable.** Once the Eve plugs are paired to HA via Matter, they'll act as Thread routers on HA's mesh and the BILRESA button should have a much more stable connection.

## Instructions — Remove Stale Device 1 (Task 4)

All 6 entities for Device 1 have been `unavailable` since **March 17**. To remove:

1. Go to **Settings → Devices & Services → Matter** in HA UI
2. Find the stale **BILRESA dual button** device (the one with entities that do NOT have the `_2` suffix)
3. Click the device → **Delete** (or "Remove" if it shows as orphaned)
4. Entities to be removed: `sensor.bilresa_dual_button_battery`, `sensor.bilresa_dual_button_battery_voltage`, `sensor.bilresa_dual_button_battery_type`, `update.bilresa_dual_button_firmware`, `event.bilresa_dual_button_button_1`, `event.bilresa_dual_button_button_2`

This is a destructive action — once removed, the device record is gone. But since it's been dead for a week and there's a working replacement (Device 2), this is safe.

## Findings — Bilresa Connectivity Flapping (Task 3)

**Protocol**: The BILRESA dual button connects via **Matter** (not ZHA/Zigbee).

**Flapping pattern** (7-day history, 36 state transitions):
- The device repeatedly cycles unavailable → available, typically dropping after 20–90 minutes of connectivity
- Mar 17: 2 drops, Mar 18: 3 drops, Mar 19: 3 drops, Mar 20: 2 drops, Mar 23: 6 drops, Mar 24: 1 drop so far
- The 3-day gap (Mar 20–23) may correspond to the device being out of range or powered off

**Battery anomaly**: Battery reports 100% but voltage is 0.0V. This is suspicious — it could mean:
- The device is reporting battery via Matter but the voltage sensor is not supported/mapped
- Or the batteries are new but the voltage reading is broken

**Likely causes**:
1. **Weak Matter/Thread signal** — IKEA BILRESA buttons use Thread (Matter over Thread). If the Thread border router is far away or there aren't enough Thread router devices nearby, the button will drop frequently
2. **IKEA Matter firmware bug** — known issue with early IKEA Matter devices having aggressive sleep and reconnection problems
3. **Duplicate device registration** — Device 1 (the permanently unavailable one) may be causing conflicts

**Recommendations**:
- Remove the stale Device 1 (task 4)
- Check if there's a Thread border router within range (the HA Voice NABU device may serve as one)
- Consider updating the BILRESA firmware if a newer version is available (currently on 1.8.5)
- If flapping persists after cleanup, move the button closer to a Thread border router or add a Thread-capable device as a relay
