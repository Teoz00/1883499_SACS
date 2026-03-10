import asyncio
import logging
from datetime import datetime, timezone
from typing import Mapping, Any
import httpx

from app.kafka.consumer import ActuatorCommandsConsumer
from app.services.simulator_client import CommandLiteral, send_actuator_command


logger = logging.getLogger(__name__)


async def update_actuator_cache(actuator_id: str, state: str) -> None:
    """Update actuator state cache in API Gateway."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            cache_data = {
                "actuator_id": actuator_id,
                "state": state,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            # Send to API Gateway cache endpoint
            response = await client.post(
                "http://api-gateway:8000/cache/actuators/update",
                json=cache_data
            )
            if response.status_code == 200:
                logger.debug(f"Updated actuator cache: {actuator_id} -> {state}")
            else:
                logger.warning(f"Failed to update actuator cache: {response.status_code}")
    except Exception as exc:
        logger.warning(f"Failed to update actuator cache: {exc}")


async def execute_actuator_command(
    actuator_id: str,
    command: CommandLiteral,
    ws_manager=None,
) -> None:
    """
    Execute a single actuator command by forwarding it to the simulator.
    """
    logger.info(
        "Executing manual actuator command: actuator_id=%s command=%s",
        actuator_id,
        command,
    )
    await send_actuator_command(actuator_id, command)
    
    # Update cache in realtime service
    await update_actuator_cache(actuator_id, command)
    
    # Broadcast actuator state change to WebSocket clients
    if ws_manager:
        await ws_manager.broadcast_json({
            "actuator_id": actuator_id,
            "state": command,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })


async def _process_command_payload(payload: Mapping[str, Any], ws_manager) -> None:
    """
    Process a single command payload received from Kafka.
    """
    actuator_id = payload.get("actuator_id")
    command = payload.get("command")

    if not actuator_id or not isinstance(actuator_id, str):
        logger.error("Received actuator command without valid 'actuator_id': %s", payload)
        return

    if command not in ("ON", "OFF"):
        logger.error(
            "Received actuator command with invalid 'command' field: %s", payload
        )
        return

    logger.info(
        "Processing automatic actuator command from Kafka: actuator_id=%s command=%s",
        actuator_id,
        command,
    )
    await send_actuator_command(actuator_id, command)  # type: ignore[arg-type]
    
    # Update cache in realtime service
    await update_actuator_cache(actuator_id, command)
    
    # Broadcast actuator state change to WebSocket clients
    if ws_manager:
        await ws_manager.broadcast_json({
            "actuator_id": actuator_id,
            "state": command,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })


async def run_command_processor(
    consumer: ActuatorCommandsConsumer,
    stop_event: asyncio.Event,
    ws_manager,
) -> None:
    """
    Background loop that:
      - consumes actuator commands from Kafka
      - forwards them to the simulator API.
    """
    logger.info("Starting actuator command processing loop.")

    try:
        async for payload in consumer.iter_commands():
            if stop_event.is_set():
                break

            try:
                await _process_command_payload(payload, ws_manager)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Error while processing actuator command: %s", exc)
    except asyncio.CancelledError:
        logger.info("Actuator command processing loop cancelled.")
        raise
    finally:
        logger.info("Actuator command processing loop stopped.")

