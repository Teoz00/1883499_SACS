"""
Cache endpoints for latest sensor and actuator data.
"""
from fastapi import APIRouter

from app.state import latest_sensor_data, latest_actuator_data

router = APIRouter(prefix="/cache", tags=["cache"])

@router.get("/sensors/latest")
async def get_latest_sensors() -> dict:
    """Return latest sensor data from API Gateway cache."""
    return {"sensors": latest_sensor_data}

@router.get("/actuators/latest")
async def get_latest_actuators() -> dict:
    """Return latest actuator data from API Gateway cache."""
    return {"actuators": latest_actuator_data}

@router.post("/sensors/update")
async def update_sensor_cache(data: dict) -> dict:
    """Update sensor cache. Called by realtime service."""
    
    # Use source_id for new UnifiedEvent schema, fallback to sensor_id for compatibility
    source_id = data.get("source_id") or data.get("sensor_id")
    if source_id:
        latest_sensor_data[source_id] = data
    return {"status": "ok"}

@router.post("/actuators/update")
async def update_actuator_cache(data: dict) -> dict:
    """Update actuator cache. Called by actuator management service."""
    
    actuator_id = data.get("actuator_id")
    if actuator_id:
        # Store only the state, not the entire data object
        latest_actuator_data[actuator_id] = {
            "actuator_id": actuator_id,
            "state": data.get("state", "OFF"),
            "timestamp": data.get("timestamp")
        }
    return {"status": "ok"}
