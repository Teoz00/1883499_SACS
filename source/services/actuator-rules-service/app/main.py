import asyncio
import logging

from fastapi import FastAPI

from app.config import settings
from app.kafka.client import ActuatorCommandsProducer, NormalizedEventsConsumer
from app.routes.health import router as health_router
from app.services.rule_engine import RuleEngine
from app.services.rules_processor import run_rules_processor
from app.services.rules_repository import RulesRepository


logger = logging.getLogger(__name__)

consumer: NormalizedEventsConsumer | None = None
producer: ActuatorCommandsProducer | None = None
rules_repository: RulesRepository | None = None
rule_engine: RuleEngine | None = None
processor_task: asyncio.Task | None = None
stop_event: asyncio.Event | None = None


def create_app() -> FastAPI:
    # Basic logging configuration for the service.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    app = FastAPI(title="Actuator Rules Service")

    app.include_router(health_router, prefix="/health", tags=["health"])

    @app.on_event("startup")
    async def on_startup() -> None:
        global consumer, producer, rules_repository, rule_engine, processor_task, stop_event

        logger.info("Starting actuator-rules-service components.")

        loop = asyncio.get_event_loop()

        consumer = NormalizedEventsConsumer(loop=loop)
        producer = ActuatorCommandsProducer(loop=loop)
        rules_repository = RulesRepository(database_url=str(settings.database_url))
        rule_engine = RuleEngine()

        await consumer.start()
        await producer.start()
        await rules_repository.start()

        stop_event = asyncio.Event()
        processor_task = loop.create_task(
            run_rules_processor(
                consumer=consumer,
                producer=producer,
                rules_repository=rules_repository,
                rule_engine=rule_engine,
                stop_event=stop_event,
            ),
            name="rules-processing-loop",
        )

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        global consumer, producer, rules_repository, rule_engine, processor_task, stop_event

        logger.info("Shutting down actuator-rules-service components.")

        if stop_event is not None:
            stop_event.set()

        if processor_task is not None:
            processor_task.cancel()
            try:
                await processor_task
            except asyncio.CancelledError:
                logger.info("Rules processing loop task cancelled successfully.")
            processor_task = None

        if consumer is not None:
            await consumer.stop()
            consumer = None

        if producer is not None:
            await producer.stop()
            producer = None

        if rules_repository is not None:
            await rules_repository.stop()
            rules_repository = None

        rule_engine = None

    return app


app = create_app()

