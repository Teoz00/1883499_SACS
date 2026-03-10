import asyncio
import logging
from typing import Dict, Any

from fastapi import FastAPI, WebSocket

from app.routes.health import router as health_router
from app.services.kafka_listener import NormalizedEventsListener
from app.services.websocket_manager import WebSocketManager


logger = logging.getLogger(__name__)

ws_manager = WebSocketManager()
listener: NormalizedEventsListener | None = None
listener_task: asyncio.Task | None = None
stop_event: asyncio.Event | None = None

# Global cache for latest sensor and actuator data
latest_sensor_data: Dict[str, Any] = {}
latest_actuator_data: Dict[str, Any] = {}


def create_app() -> FastAPI:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    app = FastAPI(title="Realtime Service")

    app.include_router(health_router, prefix="/health", tags=["health"])

    @app.get("/sensors/latest")
    async def get_latest_sensor_data() -> dict:
        """
        Return the latest value for each sensor from the in-memory cache.
        Used by frontend to restore state on page load or tab switch.
        """
        return {"sensors": latest_sensor_data}

    @app.get("/actuators/latest")
    async def get_latest_actuator_data() -> dict:
        """
        Return the latest state for each actuator from the in-memory cache.
        Used by frontend to restore state on page load or tab switch.
        """
        return {"actuators": latest_actuator_data}

    @app.post("/actuators/cache")
    async def update_actuator_cache(data: dict) -> dict:
        """
        Update actuator state cache. Called by actuator management service.
        """
        actuator_id = data.get("actuator_id")
        state = data.get("state")
        timestamp = data.get("timestamp")
        
        if actuator_id and state:
            latest_actuator_data[actuator_id] = {
                "actuator_id": actuator_id,
                "state": state,
                "timestamp": timestamp
            }
            logger.info(f"Updated actuator cache: {actuator_id} -> {state}")
        
        return {"status": "ok"}

    @app.websocket("/ws/events")
    async def websocket_events(ws: WebSocket) -> None:
        """
        WebSocket endpoint for clients subscribing to normalized events.
        """
        await ws_manager.connect(ws)
        try:
            # Keep the connection open; we don't expect messages from the client
            while True:
                # Wait for client messages to detect disconnects more quickly.
                # We ignore the actual payload.
                try:
                    await ws.receive_text()
                except Exception:
                    break
        finally:
            await ws_manager.disconnect(ws)

    @app.on_event("startup")
    async def on_startup() -> None:
        global listener, listener_task, stop_event

        logger.info("Starting realtime-service components.")

        loop = asyncio.get_event_loop()
        stop_event = asyncio.Event()

        listener = NormalizedEventsListener(ws_manager=ws_manager, sensor_cache=latest_sensor_data, loop=loop)
        await listener.start()

        listener_task = loop.create_task(
            listener.run(stop_event=stop_event),
            name="normalized-events-listener",
        )

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        global listener, listener_task, stop_event

        logger.info("Shutting down realtime-service components.")

        if stop_event is not None:
            stop_event.set()

        if listener_task is not None:
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                logger.info("Listener task cancelled successfully.")
            listener_task = None

        if listener is not None:
            await listener.stop()
            listener = None

    return app


app = create_app()

