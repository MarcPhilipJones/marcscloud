"""Marc Home Assistant - Connect to Home Assistant on Raspberry Pi 5."""

from .client import HomeAssistantClient
from .models import Entity, EntityState, ServiceCall

__all__ = ["HomeAssistantClient", "Entity", "EntityState", "ServiceCall"]
__version__ = "0.1.0"
