import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings

logger = logging.getLogger(__name__)


async def _list_sensor_ids(base_url: str) -> List[str]:
    """
    Call /api/sensors and return the list of sensor identifiers.
    The simulator returns a structure that includes sensor_ids; we
    normalize it into a simple list of strings.
    """
    url = f"{base_url}/api/sensors"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Failed to list sensors at %s: %s", url, exc)
        return []

    try:
        payload = response.json()
    except ValueError as exc:
        logger.error("Simulator /api/sensors returned invalid JSON: %s", exc)
        return []

    # Most likely shapes: ["greenhouse_temperature", ...] or {"sensors":[...]}
    if isinstance(payload, list):
        return [s for s in payload if isinstance(s, str)]

    if isinstance(payload, dict):
        sensors = payload.get("sensors")
        if isinstance(sensors, list):
            return [s for s in sensors if isinstance(s, str)]

    logger.error("Unsupported /api/sensors payload shape: %r", type(payload))
    return []


async def fetch_sensor_data() -> List[dict]:
    """
    Fetch all sensor readings from the simulator.
    Returns a list of raw dicts, each containing the full simulator 
    payload plus a sensor_id field.
    """
    # simulator_base_url is an AnyHttpUrl; convert to str before normalization.
    raw_base = str(settings.simulator_base_url) if settings.simulator_base_url else ""
    base_url = raw_base.rstrip("/")

    if not base_url:
        logger.warning("SIMULATOR_BASE_URL is not configured; skipping simulator poll.")
        return []

    # The simulator exposes REST sensors under /api/sensors.
    sensor_ids = await _list_sensor_ids(base_url)
    if not sensor_ids:
        logger.warning("Simulator returned no sensor identifiers from /api/sensors.")
        return []

    logger.info("Polling simulator for %d sensors", len(sensor_ids))

    results = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        for sensor_id in sensor_ids:
            sensor_url = f"{base_url}/api/sensors/{sensor_id}"
            try:
                response = await client.get(sensor_url)
                response.raise_for_status()
                reading = response.json()
                # Ensure sensor_id is always present in the payload
                reading["sensor_id"] = sensor_id
                results.append(reading)
            except Exception as exc:
                logger.error("Failed to poll sensor %s: %s", sensor_id, exc)
                continue
    
    logger.info("Fetched %d sensor events from simulator", len(results))
    return results

