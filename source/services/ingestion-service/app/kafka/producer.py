import asyncio
import json
import logging
from typing import Iterable, Mapping

from aiokafka import AIOKafkaProducer

from app.config import settings

logger = logging.getLogger(__name__)


class RawEventsProducer:
    """
    Kafka producer for raw sensor events.
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
                    settings.kafka_topic_raw_events,
                )
                break
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(
                    "Failed to start Kafka producer (will retry in %.1fs): %s",
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
            logger.info("Kafka producer stopped")
        finally:
            self._producer = None

    async def publish_raw_event(self, event: Mapping[str, object]) -> None:
        if self._producer is None:
            logger.error("Kafka producer not started; cannot publish event.")
            return

        payload = dict(event)

        try:
            await self._producer.send_and_wait(
                topic=settings.kafka_topic_raw_events,
                value=payload,
            )
            logger.info(
                "Published raw event for sensor_id=%s",
                payload.get("sensor_id"),
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error publishing raw event to Kafka: %s", exc)

    async def publish_raw_events(self, events: Iterable[Mapping[str, object]]) -> None:
        for event in events:
            await self.publish_raw_event(event)

