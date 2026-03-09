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

# Debug route
@router.get("/debug")
async def debug_info():
    return {"message": "API gateway is working", "routes": ["sensors", "actuators", "rules"]}


def _path_with_prefix(prefix: str, path: str) -> str:
    if path:
        return f"{prefix}/{path}".rstrip("/")
    return prefix.rstrip("/")


@router.api_route("/sensors/{path:path}", methods=METHODS)
async def proxy_sensors(request: Request, path: str) -> Response:
    """Forward /api/sensors/** to the sensors backend (simulator)."""
    # Simulator exposes sensors under /api/sensors.
    backend_path = _path_with_prefix("/api/sensors", path)
    return await proxy_request(settings.sensors_service_url, backend_path, request)


@router.api_route("/actuators", methods=METHODS)
async def proxy_actuators_root(request: Request) -> Response:
    """Forward /api/actuators to the actuator-management-service."""
    return await proxy_request(settings.actuators_service_url, "/actuators/", request)


@router.api_route("/rules", methods=METHODS)
async def proxy_rules_root(request: Request) -> Response:
    """Forward /api/rules to the rule-management-service."""
    # Rule management exposes /rules/ with a trailing slash.
    return await proxy_request(settings.rules_service_url, "/rules/", request)


@router.api_route("/rules/{path:path}", methods=METHODS)
async def proxy_rules(request: Request, path: str) -> Response:
    """Forward /api/rules/** to the rule-management-service."""
    backend_path = _path_with_prefix("/rules", path)
    return await proxy_request(settings.rules_service_url, backend_path, request)
