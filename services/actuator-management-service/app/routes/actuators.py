from fastapi import APIRouter, status

from app.services.command_executor import execute_actuator_command
from app.services.simulator_client import fetch_actuator_states


router = APIRouter(prefix="/actuators", tags=["actuators"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="List current actuator states",
)
async def list_actuators() -> dict:
    """
    Return the current state of all actuators as reported by the simulator.

    Shape:
    {
      "actuators": [
        {"id": "cooling_fan", "state": "ON"},
        ...
      ]
    }
    """
    states = await fetch_actuator_states()
    return {
      "actuators": [
        {"id": actuator_id, "state": state}
        for actuator_id, state in sorted(states.items())
      ]
    }


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

