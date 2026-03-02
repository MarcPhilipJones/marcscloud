# Personal - Raspberry Pi & Home Assistant Workspace

This workspace is for Raspberry Pi and Home Assistant development projects.

## Infrastructure Overview

### Raspberry Pi 5
- **IP Address:** 192.168.0.111
- **SSH Alias:** `pi5` (passwordless SSH configured)
- **User:** admin
- **Model:** Raspberry Pi 5 Model B Rev 1.0
- **CPU:** ARM Cortex-A76, 4 cores @ 2.4 GHz
- **RAM:** 8 GB
- **Storage:** 29 GB SD card
- **OS:** Debian 12 (Bookworm)

### Home Assistant
- **URL:** http://192.168.0.111:8123
- **Version:** 2026.1.3
- **Runs in:** Docker container (managed via Portainer)
- **Config Path:** `/home/admin/homeassistant`
- **Network Mode:** Host
- **Database:** SQLite (~95 MB)
- **Custom Components:** HACS, hikvision_next, tesla_custom

### Docker Containers on Pi (via Portainer)
| Container | Port | Purpose |
|-----------|------|---------|
| homeassistant | 8123 | Home automation |
| portainer | 9000 | Container management |
| matter-server | - | Matter/Thread support |
| homebridge | - | Apple HomeKit bridge |
| scrypted | - | Camera/NVR management |
| heimdall | 8201 | Dashboard |
| watchtower | - | Auto-updates |

### Data Paths on Pi
- Home Assistant: `/home/admin/homeassistant`
- Homebridge: `/home/admin/homebridge`
- Matter Server: `/mnt/data/matter-server`

## Project Focus

- **Raspberry Pi** - GPIO, sensors, IoT projects
- **Home Assistant** - Custom integrations, automations, scripts

## Development

- Python 3.10+
- Libraries: RPi.GPIO, gpiozero, homeassistant
- Home Assistant API token stored in `.env` files

## Structure

- `raspberry_pi/RaspberryPi5/` - Pi 5 specific projects
- `home_assistant/HomeAssistant/` - HA API client and tools
- `scripts/` - Utility scripts

## Quick Access

```bash
# SSH to Pi
ssh pi5

# Portainer UI
http://192.168.0.111:9000

# Home Assistant UI
http://192.168.0.111:8123
```

## Getting Started

1. Activate virtual environment: `.venv\Scripts\Activate.ps1`
2. Install dependencies: `pip install -r requirements.txt`
3. Run scripts with the Python interpreter
