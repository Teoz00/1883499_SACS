from fastapi import FastAPI

from .routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="Rule Management Service")

    app.include_router(health_router, prefix="/health", tags=["health"])

    # Placeholders for CRUD rule endpoints are defined in the routes package.

    return app


app = create_app()

