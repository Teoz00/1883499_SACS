import logging
from typing import Mapping, Any
from uuid import uuid4
from datetime import datetime

from pydantic import BaseModel, ValidationError

from app.models.unified_event import UnifiedEvent, Metric

logger = logging.getLogger(__name__)

# Environment unit mapping for fallback
ENVIRONMENT_UNIT_MAP = {
    "radiation_uSv_h": "µSv/h",
    "oxygen_percent": "%",
}

# Schema family lookup table for fallback
SCHEMA_FAMILY_MAP = {
    "greenhouse_temperature": "rest.scalar.v1",
    "entrance_humidity":      "rest.scalar.v1",
    "co2_hall":               "rest.scalar.v1",
    "corridor_pressure":      "rest.scalar.v1",
    "hydroponic_ph":          "rest.chemistry.v1",
    "air_quality_voc":        "rest.chemistry.v1",
    "air_quality_pm25":       "rest.particulate.v1",
    "water_tank_level":       "rest.level.v1",
    "solar_array":            "topic.power.v1",
    "power_bus":              "topic.power.v1",
    "power_consumption":      "topic.power.v1",
    "radiation":              "topic.environment.v1",
    "life_support":           "topic.environment.v1",
    "thermal_loop":           "topic.thermal_loop.v1",
    "primary":                "topic.thermal_loop.v1",  # thermal_loop uses "primary" as sensor_id
    "airlock-1":              "topic.airlock.v1",
}


class RawEvent(BaseModel):
    sensor_id: str
    type: str
    value: float
    timestamp: str
    status: str | None = None


def transform_raw_event(raw: Mapping[str, Any]) -> UnifiedEvent | None:
    """
    Normalize raw event into UnifiedEvent with proper metrics mapping.
    The raw message contains only RawSensorEvent fields: sensor_id, type, value, timestamp, status
    """
    try:
        raw_event = RawEvent.parse_obj(raw)
    except ValidationError as exc:
        logger.error("Invalid raw event payload: %s", exc)
        raise

    sensor_id = raw_event.sensor_id
    schema_family = SCHEMA_FAMILY_MAP.get(sensor_id)

    if schema_family is None:
        logger.warning(f"Unknown sensor_id '{sensor_id}', skipping")
        return None

    source_type = "telemetry" if schema_family.startswith("topic.") else "rest"

    # For thermal_loop, use "thermal_loop" as source_id regardless of actual sensor_id
    effective_source_id = "thermal_loop" if schema_family == "topic.thermal_loop.v1" else sensor_id

    # Parse timestamp to datetime
    timestamp = datetime.fromisoformat(raw_event.timestamp.replace('Z', '+00:00'))

    # Create metrics based on schema family and available data
    metrics = []
    status = raw_event.status
    state_label = None

    if schema_family == "rest.scalar.v1":
        # Single metric sensors - use type as metric name, value and infer unit
        unit = _infer_unit(sensor_id, raw_event.type)
        metrics = [Metric(name=raw_event.type, value=raw_event.value, unit=unit)]

    elif schema_family == "rest.chemistry.v1":
        # Multi-metric sensors - RawSensorEvent creates one event per measurement
        unit = _infer_unit(sensor_id, raw_event.type)
        metrics = [Metric(name=raw_event.type, value=raw_event.value, unit=unit)]

    elif schema_family == "rest.particulate.v1":
        # PM2.5 sensor - RawSensorEvent sends pm25 as primary metric
        metrics = [Metric(name="pm25", value=raw_event.value, unit="ug/m3")]

    elif schema_family == "rest.level.v1":
        # Water tank level - RawSensorEvent sends level_pct as primary metric
        metrics = [Metric(name="level_pct", value=raw_event.value, unit="%")]

    elif schema_family == "topic.power.v1":
        # Power sensors - create all 4 expected metrics
        # RawSensorEvent sends power_kw as primary metric, we create the others
        power_kw = raw_event.value
        metrics = [
            Metric(name="power", value=power_kw, unit="kW"),
            Metric(name="voltage", value=48.0, unit="V"),  # Default voltage
            Metric(name="current", value=power_kw * 1000 / 48.0, unit="A"),  # Calculated current
            Metric(name="cumulative", value=power_kw * 24.0, unit="kWh"),  # Estimated daily cumulative
        ]
        status = None

    elif schema_family == "topic.environment.v1":
        # Environment sensors - RawSensorEvent creates one event per measurement
        unit = ENVIRONMENT_UNIT_MAP.get(raw_event.type, "")
        metrics = [Metric(name=raw_event.type, value=raw_event.value, unit=unit)]

    elif schema_family == "topic.thermal_loop.v1":
        # Thermal loop - create both temperature and flow metrics
        temperature = raw_event.value
        metrics = [
            Metric(name="temperature", value=temperature, unit="°C"),
            Metric(name="flow", value=12.5, unit="L/min"),  # Default flow value
        ]

    elif schema_family == "topic.airlock.v1":
        # Airlock - RawSensorEvent sends cycles_per_hour as primary metric
        metrics = [Metric(name="cycles_per_hour", value=raw_event.value, unit="cycles/h")]
        state_label = "IDLE"  # Default state since RawSensorEvent doesn't have last_state

    return UnifiedEvent(
        event_id=str(uuid4()),
        source_type=source_type,
        source_id=effective_source_id,
        schema_family=schema_family,
        timestamp=timestamp,
        metrics=metrics,
        status=status,
        state_label=state_label,
        raw=dict(raw),
    )


def _infer_unit(sensor_id: str, metric_type: str) -> str:
    """Infer unit based on sensor_id and metric type"""
    if sensor_id in ["greenhouse_temperature"]:
        return "°C"
    elif sensor_id in ["entrance_humidity"]:
        return "%"
    elif sensor_id in ["co2_hall"]:
        return "ppm"
    elif sensor_id in ["corridor_pressure"]:
        return "Pa"
    elif sensor_id in ["hydroponic_ph"]:
        return "pH"
    elif sensor_id in ["air_quality_voc"]:
        return "ppb"
    elif sensor_id in ["radiation"]:
        return "µSv/h"
    elif sensor_id in ["life_support"]:
        return _infer_life_support_unit(metric_type)
    else:
        return ""


def _infer_life_support_unit(metric_type: str) -> str:
    """Infer unit for life support metrics"""
    if "oxygen" in metric_type.lower():
        return "%"
    elif "co2" in metric_type.lower():
        return "ppm"
    elif "pressure" in metric_type.lower():
        return "Pa"
    elif "humidity" in metric_type.lower():
        return "%"
    elif "temperature" in metric_type.lower():
        return "°C"
    else:
        return ""

