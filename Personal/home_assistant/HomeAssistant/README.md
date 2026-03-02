# Home Assistant Project

Project for accessing and controlling Home Assistant.

## Setup

1. Copy `.env.example` to `.env`
2. Add your Home Assistant URL and long-lived access token

### Getting a Long-Lived Access Token

1. Go to your Home Assistant instance
2. Click your profile (bottom left)
3. Scroll to "Long-Lived Access Tokens"
4. Click "Create Token"
5. Copy the token to your `.env` file

## Usage

```python
from client import HomeAssistantClient

client = HomeAssistantClient.from_env()

# Get all entities
states = client.get_states()

# Control devices
client.turn_on("light.living_room")
client.turn_off("switch.desk_lamp")
client.toggle("light.bedroom")

# Call any service
client.call_service("climate", "set_temperature", "climate.thermostat", temperature=21)
```
