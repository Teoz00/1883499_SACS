import logging
from typing import Literal

import httpx

from app.config import settings


logger = logging.getLogger(__name__)


CommandLiteral = Literal["ON", "OFF"]


async def send_actuator_command(actuator_id: str, command: CommandLiteral) -> None:
    """
    Send an actuator command to the external simulator.

    Logs errors and returns None on failure.
    """
    if not settings.simulator_base_url:
        logger.warning(
            "SIMULATOR_BASE_URL is not configured; "
            "skipping actuator command for actuator_id=%s command=%s",
            actuator_id,
            command,
        )
        return

    url = f"{settings.simulator_base_url}/actuators/{actuator_id}"
    payload = {"command": command}

    logger.info("Sending actuator command to simulator: url=%s payload=%s", url, payload)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error(
            "Failed to send actuator command to simulator at %s: %s", url, exc
        )
        return

    logger.info(
        "Actuator command successfully sent to simulator: actuator_id=%s command=%s",
        actuator_id,
        command,
    )

