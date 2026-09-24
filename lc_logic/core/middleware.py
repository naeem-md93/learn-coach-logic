"""HTTP request/response logging middleware."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger("lc_logic.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs one line per request: method, path, status code, duration (ms).

    Deliberately does not log query strings or headers here — request/response
    bodies and any sensitive values (e.g. the signed `file_url` token on
    /extract-title) are logged, if at all, by the endpoint/service layer with
    explicit masking. This middleware only sees the generic HTTP envelope.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "%s %s -> unhandled error (%.1fms)",
                request.method,
                request.url.path,
                duration_ms,
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
