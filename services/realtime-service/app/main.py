from fastapi import FastAPI, WebSocket

from .routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="Realtime Service")

    app.include_router(health_router, prefix="/health", tags=["health"])

    # Placeholder WebSocket endpoint. In a full implementation this
    # would broadcast Kafka events to connected clients.
    @app.websocket("/ws")
    async def websocket_endpoint(_ws: WebSocket) -> None:  # pragma: no cover - placeholder
        await _ws.accept()
        await _ws.send_json({"detail": "realtime websocket placeholder"})
        await _ws.close()

    return app


app = create_app()

