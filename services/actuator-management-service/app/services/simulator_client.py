import logging
from typing import Dict, Literal

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

    base = str(settings.simulator_base_url).rstrip("/")
    # Simulator actuator API: POST /api/actuators/{id} {"state": "ON" | "OFF"}
    url = f"{base}/api/actuators/{actuator_id}"
    payload = {"state": command}

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


async def fetch_actuator_states() -> Dict[str, str]:
    """
    Fetch current actuator states from the simulator.

    Returns a mapping {actuator_id: "ON" | "OFF"}.
    The function is defensive and tries to handle a few reasonable
    response shapes from the simulator.
    """
    states: Dict[str, str] = {}

    if not settings.simulator_base_url:
        logger.warning(
            "SIMULATOR_BASE_URL is not configured; cannot fetch actuator states."
        )
        return states

    base = str(settings.simulator_base_url).rstrip("/")
    url = f"{base}/api/actuators"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch actuator states from simulator at %s: %s", url, exc)
        return states

    # Accept a few possible shapes:
    # 1) {"actuators": [{"id": "...", "state": "ON"}]}
    # 2) [{"id": "...", "state": "ON"}]
    # 3) {"<id>": {"state": "ON"}}
    try:
        if isinstance(data, dict):
            items = data.get("actuators", data)
        else:
            items = data

        if isinstance(items, dict):
            for actuator_id, payload in items.items():
                if isinstance(payload, dict):
                    state = str(payload.get("state", "")).upper()
                    if state in ("ON", "OFF"):
                        states[str(actuator_id)] = state
                elif isinstance(payload, str):
                    # Handle case where simulator returns {"actuators": {"id": "ON"}}
                    state = payload.upper()
                    if state in ("ON", "OFF"):
                        states[str(actuator_id)] = state
        elif isinstance(items, list):
            for entry in items:
                if not isinstance(entry, dict):
                    continue
                actuator_id = entry.get("id") or entry.get("actuator_id")
                state = entry.get("state")
                if isinstance(actuator_id, str) and isinstance(state, str):
                    upper_state = state.upper()
                    if upper_state in ("ON", "OFF"):
                        states[actuator_id] = upper_state
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Error while parsing actuator states from simulator: %s", exc)

    return states


