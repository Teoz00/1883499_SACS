"""
Cache endpoints for latest sensor and actuator data.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/cache", tags=["cache"])

@router.get("/sensors/latest")
async def get_latest_sensors() -> dict:
    """Return latest sensor data from API Gateway cache."""
    # Import the global cache from main module
    from app.main import latest_sensor_data
    return {"sensors": latest_sensor_data}

@router.get("/actuators/latest")
async def get_latest_actuators() -> dict:
    """Return latest actuator data from API Gateway cache."""
    # Import the global cache from main module
    from app.main import latest_actuator_data
    return {"actuators": latest_actuator_data}

@router.post("/sensors/update")
async def update_sensor_cache(data: dict) -> dict:
    """Update sensor cache. Called by realtime service."""
    from app.main import latest_sensor_data
    
    sensor_id = data.get("sensor_id")
    if sensor_id:
        latest_sensor_data[sensor_id] = data
    return {"status": "ok"}

@router.post("/actuators/update")
async def update_actuator_cache(data: dict) -> dict:
    """Update actuator cache. Called by actuator management service."""
    from app.main import latest_actuator_data
    
    actuator_id = data.get("actuator_id")
    if actuator_id:
        latest_actuator_data[actuator_id] = data
    return {"status": "ok"}
