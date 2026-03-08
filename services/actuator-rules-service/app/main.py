from fastapi import FastAPI

from .routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="Actuator Rules Service")

    app.include_router(health_router, prefix="/health", tags=["health"])

    # Placeholder for endpoints exposing rules evaluation status and configuration.

    return app


app = create_app()

