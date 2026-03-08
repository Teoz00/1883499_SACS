"""
Proxy routes: /api/sensors, /api/actuators, /api/rules forward to backend services.
"""
from fastapi import APIRouter, Request
from starlette.responses import Response

from app.config import settings
from app.services.proxy import proxy_request

router = APIRouter(prefix="/api", tags=["api"])

# HTTP methods we forward (match typical REST + actuator POSTs)
METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


def _path_with_prefix(prefix: str, path: str) -> str:
    if path:
        return f"{prefix}/{path}".rstrip("/")
    return prefix.rstrip("/")


@router.api_route("/sensors/{path:path}", methods=METHODS)
async def proxy_sensors(request: Request, path: str) -> Response:
    """Forward /api/sensors/** to the sensors backend (simulator)."""
    backend_path = _path_with_prefix("/sensors", path)
    return await proxy_request(settings.sensors_service_url, backend_path, request)


@router.api_route("/actuators/{path:path}", methods=METHODS)
async def proxy_actuators(request: Request, path: str) -> Response:
    """Forward /api/actuators/** to the actuator-management-service."""
    backend_path = _path_with_prefix("/actuators", path)
    return await proxy_request(settings.actuators_service_url, backend_path, request)


@router.api_route("/rules/{path:path}", methods=METHODS)
async def proxy_rules(request: Request, path: str) -> Response:
    """Forward /api/rules/** to the rule-management-service."""
    backend_path = _path_with_prefix("/rules", path)
    return await proxy_request(settings.rules_service_url, backend_path, request)
