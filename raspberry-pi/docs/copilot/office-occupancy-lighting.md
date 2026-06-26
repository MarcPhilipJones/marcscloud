# Office Occupancy & Lighting Setup

## Current Configuration (as of March 2026)

### Hardware
- **Light**: Tapo Multicolour Bulb (`light.smart_multicolor_bulb`) — supports color_temp (2500–6535K), hs, xy
- **Sensor**: Aqara FP300 Presence Multi-Sensor — occupancy, illuminance (lux), temperature, humidity, battery
- **Default light settings**: 80% brightness (~204/255), 4000K neutral white, color_temp mode

### FP300 Sensor Configuration
| Setting | Value |
|---------|-------|
| Hold time | 30 seconds |
| Sensitivity | standard |
| Battery | CR2450 |

### Active Automations

**New occupancy-based (created this session):**
| Automation | ID | Trigger | Conditions | Action |
|---|---|---|---|---|
| Office Light Auto-On | `office_light_auto_on_occupied_low_light` | Occupancy → on OR illuminance < 200 | Occupied AND < 200 lux | Turn on bulb |
| Office Light Auto-Off | `office_light_auto_off_no_occupancy` | Occupancy → off | None | Turn off bulb |

**Pre-existing (kept intact):**
| Automation | Last Triggered |
|---|---|
| Office Morning Arrival - Power On | 2026-03-12 07:53 |
| Office Evening Auto-Off | 2026-02-23 18:56 |
| Office Hard Safety Cutoff (20:00) | 2026-03-11 20:00 |
| Office Welcome Back | 2026-03-11 16:52 |
| Office Light Getting Low | 2026-03-11 16:16 |
| Office Low Light Warning | 2026-03-10 16:41 |
| Bilresa Button 1 - Say Button 1 Pressed | 2026-03-12 09:54 |
| Bilresa Button 2 - Say Button 2 Pressed | 2026-03-12 09:57 |

### Design Decisions
- **Lux threshold**: 200 lux — below this triggers auto-on
- **Auto-on uses dual trigger + dual condition pattern**: Either occupancy or lux change can fire it, but both must be satisfied. This handles the case where you're already seated and light fades, or you walk into an already-dark room.
- **Auto-off has no conditions**: Occupancy off = turn off, unconditionally
- **Existing automations preserved**: No conflicts identified — existing automations cover different scenarios (morning arrival, evening cutoff, low-light warnings)
