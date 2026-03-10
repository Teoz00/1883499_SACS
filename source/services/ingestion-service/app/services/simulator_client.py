import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings

logger = logging.getLogger(__name__)


class RawSensorEvent(BaseModel):
    sensor_id: str
    type: str
    value: float
    timestamp: str
    status: str | None = None


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


def _reading_to_events(sensor_id: str, reading: Dict[str, Any]) -> List[RawSensorEvent]:
    """
    Map a single sensor reading object into one or more RawSensorEvent
    instances, based on the schema family.
    """
    events: List[RawSensorEvent] = []
    captured_at = reading.get("captured_at") or datetime.now(timezone.utc).isoformat()

    # rest.scalar.v1 : metric + value + unit + status
    if "metric" in reading and "value" in reading:
        events.append(
            RawSensorEvent(
                sensor_id=sensor_id,
                type=str(reading.get("metric")),
                value=float(reading.get("value")),
                timestamp=captured_at,
                status=str(reading.get("status") or "ok"),
            )
        )
        return events

    # rest.chemistry.v1 : measurements[] + status
    if isinstance(reading.get("measurements"), list):
        for m in reading["measurements"]:
            if not isinstance(m, dict):
                continue
            if "metric" not in m or "value" not in m:
                continue
            events.append(
                RawSensorEvent(
                    sensor_id=sensor_id,
                    type=str(m.get("metric")),
                    value=float(m.get("value")),
                    timestamp=captured_at,
                        status=str(reading.get("status") or "ok"),
                )
            )
        return events

    # rest.particulate.v1 : pm* fields – use pm25 as primary metric
    if "pm25_ug_m3" in reading:
        events.append(
            RawSensorEvent(
                sensor_id=sensor_id,
                type="pm25_ug_m3",
                value=float(reading.get("pm25_ug_m3")),
                timestamp=captured_at,
                status=str(reading.get("status") or "ok"),
            )
        )
        return events

    # rest.level.v1 : level_pct + status
    if "level_pct" in reading:
        events.append(
            RawSensorEvent(
                sensor_id=sensor_id,
                type="level_pct",
                value=float(reading.get("level_pct")),
                timestamp=captured_at,
                status=str(reading.get("status") or "ok"),
            )
        )
        return events

    logger.error(
        "Unsupported sensor reading schema for sensor_id=%s: keys=%s",
        sensor_id,
        list(reading.keys()),
    )
    return []


async def fetch_sensor_data() -> List[RawSensorEvent]:
    """
    Fetch sensor data from the external simulator.

    Returns an empty list on error; errors are logged.
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

    events: List[RawSensorEvent] = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        for sensor_id in sensor_ids:
            sensor_url = f"{base_url}/api/sensors/{sensor_id}"
            try:
                response = await client.get(sensor_url)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                logger.error(
                    "Failed to poll sensor %s at %s: %s", sensor_id, sensor_url, exc
                )
                continue

            try:
                reading = response.json()
            except ValueError as exc:
                logger.error(
                    "Simulator returned invalid JSON for sensor %s: %s",
                    sensor_id,
                    exc,
                )
                continue

            for evt in _reading_to_events(sensor_id, reading):
                try:
                    # Validate via Pydantic to ensure we publish well-formed payloads.
                    events.append(RawSensorEvent.parse_obj(evt.dict()))
                except ValidationError as exc:
                    logger.error(
                        "Invalid sensor event for sensor %s: %s", sensor_id, exc
                    )
                    continue

    logger.info("Fetched %d sensor events from simulator", len(events))
    return events

