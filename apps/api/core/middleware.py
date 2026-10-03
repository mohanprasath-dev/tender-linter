"""Request tracing, context, and structured logging middleware for Tender Linter API.
Ensures every request has a traceable X-Request-ID, logs response metrics,
and catches unhandled errors cleanly.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable to make request_id accessible in downstream logging or services
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
logger = logging.getLogger("tender_linter.access")


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Middleware that injects and traces X-Request-ID and logs access metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract existing X-Request-ID or generate new unique identifier
        req_id = request.headers.get("X-Request-ID")
        if not req_id or not req_id.strip():
            req_id = f"req_{uuid.uuid4().hex[:16]}"

        request.state.request_id = req_id
        token = request_id_ctx.set(req_id)

        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Ensure response carries X-Request-ID header
            response.headers["X-Request-ID"] = req_id

            # Emit structured access log
            logger.info(
                "%s %s %s %sms request_id=%s ip=%s",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                req_id,
                client_ip,
            )
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "UNCAUGHT_ERROR %s %s %sms request_id=%s ip=%s error=%s",
                request.method,
                request.url.path,
                duration_ms,
                req_id,
                client_ip,
                str(exc),
                exc_info=True,
            )
            raise
        finally:
            request_id_ctx.reset(token)
