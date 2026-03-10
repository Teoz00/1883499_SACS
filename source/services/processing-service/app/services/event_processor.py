import asyncio
import logging

from app.kafka.consumer import RawEventsConsumer
from app.kafka.producer import NormalizedEventsProducer
from app.services.event_transformer import transform_raw_event

logger = logging.getLogger(__name__)


async def run_event_processor(
    consumer: RawEventsConsumer,
    producer: NormalizedEventsProducer,
    stop_event: asyncio.Event,
) -> None:
    """
    Background loop that:
      - consumes raw events from Kafka
      - transforms them into UnifiedEvent instances
      - publishes normalized events to Kafka
    """
    logger.info("Starting processing loop for raw → normalized events.")

    try:
        async for raw in consumer.iter_events():
            if stop_event.is_set():
                break

            try:
                unified = transform_raw_event(raw)
                if unified is None:
                    # Skip events with unknown sensor_id
                    continue
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to transform raw event: %s", exc)
                continue

            await producer.publish_normalized_event(unified)
    except asyncio.CancelledError:
        logger.info("Event processing loop cancelled.")
        raise
    finally:
        logger.info("Event processing loop stopped.")

