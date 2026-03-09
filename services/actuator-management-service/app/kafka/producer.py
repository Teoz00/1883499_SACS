import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Mapping

from aiokafka import AIOKafkaProducer

from app.config import settings


logger = logging.getLogger(__name__)


class ActuatorEventsProducer:
    """
    Kafka producer for actuator state events.
    Payload shape (as consumed by the frontend WebSocket client):
      {
        "event_id": "<uuid>",
        "actuator_id": "<id>",
        "state": "ON" | "OFF",
        "timestamp": "<iso8601>"
      }
    """

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self._loop = loop or asyncio.get_event_loop()
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        if self._producer is not None:
            return

        self._producer = AIOKafkaProducer(
            loop=self._loop,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )

        delay = 1.0
        while True:
            try:
                await self._producer.start()
                logger.info(
                    "Kafka producer started for topic '%s'",
                    settings.kafka_topic_actuator_events,
                )
                break
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(
                    "Failed to start actuator events producer (will retry in %.1fs): %s",
                    delay,
                    exc,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30.0)

    async def stop(self) -> None:
        if self._producer is None:
            return

        try:
            await self._producer.stop()
            logger.info("Kafka producer for actuator events stopped")
        finally:
            self._producer = None

    async def publish_event(self, payload: Mapping[str, object]) -> None:
        if self._producer is None:
            logger.error("Kafka producer not started; cannot publish actuator event.")
            return

        try:
            await self._producer.send_and_wait(
                topic=settings.kafka_topic_actuator_events,
                value=dict(payload),
            )
            logger.info(
                "Published actuator event actuator_id=%s state=%s",
                payload.get("actuator_id"),
                payload.get("state"),
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error publishing actuator event to Kafka: %s", exc)


def build_actuator_event(actuator_id: str, state: str) -> dict[str, object]:
    """
    Helper to build a standard actuator event payload.
    """
    return {
        "event_id": f"act-{actuator_id}-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        "actuator_id": actuator_id,
        "state": state,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

