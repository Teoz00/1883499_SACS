import asyncio
import logging

from fastapi import FastAPI

from app.kafka.consumer import RawEventsConsumer
from app.kafka.producer import NormalizedEventsProducer
from app.routes.health import router as health_router
from app.services.event_processor import run_event_processor


logger = logging.getLogger(__name__)

consumer: RawEventsConsumer | None = None
producer: NormalizedEventsProducer | None = None
processor_task: asyncio.Task | None = None
stop_event: asyncio.Event | None = None


def create_app() -> FastAPI:
    # Basic logging configuration for the service.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    app = FastAPI(title="Processing Service")

    app.include_router(health_router, prefix="/health", tags=["health"])

    @app.on_event("startup")
    async def on_startup() -> None:
        global consumer, producer, processor_task, stop_event

        logger.info("Starting processing service components.")

        loop = asyncio.get_event_loop()
        consumer = RawEventsConsumer(loop=loop)
        producer = NormalizedEventsProducer(loop=loop)

        await consumer.start()
        await producer.start()

        stop_event = asyncio.Event()
        processor_task = loop.create_task(
            run_event_processor(
                consumer=consumer,
                producer=producer,
                stop_event=stop_event,
            ),
            name="processing-loop",
        )

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        global consumer, producer, processor_task, stop_event

        logger.info("Shutting down processing service components.")

        if stop_event is not None:
            stop_event.set()

        if processor_task is not None:
            processor_task.cancel()
            try:
                await processor_task
            except asyncio.CancelledError:
                logger.info("Processing loop task cancelled successfully.")
            processor_task = None

        if consumer is not None:
            await consumer.stop()
            consumer = None

        if producer is not None:
            await producer.stop()
            producer = None

    return app


app = create_app()


