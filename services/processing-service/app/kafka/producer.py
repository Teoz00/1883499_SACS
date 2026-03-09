import asyncio
import json
import logging

from aiokafka import AIOKafkaProducer

from app.config import settings
from app.models.unified_event import UnifiedEvent

logger = logging.getLogger(__name__)


class NormalizedEventsProducer:
    """
    Kafka producer for normalized events.
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
                    settings.kafka_topic_normalized_events,
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

    async def publish_normalized_event(self, event: UnifiedEvent) -> None:
        if self._producer is None:
            logger.error("Kafka producer not started; cannot publish normalized event.")
            return

        payload = event.dict()

        try:
            await self._producer.send_and_wait(
                topic=settings.kafka_topic_normalized_events,
                value=payload,
            )
            logger.info(
                "Published normalized event event_id=%s sensor_id=%s",
                payload.get("event_id"),
                payload.get("sensor_id"),
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error publishing normalized event to Kafka: %s", exc)

