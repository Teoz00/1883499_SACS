from typing import Any

from aiokafka import AIOKafkaProducer

from app.config import settings


class KafkaIngestionProducer:
    """
    Placeholder wrapper around AIOKafkaProducer for the ingestion service.

    This class is responsible for publishing raw sensor events to the
    `raw-sensor-events` topic. Full lifecycle management and business
    logic are intentionally omitted at this stage.
    """

    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        # Placeholder for initializing the producer.
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers
        )
        # Actual start call intentionally omitted.

    async def stop(self) -> None:
        # Placeholder for shutting down the producer.
        if self._producer is not None:
            # await self._producer.stop()
            self._producer = None

    async def publish_raw_event(self, payload: Any) -> None:
        """
        Placeholder method for publishing a raw event to Kafka.
        """
        if self._producer is None:
            # In a full implementation this would either start the producer
            # or raise an appropriate error.
            return

        topic = settings.kafka_topic_raw_events

