import asyncio
import logging

from app.kafka.client import ActuatorCommandsProducer, NormalizedEventsConsumer
from app.services.rule_engine import RuleEngine
from app.services.rules_repository import RulesRepository


logger = logging.getLogger(__name__)


async def run_rules_processor(
    consumer: NormalizedEventsConsumer,
    producer: ActuatorCommandsProducer,
    rules_repository: RulesRepository,
    rule_engine: RuleEngine,
    stop_event: asyncio.Event,
) -> None:
    """
    Background loop that:
      - consumes normalized events from Kafka
      - loads enabled rules from the repository
      - evaluates rules against the event
      - publishes actuator commands for matched rules
    """
    logger.info("Starting rules processing loop for normalized events → actuator commands.")

    try:
        async for event in consumer.iter_events():
            if stop_event.is_set():
                break

            try:
                rules = await rules_repository.get_rules()
                commands = rule_engine.evaluate_event(event, rules)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to evaluate rules for event: %s", exc)
                continue

            for command in commands:
                await producer.publish_actuator_command(command)
    except asyncio.CancelledError:
        logger.info("Rules processing loop cancelled.")
        raise
    finally:
        logger.info("Rules processing loop stopped.")

