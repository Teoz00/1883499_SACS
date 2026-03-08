import asyncio
import json
import logging
from typing import Iterable, Mapping, Union

from aiokafka import AIOKafkaProducer

from app.config import settings
from app.services.simulator_client import RawSensorEvent

logger = logging.getLogger(__name__)

RawEventPayload = Union[RawSensorEvent, Mapping[str, object]]


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
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await self._producer.start()
        logger.info(
            "Kafka producer started for topic '%s'", settings.kafka_topic_raw_events
        )

    async def stop(self) -> None:
        if self._producer is None:
            return

        try:
            await self._producer.stop()
            logger.info("Kafka producer stopped")
        finally:
            self._producer = None

    async def publish_raw_event(self, event: RawEventPayload) -> None:
        if self._producer is None:
            logger.error("Kafka producer not started; cannot publish event.")
            return

        payload = event.dict() if isinstance(event, RawSensorEvent) else dict(event)

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

    async def publish_raw_events(self, events: Iterable[RawSensorEvent]) -> None:
        for event in events:
            await self.publish_raw_event(event)

