"""Home Assistant REST API client.

A simple client for interacting with Home Assistant's REST API.
"""

import os
from dataclasses import dataclass
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


@dataclass
class HAConfig:
    """Home Assistant configuration."""
    
    url: str
    token: str
    
    @classmethod
    def from_env(cls) -> "HAConfig":
        """Load configuration from environment variables."""
        url = os.getenv("HA_URL", "http://homeassistant.local:8123")
        token = os.getenv("HA_TOKEN", "")
        
        if not token:
            raise ValueError("HA_TOKEN environment variable is required")
        
        return cls(url=url.rstrip("/"), token=token)


class HomeAssistantClient:
    """Client for Home Assistant REST API."""
    
    def __init__(self, config: HAConfig) -> None:
        """Initialize the client."""
        self.config = config
        self.client = httpx.Client(headers={
            "Authorization": f"Bearer {config.token}",
            "Content-Type": "application/json",
        })
    
    def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make a request to the Home Assistant API."""
        url = f"{self.config.url}/api/{endpoint}"
        response = self.client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json() if response.text else {}
    
    def get_states(self) -> list[dict[str, Any]]:
        """Get all entity states."""
        return self._request("GET", "states")
    
    def get_state(self, entity_id: str) -> dict[str, Any]:
        """Get state of a specific entity."""
        return self._request("GET", f"states/{entity_id}")
    
    def call_service(
        self,
        domain: str,
        service: str,
        entity_id: str | None = None,
        **data: Any,
    ) -> list[dict[str, Any]]:
        """Call a Home Assistant service."""
        payload = dict(data)
        if entity_id:
            payload["entity_id"] = entity_id
        
        return self._request("POST", f"services/{domain}/{service}", json=payload)
    
    def turn_on(self, entity_id: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Turn on an entity."""
        domain = entity_id.split(".")[0]
        return self.call_service(domain, "turn_on", entity_id, **kwargs)
    
    def turn_off(self, entity_id: str) -> list[dict[str, Any]]:
        """Turn off an entity."""
        domain = entity_id.split(".")[0]
        return self.call_service(domain, "turn_off", entity_id)
    
    def toggle(self, entity_id: str) -> list[dict[str, Any]]:
        """Toggle an entity."""
        domain = entity_id.split(".")[0]
        return self.call_service(domain, "toggle", entity_id)


def main() -> None:
    """Example usage."""
    print("Home Assistant Client Example")
    print("=" * 40)
    print()
    print("To use this client, set these environment variables:")
    print("  HA_URL   - Your Home Assistant URL (e.g., http://homeassistant.local:8123)")
    print("  HA_TOKEN - Your long-lived access token")
    print()
    print("Or create a .env file in the project root with these values.")


if __name__ == "__main__":
    main()
