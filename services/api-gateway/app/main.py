from fastapi import FastAPI

from .routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="API Gateway")

    # Health check
    app.include_router(health_router, prefix="/health", tags=["health"])

    # Placeholder for proxy routes to underlying services
    # Routers for /ingestion, /processing, /rules, /actuators, /realtime would be included here.

    return app


app = create_app()

