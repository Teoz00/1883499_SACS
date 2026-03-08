"""
Reverse-proxy logic: forward requests to backend services with error handling.
"""
import logging

import httpx
from fastapi import Request, Response
from starlette.datastructures import Headers as StarletteHeaders

from app.config import settings

logger = logging.getLogger(__name__)

# Headers that should not be forwarded to the backend (hop-by-hop or gateway-specific)
SKIP_REQUEST_HEADERS = frozenset(
    {
        "host",
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }
)


def _build_backend_url(base_url: str, path: str, query: str) -> str:
    base = base_url.rstrip("/")
    path_part = path if path.startswith("/") else f"/{path}"
    if query:
        return f"{base}{path_part}?{query}"
    return f"{base}{path_part}"


def _forward_headers(headers: StarletteHeaders) -> dict[str, str]:
    return {
        k: v
        for k, v in headers.items()
        if k.lower() not in SKIP_REQUEST_HEADERS
    }


async def _read_body(request: Request) -> bytes:
    return await request.body()


async def proxy_request(
    backend_base_url: str,
    path: str,
    request: Request,
) -> Response:
    """
    Forward the incoming request to the backend and return the backend response.
    Raises no exceptions; returns 502/504 response on proxy errors.
    """
    query = request.url.query
    url = _build_backend_url(backend_base_url, path, query)
    headers = _forward_headers(request.headers)
    timeout = httpx.Timeout(settings.proxy_timeout_seconds)
    body = await _read_body(request)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
            )
    except httpx.TimeoutException as exc:
        logger.warning("Backend timeout: %s %s - %s", request.method, url, exc)
        return Response(
            content=b'{"detail":"Backend request timed out"}',
            status_code=504,
            media_type="application/json",
        )
    except httpx.ConnectError as exc:
        logger.warning("Backend connection error: %s %s - %s", request.method, url, exc)
        return Response(
            content=b'{"detail":"Backend service unavailable"}',
            status_code=502,
            media_type="application/json",
        )
    except Exception as exc:
        logger.exception("Unexpected error proxying to backend: %s", exc)
        return Response(
            content=b'{"detail":"Gateway error"}',
            status_code=502,
            media_type="application/json",
        )

    # Build response; skip hop-by-hop and transfer-encoding from backend
    skip_response_headers = frozenset(
        {"transfer-encoding", "connection", "keep-alive"}
    )
    response_headers = [
        (k, v)
        for k, v in response.headers.items()
        if k.lower() not in skip_response_headers
    ]

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=response_headers,
        media_type=response.headers.get("content-type"),
    )
