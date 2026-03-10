import asyncio
import logging
from typing import Dict, Any

from fastapi import WebSocket
from app.services.websocket_manager import WebSocketManager


logger = logging.getLogger(__name__)


class ActuatorStateListener:
    """
    Listens for actuator state changes from actuator management service
    and maintains an in-memory cache of latest actuator states.
    """

    def __init__(self, actuator_cache: Dict[str, Any], ws_manager: WebSocketManager) -> None:
        self.actuator_cache = actuator_cache
        self.ws_manager = ws_manager
        self._connections: Dict[str, WebSocket] = {}

    async def start(self) -> None:
        """Start listening for actuator state changes."""
        logger.info("Starting actuator state listener.")
        
        # For now, we'll update the cache when actuator commands are processed
        # This is handled in the actuator management service command_executor
        
    async def update_actuator_state(self, actuator_id: str, state: str, timestamp: str) -> None:
        """Update actuator state in cache."""
        self.actuator_cache[actuator_id] = {
            "actuator_id": actuator_id,
            "state": state,
            "timestamp": timestamp
        }
        logger.debug(f"Updated actuator cache: {actuator_id} -> {state}")

    async def stop(self) -> None:
        """Stop the listener."""
        logger.info("Stopping actuator state listener.")
