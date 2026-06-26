# Known Issues & Limitations

## Office Lighting

- **Single bulb insufficient**: The Tapo Multicolour Bulb (`light.smart_multicolor_bulb`) at max brightness (255) and 5000K produces ~178 lux. The recommended office illuminance is 300–500 lux. Supplemental lighting is needed.
- **FP300 illuminance fluctuation**: The FP300 sensor (`sensor.presence_multi_sensor_fp300_illuminance`) reads between 130–520 lux in practice. Automation thresholds (200 lux on, auto-off on vacancy) should account for this range.
- **No hysteresis on light automation**: The current `office_light_auto_on_occupied_low_light` automation triggers below 200 lux with no offset for off. At the boundary, the light turning on raises lux above 200, which won't retrigger, but natural light changes near the threshold could cause rapid toggling. Consider adding a higher off-threshold (e.g., 250 lux) if flickering is observed.

## Tesla Integration (HA 2026.3.2)

- **Entity renames**: All Tesla entities changed from `tesla_*` to `tesla_model_y_*` after the 2026.3.2 upgrade. Scripts and dashboards in `ha-config-backup/` have been updated to reflect this.
- **Sentry mode removed**: `switch.tesla_model_y_sentry_mode` no longer exists in the Tesla integration. It has been removed from dashboards.
- **`tesla_custom.api`**: The `navigate_tesla_to_ets_tutoring` script uses the custom Tesla API integration. Entity references have been updated but the `tesla_custom.api` service call may need separate verification.

## Tado X Thermostats

- Tado X hardware uses **Matter integration** only — the native HA Tado integration does NOT work with Tado X.
- Tado integration log errors (device activation / Bad Request) are expected noise. Consider removing the Tado integration entirely if only using Matter.
- Thermostat entity names changed in 2026.3.2 from generic (`smart_radiator_thermostat_x_temperature`) to room-specific (`kitchen_tado_smart_x_smart_radiator_thermostat_temperature`). Dashboards already use the new names.

## Tapo Smart Plug Sensors

- Energy consumption entities renamed in 2026.3.2: `sensor.living_room_tapo_smart_plug_1_*` → `sensor.living_room_plug_cost_*` (daily/weekly/monthly/yearly/total).
- Old entity `sensor.living_room_tapo_smart_plug_1_this_month_s_consumption` no longer exists. Dashboard has been updated to `sensor.living_room_plug_cost_monthly`.

## MCP Server

- The HA MCP server (`@jango-blockchained/homeassistant-mcp`) is **disabled** due to crashes (exit code 3221226505) and "Entity not found" errors on parameterized commands.
- `get_history` returns limited data (1 day) vs REST API (full recorder range).
- Re-enable in `.vscode/mcp.json` if a stable version becomes available.

## Pi Health Monitoring

- Command-line sensors (`sensor.pi_cpu_temperature`, `sensor.pi_memory_used_percent`, etc.) run shell commands inside the HA Docker container. Since the container uses `network_mode: host` and mounts `/run/dbus`, most host metrics are accessible. If a sensor shows unexpected values, verify the container can access the relevant `/proc` or `/sys` path.
- `sensor.pi_cpu_usage` parses `top -bn1` output, which can vary across Linux versions. If the value is always 0, check the `top` output format on the Pi.

## SSH Client

- The Python SSH client now tries key-based auth (`~/.ssh/id_rsa`) first and falls back to password. If neither works, connection fails with a clear error.
- `PI_PASSWORD` is no longer required in `.env` if SSH key auth is configured (it is — see `~/.ssh/config`).

## Docker Services

- **No auth on web UIs**: Portainer (9000), Heimdall (8200), and Changedetection (5000) are accessible without authentication from the LAN. Consider adding a reverse proxy with basic auth if the network is shared.
- **Watchtower**: Configured with label-based opt-in. No containers currently have the opt-in label, so all updates are manual. HA is explicitly excluded.
