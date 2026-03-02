"""Home Assistant REST API Client."""

import os
from dataclasses import dataclass
from typing import Any

import httpx
from dotenv import load_dotenv


@dataclass
class HAConfig:
    """Home Assistant configuration."""
    
    url: str
    token: str
    
    @classmethod
    def from_env(cls) -> "HAConfig":
        """Load configuration from environment variables."""
        load_dotenv()
        
        url = os.getenv("HA_URL", "http://homeassistant.local:8123")
        token = os.getenv("HA_TOKEN", "")
        
        if not token:
            raise ValueError("HA_TOKEN environment variable is required")
        
        return cls(url=url.rstrip("/"), token=token)


class HomeAssistantClient:
    """Client for Home Assistant REST API."""
    
    def __init__(self, url: str, token: str) -> None:
        """Initialize the client."""
        self.url = url.rstrip("/")
        self.client = httpx.Client(headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })
    
    @classmethod
    def from_env(cls) -> "HomeAssistantClient":
        """Create client from environment variables."""
        config = HAConfig.from_env()
        return cls(config.url, config.token)
    
    def _get(self, endpoint: str) -> Any:
        """GET request to Home Assistant API."""
        response = self.client.get(f"{self.url}/api/{endpoint}")
        response.raise_for_status()
        return response.json() if response.text else {}
    
    def _post(self, endpoint: str, data: dict | None = None) -> Any:
        """POST request to Home Assistant API."""
        response = self.client.post(f"{self.url}/api/{endpoint}", json=data or {})
        response.raise_for_status()
        return response.json() if response.text else {}
    
    # --- Info Methods ---
    
    def check_api(self) -> dict:
        """Check if the API is running."""
        return self._get("")
    
    def get_config(self) -> dict:
        """Get Home Assistant configuration."""
        return self._get("config")
    
    # --- State Methods ---
    
    def get_states(self) -> list[dict]:
        """Get all entity states."""
        return self._get("states")
    
    def get_state(self, entity_id: str) -> dict:
        """Get state of a specific entity."""
        return self._get(f"states/{entity_id}")
    
    def get_entities_by_domain(self, domain: str) -> list[dict]:
        """Get all entities for a domain (e.g., 'light', 'switch')."""
        states = self.get_states()
        return [s for s in states if s["entity_id"].startswith(f"{domain}.")]
    
    # --- Service Methods ---
    
    def get_services(self) -> dict:
        """Get all available services."""
        return self._get("services")
    
    def call_service(
        self,
        domain: str,
        service: str,
        entity_id: str | None = None,
        **data: Any,
    ) -> list[dict]:
        """Call a Home Assistant service."""
        payload = dict(data)
        if entity_id:
            payload["entity_id"] = entity_id
        
        return self._post(f"services/{domain}/{service}", payload)
    
    # --- Convenience Methods ---
    
    def turn_on(self, entity_id: str, **kwargs: Any) -> list[dict]:
        """Turn on an entity."""
        domain = entity_id.split(".")[0]
        return self.call_service(domain, "turn_on", entity_id, **kwargs)
    
    def turn_off(self, entity_id: str) -> list[dict]:
        """Turn off an entity."""
        domain = entity_id.split(".")[0]
        return self.call_service(domain, "turn_off", entity_id)
    
    def toggle(self, entity_id: str) -> list[dict]:
        """Toggle an entity."""
        domain = entity_id.split(".")[0]
        return self.call_service(domain, "toggle", entity_id)
    
    # --- Light Methods ---
    
    def set_light_brightness(self, entity_id: str, brightness: int) -> list[dict]:
        """Set light brightness (0-255)."""
        return self.turn_on(entity_id, brightness=brightness)
    
    def set_light_color(self, entity_id: str, rgb: tuple[int, int, int]) -> list[dict]:
        """Set light color using RGB values."""
        return self.turn_on(entity_id, rgb_color=list(rgb))
    
    # --- Climate Methods ---
    
    def set_temperature(self, entity_id: str, temperature: float) -> list[dict]:
        """Set thermostat temperature."""
        return self.call_service("climate", "set_temperature", entity_id, temperature=temperature)
    
    def set_hvac_mode(self, entity_id: str, mode: str) -> list[dict]:
        """Set HVAC mode (heat, cool, auto, off)."""
        return self.call_service("climate", "set_hvac_mode", entity_id, hvac_mode=mode)


def main() -> None:
    """Example usage and connection test."""
    print("Home Assistant Client")
    print("=" * 40)
    
    try:
        client = HomeAssistantClient.from_env()
        
        # Test connection
        api_status = client.check_api()
        print(f"✓ Connected to Home Assistant")
        print(f"  Message: {api_status.get('message', 'OK')}")
        
        # Get config
        config = client.get_config()
        print(f"\n  Location: {config.get('location_name', 'Unknown')}")
        print(f"  Version: {config.get('version', 'Unknown')}")
        
        # Count entities
        states = client.get_states()
        print(f"\n  Total entities: {len(states)}")
        
        # Count by domain
        domains: dict[str, int] = {}
        for state in states:
            domain = state["entity_id"].split(".")[0]
            domains[domain] = domains.get(domain, 0) + 1
        
        print("\n  Entities by domain:")
        for domain, count in sorted(domains.items(), key=lambda x: -x[1])[:10]:
            print(f"    {domain}: {count}")
            
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nCreate a .env file with:")
        print("  HA_URL=http://your-ha-instance:8123")
        print("  HA_TOKEN=your_long_lived_access_token")
    except httpx.RequestError as e:
        print(f"Connection error: {e}")


if __name__ == "__main__":
    main()
