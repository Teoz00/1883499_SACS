import asyncio
import json
import logging
from typing import AsyncIterator, Mapping, Any

from aiokafka import AIOKafkaConsumer

from app.config import settings

logger = logging.getLogger(__name__)


class RawEventsConsumer:
    """
    Kafka consumer subscribed to the `raw-sensor-events` topic.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self._loop = loop or asyncio.get_event_loop()
        self._consumer: AIOKafkaConsumer | None = None

    async def start(self) -> None:
        if self._consumer is not None:
            return

        self._consumer = AIOKafkaConsumer(
            settings.kafka_topic_raw_events,
            loop=self._loop,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id="processing-service",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            enable_auto_commit=True,
        )
        await self._consumer.start()
        logger.info(
            "Kafka consumer started for topic '%s'", settings.kafka_topic_raw_events
        )

    async def stop(self) -> None:
        if self._consumer is None:
            return

        try:
            await self._consumer.stop()
            logger.info("Kafka consumer stopped")
        finally:
            self._consumer = None

    async def iter_events(self) -> AsyncIterator[Mapping[str, Any]]:
        """
        Yield raw event payloads as dictionaries.
        """
        if self._consumer is None:
            raise RuntimeError("Consumer not started.")

        async for msg in self._consumer:
            yield msg.value

