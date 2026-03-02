"""Home Assistant WebSocket client for real-time events."""

import asyncio
import json
import os
from typing import Any, Callable, Optional

from dotenv import load_dotenv

from .models import Event, EntityState


class HomeAssistantWebSocket:
    """WebSocket client for real-time Home Assistant events."""
    
    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """
        Initialize the WebSocket client.
        
        Args:
            url: Home Assistant URL (or set HOME_ASSISTANT_URL env var)
            token: Long-lived access token (or set HOME_ASSISTANT_TOKEN env var)
        """
        load_dotenv()
        
        self.url = (url or os.getenv("HOME_ASSISTANT_URL", "")).rstrip("/")
        self.token = token or os.getenv("HOME_ASSISTANT_TOKEN", "")
        
        if not self.url:
            raise ValueError("Missing Home Assistant URL")
        if not self.token:
            raise ValueError("Missing Home Assistant token")
        
        # Convert http(s) to ws(s)
        ws_url = self.url.replace("https://", "wss://").replace("http://", "ws://")
        self.ws_url = f"{ws_url}/api/websocket"
        
        self._websocket = None
        self._message_id = 0
        self._callbacks: dict[str, list[Callable]] = {}
        self._running = False
    
    def _next_id(self) -> int:
        """Get next message ID."""
        self._message_id += 1
        return self._message_id
    
    async def connect(self) -> None:
        """Connect to the WebSocket and authenticate."""
        try:
            import websockets
        except ImportError:
            raise ImportError("websockets package required. Install with: pip install websockets")
        
        self._websocket = await websockets.connect(self.ws_url)
        
        # Wait for auth_required message
        msg = await self._websocket.recv()
        data = json.loads(msg)
        
        if data.get("type") != "auth_required":
            raise RuntimeError(f"Unexpected message: {data}")
        
        # Send auth
        await self._websocket.send(json.dumps({
            "type": "auth",
            "access_token": self.token
        }))
        
        # Wait for auth response
        msg = await self._websocket.recv()
        data = json.loads(msg)
        
        if data.get("type") == "auth_invalid":
            raise RuntimeError(f"Authentication failed: {data.get('message')}")
        
        if data.get("type") != "auth_ok":
            raise RuntimeError(f"Unexpected auth response: {data}")
        
        print(f"Connected to Home Assistant {data.get('ha_version', 'unknown')}")
    
    async def subscribe_events(
        self,
        callback: Callable[[Event], None],
        event_type: Optional[str] = None,
    ) -> int:
        """
        Subscribe to events.
        
        Args:
            callback: Function to call when event is received
            event_type: Specific event type to subscribe to (None for all)
        
        Returns:
            Subscription ID
        """
        msg_id = self._next_id()
        
        subscribe_msg: dict[str, Any] = {
            "id": msg_id,
            "type": "subscribe_events",
        }
        
        if event_type:
            subscribe_msg["event_type"] = event_type
        
        await self._websocket.send(json.dumps(subscribe_msg))
        
        # Store callback
        key = event_type or "*"
        if key not in self._callbacks:
            self._callbacks[key] = []
        self._callbacks[key].append(callback)
        
        # Wait for confirmation
        msg = await self._websocket.recv()
        data = json.loads(msg)
        
        if data.get("success"):
            print(f"Subscribed to events: {event_type or 'all'}")
        
        return msg_id
    
    async def subscribe_state_changes(
        self,
        callback: Callable[[EntityState, EntityState], None],
        entity_id: Optional[str] = None,
    ) -> int:
        """
        Subscribe to state change events.
        
        Args:
            callback: Function called with (old_state, new_state)
            entity_id: Specific entity to watch (None for all)
        
        Returns:
            Subscription ID
        """
        async def state_handler(event: Event) -> None:
            data = event.data
            old_state = EntityState.from_dict(data.get("old_state", {})) if data.get("old_state") else None
            new_state = EntityState.from_dict(data.get("new_state", {})) if data.get("new_state") else None
            
            if entity_id and new_state and new_state.entity_id != entity_id:
                return
            
            if new_state:
                callback(old_state, new_state)
        
        return await self.subscribe_events(
            lambda e: asyncio.create_task(state_handler(e)),
            "state_changed"
        )
    
    async def listen(self) -> None:
        """Listen for messages and dispatch to callbacks."""
        self._running = True
        
        while self._running:
            try:
                msg = await self._websocket.recv()
                data = json.loads(msg)
                
                if data.get("type") == "event":
                    event = Event.from_dict(data.get("event", {}))
                    
                    # Call matching callbacks
                    event_type = event.event_type
                    for cb in self._callbacks.get(event_type, []):
                        try:
                            result = cb(event)
                            if asyncio.iscoroutine(result):
                                await result
                        except Exception as e:
                            print(f"Callback error: {e}")
                    
                    # Call wildcard callbacks
                    for cb in self._callbacks.get("*", []):
                        try:
                            result = cb(event)
                            if asyncio.iscoroutine(result):
                                await result
                        except Exception as e:
                            print(f"Callback error: {e}")
            
            except Exception as e:
                if self._running:
                    print(f"WebSocket error: {e}")
                break
    
    async def call_service(
        self,
        domain: str,
        service: str,
        entity_id: Optional[str] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Call a service via WebSocket."""
        msg_id = self._next_id()
        
        service_data: dict[str, Any] = {}
        if entity_id:
            service_data["entity_id"] = entity_id
        service_data.update(kwargs)
        
        await self._websocket.send(json.dumps({
            "id": msg_id,
            "type": "call_service",
            "domain": domain,
            "service": service,
            "service_data": service_data,
        }))
        
        msg = await self._websocket.recv()
        return json.loads(msg)
    
    async def close(self) -> None:
        """Close the WebSocket connection."""
        self._running = False
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
    
    async def __aenter__(self) -> "HomeAssistantWebSocket":
        await self.connect()
        return self
    
    async def __aexit__(self, *args: Any) -> None:
        await self.close()


# Example usage
async def example():
    """Example of using the WebSocket client."""
    async with HomeAssistantWebSocket() as ws:
        def on_state_change(old_state, new_state):
            print(f"{new_state.entity_id}: {old_state.state if old_state else '?'} -> {new_state.state}")
        
        await ws.subscribe_state_changes(on_state_change)
        
        print("Listening for state changes... (Ctrl+C to stop)")
        await ws.listen()


if __name__ == "__main__":
    asyncio.run(example())
