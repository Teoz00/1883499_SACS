import logging
from typing import Mapping, Any
from uuid import uuid4
from datetime import datetime

from pydantic import BaseModel, ValidationError

from app.models.unified_event import UnifiedEvent, Metric

logger = logging.getLogger(__name__)

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


def transform_raw_event(raw: Mapping[str, Any]) -> UnifiedEvent | None:
    """
    Normalize raw event into UnifiedEvent with proper metrics mapping.
    The raw message contains the full simulator payload with all fields.
    """
    sensor_id = raw.get("sensor_id")
    if not sensor_id:
        logger.error("Missing sensor_id in raw payload")
        return None

    schema_family = SCHEMA_FAMILY_MAP.get(sensor_id)
    if schema_family is None:
        logger.warning(f"Unknown sensor_id '{sensor_id}', skipping")
        return None

    source_type = "telemetry" if schema_family.startswith("topic.") else "rest"

    # For thermal_loop, use "thermal_loop" as source_id regardless of actual sensor_id
    effective_source_id = "thermal_loop" if schema_family == "topic.thermal_loop.v1" else sensor_id

    # Parse timestamp from raw dict
    timestamp_str = raw.get("event_time") or raw.get("captured_at")
    if not timestamp_str:
        logger.error(f"Missing timestamp in payload for sensor {sensor_id}")
        return None
    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

    # Create metrics based on schema family and available data
    metrics = []
    status = raw.get("status")
    state_label = None

    try:
        if schema_family == "rest.scalar.v1":
            # Single metric sensors - metric, value, unit from payload
            metrics = [Metric(name=raw["metric"], value=raw["value"], unit=raw["unit"])]

        elif schema_family == "rest.chemistry.v1":
            # Multi-metric sensors - measurements array
            metrics = [Metric(name=m["metric"], value=m["value"], unit=m["unit"])
                       for m in raw["measurements"]]

        elif schema_family == "rest.particulate.v1":
            # Particulate sensors - pm1, pm25, pm10 fields
            metrics = [
                Metric(name="pm1",  value=raw["pm1_ug_m3"],  unit="ug/m3"),
                Metric(name="pm25", value=raw["pm25_ug_m3"], unit="ug/m3"),
                Metric(name="pm10", value=raw["pm10_ug_m3"], unit="ug/m3"),
            ]

        elif schema_family == "rest.level.v1":
            # Water tank level - level_pct and level_liters
            metrics = [
                Metric(name="level_pct",    value=raw["level_pct"],    unit="%"),
                Metric(name="level_liters", value=raw["level_liters"], unit="L"),
            ]

        elif schema_family == "topic.power.v1":
            # Power sensors - power_kw, voltage_v, current_a, cumulative_kwh
            metrics = [
                Metric(name="power",      value=raw["power_kw"],       unit="kW"),
                Metric(name="voltage",    value=raw["voltage_v"],      unit="V"),
                Metric(name="current",    value=raw["current_a"],      unit="A"),
                Metric(name="cumulative", value=raw["cumulative_kwh"], unit="kWh"),
            ]

        elif schema_family == "topic.environment.v1":
            # Environment sensors - measurements array with proper units
            unit_map = {"radiation_uSv_h": "µSv/h", "oxygen_percent": "%"}
            metrics = [
                Metric(
                    name=m["metric"],
                    value=m["value"],
                    unit=m.get("unit") or unit_map.get(m["metric"], "")
                )
                for m in raw["measurements"]
            ]

        elif schema_family == "topic.thermal_loop.v1":
            # Thermal loop - temperature_c and flow_l_min
            metrics = [
                Metric(name="temperature", value=raw["temperature_c"], unit="°C"),
                Metric(name="flow",        value=raw["flow_l_min"],    unit="L/min"),
            ]

        elif schema_family == "topic.airlock.v1":
            # Airlock - cycles_per_hour and last_state
            metrics = [
                Metric(name="cycles_per_hour", value=raw["cycles_per_hour"], unit="cycles/h"),
            ]
            state_label = raw.get("last_state", "IDLE")

    except KeyError as exc:
        logger.error(
            "Missing expected field %s in payload for sensor %s", exc, sensor_id
        )
        return None

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

