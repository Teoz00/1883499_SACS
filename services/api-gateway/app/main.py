from fastapi import FastAPI

from app.routes.api import router as api_router
from app.routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="API Gateway")

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(api_router)

    return app


app = create_app()

