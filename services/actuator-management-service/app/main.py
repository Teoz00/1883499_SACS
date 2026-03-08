from fastapi import FastAPI

from .routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="Actuator Management Service")

    app.include_router(health_router, prefix="/health", tags=["health"])

    # Placeholder for manual actuator control endpoints and status inspection.

    return app


app = create_app()

