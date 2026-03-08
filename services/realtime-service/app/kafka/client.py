from aiokafka import AIOKafkaConsumer

from app.config import settings


class RealtimeKafkaConsumer:
    """
    Placeholder Kafka consumer for normalized events that will be
    forwarded to WebSocket clients.
    """

    def __init__(self) -> None:
        self._consumer: AIOKafkaConsumer | None = None

    async def start(self) -> None:
        # Placeholder initialization logic.
        self._consumer = AIOKafkaConsumer(
            settings.kafka_topic_normalized_events,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id="realtime-service",
        )
        # Actual start call intentionally omitted.

    async def stop(self) -> None:
        if self._consumer is not None:
            # await self._consumer.stop()
            self._consumer = None

