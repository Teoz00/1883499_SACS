import asyncio
import json
import logging
from typing import AsyncIterator

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from app.config import settings
from app.models.actuator_command import ActuatorCommand
from app.models.unified_event import UnifiedEvent


logger = logging.getLogger(__name__)


class NormalizedEventsConsumer:
    """
    Kafka consumer subscribed to the `normalized-events` topic.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self._loop = loop or asyncio.get_event_loop()
        self._consumer: AIOKafkaConsumer | None = None

    async def start(self) -> None:
        if self._consumer is not None:
            return

        self._consumer = AIOKafkaConsumer(
            settings.kafka_topic_normalized_events,
            loop=self._loop,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id="actuator-rules-service",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            enable_auto_commit=True,
        )
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

    async def iter_events(self) -> AsyncIterator[UnifiedEvent]:
        """
        Yield normalized events as UnifiedEvent instances.
        """
        if self._consumer is None:
            raise RuntimeError("Consumer not started.")

        async for msg in self._consumer:
            try:
                payload = msg.value
                event = UnifiedEvent(**payload)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to deserialize UnifiedEvent from Kafka: %s", exc)
                continue

            yield event


class ActuatorCommandsProducer:
    """
    Kafka producer for actuator commands.
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
                    settings.kafka_topic_actuator_commands,
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
            logger.info("Kafka producer for actuator commands stopped")
        finally:
            self._producer = None

    async def publish_actuator_command(self, command: ActuatorCommand) -> None:
        """
        Publish a single actuator command to Kafka.
        """
        if self._producer is None:
            logger.error("Kafka producer not started; cannot publish actuator command.")
            return

        payload = command.dict()

        try:
            await self._producer.send_and_wait(
                topic=settings.kafka_topic_actuator_commands,
                value=payload,
            )
            logger.info(
                "Published actuator command actuator_id=%s command=%s",
                payload.get("actuator_id"),
                payload.get("command"),
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error publishing actuator command to Kafka: %s", exc)


