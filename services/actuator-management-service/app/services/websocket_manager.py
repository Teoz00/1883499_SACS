import logging
from typing import Set

from fastapi import WebSocket


logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Tracks connected WebSocket clients and provides broadcast capability.
    """

    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        logger.info("WebSocket client connected. total=%d", len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)
            logger.info(
                "WebSocket client disconnected. total=%d", len(self._connections)
            )

    async def broadcast_json(self, message: dict) -> None:
        """
        Broadcast a JSON-serializable message to all connected clients.
        Removes clients that fail during send (reconnect safety).
        """
        if not self._connections:
            return

        failed: Set[WebSocket] = set()

        for ws in list(self._connections):
            try:
                await ws.send_json(message)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to send message to websocket client: %s", exc)
                failed.add(ws)

        for ws in failed:
            await self.disconnect(ws)
