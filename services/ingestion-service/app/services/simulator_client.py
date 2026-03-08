import logging
from typing import List

import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings

logger = logging.getLogger(__name__)


class RawSensorEvent(BaseModel):
    sensor_id: str
    type: str
    value: float
    timestamp: str


async def fetch_sensor_data() -> List[RawSensorEvent]:
    """
    Fetch sensor data from the external simulator.

    Returns an empty list on error; errors are logged.
    """
    if not settings.simulator_base_url:
        logger.warning("SIMULATOR_BASE_URL is not configured; skipping simulator poll.")
        return []

    url = f"{settings.simulator_base_url}/sensors"
    logger.info("Polling simulator at %s", url)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Failed to poll simulator at %s: %s", url, exc)
        return []

    try:
        payload = response.json()
    except ValueError as exc:
        logger.error("Simulator returned invalid JSON: %s", exc)
        return []

    if not isinstance(payload, list):
        logger.error("Expected list from simulator, got %s", type(payload))
        return []

    events: List[RawSensorEvent] = []
    for item in payload:
        try:
            event = RawSensorEvent.parse_obj(item)
        except ValidationError as exc:
            logger.error("Invalid sensor event from simulator: %s", exc)
            continue
        events.append(event)

    logger.info("Fetched %d sensor events from simulator", len(events))
    return events

