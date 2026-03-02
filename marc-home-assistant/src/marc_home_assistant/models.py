"""Data models for Home Assistant entities and states."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class EntityState:
    """Represents the state of a Home Assistant entity."""
    
    entity_id: str
    state: str
    attributes: dict[str, Any] = field(default_factory=dict)
    last_changed: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    context: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EntityState":
        """Create an EntityState from API response data."""
        return cls(
            entity_id=data.get("entity_id", ""),
            state=data.get("state", "unknown"),
            attributes=data.get("attributes", {}),
            last_changed=cls._parse_datetime(data.get("last_changed")),
            last_updated=cls._parse_datetime(data.get("last_updated")),
            context=data.get("context", {}),
        )
    
    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string."""
        if not value:
            return None
        try:
            # Handle Z suffix and various formats
            v = value.replace("Z", "+00:00")
            return datetime.fromisoformat(v)
        except (ValueError, TypeError):
            return None
    
    @property
    def domain(self) -> str:
        """Get the entity domain (e.g., 'light', 'switch', 'sensor')."""
        return self.entity_id.split(".")[0] if "." in self.entity_id else ""
    
    @property
    def name(self) -> str:
        """Get the friendly name or entity name."""
        return self.attributes.get("friendly_name", self.entity_id.split(".")[-1])
    
    @property
    def is_on(self) -> bool:
        """Check if entity is in 'on' state."""
        return self.state.lower() == "on"
    
    @property
    def is_available(self) -> bool:
        """Check if entity is available (not unavailable/unknown)."""
        return self.state.lower() not in ("unavailable", "unknown")


@dataclass
class Entity:
    """Represents a Home Assistant entity with its current state."""
    
    entity_id: str
    state: EntityState
    
    @property
    def domain(self) -> str:
        return self.entity_id.split(".")[0] if "." in self.entity_id else ""
    
    @property
    def name(self) -> str:
        return self.state.name


@dataclass
class ServiceCall:
    """Represents a service call to Home Assistant."""
    
    domain: str
    service: str
    target: Optional[dict[str, Any]] = None
    data: Optional[dict[str, Any]] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to API request payload."""
        payload: dict[str, Any] = {}
        if self.target:
            payload["target"] = self.target
        if self.data:
            payload.update(self.data)
        return payload


@dataclass
class Event:
    """Represents a Home Assistant event."""
    
    event_type: str
    data: dict[str, Any] = field(default_factory=dict)
    origin: str = "LOCAL"
    time_fired: Optional[datetime] = None
    context: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Create an Event from WebSocket data."""
        return cls(
            event_type=data.get("event_type", ""),
            data=data.get("data", {}),
            origin=data.get("origin", "LOCAL"),
            time_fired=EntityState._parse_datetime(data.get("time_fired")),
            context=data.get("context", {}),
        )


@dataclass
class Config:
    """Home Assistant configuration."""
    
    location_name: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    elevation: int = 0
    unit_system: dict[str, str] = field(default_factory=dict)
    time_zone: str = ""
    version: str = ""
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """Create Config from API response."""
        return cls(
            location_name=data.get("location_name", ""),
            latitude=data.get("latitude", 0.0),
            longitude=data.get("longitude", 0.0),
            elevation=data.get("elevation", 0),
            unit_system=data.get("unit_system", {}),
            time_zone=data.get("time_zone", ""),
            version=data.get("version", ""),
        )
