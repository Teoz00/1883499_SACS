import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.api import router as api_router
from app.routes.health import router as health_router
from app.routes.cache import router as cache_router

logger = logging.getLogger(__name__)

# Global caches for latest data
latest_sensor_data: dict = {}
latest_actuator_data: dict = {}

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application for API Gateway.
    Sets up CORS, routes, and global caches for sensor/actuator data.
    """
    app = FastAPI(title="API Gateway")

    # Enable CORS for frontend access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(api_router)
    app.include_router(cache_router)

    return app


app = create_app()

