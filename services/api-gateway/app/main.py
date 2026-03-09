from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.api import router as api_router
from app.routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="API Gateway")

    # Allow browser apps (Vite dev server, etc.) to call the gateway.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(api_router)

    return app


app = create_app()

