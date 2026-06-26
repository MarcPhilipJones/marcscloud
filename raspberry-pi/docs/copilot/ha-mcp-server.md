# Home Assistant MCP — Three-Tier Strategy

As of HA 2025.2 there are **two official MCP integrations** plus a much richer
**community server**. Use them in this order.

## Tier 1 — Official `mcp_server` (PRIMARY)

- HA core integration (`mcp_server`), Streamable HTTP at `http://192.168.0.111:8123/api/mcp`
- Tools = whatever is exposed via Settings → Voice assistants → Expose entities
  (see [scripts/expose_entities_to_assist.py](../../scripts/expose_entities_to_assist.py))
- Configured in [.vscode/mcp.json](../../.vscode/mcp.json) as server `homeassistant`
- **Use first** for: state queries, on/off/brightness/colour, scene activation,
  climate set-point — anything covered by the Assist API
- Strengths: in-process (stable), OAuth/LLAT auth, per-entity allowlist
- Limits: only Assist intents — no automation CRUD, no service-call escape hatch

## Tier 2 — Community `voska/hass-mcp` (FALLBACK)

- Source: <https://github.com/voska/hass-mcp> (MIT, Python, ~300 stars)
- Configured in [.vscode/mcp.json](../../.vscode/mcp.json) as server `ha-mcp` (stdio via `uvx hass-mcp`)
- **Use only when Tier 1 lacks the capability.** Tools available:
  - `call_service_tool` — call ANY HA service (escape hatch)
  - `restart_ha`
  - `get_error_log`
  - `list_automations`, `entity_action`
  - `get_history` (richer than the Assist context snapshot)
  - `search_entities_tool`, `domain_summary_tool`, `list_entities`
  - Guided prompts: `create_automation`, `debug_automation`, `automation_health_check`,
    `routine_optimizer`, `dashboard_layout_generator`, `entity_naming_consistency`
  - Resources: `hass://entities/...`
- Strengths: full HA REST surface, rich prompts
- Limits: third-party, sees ALL entities (no exposure allowlist), token used as plain bearer

## Tier 3 — REST API / SSH (LAST RESORT)

- REST API for things neither MCP server handles cleanly (e.g. creating automations
  via `POST /api/config/automation/config/<id>`, dashboard storage edits)
- SSH for direct file edits and Docker service restarts

## Decision flow

```
Read state / toggle an exposed entity?                      → Tier 1
call_service / restart / error log / history / automations? → Tier 2
Create/edit automations or dashboard files?                 → Tier 3 (REST)
Edit /config/*.yaml or restart Docker containers?           → Tier 3 (SSH)
```

## Other community servers (not currently configured)

- `@jango-blockchained/homeassistant-mcp` — previously used, removed May 2026
  (crashed with exit code `3221226505`, "Entity not found" errors).
- `tevonsb/homeassistant-mcp` and forks — superseded by voska's server.

## Tip — entity naming

Aqara FP300 entities follow `*_presence_multi_sensor_fp300_*` (not `fp300_*` or
`office_*`). When in doubt, ask the `ha-mcp` `search_entities_tool`.
