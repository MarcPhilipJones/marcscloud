# Creating HA Automations via REST API

The MCP server cannot create automations. Use the HA REST API instead.

## Endpoint

```
POST http://192.168.0.111:8123/api/config/automation/config/<automation_id>
```

- `<automation_id>` is a `snake_case` string (becomes `automation.<automation_id>` entity)
- Returns `{"result":"ok"}` on success (HTTP 200)
- Overwrites if the ID already exists — use unique descriptive IDs

## Automation JSON Structure

```json
{
  "alias": "Human-Readable Name",
  "description": "What this automation does",
  "mode": "single",
  "trigger": [
    {
      "platform": "state",
      "entity_id": "binary_sensor.xxx",
      "to": "on"
    },
    {
      "platform": "numeric_state",
      "entity_id": "sensor.xxx",
      "below": 200
    }
  ],
  "condition": [
    {
      "condition": "state",
      "entity_id": "binary_sensor.xxx",
      "state": "on"
    },
    {
      "condition": "numeric_state",
      "entity_id": "sensor.xxx",
      "below": 200
    }
  ],
  "action": [
    {
      "service": "light.turn_on",
      "target": { "entity_id": "light.xxx" }
    }
  ]
}
```

## After Creating — Reload

Always reload automations after creating/updating:

```powershell
Invoke-WebRequest -Uri "$baseUrl/api/services/automation/reload" -Headers $headers -Method Post -Body "{}" -UseBasicParsing
```

## Verification

Query all automation states to confirm they're registered and enabled:

```powershell
$states = Invoke-RestMethod -Uri "$baseUrl/api/states" -Headers $headers
$states | Where-Object { $_.entity_id -match "automation\." } | ForEach-Object {
    "$($_.entity_id) | state=$($_.state) | last_triggered=$($_.attributes.last_triggered)"
}
```

## Script Pattern

For reliability, write automation creation as a `.ps1` script in `scripts/`, run with output to `scripts/last-run.log`, then read the log. See `scripts/create_office_light_automations.ps1` as a reference implementation.

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Automation ID | `snake_case`, descriptive | `office_light_auto_on_occupied_low_light` |
| Alias (friendly name) | Title Case with context prefix | "Office Light Auto-On (Occupied + Low Light)" |
| Description | Full sentence explaining trigger logic | "Turn on office Tapo bulb when FP300 detects occupancy and illuminance is below 200 lux" |
