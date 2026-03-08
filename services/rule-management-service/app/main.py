import logging

from fastapi import FastAPI

from app.config import init_db
from app.routes.health import router as health_router
from app.routes.rules import router as rules_router


def create_app() -> FastAPI:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    app = FastAPI(title="Rule Management Service")

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(rules_router, tags=["rules"])

    @app.on_event("startup")
    async def on_startup() -> None:
        await init_db()

    return app


app = create_app()

