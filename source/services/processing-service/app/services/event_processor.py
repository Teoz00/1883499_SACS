import asyncio
import logging
import json

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
                # DEBUG: Log raw Kafka message structure
                logger.debug("RAW KAFKA MESSAGE: %s", json.dumps(raw, default=str))
                
                # DEBUG: Check for thermal_loop topic
                if isinstance(raw, dict) and raw.get("topic") == "mars/telemetry/thermal_loop":
                    logger.info("THERMAL_LOOP DEBUG: sensor_id=%s, full_message=%s", 
                               raw.get("sensor_id"), json.dumps(raw, default=str))
                
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

