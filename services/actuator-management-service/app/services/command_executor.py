import asyncio
import logging
from typing import Mapping, Any

from app.kafka.consumer import ActuatorCommandsConsumer
from app.services.simulator_client import CommandLiteral, send_actuator_command


logger = logging.getLogger(__name__)


async def execute_actuator_command(
    actuator_id: str,
    command: CommandLiteral,
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


async def _process_command_payload(payload: Mapping[str, Any]) -> None:
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


async def run_command_processor(
    consumer: ActuatorCommandsConsumer,
    stop_event: asyncio.Event,
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
                await _process_command_payload(payload)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Error while processing actuator command: %s", exc)
    except asyncio.CancelledError:
        logger.info("Actuator command processing loop cancelled.")
        raise
    finally:
        logger.info("Actuator command processing loop stopped.")

