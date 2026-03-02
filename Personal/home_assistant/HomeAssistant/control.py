"""Control Home Assistant devices from command line."""

import sys
from client import HomeAssistantClient


def main() -> None:
    """Control devices via command line arguments."""
    if len(sys.argv) < 3:
        print("Usage: python control.py <action> <entity_id> [args]")
        print()
        print("Actions:")
        print("  on       - Turn on entity")
        print("  off      - Turn off entity")
        print("  toggle   - Toggle entity")
        print("  state    - Get entity state")
        print("  brightness <0-255> - Set light brightness")
        print()
        print("Examples:")
        print("  python control.py on light.living_room")
        print("  python control.py toggle switch.desk_lamp")
        print("  python control.py brightness light.bedroom 128")
        print("  python control.py state sensor.temperature")
        return
    
    action = sys.argv[1].lower()
    entity_id = sys.argv[2]
    
    client = HomeAssistantClient.from_env()
    
    if action == "on":
        client.turn_on(entity_id)
        print(f"✓ Turned on {entity_id}")
    
    elif action == "off":
        client.turn_off(entity_id)
        print(f"✓ Turned off {entity_id}")
    
    elif action == "toggle":
        client.toggle(entity_id)
        print(f"✓ Toggled {entity_id}")
    
    elif action == "state":
        state = client.get_state(entity_id)
        print(f"Entity: {entity_id}")
        print(f"State: {state.get('state')}")
        attrs = state.get("attributes", {})
        if attrs:
            print("Attributes:")
            for key, value in attrs.items():
                print(f"  {key}: {value}")
    
    elif action == "brightness":
        if len(sys.argv) < 4:
            print("Error: brightness requires a value (0-255)")
            return
        brightness = int(sys.argv[3])
        client.set_light_brightness(entity_id, brightness)
        print(f"✓ Set {entity_id} brightness to {brightness}")
    
    else:
        print(f"Unknown action: {action}")


if __name__ == "__main__":
    main()
