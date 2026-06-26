# Copilot Instructions — Raspberry Pi Home Lab

## Project Overview

This project manages a **Raspberry Pi 5** home lab running **Home Assistant** and various services. It includes:

- A Python SSH client (`src/raspberry_pi/`) for remote Pi management (commands, file transfer, Docker control)
- Automation scripts (`scripts/`) for Pi setup and configuration
- Home Assistant automation management via API

## Infrastructure

| Component | Address | Notes |
|-----------|---------|-------|
| Raspberry Pi 5 | `192.168.0.111` | SSH user: `admin`, port 22 |
| Home Assistant | `http://192.168.0.111:8123` | Running on the Pi |
| HA MCP Extension | VS Code `homeassistant-mcp` | Limited; falls back to REST API |
| UniFi Cloud Key Gen2+ | `192.168.0.180` | UniFi OS 5.1.19 / Network 10.4.57 — see below |

## UniFi — ALWAYS ground in `docs/unifi.md`

For ANY UniFi/network request (UI steps, API calls, firmware, troubleshooting),
**read [`docs/unifi.md`](../docs/unifi.md) FIRST** and tailor every instruction to
the exact hardware and firmware recorded there (UniFi OS **5.1.19**, Network app
**10.4.57**, Gateway Lite/UXG, US8P60 + USW-Flex-Mini switches, U7LT/U7IW/U6Lite APs).
Generic UniFi advice is frequently wrong for this version — do not give version- or
path-specific guidance that contradicts that file.

- Read-only access account `CopilotViewOnly` (View Only, local-only); creds in git-ignored `.env`.
- Read live data with `python scripts/unifi_audit.py` (`--json` for raw inventory).
- Known limitation: the admin-login **audit log is not retrievable** via the Network
  API on this version (`stat/event`/v2 `system-log` 404). Read it in the UI System Log.
- If firmware has changed, re-run the script and update `docs/unifi.md` before advising.


## Home Assistant — Key Entities

### Office Devices
| Entity | Type | Description |
|--------|------|-------------|
| `light.smart_multicolor_bulb` | Light | Tapo Multicolour Bulb (office) — supports color_temp, hs, xy |
| `binary_sensor.presence_multi_sensor_fp300_occupancy` | Binary Sensor | Aqara FP300 presence/occupancy |
| `sensor.presence_multi_sensor_fp300_illuminance` | Sensor | FP300 light level (lux) |
| `sensor.presence_multi_sensor_fp300_temperature` | Sensor | FP300 temperature |
| `sensor.presence_multi_sensor_fp300_humidity` | Sensor | FP300 humidity |
| `sensor.presence_multi_sensor_fp300_battery` | Sensor | FP300 battery level |
| `number.presence_multi_sensor_fp300_hold_time` | Number | FP300 occupancy hold time (seconds) |
| `select.presence_multi_sensor_fp300_sensitivity` | Select | FP300 detection sensitivity |
| `light.office_in_wall_led` | Light | Office in-wall switch LED |

### Other Devices
| Entity | Type | Description |
|--------|------|-------------|
| `light.gateway_lite_led` | Light | Gateway LED indicator |
| `light.garage_led` | Light | Garage LED |
| `light.living_room_wifi_6_led` | Light | Living room router LED |
| `light.switch_led` | Light | Switch LED |

## Implementation Priority for HA Operations

Always attempt in this order:
1. **MCP Server** (`mcp_homeassistant_*` tools) — fastest when it works
2. **HA REST API** — reliable fallback; use long-lived access token
3. **SSH to Pi** — last resort for direct file edits or service restarts

## HA REST API Access Pattern

```powershell
$token = "<HA_LONG_LIVED_TOKEN>"  # Stored in VS Code settings
$baseUrl = "http://192.168.0.111:8123"
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type"  = "application/json"
}
```

The token is configured in VS Code setting `homeassistant-mcp.url`. The long-lived access token is provided at runtime — never hardcode it in committed files.

## Conventions

- **Scripts**: Write `.ps1` scripts to `scripts/`, run with output redirected to `scripts/last-run.log`, then read the log to verify results
- **Python**: 3.11+, uses `paramiko` for SSH, `rich` for terminal output, `python-dotenv` for config
- **Automations**: Created via HA REST API at `POST /api/config/automation/config/<snake_case_id>`
- **Naming**: Automation IDs use `snake_case`, friendly names use Title Case with context prefix (e.g. "Office Light Auto-On")
