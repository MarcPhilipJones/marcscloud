# HA Entity Discovery Patterns

## Finding Entity IDs

HA entity IDs don't always follow predictable patterns. When the MCP `list_devices` tool doesn't cover a domain (e.g. `sensor`, `binary_sensor`), use the REST API.

### Bulk Discovery

```powershell
$states = Invoke-RestMethod -Uri "$baseUrl/api/states" -Headers $headers
$states | Where-Object { $_.entity_id -match "search_term" } | ForEach-Object {
    "$($_.entity_id) = $($_.state) ($($_.attributes.friendly_name))"
}
```

### Known Entity Naming Patterns

| Device | Entity Prefix | Example |
|--------|---------------|---------|
| Aqara FP300 | `*_presence_multi_sensor_fp300_*` | `binary_sensor.presence_multi_sensor_fp300_occupancy` |
| Tapo Bulb | `light.smart_multicolor_bulb` | Single entity |
| Tado Thermostat | `climate.*_tado_smart_x_*` | `climate.kitchen_tado_smart_x_smart_radiator_thermostat` |

### Common Gotchas
- Aqara devices use `presence_multi_sensor_fp300` not just `fp300` — the full device name is in the entity ID
- Don't assume `office_` prefix — HA uses the device name, not the room, as the entity ID base
- `mcp_homeassistant_get_history` returns empty `[]` for non-existent entities — useful as a quick existence probe but inefficient for discovery. Use REST API bulk query instead.

## Useful REST API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/states` | GET | All entity states — filter client-side |
| `/api/states/<entity_id>` | GET | Single entity state + attributes |
| `/api/config` | GET | HA version, location, unit system |
| `/api/services` | GET | All available service domains and methods |
| `/api/services/<domain>/<service>` | POST | Call a service (e.g. `light/turn_on`) |
| `/api/config/automation/config/<id>` | POST | Create/update automation |
| `/api/services/automation/reload` | POST | Reload automations after creation |
