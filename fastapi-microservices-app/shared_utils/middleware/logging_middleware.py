"""
Logging Middleware for SothemaAI Services

This middleware provides automatic request/response logging with correlation IDs,
performance monitoring, and structured logging integration.
"""

import time
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..logging_utils import get_logger, generate_correlation_id, generate_request_id


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response logging."""

    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name
        self.logger = get_logger(service_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation and request IDs
        correlation_id = request.headers.get('X-Correlation-ID', generate_correlation_id())
        request_id = generate_request_id()

        # Add correlation ID to request state for use in handlers
        request.state.correlation_id = correlation_id
        request.state.request_id = request_id

        # Extract client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get('User-Agent')

        # Log the incoming request
        self.logger.log_request(
            method=request.method,
            endpoint=str(request.url.path),
            correlation_id=correlation_id,
            request_id=request_id,
            ip_address=client_ip,
            user_agent=user_agent
        )

        # Record start time
        start_time = time.time()

        try:
            # Process the request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Add correlation ID to response headers
            response.headers['X-Correlation-ID'] = correlation_id
            response.headers['X-Request-ID'] = request_id

            # Extract user ID if available (from auth middleware)
            user_id = getattr(request.state, 'user_id', None)

            # Log the response
            self.logger.log_response(
                method=request.method,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                request_id=request_id,
                user_id=user_id
            )

            return response

        except Exception as e:
            # Calculate duration for error case
            duration_ms = (time.time() - start_time) * 1000

            # Log the error
            self.logger.log_error(
                error=e,
                message=f"Unhandled exception in {request.method} {request.url.path}",
                correlation_id=correlation_id,
                request_id=request_id,
                endpoint=str(request.url.path)
            )

            # Return error response
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
                headers={
                    'X-Correlation-ID': correlation_id,
                    'X-Request-ID': request_id
                }
            )

    def _get_client_ip(self, request: Request) -> str:
        """Extract the real client IP address."""
        # Check for forwarded headers (common in proxy setups)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Take the first IP in case of multiple
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        return request.client.host if request.client else 'unknown'