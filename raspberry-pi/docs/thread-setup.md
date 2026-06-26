# Thread / Matter Setup — Home Lab

**Last verified:** 2026-06-26 (read-only audit, nothing changed)
**Status:** Healthy and working — this document is reference only.

> Companion reusable health check: [`scripts/thread_health_check.py`](../scripts/thread_health_check.py)
> Run anytime with the venv Python:
> ```powershell
> & .venv\Scripts\python.exe scripts\thread_health_check.py
> ```
> It is **read-only** and queries Home Assistant, the Matter server, and the LAN
> (mDNS) — it never changes anything.

---

## TL;DR

- You run **two separate Thread networks**: a large **Apple** one (the main mesh)
  and a small isolated **Amazon** one.
- Your **Apple TV "Living Room"** is a Thread Border Router, and it is **not
  alone** — a HomePod and the tado bridge also route for the same Apple mesh
  (good redundancy).
- Home Assistant's Thread devices ride on the **Apple** border routers; HA has no
  border router of its own.
- A few devices are offline, but they're long-standing/non-critical (see below).

---

## The two Thread networks on your LAN

### 1. Apple network `MyHome1541761114` (the main mesh)

- Extended PAN ID: `0x452fc667f1034860`
- Thread IPv6 prefix (OMR): `fd45:2fc6:67f1:4860::/64`
- **Border routers (3 — good redundancy):**

  | Device | IP | Vendor | Thread ver |
  |---|---|---|---|
  | Apple TV "Living Room" | `192.168.0.228` | Apple | 1.3.0 |
  | HomePod "Marc's Bedroom" | `192.168.0.190` | Apple | 1.3.0 |
  | tado Internet Bridge | `192.168.0.234` | OpenThread | 1.3.0 |

- This network carries your Apple Home Thread accessories (Eve plugs, tado, etc.)
  **and** Home Assistant's Matter-over-Thread devices (Aqara FP300, IKEA BILRESA
  buttons). ~35 operational Matter services were advertising on the LAN at audit
  time, most on the `fd45:…` prefix.

### 2. Amazon network `AMZN-Thread-3e63` (isolated)

- Extended PAN ID: `0xc90b7a948b16d552`
- **Border router (1 — no redundancy):** Amazon Echo `192.168.0.130`
- This is a separate island. Anything paired into Alexa's Thread lives here and
  **cannot** route with the Apple mesh. Single border router = if the Echo is off,
  that mesh has no route to Wi-Fi.

> Two networks is normal when both Apple and Alexa ecosystems are in use — they
> each insist on their own Thread fabric. It's only worth consolidating if you
> want all Thread devices on one resilient mesh.

---

## Home Assistant Matter fabric (snapshot)

As of **2026-06-26** (after migration to matterjs-server + dead-node cleanup), the
fabric holds **5 nodes**, all online:

| Node | Device | Radio | Status |
|---|---|---|---|
| 1 | tado Smart Radiator Thermostat X | Thread | OK |
| 2 | Tapo Smart Wi-Fi Plug | Wi-Fi | OK |
| 3 | tado Smart Radiator Thermostat X | Thread | OK |
| 4 | tado Smart Radiator Thermostat X | Thread | OK |
| 7 | Aqara Presence Multi-Sensor FP300 | Thread | OK |

> Nodes **5 & 9** (IKEA BILRESA dual buttons) and **8** (Tapo Multicolor Bulb) were
> long-dead/unused and were **removed from the fabric on 2026-06-26** via the matter
> server `remove_node` command. Previously the fabric had 8 nodes (3 offline).

**Offline notes (not urgent):**
- The two **BILRESA buttons** are battery "sleepy end devices" and have been
  flaky/dead for a while (see [`TODO.md`](../TODO.md) — one stale since March).
  Likely dead batteries or de-pairing, not a mesh fault.
- The **Tapo Multicolor Bulb** (office light) is Wi-Fi Matter, so its offline
  state is a Wi-Fi/power issue, not Thread. It may still respond via the Tapo
  cloud integration.

---

## Two quirks worth knowing

1. **HA has no Thread border router of its own.** The HA Thread panel stores
   **0 datasets**. HA's Thread devices joined the **Apple** mesh using credentials
   imported earlier (iPhone → HA Companion app). They reach the network through
   the Apple TV / HomePod / tado border routers.

2. **`thread_credentials_set = False` on the Matter server.** Existing Thread
   devices keep working, but **HA cannot commission *new* Thread devices** until
   Apple's Thread credentials are re-imported (or HA gets its own border router).

---

## What is NOT possible

- **Direct Apple TV access.** Apple TVs and HomePods expose **no API and no SSH**.
  You cannot query them programmatically. Apple's per-device Thread internals
  (RSSI, leader/router/child roles, parent-child links) are only visible in:
  - **iOS Home app** → Home Settings → tap a hub → **Thread Network**
  - **Eve app** → Settings → Thread Network (best consumer topology map with
    signal strength)

---

## What IS possible in the future (ideas, not actions)

Nothing here is needed today — recorded for curiosity / future reference.

1. **Give HA its own Thread Border Router** (so it can run real OpenThread
   diagnostics). Add the Home Assistant **OpenThread Border Router** add-on with a
   **SkyConnect / Connect ZBT-1** USB radio, then import Apple's Thread credentials.
   Benefits:
   - Programmatic mesh diagnostics via SSH: `ot-ctl router table`,
     `ot-ctl neighbor table`, `ot-ctl leaderdata` (per-device RSSI, roles, routes).
   - Re-enables commissioning new Thread devices into HA.
   - A 4th border router on the Apple mesh = even more resilience.

2. **Consolidate the Amazon Thread island** onto the Apple mesh (or vice-versa) if
   you ever want a single, more resilient Thread fabric. Practically: re-commission
   the Alexa-only Thread accessories into Apple Home / HA.

3. **Add a second border router to whichever mesh is single-homed** (the Amazon one
   today) for redundancy — e.g. another Echo with Thread, or move those devices to
   the Apple mesh.

4. **Enable IPv6 on the UniFi LAN** (currently deferred — see
   [`docs/possible-unifi-updates-ipv6.md`](possible-unifi-updates-ipv6.md)). Only
   worth doing if you start seeing Matter/Thread commissioning or cross-VLAN
   discovery problems. Everything works on IPv4-only today.

5. **Automated periodic health checks.** The script above could be scheduled (e.g.
   a Windows task or a cron job on the Pi) to log Thread/Matter health over time
   and alert on new offline devices.

---

## Matter 1.6 "Joint Fabric" & the matter.js server (researched 2026-06-26)

### Matter 1.6 — Joint Fabric (announced 17 Jun 2026)
- A Matter **fabric** is a *controller* trust domain (Apple Home, Alexa and HA each
  build their own). It is **not** a Thread network (the radio mesh). The two are
  different layers.
- **Joint Fabric** (the headline 1.6 feature) makes one fabric shared across
  multiple platforms: commission a device once and every joined controller sees it,
  replacing today's multi-admin "share one device at a time" flow.
- **Impact here:** future convenience — no more multi-admin pairing of Apple Home
  devices into HA. It does **not** merge the Apple vs Amazon Thread islands (that's a
  Thread-layer job — see idea #2 above) and does **not** fix
  `thread_credentials_set = False`. It is future-dated and needs Apple + Amazon + HA
  to each ship support.
- Other 1.6 features: full NFC onboarding (needs new NFC-chip hardware), Thermostat
  Suggestions, security-sensor event history, smoke-alarm unmount alerts.

### Matter Server upgrade (matter.js) — DONE 2026-06-26
This lab runs HA **Container** + a **standalone** `matter-server` Docker service,
so the HA-OS "Matter Server app 9.0" add-on does NOT apply — we swapped the image.

**Migrated 2026-06-26** from `python-matter-server:stable` (sdk 2025.7.0, EOL —
repo archived, final 8.1.2) to **`ghcr.io/matter-js/matterjs-server:1.1.2`**
(matter.js 0.17.4). Outcome: fabric 1 preserved (compressed id
`15731351337380687461`), all 8 nodes migrated via the legacy-data loader, FP300
(node 7) back online, HA Matter integration reconnected, FP300 entities live with
fresh data. All 9 office automations unaffected (same entity IDs).

Key gotchas captured for next time:
- The matter.js container runs **unprivileged (UID 1000)**; the old Python server
  ran as root, so the data files were root-owned. **`sudo chown -R 1000:1000
  /mnt/data/matter-server`** is required or the new server can't read the fabric.
- `container_name: matter-server` is pinned, so `docker compose up -d` after a
  `stop` hits a name conflict — must `docker rm -f matter-server` first, then `up`.
- Pin a version tag (not `:stable`) given Beta status. Backups taken first:
  `~/matter-server-backup-2026-06-26.tgz` (data volume) + compose/config backups.
- Future updates are a quick tag bump: edit image tag →
  `docker compose pull matter-server && docker rm -f matter-server && docker compose up -d matter-server`.

### Dashboard access (both, set up 2026-06-26)
- **Direct:** `http://192.168.0.111:5580` (HTTP 200) — Thread/Wi-Fi mesh
  visualization (node roles, link quality, border-router discovery via mDNS).
- **Inside HA:** a Lovelace dashboard **"Matter Network"** (url_path
  `matter-network`, admin-only, sidebar) with a single panel **iframe card** →
  `http://192.168.0.111:5580`. NOTE: YAML `panel_iframe` is **removed** in this HA
  version ("integration not found") — the iframe-card dashboard is the working
  method, created via the `lovelace/dashboards/create` + `lovelace/config/save` WS API.

---

## How the audit was done (for reproducing)

Three read-only vantage points, all already reachable on the LAN:

1. **Home Assistant WebSocket API** (`ws://192.168.0.111:8123`) — loaded
   integrations + `thread/list_datasets`.
2. **Matter server** (`ws://192.168.0.111:5580/ws`) — `get_nodes`, per-node
   reachability and radio type.
3. **LAN mDNS scan** — `_meshcop._udp` (every Thread Border Router, incl. Apple TV)
   and `_matter._tcp` (operational Matter nodes).

Requires `zeroconf`, `websockets`, `python-dotenv` (installed in `.venv`) and
`HA_TOKEN` / `PI_HOST` from `.env`.
