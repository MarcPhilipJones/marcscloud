# Plan — Official Tesla Fleet API climate control in Home Assistant

> **Status: ✅ COMPLETE & VERIFIED (2026-06-26).** The `tesla_fleet` integration is live
> with 88 entities for "Driveway Tesla Model Y"; `climate.driveway_tesla_model_y_climate`
> verified available (off, cabin 22 °C). Hosting key: GitHub Pages user site
> `marcphilipjones.github.io` (real HA public key). Setup gotchas hit & fixed: stale
> `e7064326` app credential, then a truncated 26-char client secret; leased car needed a
> physical key-card tap + on-screen Approve to pair the virtual key. Full detail in
> `/memories/repo/tesla-fleet-api.md`. Remaining optional: Octopus cheap-rate
> preconditioning automation.
> **Date:** 2026-06-26. Grounded in this repo's docs/memory (Tesla, HA, UniFi, network).

## 1. Why we're doing this

- The HACS **`tesla_custom`** integration is **dead for Marc's account**: Tesla shut down
  the legacy Owner API auth host (~10–12 Jun 2026). `tesla_custom` 3.26.3 still 403s
  (`UNKNOWN_ERROR_403`) even after a fresh token + full HA restart (see
  `/memories/repo/tesla-403.md`). The TLS-1.2-cap fix did not satisfy Tesla's gate for us.
- **TeslaMate v4.0.1** (self-hosted on the Pi) gives us *data* (44 `sensor.tesla_*`
  entities) because it adopted HTTP/2 + TLS 1.3. But TeslaMate is **read-only** — it
  cannot send commands (climate, defrost, charge control).
- To get **control** (climate on/off, defrost, set temp, charge limit) we must move to
  Tesla's **official Fleet API** via Home Assistant's built-in **`tesla_fleet`**
  integration (HA 2024.8+; we're on HA 2026.6.4). This is the supported long-term path.

## 2. What the official integration actually requires

The HA `tesla_fleet` integration (https://www.home-assistant.io/integrations/tesla_fleet/):

1. A **Tesla Developer application** → gives a **Client ID + Client Secret** (free).
2. A **public key file** served at
   `https://<your-domain>/.well-known/appspecific/com.tesla.3p.public-key.pem`
   over **valid HTTPS**. This is the part that trips everyone up.
3. **Command signing**: newer cars (all since late 2023) require signed commands.
   **HA signs them itself** — it auto-generates `config/tesla_fleet.key`, and you pair
   the matching public key to the car via `https://tesla.com/_ak/<your-domain>`.
   **No third-party command proxy is needed.**
4. OAuth redirect uses `https://my.home-assistant.io/redirect/oauth` (My HA is enabled
   by default) — works regardless of how you reach HA.

### Cost
- Tesla gives **$10/month free API credit** for personal use; the integration polls each
  awake vehicle every ~10 min specifically to stay inside that. Energy APIs are free.
- **Net recurring cost can be £0** (see §5 / §6).

## 3. Environment facts that change the generic advice

ChatGPT's generic guide is mostly right but **wrong/incomplete for this setup**:

- ❌ **"Use the NGINX Home Assistant SSL proxy add-on"** — we run **HA in Docker
  (Container), not HA OS**, so **add-ons do not exist**. The doc's "recommended" hosting
  path is unavailable. We must host the key another way (see §4).
- ⚠️ **Nabu Casa (Voice preview subscription)** gives a `*.ui.nabu.casa` URL, **but it is
  auth-gated** — you cannot serve an unauthenticated file at a fixed path, so it **cannot
  host the public key**. (It's fine for the OAuth redirect, but that already works via
  My HA.) **Verdict: doesn't help for hosting.**
- ✅ **WAN**: BT line, real public IPv4 `86.175.95.43`, UniFi Gateway Lite — port-forward
  is technically possible.
- ✅ **Dynamic DNS already configured** on the Gateway (No-IP): service `dyndns`, host
  **`marcjones.freedynamicdns.net`**, login `orders@marcjones.co.uk`. **But** a live A
  lookup did **not** cleanly return the WAN IP — No-IP free hosts need re-confirming every
  30 days, so treat it as **possibly stale**. Self-hosting also drags in dynamic-IP +
  cert renewal. Fragile.
- ✅ Marc appears to **own `marcjones.co.uk`** (it's the DDNS account login) — useful for
  the clean self-owned option.

## 4. Public-key hosting options (free), ranked for this setup

The key file is **static and public** and does **not** have to live on the Pi or share
HA's domain. So decouple it from HA entirely.

1. **Purpose-built free host — easiest, zero infra (recommended start)**
   - **MyTeslaMate "Fleet Tokens" (Free tier)** or **FleetKey.net** (both supported in HA
     docs). They host the key at the correct `.well-known` path with valid TLS. No domain,
     no port-forward, no cert, no dynamic-IP worry. Fastest route to a working climate
     entity. See §5 for the MyTeslaMate free-tier analysis.
2. **GitHub Pages — CHOSEN & IMPLEMENTED (free) ✅**
   - **Live and tested 2026-06-26.** Repo: `MarcPhilipJones/marcphilipjones.github.io`
     (public **user site** → serves from the domain root, which Tesla requires).
   - Key URL (returns **HTTP 200**, valid HTTPS):
     `https://marcphilipjones.github.io/.well-known/appspecific/com.tesla.3p.public-key.pem`
   - Empty **`.nojekyll`** committed so Jekyll doesn't drop the dot-folder (`.well-known`
     would otherwise 404). Local working copy: `C:\VSCODE_Developement\marcphilipjones.github.io`.
   - ⚠️ The published key is a **throwaway P-256 test key** — must be **replaced** with the
     real key HA generates during `tesla_fleet` setup (commit + push the new `.pem`).
   - Tesla app **Allowed Origin** = `https://marcphilipjones.github.io/`.
3. **Cloudflare Pages / Netlify / Vercel on `marcjones.co.uk` — equivalent free alternative**
   - Free static hosting, automatic HTTPS, serves `.well-known` dotfiles natively (no
     `.nojekyll` needed), custom domain. Pick this instead of GitHub Pages if preferred.
4. **Self-host on the Pi (Caddy container) — only if everything must be in-house**
   - Add a small Caddy container to `docker-compose.yml` serving `/.well-known/...` with
     auto Let's Encrypt, behind `marcjones.co.uk` DNS + forwarded 80/443. Most control,
     **most fragile**: depends on the stale No-IP DDNS, port-forwarding, and cert renewal.
     Avoid unless desired.

## 5. MyTeslaMate screenshot — what's free vs paid

| Box | Price | Needed? |
|---|---|---|
| **My TeslaMate Instance** (hosted Grafana/TeslaMate) | 3.75€/mo | **No** — we self-host TeslaMate v4.0.1 already. |
| **Fleet API & Telemetry** (secure proxy, "Send commands") | Pay as you go | **No** — HA signs commands locally; no proxy needed. |
| **Fleet Tokens** (Create Tesla App, Generate Tokens, evcc/HA) | **Free** ✅ | **Yes** — creates the dev app + hosts the public key for free. |

**Conclusion: the part Marc needs is FREE.** Only verify the free tier yields a public-key
URL usable by the HA-*native* integration (not just their proxy). If unsure, fall back to
the self-owned free route — own Tesla dev app + **GitHub Pages** (with `.nojekyll`) or
Cloudflare Pages — also £0.

## 6. Proposed end-to-end steps (to execute later, after sign-off)

1. **Create Tesla Developer app** at developer.tesla.com/request (Marc's Tesla account).
   - Grant type: **Authorization Code + Machine-to-Machine**.
   - Allowed Origin: **`https://marcphilipjones.github.io/`** (the chosen key host, §4 opt 2).
   - Redirect URI: `https://my.home-assistant.io/redirect/oauth`.
   - Scopes: Vehicle Information (req), Vehicle Location, **Vehicle Commands**.
   - Save **Client ID + Client Secret**.
2. **Host the public key** — ✅ **DONE (test key)** via GitHub Pages user site
   `marcphilipjones.github.io` (see §4 option 2). When HA shows the real key during setup,
   replace `.well-known/appspecific/com.tesla.3p.public-key.pem` in that repo and push.
3. **Add the `tesla_fleet` integration** in HA (Settings → Devices & Services → Add →
   Tesla Fleet): enter Client ID/Secret, sign in to Tesla, enter the hosting domain.
4. **Pair the virtual key** to the car: open `https://tesla.com/_ak/<your-domain>` on the
   iPhone (Safari) and approve in the Tesla app. Repeat per vehicle.
5. **Verify** the new `climate.*` entity appears and commands succeed.
6. **Decide coexistence**: keep TeslaMate (data/history) + `tesla_fleet` (control).
   Optionally remove the broken `tesla_custom` later — but note `/memories/repo/tesla-403.md`
   says Marc wants the 403 errors left visible until upstream fixes it, so don't remove
   `tesla_custom` without confirming.

## 7. Octopus / automation tie-in (already in place)

- `ha-config-backup/packages/tesla_octopus.yaml` already builds cheap-rate template
  sensors off `sensor.octopus_intelligent_go_price` and `sensor.tesla_charger_power`.
  Once `tesla_fleet` adds a controllable `climate.*` + charge entities, we can add the
  "precondition on cheap rate / before leaving work" automation ChatGPT suggested.

## 8. Open items needing Marc (cannot be done for him)

- Tesla sign-in / dev-app creation (his Tesla credentials + MFA).
- Confirm domain choice: MyTeslaMate free host vs own `marcjones.co.uk` (Cloudflare Pages).
- Virtual-key pairing on the iPhone.
- Confirm whether to retire `tesla_custom` or keep its 403 visible (current decision: keep).

## 9. Explicitly NOT in scope yet

- No code, config, container, port-forward, DNS, or HA change has been made.
- This file is a review artifact only.
