# Marc Home Assistant

A Python project for connecting to Home Assistant running on Raspberry Pi 5 (via Portainer).

## Overview

This project provides a Python client to interact with your Home Assistant instance, enabling automation, monitoring, and control of your smart home devices.

## Setup

### Prerequisites

- Python 3.11 or higher
- Home Assistant running on Raspberry Pi 5 (Portainer)
- Home Assistant Long-Lived Access Token

### Getting Your Home Assistant Token

1. Open Home Assistant web UI
2. Click on your profile (bottom left)
3. Scroll down to "Long-Lived Access Tokens"
4. Click "Create Token"
5. Give it a name (e.g., "Marc Home Assistant Python")
6. Copy the token immediately (you won't see it again!)

### Installation

1. Create a virtual environment:
   ```powershell
   cd marc-home-assistant
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. Install the package in development mode:
   ```powershell
   pip install -e .
   ```

3. Copy the example environment file and configure:
   ```powershell
   copy .env.example .env
   ```

4. Edit `.env` with your Home Assistant details:
   - `HOME_ASSISTANT_URL`: Your HA URL (e.g., `http://192.168.1.100:8123`)
   - `HOME_ASSISTANT_TOKEN`: Your long-lived access token

## Usage

### Command Line

```powershell
# Run the CLI
python -m marc_home_assistant

# List all entities
python -m marc_home_assistant --list

# Get state of a specific entity
python -m marc_home_assistant --entity light.living_room

# Call a service
python -m marc_home_assistant --service light.turn_on --entity light.living_room
```

### As a Module

```python
from marc_home_assistant import HomeAssistantClient

# Create client
client = HomeAssistantClient()

# Get all states
states = client.get_states()

# Get specific entity state
light = client.get_state("light.living_room")
print(f"Light is {light.state}")

# Turn on a light
client.call_service("light", "turn_on", entity_id="light.living_room")

# Turn off with brightness
client.call_service("light", "turn_on", entity_id="light.living_room", brightness=128)
```

## Project Structure

```
marc-home-assistant/
├── pyproject.toml              # Project configuration
├── README.md                   # This file
├── .env.example                # Example environment configuration
└── src/
    └── marc_home_assistant/
        ├── __init__.py         # Package initialization
        ├── __main__.py         # CLI entry point
        ├── client.py           # Home Assistant API client
        ├── models.py           # Data models
        └── websocket.py        # WebSocket client for real-time events
```

## Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `HOME_ASSISTANT_URL` | URL of your Home Assistant instance | `http://192.168.1.100:8123` |
| `HOME_ASSISTANT_TOKEN` | Long-lived access token | `eyJ0eXAiOiJKV1Q...` |

## Features

- **REST API Client**: Get states, call services, trigger automations
- **WebSocket Client**: Subscribe to real-time state changes
- **Entity Discovery**: List all entities by domain (lights, switches, sensors, etc.)
- **Rich CLI Output**: Formatted tables and colored output

## Raspberry Pi 5 / Portainer Notes

If Home Assistant is running in a Docker container via Portainer:

1. Make sure the container port 8123 is exposed
2. Use the Raspberry Pi's IP address (not localhost)
3. If using SSL/HTTPS, update the URL accordingly

Find your Pi's IP:
```bash
# On the Raspberry Pi
hostname -I
```

## License

Internal use only.
