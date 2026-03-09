import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from app.kafka.consumer import ActuatorCommandsConsumer
from app.kafka.producer import ActuatorEventsProducer, build_actuator_event
from app.services.simulator_client import CommandLiteral, send_actuator_command


logger = logging.getLogger(__name__)


_MANUAL_OVERRIDE_WINDOW = timedelta(seconds=15)
_recent_manual_overrides: dict[str, datetime] = {}
_events_producer: ActuatorEventsProducer | None = None
_producer_lock = asyncio.Lock()


async def _get_events_producer() -> ActuatorEventsProducer | None:
  """
  Lazily initialize and return the actuator events producer.
  """
  global _events_producer

  if _events_producer is not None:
      return _events_producer

  async with _producer_lock:
      if _events_producer is None:
          producer = ActuatorEventsProducer()
          try:
              await producer.start()
              _events_producer = producer
          except Exception as exc:  # pragma: no cover - defensive
              logger.error("Failed to start actuator events producer: %s", exc)
              return None

  return _events_producer


async def _publish_actuator_event(actuator_id: str, command: CommandLiteral) -> None:
    producer = await _get_events_producer()
    if producer is None:
        return

    payload = build_actuator_event(actuator_id=actuator_id, state=command)
    await producer.publish_event(payload)


async def execute_actuator_command(
    actuator_id: str,
    command: CommandLiteral,
) -> None:
    """
    Execute a single actuator command by forwarding it to the simulator.
    Also records a short-lived manual override window during which
    automatic commands from rules are ignored for this actuator.
    """
    now = datetime.now(timezone.utc)
    _recent_manual_overrides[actuator_id] = now + _MANUAL_OVERRIDE_WINDOW

    logger.info(
        "Executing manual actuator command: actuator_id=%s command=%s (override until %s)",
        actuator_id,
        command,
        _recent_manual_overrides[actuator_id].isoformat(),
    )
    await send_actuator_command(actuator_id, command)
    await _publish_actuator_event(actuator_id, command)


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

    now = datetime.now(timezone.utc)
    override_until = _recent_manual_overrides.get(actuator_id)
    if override_until and override_until > now:
        logger.info(
            "Ignoring automatic actuator command due to recent manual override: "
            "actuator_id=%s command=%s override_until=%s",
            actuator_id,
            command,
            override_until.isoformat(),
        )
        return

    logger.info(
        "Processing automatic actuator command from Kafka: actuator_id=%s command=%s",
        actuator_id,
        command,
    )
    await send_actuator_command(actuator_id, command)  # type: ignore[arg-type]
    await _publish_actuator_event(actuator_id, command)  # type: ignore[arg-type]


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

