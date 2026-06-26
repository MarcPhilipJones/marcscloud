# UniFi — Hardware, Versions & Access (grounding reference)

> **READ THIS FIRST for any UniFi request.** Every instruction, API call, or
> troubleshooting step must be grounded in the exact hardware and firmware
> versions below — UniFi UI paths and API endpoints change between versions, so
> generic advice is often wrong for this specific setup.
>
> **Last verified:** 2026-06-26 via `scripts/unifi_audit.py` (read-only).
> Re-run that script to refresh this data when firmware changes.
>
> **Overall status (2026-06-26): everything is working fine** — all 6 UniFi devices
> adopted/online, firmware current, cameras streaming into HA, no faults observed.

---

## Console / Controller

| Item | Value |
|---|---|
| Console model | **UniFi Cloud Key Gen2 Plus (UCK-G2-Plus)** |
| Console LAN IP | `192.168.0.180` (HTTPS, self-signed cert) |
| **UniFi OS version** | **5.1.19** (`console_display_version`) |
| Cloud Key firmware | `UCKP.apq8053.v5.1.19.3fbc1da.260613.1128` |
| **UniFi Network application** | **10.4.57** (build `atag_10.4.57_34628`) |
| Previous Network version | 10.3.58 |
| Site name (internal) | `default` — display name **"Main Jones"** |
| Cloud (UI.com) site | "Main Jones" |
| `is_cloud_console` | false (local UniFi OS console) |

> When giving UI navigation steps, assume **UniFi OS 5.1.19 + Network 10.4.57**.
> In this version, **admin accounts are managed in Site Manager → People**
> (unifi.ui.com), NOT inside the Network app settings sidebar.

---

## Adopted infrastructure devices (6)

| Name | Model | Type | Firmware | IP | Notes |
|---|---|---|---|---|---|
| Gateway Lite | **UXG** (UniFi Gateway Lite) | gateway | `5.0.16.30689` | WAN `86.175.95.43` | LAN gateway `192.168.0.1`; ISP **BT** |
| Switch | **US8P60** (USW-8-PoE-60W) | switch | `7.4.1.16850` | `192.168.0.2` | main PoE switch |
| USW Flex Mini | **USMINI** (USW-Flex-Mini) | switch | `2.1.6.762` | `192.168.0.229` | 5-port mini switch |
| Garage | **U7LT** (U7 Lite) | AP (WiFi 6) | `6.8.2.15592` | `192.168.0.5` | |
| Office In Wall | **U7IW** (U6/U7 In-Wall) | AP (WiFi 6) | `6.8.2.15592` | `192.168.0.4` | |
| Living Room Wifi 6 | **UAL6** (U6 Lite) | AP (WiFi 6) | `6.7.54.15663` | `192.168.0.137` | |

> All three APs broadcast a single SSID **"Hathai"** (WPA2, 2.4 + 5 GHz).
> Firmware families differ: U7 APs on 6.8.x, U6 Lite on 6.7.x — don't assume
> a single AP firmware when advising upgrades.

## Wi-Fi radios, mesh topology & TX power (verified 2026-06-26)

**Backhaul / uplink topology (critical):**
- **Garage U7LT = WIRELESS mesh child.** Its uplink is **wireless → Living Room AP**
  over **5 GHz**. Its 5 GHz channel/width are **locked to the parent** (greyed out in
  the UI: "controlled by uplink AP"). `Mesh Connect ✓`.
- **Living Room U6 Lite = wired** (US8P60 **port 7**) and is the Garage's **mesh parent**
  (`Mesh Parent ✓`).
- **Office In-Wall U7IW = wired** (US8P60 **port 8**, static IP).
- Switch US8P60 → Gateway on **port 1** (static IP); USW Flex Mini uplinks on **port 6**;
  Hikvision DVR on Flex Mini **port 5**.

**⚠️ Why all three 5 GHz radios share channel 44 — this is REQUIRED, not an error.**
Because the Garage uplinks wirelessly over 5 GHz, the mesh parent (Living Room) and the
child (Garage) MUST share the same 5 GHz channel/width. With Office also on 44 they all
align. **Do NOT "fix" this by giving each AP a different 5 GHz channel — that breaks the
Garage's wireless backhaul.** (An earlier health check flagged it as co-channel error;
that was a misdiagnosis before the mesh topology was known.)

**Current / recommended radio settings (they now match):**

| AP | Backhaul | 2.4 Width | 2.4 Ch | 2.4 TX | 5 Width | 5 Ch | 5 TX |
|---|---|---|---|---|---|---|---|
| Living Room (U6 Lite) | Wired (port 7) + **mesh parent** | 20 MHz | **1** | Medium | 80 MHz | **44** | **High** |
| Office In-Wall (U7IW) | Wired (port 8) | 20 MHz | **6** | Low | 80 MHz | **44** | Medium |
| Garage (U7LT) | **Wireless mesh child** | 20 MHz | **11** | High | 80 MHz | **44** *(locked by uplink)* | Auto |

- 2.4 GHz plan is clean **1 / 6 / 11** (LR/Office/Garage). Living Room is **pinned to ch1**
  (not Auto) so it can't drift. Min-RSSI off on all radios (intentional).
- Living Room 5 GHz = **High** to keep a strong wireless backhaul to the Garage.
- **To remove the 5 GHz shared-channel constraint:** run **Ethernet to the Garage AP**
  (convert it from wireless mesh to wired). Only then can the three 5 GHz radios use
  distinct channels (e.g. 36 / 100 / 149). Cabling job, not a settings change.

## Config / security sanity check (2026-06-26)

- ✅ All 6 devices adopted & online; firmware current (0 upgrades pending); 0 active alarms.
- ✅ WAN up (BT, 7 ms latency); DHCP ~37/205 leases; AP satisfaction 94–100%, switch 91%.
- ✅ 2.4 GHz channel plan 1/6/11; 5 GHz shared ch44 is correct (mesh, see above).
- ⚠️ **Security hardening opportunities (optional):** SSID "Hathai" is **WPA2-PSK only**
  (no WPA3, PMF disabled) — could move to WPA2/WPA3 transition + PMF=Optional (test IoT
  after). Single flat LAN, **no IoT VLAN** — cameras already isolated behind the DVR, so
  low risk; an IoT VLAN/SSID is a future project, not a fix.

## Network

| Item | Value |
|---|---|
| LAN subnet | `192.168.0.0/24` (single "Default" network, no VLANs) |
| Gateway (LAN) | `192.168.0.1` (Gateway Lite) |
| DHCP | Server on Gateway Lite (~37 leases of 205 in pool) |
| IPv6 | Not configured (IPv4-only LAN — see `docs/possible-unifi-updates-ipv6.md`) |
| WAN | **BT**, IPv4 `86.175.95.43`, no IPv6. **~1 Gbps down / 100 Mbps up** |
| Key static hosts | Raspberry Pi/HA `192.168.0.111`; Cloud Key `192.168.0.180` |

## Clients (snapshot 2026-06-26)

- **29 connected** — 6 wired, 23 wireless.
- Endpoints have **no firmware version** in UniFi (only infra devices do).
- Vendor mix: Apple ×4, Amazon ×4 (Echo), Nabu Casa (HA Voice/Green), TI/SPIDCOM
  (Zigbee/powerline), plus many MAC-randomised (`?` OUI) phones/IoT.

## Cameras & CCTV (verified 2026-06-26 via UniFi + Home Assistant)

### Recorder: Hikvision DVR (the "CCTV Netgear" device)
- **Model:** Hikvision-OEM **DVR-204Q** ("Embedded Net DVR"), 4-channel.
- **Serial:** `M10420250308CCWRFX3431707WCVU`.
- **LAN:** IP `192.168.0.144`, MAC `54:8c:81:1f:ca:67` (Hikvision OUI), **wired to
  USW Flex Mini, port 5**. UniFi fingerprint = security/NVR (`dev_cat 31`).
  Uptime 79 days, satisfaction 90. Web UI: `https://192.168.0.144`.
- **Recording disk:** internal SATA **HDD1 = OK** (`sensor.dvr_204q_..._1_hdd1`).
- This is a **DVR with 4 directly-attached cameras** (coax/IP into the DVR's own
  ports), NOT a UniFi-managed PoE setup. The **4 cameras have no presence on the
  `192.168.0.0/24` LAN** — UniFi can only ever see the DVR at `.144`. This is by
  design and is why a network scan shows 1 device, not 4 cameras.

### The 4 cameras (only visible via Home Assistant → `hikvision_next`)
HA integration **`hikvision_next` v1.1.1** (custom, github maciej-or/hikvision_next),
firmware up to date. Channels 1–4 main stream = `_101/_201/_301/_401`.

| Ch | Camera | HA area | Camera entity | Snapshot entity |
|---|---|---|---|---|
| 1 | **Front Garden** | Front Garden | `camera.dvr_204q_m104...wcvu_101` | `image.dvr_204q_..._101_snapshot` |
| 2 | **Driveway** | — | `camera.dvr_204q_..._201` | `image.dvr_204q_..._201_snapshot` |
| 3 | **Extension Roof** | — | `camera.dvr_204q_..._301` | `image.dvr_204q_..._301_snapshot` |
| 4 | **Back Garden** | — | `camera.dvr_204q_..._401` | `image.dvr_204q_..._401_snapshot` |

- **Event push:** the DVR posts alarms (motion etc.) to HA at
  **`http://192.168.0.111:8123/api/hikvision`** (sensors `..._alarm_server_*`).
- Other entities: `switch.dvr_204q_..._holiday_mode` (off),
  `update.hikvision_nvr_ip_camera_update` (installed v1.1.1 = latest).
- To enumerate per-camera model/resolution/firmware, use the DVR web UI at
  `https://192.168.0.144` (needs the DVR's own login — NOT the UniFi account).

### Ring devices (Wi-Fi, on the LAN)
| Device | IP | MAC | AP | Signal | Notes |
|---|---|---|---|---|---|
| Ring Video Doorbell | `192.168.0.216` | `c8:df:84:51:18:f6` | Garage (U7LT) | **-69 dBm (weakest)** | **battery-powered**; see note below |
| Ring Office Camera | `192.168.0.176` | `64:9a:63:50:d4:21` | Office In-Wall (U7IW) | -38 dBm (excellent) | satisfaction 98% |
| Ring Chime | `192.168.0.121` | `34:03:de:14:2e:41` | Living Room (U6 Lite) | -50 dBm (good) | accessory, not a camera |

> AP MAC map: `78:45:58:6b:7d:68`=Living Room U6 Lite, `f0:9f:c2:f3:13:0b`=Office
> U7IW, `fc:ec:da:37:3d:e2`=Garage U7LT.
>
> **Ring Doorbell note (2026-06-26):** it is **battery-powered** and the battery
> needs replacing frequently. Marc plans to convert it to a **wired trickle-charge**
> feed in future, which should keep it powered continuously and likely improve
> reliability (a constantly-powered doorbell holds Wi-Fi better than one that sleeps
> to save battery) — though the weak **-69 dBm** signal on the Garage AP is a separate
> factor; a closer AP/extender would help signal regardless of power.
>
> **Signal tuning (2026-06-26):** Garage AP 2.4 GHz TX power set **Auto → High**.
> Result: doorbell **roamed to the Living Room AP (U6 Lite), channel 1**, and
> **satisfaction rose 97% → 100%** (cleaner channel than the congested ch11 on
> Garage). Signal stayed **-69 dBm** from BOTH nearby APs — i.e. it's a **positional
> RF "void"** caused by two tiled toilet walls, NOT an AP/power problem, so a new AP
> would be overkill (it'd read -69 too). Only clearer line-of-sight would lift it.
> **Outstanding tidy-up:** Living Room AP is on ch1 and **Office In-Wall is also ch1**
> (co-channel clash) — set Office In-Wall 2.4 GHz to **channel 6** for proper 1/6/11.
> Current 2.4 GHz TX modes: Garage=High(ch11), Office In-Wall=Low(ch1), Living Room=Auto(ch1).
>
> **Update (2026-06-26):** Office In-Wall moved to **ch6** → 2.4 GHz plan now clean
> **Living Room ch1 / Office ch6 / Garage ch11** (proper 1/6/11). Doorbell stable on
> Living Room AP, satisfaction ~98–100%, signal fluctuates -69↔-73 dBm (normal outdoor).
> **Decision: do NOT pin the doorbell to the Living Room AP.** It already associates
> there voluntarily, pinning gives no signal gain (positional void), and it would
> remove auto-failover to the Garage AP if Living Room reboots — bad for a security
> device. Only pin if "ping-ponging" (rapid AP flapping / repeated brief offlines)
> appears; none observed. (Marc's laptop is wired Ethernet, unaffected by 2.4 changes.)
>
> **Doorbell client details (screenshot 2026-06-26):** UniFi *mis-identifies* the model
> as "Ring Video Doorbell Elite" — **CORRECTION: it is a Ring Video Doorbell 2,
> battery-only, NO Ethernet** (confirmed by Marc). Hostname `Ring-5118f6`,
> MAC `c8:df:84:51:18:f6`. Link: **WiFi 4 (802.11n), 1×1, ch1, 20 MHz**, signal
> **-71 dBm**, TX retries 0.0%, Rx 1.0 / Tx 65 Mbps, on Living Room AP (SSID Hathai).
> **AP/Client Signal Balance: Poor** (uplink weaker than downlink — typical of a small
> low-power battery client behind the tiled-wall void).
> **Implication for the future "wired" plan:** since it's a Doorbell 2 (no Ethernet
> port), the upgrade is a **wired trickle-charge / hardwired transformer feed** (8–24 V AC
> doorbell wiring), NOT PoE. That keeps it continuously powered (no battery swaps,
> radio stays awake) but it remains a **Wi-Fi** client, so the -71 dBm signal won't
> change — the tiled-wall void is positional. Decision today: change nothing.

### Camera → HomeKit → Apple TV flow
All cameras (4× DVR + Ring) stream into **Home Assistant** dashboards and are
bridged to **Apple HomeKit**; **HomeKit Secure Video** on the **Living Room Apple
TV hub** uploads recordings to iCloud (explains its ~27 GB/day upload — benign).

## Apple TV home hubs / HKSV upload


- **Two Apple TV 4Ks**: "Apple TV 4K" (Living Room, `192.168.0.228`) and
  "Marcs-Bedroom" (`192.168.0.190`). Both are HomeKit hubs + Thread border routers.
- The Living Room Apple TV is the **active HKSV hub** — it uploads camera footage to
  iCloud, hence its very high **upload** (e.g. ~194 GB tx over a 7-day session,
  ~27 GB/day). This is **expected/benign**, not an anomaly.
- **Bandwidth verdict (do not chase):** ~27 GB/day ≈ 2.5 Mbps average; worst-case all
  cameras uploading ≈ 15–25 Mbps. On the **1 Gbps / 100 Mbps** line this is well
  within headroom — leave it alone. (Marc confirmed not concerned, 2026-06-26.)

---

## Read-only access (for scripts / Copilot)

- **Local-only admin:** username `CopilotViewOnly`, role **View Only**
  (`"role":"readonly"` confirmed via `self/sites`), "Restrict to Local Access Only".
- Credentials live ONLY in git-ignored `.env`:
  `UNIFI_HOST=192.168.0.180`, `UNIFI_PORT=443`, `UNIFI_USERNAME`, `UNIFI_PASSWORD`,
  `UNIFI_SITE=default`, `UNIFI_VERIFY_SSL=false`.
- **Password is never stored in memory, chat, or any committed file.**
- Tooling: `scripts/unifi_audit.py` (Python 3.12 system interp at
  `C:/Users/marcjones/AppData/Local/Programs/Python/Python312/python.exe`;
  needs `requests`, `python-dotenv`, `rich`).
  - `python scripts/unifi_audit.py` → console + devices + clients + events table
  - `python scripts/unifi_audit.py --json` → machine-readable inventory (stdout)

## API access patterns — grounded in UniFi OS 5.1.19 / Network 10.4.57

UniFi OS proxies the Network app under `/proxy/network`. Auth is a POST to the
**OS** login, then Network API calls carry the session cookie (+ CSRF for POST).

**WORKS (GET unless noted):**
- Login: `POST https://192.168.0.180/api/auth/login` `{username,password}` → sets cookie + `x-csrf-token`
- Sites/role: `/proxy/network/api/s/default/stat/sysinfo`, `/proxy/network/api/self/sites`
- Devices (infra + firmware): `/proxy/network/api/s/default/stat/device`
- Clients: `/proxy/network/api/s/default/stat/sta`
- Health: `/proxy/network/api/s/default/stat/health`
- Alarms: `/proxy/network/api/s/default/list/alarm`
- Logout: `POST /api/auth/logout`

**DOES NOT WORK on this version / readonly role (all return 404):**
- `/proxy/network/api/s/default/stat/event` (GET and POST) — the classic events endpoint
- `/proxy/network/api/s/default/stat/alarm` (POST)
- `/proxy/network/v2/api/site/default/system-log` (Tomcat 404 — route absent)

**Consequence:** the **admin-login audit log** (source IP behind
"admin accessed UniFi Network" alerts) is **not retrievable** via the Network
API here. It's a UniFi OS-level activity log — read it in the UI under
**System Log / Activity**, or investigate an OS-level endpoint (would likely need
a higher-priv account, which conflicts with the read-only principle).

---

## Known incident — 2026-06-26 "admin accessed UniFi" alert

Benign. HA's UniFi integration re-authenticated (using the `admin` account) after
a ~4 min controller service blip: all UniFi entities went unavailable 02:45→02:50
UTC (3:45→3:50 BST — matches the alert). Cloud Key uptime intact since Jun 20 (no
reboot), WAN/public IP unchanged, no new device joined. The dedicated
`CopilotViewOnly` account now separates automation logins from real human logins.

## HA-side UniFi telemetry (no UniFi creds needed)

HA's UniFi integration exposes `device_tracker.*`, `sensor.gateway_lite_*`,
`sensor.uck_g2_plus_*`. It does NOT expose the controller audit log.

---

## Rule for future UniFi instructions

1. **Start from this file.** Confirm the version/model before answering.
2. Tailor UI navigation to **UniFi OS 5.1.19 + Network 10.4.57** (admins live in
   Site Manager → People).
3. Tailor API calls to the WORKS/DOESN'T-WORK lists above; don't suggest `stat/event`.
4. Prefer the read-only `CopilotViewOnly` account; never escalate privileges
   without explicitly flagging the security trade-off.
5. If firmware has changed since "Last verified", re-run `scripts/unifi_audit.py`
   and update this file before giving version-specific advice.
6. **Don't trust UniFi's device-model fingerprints — they can be wrong.** Confirmed
   2026-06-26: UniFi labelled the doorbell "Ring Video Doorbell Elite", but it is
   actually a **Ring Video Doorbell 2** (battery-only, no Ethernet) per the user.
   Always treat UniFi `Model`/OUI guesses as approximate and confirm with the user
   before acting on model-specific advice (e.g. PoE vs battery, wiring options).
7. **Check mesh/uplink topology BEFORE advising on 5 GHz channels.** The Garage AP is
   a **wireless mesh child** of Living Room — so all 5 GHz radios MUST share ch44.
   Never recommend splitting 5 GHz channels while an AP is wirelessly meshed; it breaks
   the backhaul. (Lesson: a "co-channel error" can actually be a required mesh constraint.)
