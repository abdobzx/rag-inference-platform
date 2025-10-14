from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from typing import Dict, Optional, List
from collections import defaultdict
import asyncio
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self, requests_per_minute: int = 60, burst_limit: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.requests: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str) -> tuple[bool, Optional[Dict[str, int]]]:
        """Check if request is allowed under rate limit"""
        async with self._lock:
            now = time.time()
            # Clean old requests (older than 1 minute)
            self.requests[key] = [req_time for req_time in self.requests[key] if now - req_time < 60]

            current_requests = len(self.requests[key])

            # Check burst limit (requests in last few seconds)
            recent_requests = [req_time for req_time in self.requests[key] if now - req_time < 10]
            if len(recent_requests) >= self.burst_limit:
                reset_time = recent_requests[0] + 10
                return False, {
                    "retry_after": int(reset_time - now),
                    "limit": self.burst_limit,
                    "remaining": 0,
                    "reset": int(reset_time)
                }

            # Check per-minute limit
            if current_requests >= self.requests_per_minute:
                reset_time = self.requests[key][0] + 60
                return False, {
                    "retry_after": int(reset_time - now),
                    "limit": self.requests_per_minute,
                    "remaining": 0,
                    "reset": int(reset_time)
                }

            # Add current request
            self.requests[key].append(now)

            remaining = self.requests_per_minute - (current_requests + 1)
            reset_time = now + 60 if self.requests[key] else now + 60

            return True, {
                "limit": self.requests_per_minute,
                "remaining": max(0, remaining),
                "reset": int(reset_time)
            }

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI"""

    def __init__(self, app, rate_limiter: RateLimiter, exclude_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Create rate limit key (could be IP, user ID, API key, etc.)
        client_ip = self._get_client_ip(request)
        rate_limit_key = f"ip:{client_ip}"

        # Check rate limit
        allowed, rate_limit_info = await self.rate_limiter.is_allowed(rate_limit_key)

        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
            if rate_limit_info:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "Retry-After": str(rate_limit_info["retry_after"]),
                        "X-RateLimit-Limit": str(rate_limit_info["limit"]),
                        "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
                        "X-RateLimit-Reset": str(rate_limit_info["reset"])
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )

        # Add rate limit headers to response
        response = await call_next(request)

        # Set rate limit headers
        if rate_limit_info:
            response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset"])

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers (useful behind proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP if multiple are present
            return forwarded_for.split(",")[0].strip()

        # Check for other proxy headers
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client host
        client_host = getattr(request.client, 'host', None) if request.client else None
        return client_host or "unknown"

# Global rate limiter instance
rate_limiter = RateLimiter(
    requests_per_minute=int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60")),
    burst_limit=int(os.getenv("RATE_LIMIT_BURST", "10"))
)