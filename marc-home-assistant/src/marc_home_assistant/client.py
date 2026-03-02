"""Home Assistant REST API client."""

import os
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

from .models import EntityState, Config, ServiceCall


class HomeAssistantClient:
    """Client for interacting with Home Assistant REST API."""
    
    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """
        Initialize the Home Assistant client.
        
        Args:
            url: Home Assistant URL (or set HOME_ASSISTANT_URL env var)
            token: Long-lived access token (or set HOME_ASSISTANT_TOKEN env var)
        """
        load_dotenv()
        
        self.url = (url or os.getenv("HOME_ASSISTANT_URL", "")).rstrip("/")
        self.token = token or os.getenv("HOME_ASSISTANT_TOKEN", "")
        
        if not self.url:
            raise ValueError(
                "Missing Home Assistant URL. Set HOME_ASSISTANT_URL environment "
                "variable or pass url parameter."
            )
        
        if not self.token:
            raise ValueError(
                "Missing Home Assistant token. Set HOME_ASSISTANT_TOKEN environment "
                "variable or pass token parameter."
            )
        
        self._http_client: Optional[httpx.Client] = None
    
    @property
    def http_client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client(
                base_url=f"{self.url}/api",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._http_client
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Make an API request."""
        response = self.http_client.request(
            method=method,
            url=endpoint,
            json=data,
        )
        response.raise_for_status()
        
        if response.status_code == 204:
            return None
        
        return response.json()
    
    # =========================================================================
    # API Status
    # =========================================================================
    
    def check_api(self) -> bool:
        """Check if the API is running."""
        try:
            result = self._request("GET", "/")
            return result.get("message") == "API running."
        except Exception:
            return False
    
    def get_config(self) -> Config:
        """Get Home Assistant configuration."""
        data = self._request("GET", "/config")
        return Config.from_dict(data)
    
    # =========================================================================
    # States
    # =========================================================================
    
    def get_states(self) -> list[EntityState]:
        """Get states of all entities."""
        data = self._request("GET", "/states")
        return [EntityState.from_dict(item) for item in data]
    
    def get_state(self, entity_id: str) -> Optional[EntityState]:
        """Get state of a specific entity."""
        try:
            data = self._request("GET", f"/states/{entity_id}")
            return EntityState.from_dict(data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def set_state(
        self,
        entity_id: str,
        state: str,
        attributes: Optional[dict[str, Any]] = None,
    ) -> EntityState:
        """Set the state of an entity (for testing/virtual entities)."""
        data: dict[str, Any] = {"state": state}
        if attributes:
            data["attributes"] = attributes
        
        result = self._request("POST", f"/states/{entity_id}", data)
        return EntityState.from_dict(result)
    
    # =========================================================================
    # Services
    # =========================================================================
    
    def get_services(self) -> dict[str, Any]:
        """Get all available services."""
        return self._request("GET", "/services")
    
    def call_service(
        self,
        domain: str,
        service: str,
        entity_id: Optional[str] = None,
        **kwargs: Any,
    ) -> list[EntityState]:
        """
        Call a Home Assistant service.
        
        Args:
            domain: Service domain (e.g., 'light', 'switch', 'automation')
            service: Service name (e.g., 'turn_on', 'turn_off', 'toggle')
            entity_id: Target entity ID (optional for some services)
            **kwargs: Additional service data (e.g., brightness=128)
        
        Returns:
            List of affected entity states
        """
        data: dict[str, Any] = {}
        
        if entity_id:
            data["entity_id"] = entity_id
        
        data.update(kwargs)
        
        result = self._request("POST", f"/services/{domain}/{service}", data)
        return [EntityState.from_dict(item) for item in (result or [])]
    
    # =========================================================================
    # Convenience Methods
    # =========================================================================
    
    def turn_on(self, entity_id: str, **kwargs: Any) -> list[EntityState]:
        """Turn on an entity."""
        domain = entity_id.split(".")[0]
        return self.call_service(domain, "turn_on", entity_id, **kwargs)
    
    def turn_off(self, entity_id: str, **kwargs: Any) -> list[EntityState]:
        """Turn off an entity."""
        domain = entity_id.split(".")[0]
        return self.call_service(domain, "turn_off", entity_id, **kwargs)
    
    def toggle(self, entity_id: str, **kwargs: Any) -> list[EntityState]:
        """Toggle an entity."""
        domain = entity_id.split(".")[0]
        return self.call_service(domain, "toggle", entity_id, **kwargs)
    
    def get_entities_by_domain(self, domain: str) -> list[EntityState]:
        """Get all entities for a specific domain."""
        states = self.get_states()
        return [s for s in states if s.domain == domain]
    
    def get_lights(self) -> list[EntityState]:
        """Get all light entities."""
        return self.get_entities_by_domain("light")
    
    def get_switches(self) -> list[EntityState]:
        """Get all switch entities."""
        return self.get_entities_by_domain("switch")
    
    def get_sensors(self) -> list[EntityState]:
        """Get all sensor entities."""
        return self.get_entities_by_domain("sensor")
    
    def get_binary_sensors(self) -> list[EntityState]:
        """Get all binary sensor entities."""
        return self.get_entities_by_domain("binary_sensor")
    
    def get_automations(self) -> list[EntityState]:
        """Get all automation entities."""
        return self.get_entities_by_domain("automation")
    
    def trigger_automation(self, entity_id: str) -> list[EntityState]:
        """Trigger an automation."""
        return self.call_service("automation", "trigger", entity_id)
    
    # =========================================================================
    # Events & History
    # =========================================================================
    
    def fire_event(self, event_type: str, event_data: Optional[dict[str, Any]] = None) -> None:
        """Fire an event."""
        self._request("POST", f"/events/{event_type}", event_data or {})
    
    # =========================================================================
    # Lovelace Dashboards
    # =========================================================================
    
    def get_dashboards(self) -> list[dict[str, Any]]:
        """
        Get list of all Lovelace dashboards.
        
        Returns:
            List of dashboard definitions with id, title, url_path, etc.
        """
        return self._request("GET", "/lovelace/dashboards")
    
    def get_dashboard_config(self, url_path: Optional[str] = None) -> dict[str, Any]:
        """
        Get configuration of a dashboard.
        
        Args:
            url_path: Dashboard URL path (e.g., 'dashboard-temperatures'). 
                      If None, returns the default/overview dashboard.
        
        Returns:
            Dashboard configuration with title, views, cards, etc.
        """
        endpoint = f"/lovelace/config/{url_path}" if url_path else "/lovelace/config"
        return self._request("GET", endpoint)
    
    def create_dashboard(
        self,
        url_path: str,
        title: str,
        icon: str = "mdi:view-dashboard",
        require_admin: bool = False,
        show_in_sidebar: bool = True,
    ) -> dict[str, Any]:
        """
        Create a new Lovelace dashboard.
        
        Args:
            url_path: URL path for the dashboard (e.g., 'temperatures')
            title: Display title for the dashboard
            icon: MDI icon (e.g., 'mdi:thermometer')
            require_admin: Whether dashboard requires admin access
            show_in_sidebar: Whether to show in sidebar
        
        Returns:
            Created dashboard definition
        """
        data = {
            "url_path": url_path,
            "title": title,
            "icon": icon,
            "require_admin": require_admin,
            "show_in_sidebar": show_in_sidebar,
        }
        return self._request("POST", "/lovelace/dashboards", data)
    
    def update_dashboard_config(
        self,
        config: dict[str, Any],
        url_path: Optional[str] = None,
    ) -> None:
        """
        Update a dashboard's configuration (views, cards, etc.).
        
        Args:
            config: Dashboard config containing 'views' array with cards
            url_path: Dashboard URL path. If None, updates default dashboard.
        
        Example config:
            {
                "title": "Temperatures",
                "views": [{
                    "title": "All Rooms",
                    "path": "all-rooms",
                    "icon": "mdi:thermometer",
                    "cards": [...]
                }]
            }
        """
        endpoint = f"/lovelace/config/{url_path}" if url_path else "/lovelace/config"
        self._request("POST", endpoint, config)
    
    def delete_dashboard(self, dashboard_id: str) -> None:
        """
        Delete a Lovelace dashboard.
        
        Args:
            dashboard_id: The dashboard ID (not url_path)
        """
        self._request("DELETE", f"/lovelace/dashboards/{dashboard_id}")
    
    def create_mini_graph_card(
        self,
        entity_id: str,
        name: str,
        icon: str = "mdi:thermometer",
        hours_to_show: int = 24,
        points_per_hour: int = 4,
    ) -> dict[str, Any]:
        """
        Create a mini-graph-card configuration for temperature display.
        
        Args:
            entity_id: Sensor entity ID (e.g., 'sensor.kitchen_temperature')
            name: Display name for the card
            icon: MDI icon for the card
            hours_to_show: Hours of history to display
            points_per_hour: Data points per hour
        
        Returns:
            Card configuration dictionary
        """
        return {
            "type": "custom:mini-graph-card",
            "name": name,
            "icon": icon,
            "entities": [{"entity": entity_id, "name": "Temperature"}],
            "hours_to_show": hours_to_show,
            "points_per_hour": points_per_hour,
            "line_width": 2,
            "font_size": 75,
            "animate": True,
            "show": {
                "labels": True,
                "points": False,
                "legend": False,
                "state": True,
                "name": True,
                "icon": True,
                "extrema": True,
                "average": True,
            },
            "color_thresholds": [
                {"value": 16, "color": "#1e88e5"},  # Blue - cold
                {"value": 18, "color": "#43a047"},  # Green - comfortable
                {"value": 20, "color": "#fb8c00"},  # Orange - warm
                {"value": 22, "color": "#e53935"},  # Red - hot
            ],
        }
    
    # =========================================================================
    # Cleanup
    # =========================================================================
    
    def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None
    
    def __enter__(self) -> "HomeAssistantClient":
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.close()
