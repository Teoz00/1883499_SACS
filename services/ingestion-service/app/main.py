import asyncio
import logging

from fastapi import FastAPI

from app.kafka.producer import RawEventsProducer
from app.routes.health import router as health_router
from app.services.poller import run_poller


logger = logging.getLogger(__name__)

producer: RawEventsProducer | None = None
poller_task: asyncio.Task | None = None
stop_event: asyncio.Event | None = None


def create_app() -> FastAPI:
    # Basic logging configuration for the service.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    app = FastAPI(title="Ingestion Service")

    app.include_router(health_router, prefix="/health", tags=["health"])

    @app.on_event("startup")
    async def on_startup() -> None:
        global producer, poller_task, stop_event

        logger.info("Starting ingestion service components.")

        loop = asyncio.get_event_loop()
        producer = RawEventsProducer(loop=loop)
        await producer.start()

        stop_event = asyncio.Event()
        poller_task = loop.create_task(
            run_poller(producer=producer, stop_event=stop_event),
            name="ingestion-poller",
        )

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        global producer, poller_task, stop_event

        logger.info("Shutting down ingestion service components.")

        if stop_event is not None:
            stop_event.set()

        if poller_task is not None:
            poller_task.cancel()
            try:
                await poller_task
            except asyncio.CancelledError:
                logger.info("Polling task cancelled successfully.")
            poller_task = None

        if producer is not None:
            await producer.stop()
            producer = None

    return app


app = create_app()


