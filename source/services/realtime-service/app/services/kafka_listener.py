import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any
import httpx
import json
from aiokafka import AIOKafkaConsumer

from app.config import settings
from app.services.websocket_manager import WebSocketManager


logger = logging.getLogger(__name__)


class NormalizedEventsListener:
    """
    Kafka listener that consumes normalized events and forwards them to
    connected WebSocket clients via the provided WebSocketManager.
    Also maintains an in-memory cache of the latest sensor values.
    """

    def __init__(
        self,
        ws_manager: WebSocketManager,
        sensor_cache: Dict[str, dict],
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        self._ws_manager = ws_manager
        self._sensor_cache = sensor_cache
        self._loop = loop or asyncio.get_event_loop()
        self._consumer: AIOKafkaConsumer | None = None

    async def start(self) -> None:
        if self._consumer is not None:
            return

        self._consumer = AIOKafkaConsumer(
            settings.kafka_topic_normalized_events,
            loop=self._loop,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id="realtime-service",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            enable_auto_commit=True,
        )

        # Reconnect safety: retry start with backoff.
        delay = 1.0
        while True:
            try:
                await self._consumer.start()
                logger.info(
                    "Kafka consumer started for topic '%s'",
                    settings.kafka_topic_normalized_events,
                )
                break
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(
                    "Failed to start Kafka consumer (will retry in %.1fs): %s",
                    delay,
                    exc,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30.0)

    async def stop(self) -> None:
        if self._consumer is None:
            return

        try:
            await self._consumer.stop()
            logger.info("Kafka consumer for normalized events stopped")
        finally:
            self._consumer = None

    async def run(self, stop_event: asyncio.Event) -> None:
        """
        Background loop that reads from Kafka and broadcasts each event
        to all connected websocket clients.
        """
        if self._consumer is None:
            raise RuntimeError("Listener not started.")

        logger.info("Starting normalized events listener loop.")

        try:
            async for msg in self._consumer:
                if stop_event.is_set():
                    break

                payload = msg.value
                if not isinstance(payload, dict):
                    logger.warning(
                        "Received non-dict payload from Kafka; skipping: %r", payload
                    )
                    continue

                try:
                    # Update sensor cache with latest value
                    source_id = payload.get("source_id")
                    if source_id:
                        self._sensor_cache[source_id] = payload
                        
                        # Update API Gateway cache
                        try:
                            async with httpx.AsyncClient(timeout=2.0) as client:
                                await client.post(
                                    "http://api-gateway:8000/cache/sensors/update",
                                    json=payload
                                )
                        except Exception as exc:
                            logger.warning(f"Failed to update API Gateway sensor cache: {exc}")
                        
                    await self._ws_manager.broadcast_json(payload)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.error("Failed to broadcast message to websockets: %s", exc)
        except asyncio.CancelledError:
            logger.info("Normalized events listener loop cancelled.")
            raise
        finally:
            logger.info("Normalized events listener loop stopped.")

