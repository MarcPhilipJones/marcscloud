# Possible UniFi Updates — IPv6 (Deferred)

**Status:** Not implemented (May 12, 2026). Apple Home / Thread / Matter / Home Assistant all working fine with current IPv4-only LAN config. Recorded for future reference if issues arise.

> **Future Copilot reminder:** If Marc reports problems with Apple Home commissioning, Matter device discovery, Thread reliability, HomePod/Apple TV responsiveness, cross-VLAN mDNS discovery, or Home Assistant Matter integration on the Pi — **consider whether enabling IPv6 on the LAN (per this doc) would help** before chasing other causes.

---

## Context

- **Setup:** Apple TV 4K as primary HomeKit hub + Thread Border Router, Apple Home over Thread/Matter as main automation, Amazon Alexa secondary, Raspberry Pi 5 (`192.168.0.111`) running Home Assistant.
- **Source:** YouTube "expert" recommended enabling IPv6 in UniFi for better Matter/Thread reliability.
- **Decision:** Defer. Everything works today; revisit only if symptoms below appear.

## Proposed UniFi LAN IPv6 settings (from screenshot)

| Setting | Value |
|---|---|
| Interface Type | Static |
| IPv6 Address | `fd00:1::1` |
| Netmask | `/64` |
| Client Address Assignment | SLAAC |
| Auto DNS Server | ✅ |
| Router Advertisement (RA) | ✅ |
| RA Priority | High |
| Additional IPs | ❌ |

### What each does (short)

- **Static ULA `fd00:1::1/64`** — Unique Local Address, IPv6 equivalent of `192.168.x.x`. Internal-only, never internet-routable. Survives ISP prefix changes.
- **SLAAC** — Devices auto-generate their own IPv6. **Required for Apple devices and Matter accessories** (DHCPv6 is poorly supported by Apple/IoT).
- **Auto DNS** — Router advertises DNS via RDNSS in RAs. Needed for IPv6-only name resolution.
- **RA enabled** — Mandatory for SLAAC to function. Tells clients the prefix, gateway, DNS.
- **RA Priority High** — Preferred default IPv6 gateway when multiple routers exist. Single-router home: harmless.

## Why IPv6 *might* help Apple Home / Thread / Matter

1. **Matter-over-Wi-Fi requires IPv6** per spec. Today it works because link-local `fe80::/10` is always on per-interface, but a routable ULA improves commissioning and cross-VLAN discovery reliability.
2. **Thread is IPv6-only internally.** Apple TV / HomePod border routers bridge Thread ↔ Wi-Fi using IPv6 + SRP/mDNS. A proper LAN IPv6 prefix avoids NAT/translation hacks.
3. **Home Assistant Matter integration** on the Pi discovers/talks to Matter devices over IPv6. Critical if HA is ever moved to a separate VLAN from Apple TV/Thread devices.
4. **Alexa unaffected** — Echo is IPv4 + cloud-routed.

## What to also do *if* enabling later

- ➕ Enable **WAN IPv6 (Prefix Delegation)** if ISP supports it — gives global IPv6 alongside the ULA for cleanest Matter/Thread operation.
- ➕ Enable **mDNS reflector** on every VLAN with Apple TV / HomePods / HA / Matter devices (Settings → Networks → Advanced → Multicast DNS). IPv6 alone does NOT fix cross-VLAN discovery.
- ➕ Audit IPv6 firewall rules (LAN-IN / LAN-LOCAL) — ensure UDP 5353 mDNS and MLDv2 multicast flow for Thread border routers.
- ➕ Consider regenerating the ULA to a random RFC 4193 `/48` (e.g. `fd9a:b3c2:7e44::/48`) to avoid collisions if a site-to-site VPN is ever added. Cosmetic only.
- ⚠️ **iOS privacy extensions** rotate device IPv6 addresses. Don't key firewall rules / HA automations on IPv6 — use MAC reservations or hostnames.

## Symptoms that should trigger revisiting this

- Matter accessory commissioning fails or is flaky from the iPhone Home app
- Apple TV / HomePod loses sight of Thread devices after power cuts
- Home Assistant Matter integration can't discover or loses connection to Thread-backed accessories
- Cross-VLAN device discovery breaks after a network segmentation change
- HomeKit "No Response" tiles for Thread devices despite the device being reachable on the mesh

## Symptoms NOT related to IPv6 (don't blame this)

- Alexa routine failures
- Cloud-only integrations (Tesla, Tapo cloud, etc.)
- Wi-Fi signal / roaming issues
- Zigbee (FP300, etc.) — separate radio, IP irrelevant

---

**Re-evaluate:** If any of the trigger symptoms above appear, revisit this doc and consider applying the settings as a diagnostic step.
