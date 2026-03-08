import asyncio
import logging

from fastapi import FastAPI

from app.kafka.consumer import ActuatorCommandsConsumer
from app.routes.health import router as health_router
from app.routes.actuators import router as actuators_router
from app.services.command_executor import run_command_processor


logger = logging.getLogger(__name__)

consumer: ActuatorCommandsConsumer | None = None
processor_task: asyncio.Task | None = None
stop_event: asyncio.Event | None = None


def create_app() -> FastAPI:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    app = FastAPI(title="Actuator Management Service")

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(actuators_router)

    @app.on_event("startup")
    async def on_startup() -> None:
        global consumer, processor_task, stop_event

        logger.info("Starting actuator-management-service components.")

        loop = asyncio.get_event_loop()
        consumer = ActuatorCommandsConsumer(loop=loop)
        await consumer.start()

        stop_event = asyncio.Event()
        processor_task = loop.create_task(
            run_command_processor(consumer=consumer, stop_event=stop_event),
            name="actuator-command-processor",
        )

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        global consumer, processor_task, stop_event

        logger.info("Shutting down actuator-management-service components.")

        if stop_event is not None:
            stop_event.set()

        if processor_task is not None:
            processor_task.cancel()
            try:
                await processor_task
            except asyncio.CancelledError:
                logger.info("Actuator command processor task cancelled successfully.")
            processor_task = None

        if consumer is not None:
            await consumer.stop()
            consumer = None

    return app


app = create_app()

