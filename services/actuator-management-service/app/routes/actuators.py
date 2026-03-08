from fastapi import APIRouter, status

from app.services.command_executor import execute_actuator_command


router = APIRouter(prefix="/actuators", tags=["actuators"])


@router.post(
    "/{actuator_id}/on",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Turn actuator ON manually",
)
async def actuator_on(actuator_id: str) -> dict:
    await execute_actuator_command(actuator_id, "ON")
    return {"actuator_id": actuator_id, "command": "ON"}


@router.post(
    "/{actuator_id}/off",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Turn actuator OFF manually",
)
async def actuator_off(actuator_id: str) -> dict:
    await execute_actuator_command(actuator_id, "OFF")
    return {"actuator_id": actuator_id, "command": "OFF"}

