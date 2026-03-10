import asyncio
import json
import logging
from typing import Any, Dict, Iterable, List

import httpx

from app.config import settings
from app.kafka.producer import RawEventsProducer
from app.services.simulator_client import RawSensorEvent

logger = logging.getLogger(__name__)


TELEMETRY_TOPICS: List[str] = [
    "mars/telemetry/solar_array",
    "mars/telemetry/power_bus",
    "mars/telemetry/power_consumption",
    "mars/telemetry/radiation",
    "mars/telemetry/life_support",
    "mars/telemetry/thermal_loop",
    "mars/telemetry/airlock",
]


def _power_payload_to_events(topic: str, payload: Dict[str, Any]) -> Iterable[RawSensorEvent]:
    simple_id = topic.split("/")[-1]
    sensor_id = simple_id
    event_time = payload.get("event_time")
    power_kw = payload.get("power_kw")
    if power_kw is None:
        return []
    return [
        RawSensorEvent(
            sensor_id=str(sensor_id),
            type="power_kw",
            value=float(power_kw),
            timestamp=str(event_time),
            status=str(payload.get("status") or "ok"),
        )
    ]


def _environment_payload_to_events(topic: str, payload: Dict[str, Any]) -> Iterable[RawSensorEvent]:
    measurements = payload.get("measurements") or []
    simple_id = topic.split("/")[-1]
    event_time = payload.get("event_time")
    status = str(payload.get("status") or "ok")

    events: List[RawSensorEvent] = []
    # For the purposes of the UI, we treat each telemetry topic as a single
    # logical stream. Take the first measurement as the representative value.
    for m in measurements:
        metric = m.get("metric")
        value = m.get("value")
        if metric is None or value is None:
            continue
        events.append(
            RawSensorEvent(
                sensor_id=str(simple_id),
                type=str(metric),
                value=float(value),
                timestamp=str(event_time),
                status=status,
            )
        )
        break
    return events


def _thermal_payload_to_events(payload: Dict[str, Any]) -> Iterable[RawSensorEvent]:
    loop_name = payload.get("loop") or "thermal_loop"
    event_time = payload.get("event_time")
    temp_c = payload.get("temperature_c")
    if temp_c is None:
        return []
    return [
        RawSensorEvent(
            sensor_id=str(loop_name),
            type="temperature_c",
            value=float(temp_c),
            timestamp=str(event_time),
            status=str(payload.get("status") or "ok"),
        )
    ]


def _airlock_payload_to_events(payload: Dict[str, Any]) -> Iterable[RawSensorEvent]:
    airlock_id = payload.get("airlock_id") or "airlock"
    event_time = payload.get("event_time")
    cycles_per_hour = payload.get("cycles_per_hour")
    if cycles_per_hour is None:
        return []
    return [
        RawSensorEvent(
            sensor_id=str(airlock_id),
            type="cycles_per_hour",
            value=float(cycles_per_hour),
            timestamp=str(event_time),
            status=None,
        )
    ]


def telemetry_payload_to_events(topic: str, payload: Dict[str, Any]) -> Iterable[RawSensorEvent]:
    if topic.endswith("thermal_loop"):
        return _thermal_payload_to_events(payload)
    if topic.endswith("airlock"):
        return _airlock_payload_to_events(payload)
    if payload.get("measurements"):
        return _environment_payload_to_events(topic, payload)
    return _power_payload_to_events(topic, payload)


async def _stream_topic(
    topic: str,
    producer: RawEventsProducer,
    stop_event: asyncio.Event,
) -> None:
    base_url = str(settings.simulator_base_url).rstrip("/")
    url = f"{base_url}/api/telemetry/stream/{topic}"

    backoff = 1.0
    max_backoff = 30.0

    while not stop_event.is_set():
        try:
            logger.info("Starting telemetry stream for topic %s", topic)
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if stop_event.is_set():
                            break
                        if not line:
                            continue
                        if line.startswith("data:"):
                            data_str = line[len("data:") :].strip()
                            if not data_str:
                                continue
                            try:
                                payload = json.loads(data_str)
                            except json.JSONDecodeError:
                                logger.warning(
                                    "Failed to decode telemetry JSON for topic %s: %s",
                                    topic,
                                    data_str,
                                )
                                continue

                            for event in telemetry_payload_to_events(topic, payload):
                                try:
                                    await producer.publish_raw_event(event)
                                except Exception:
                                    logger.exception(
                                        "Failed to publish telemetry event for topic %s", topic
                                    )
            backoff = 1.0
        except asyncio.CancelledError:
            logger.info("Telemetry stream task for %s cancelled", topic)
            break
        except Exception:
            logger.exception(
                "Error in telemetry stream for topic %s. Will retry in %.1fs",
                topic,
                backoff,
            )
            await asyncio.sleep(backoff)
            backoff = min(max_backoff, backoff * 2)


async def run_telemetry_streams(
    producer: RawEventsProducer,
    stop_event: asyncio.Event,
) -> None:
    loop = asyncio.get_event_loop()
    tasks: List[asyncio.Task] = []

    for topic in TELEMETRY_TOPICS:
        task = loop.create_task(
            _stream_topic(topic, producer, stop_event),
            name=f"telemetry-{topic}",
        )
        tasks.append(task)

    try:
        await stop_event.wait()
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

