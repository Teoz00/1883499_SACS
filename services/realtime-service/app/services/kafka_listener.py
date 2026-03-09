import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer

from app.config import settings
from app.services.websocket_manager import WebSocketManager


logger = logging.getLogger(__name__)


class NormalizedEventsListener:
    """
    Kafka listener that consumes normalized events and forwards them to
    connected WebSocket clients via the provided WebSocketManager.
    """

    def __init__(
        self,
        ws_manager: WebSocketManager,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        self._ws_manager = ws_manager
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
                    await self._ws_manager.broadcast_json(payload)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.error("Failed to broadcast message to websockets: %s", exc)
        except asyncio.CancelledError:
            logger.info("Normalized events listener loop cancelled.")
            raise
        finally:
            logger.info("Normalized events listener loop stopped.")


class ActuatorEventsListener:
    """
    Kafka listener that consumes actuator state events and forwards them to
    connected WebSocket clients.
    """

    def __init__(
        self,
        ws_manager: WebSocketManager,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        self._ws_manager = ws_manager
        self._loop = loop or asyncio.get_event_loop()
        self._consumer: AIOKafkaConsumer | None = None

    async def start(self) -> None:
        if self._consumer is not None:
            return

        self._consumer = AIOKafkaConsumer(
            settings.kafka_topic_actuator_events,
            loop=self._loop,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id="realtime-service-actuators",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            enable_auto_commit=True,
        )

        delay = 1.0
        while True:
            try:
                await self._consumer.start()
                logger.info(
                    "Kafka consumer started for actuator events topic '%s'",
                    settings.kafka_topic_actuator_events,
                )
                break
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(
                    "Failed to start actuator events consumer (will retry in %.1fs): %s",
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
            logger.info("Kafka consumer for actuator events stopped")
        finally:
            self._consumer = None

    async def run(self, stop_event: asyncio.Event) -> None:
        """
        Background loop that reads actuator events from Kafka and broadcasts
        each event to all connected websocket clients.
        """
        if self._consumer is None:
            raise RuntimeError("Actuator events listener not started.")

        logger.info("Starting actuator events listener loop.")

        try:
            async for msg in self._consumer:
                if stop_event.is_set():
                    break

                payload = msg.value
                if not isinstance(payload, dict):
                    logger.warning(
                        "Received non-dict actuator payload from Kafka; skipping: %r",
                        payload,
                    )
                    continue

                try:
                    await self._ws_manager.broadcast_json(payload)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.error(
                        "Failed to broadcast actuator message to websockets: %s", exc
                    )
        except asyncio.CancelledError:
            logger.info("Actuator events listener loop cancelled.")
            raise
        finally:
            logger.info("Actuator events listener loop stopped.")

