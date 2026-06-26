---
name: unifi-network-admin
description: Read-first UniFi Network administration for THIS home lab (Cloud Key G2+, UniFi OS 5.1.19, Network 10.4.57). Use when the user asks to query/audit UniFi devices, clients, Wi-Fi, ports, firewall, or wants to add a UniFi MCP server or "device finder" style lookups. Distilled from public UniFi MCP projects + verified against the live console.
---

# UniFi Network Admin (this home lab)

> **ALWAYS read [`../../../docs/unifi.md`](../../../docs/unifi.md) FIRST.** It is the single
> source of truth for hardware, firmware, IPs, mesh topology, and the read-only account.
> Generic UniFi advice is frequently wrong for **UniFi OS 5.1.19 / Network 10.4.57**.

## What applies here vs. what to ignore

This lab has **UniFi Network only** — there is **no UniFi Protect** (cameras are a Hikvision
DVR via HA) and **no UniFi Access** (no door hardware). So:

- ✅ Relevant: Network health, client/device inventory, Wi-Fi/radio, switch ports, firewall.
- ❌ Ignore: any Protect server, "Security Digest", or "UniFi Access" tooling/skills — dead weight.

## Auth models on this console (verified 2026-06-26, read-only probe)

There are **four distinct auth artifacts** on this network — do not conflate them:

| Artifact | Used by | Talks to | Type |
|---|---|---|---|
| Local UniFi account (HA's) | Home Assistant `unifi` integration | UniFi controller | username/password |
| `CopilotViewOnly` local account | `scripts/unifi_audit.py` | UniFi controller | username/password (View Only) |
| HA long-lived access token | repo scripts, HA MCP | **Home Assistant** itself | bearer token |
| Local UniFi **API key** *(not yet created)* | a UniFi MCP server, if added | UniFi controller | `X-API-KEY` |

- **HA → UniFi uses username/password, NOT an API key** (SSO cloud users don't work; uses
  `aiounifi` + WebSocket local push). Source: HA UniFi docs (see References).
- The local **Network Integration API IS present + enabled** here: probe of
  `/proxy/network/integration/v1/sites` returned **401 (not 404)**, and `/unifi-api/network`
  returned **200**. So API-key servers can authenticate once a key is minted.
- **Mint a key (read-only posture):** Network app → **Settings → Control Plane → Integrations
  → Create API Key**; scope it to a **View-Only** admin. Keep creds in git-ignored `.env` only.

## Implementation priority (read-first, lowest-risk-first)

1. **`scripts/unifi_audit.py`** (existing, read-only) — preferred for inventory/health/clients.
   Auth: POST `/api/auth/login`; Network API proxied under `/proxy/network/api/s/default/...`.
   - **`scripts/unifi_device_finder.py`** (read-only) — "where is X?" lookups. Resolves AP name
     for wireless and **switch + port** for wired. `python scripts/unifi_device_finder.py <name|ip|mac>`
     (no arg = list all LIVE clients; `--json` for machine-readable). Add **`--offline`** to search the
     known-client DB (`rest/user`) incl. currently-disconnected devices, showing where each was *last
     seen* + how long ago. Reuses `unifi_audit.UniFiClient`.
2. **HA UniFi telemetry** — device_trackers + `gateway_lite_*` / `uck_g2_plus_*` sensors,
   no UniFi creds needed (but HA does NOT expose the controller audit/security log).
3. **A UniFi MCP server** — only if natural-language ops are wanted. See selection table below.
   Default to a **View-Only** account/key so writes fail by design.

## Known endpoint gotchas on Network 10.4.57 (verified)

- Admin-login **audit log is NOT retrievable** via the Network API for a readonly role:
  `stat/event` and v2 `system-log` return 404; `list/alarm` works but returns 0. Read the
  source IP of admin logins in the **UI System Log** instead.
- The **5 GHz shared channel 44** across all three APs is **required** (Garage is a wireless
  mesh child of Living Room). Do NOT "fix" it. See `docs/unifi.md`.

## Choosing a UniFi MCP server (re-rated for THIS lab)

Generic "10/10" ratings assume Protect+Access; here only the **Network** piece matters.

| Project | Auth | Works here? | Notes |
|---|---|---|---|
| **enuno/unifi-mcp-server** | local API key | ✅ (Network 9.x+, key present) | Has `UNIFI_PROFILE=read-only`/`minimal` → best read-only fit |
| **sirkirby/unifi-mcp** (Network only) | local user/pass *or* exp. key | ✅ (same auth as HA) | Most actively maintained; install ONLY the `unifi-network` plugin |
| **pproenca/unifi-mcp** | local API key | ✅ (Network 10.x+) | Lightweight (31 tools, `npx`), but v0.1.0 / 1 author — least proven |
| ~~jmagar/unifi-mcp~~ | — | ❌ does not exist (404) | AI-overview hallucination; ignore |

All three support a **preview-then-confirm** model for writes. To preserve the read-only
guarantee, point them at a View-Only account/key and expect mutations to fail.

## Safety rules

- Read freely; **never mutate** UniFi config without explicit user confirmation.
- Never print or commit UniFi credentials/keys. `.env` only; `.env.example` has placeholders.
- If firmware changed, re-run `scripts/unifi_audit.py` and update `docs/unifi.md` before advising.

## References (where this knowledge came from)

- **Canonical local truth:** [`docs/unifi.md`](../../../docs/unifi.md); repo memory `unifi-access.md`.
- **Local scripts:** `scripts/unifi_audit.py` (audit/health), `scripts/unifi_device_finder.py` (where-is-X).
- **Live probe (2026-06-26):** local login + `GET /proxy/network/integration/v1/sites` → 401,
  `/unifi-api/network` → 200 (recorded in repo memory).
- **sirkirby/unifi-mcp** — https://github.com/sirkirby/unifi-mcp (Network/Protect/Access split,
  agent skills, local user/pass auth, preview-then-confirm).
- **enuno/unifi-mcp-server** — https://github.com/enuno/unifi-mcp-server (`UNIFI_PROFILE`
  scopes incl. `read-only`; API-key auth; `UNIFI_API_TYPE=local`).
- **pproenca/unifi-mcp** — https://github.com/pproenca/unifi-mcp (lightweight, `npx`, API key).
- **HA UniFi integration** — https://www.home-assistant.io/integrations/unifi/ (local user, no API key).
- **UniFi Site Manager API (cloud, read-only)** — https://developer.ui.com/site-manager-api/
  (distinct from the LOCAL integration API used above).
