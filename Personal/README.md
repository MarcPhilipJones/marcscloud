# Personal - Raspberry Pi & Home Assistant Workspace

A personal workspace for Raspberry Pi and Home Assistant development projects.

## Prerequisites

- Python 3.10+
- For Raspberry Pi: RPi.GPIO or gpiozero
- For Home Assistant: Access token from your HA instance

## Setup

1. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1  # Windows
   # or
   source .venv/bin/activate   # Linux/macOS/Pi
   ```

2. Install base dependencies:
   ```bash
   pip install -e .
   ```

3. For Raspberry Pi development (on Pi):
   ```bash
   pip install -e ".[raspberry_pi]"
   ```

4. For Home Assistant development:
   ```bash
   pip install -e ".[home_assistant]"
   ```

## Configuration

Copy `.env.example` to `.env` and update with your values:

```bash
cp .env.example .env
```

### Home Assistant Token

1. Go to your Home Assistant instance
2. Click on your profile (bottom left)
3. Scroll to "Long-Lived Access Tokens"
4. Create a new token and add it to `.env`

## Project Structure

```
Personal/
├── raspberry_pi/           # Raspberry Pi projects
│   ├── __init__.py
│   └── gpio_example.py     # GPIO example script
├── home_assistant/         # Home Assistant projects  
│   ├── __init__.py
│   └── ha_client.py        # HA REST API client
├── scripts/                # Utility scripts
├── .env.example            # Environment template
├── pyproject.toml          # Project configuration
└── README.md
```

## Usage Examples

### Raspberry Pi GPIO (on Pi)
```bash
python raspberry_pi/gpio_example.py
```

### Home Assistant Client
```python
from home_assistant.ha_client import HomeAssistantClient, HAConfig

config = HAConfig.from_env()
client = HomeAssistantClient(config)

# Get all states
states = client.get_states()

# Turn on a light
client.turn_on("light.living_room")

# Toggle a switch
client.toggle("switch.desk_lamp")
```

## License

MIT
