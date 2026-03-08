import asyncio
import logging

from app.kafka.producer import RawEventsProducer
from app.services.simulator_client import fetch_sensor_data

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 3.0


async def run_poller(
    producer: RawEventsProducer,
    stop_event: asyncio.Event,
) -> None:
    """
    Background polling loop.

    Every POLL_INTERVAL_SECONDS:
      - fetch sensor data from the simulator
      - publish each raw event to Kafka
    """
    logger.info("Starting ingestion poller with interval=%s seconds", POLL_INTERVAL_SECONDS)

    try:
        while not stop_event.is_set():
            try:
                events = await fetch_sensor_data()
                if events:
                    logger.info("Publishing %d raw events to Kafka", len(events))
                    await producer.publish_raw_events(events)
                else:
                    logger.debug("No sensor events returned from simulator.")
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Error in ingestion polling loop: %s", exc)

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=POLL_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                # Timeout is expected; triggers next polling iteration.
                continue
    except asyncio.CancelledError:
        logger.info("Ingestion poller task cancelled.")
        raise
    finally:
        logger.info("Ingestion poller stopped.")

