import time
import logging
from typing import Dict, Tuple, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("tracelink.ratelimit")

class TokenBucketRateLimiter:
    """
    In-memory Token Bucket rate limiter designed for institutional forensic workstations.
    Supports per-officer/badge and per-client-IP throttling with automatic bucket replenishment.
    """
    def __init__(self, default_rate: float = 60.0, default_capacity: int = 60):
        # default_rate: tokens added per minute
        # default_capacity: max burst capacity
        self.rate = default_rate / 60.0  # tokens per second
        self.capacity = float(default_capacity)
        # key -> (tokens, last_update_timestamp)
        self.buckets: Dict[str, Tuple[float, float]] = {}

    def is_allowed(self, key: str, cost: float = 1.0) -> Tuple[bool, int, int]:
        """
        Check if request is allowed.
        Returns: (allowed: bool, remaining_tokens: int, reset_seconds: int)
        """
        now = time.time()
        if key not in self.buckets:
            self.buckets[key] = (self.capacity - cost, now)
            return True, int(self.capacity - cost), 0

        tokens, last_update = self.buckets[key]
        elapsed = now - last_update
        # Replenish tokens based on elapsed time
        tokens = min(self.capacity, tokens + (elapsed * self.rate))

        if tokens >= cost:
            tokens -= cost
            self.buckets[key] = (tokens, now)
            return True, int(tokens), 0
        else:
            self.buckets[key] = (tokens, now)
            # Seconds until at least 1 token is available
            needed = cost - tokens
            reset_secs = int(needed / self.rate) + 1 if self.rate > 0 else 60
            return False, int(tokens), reset_secs

    def reset(self, key: Optional[str] = None):
        if key:
            self.buckets.pop(key, None)
        else:
            self.buckets.clear()

limiter = TokenBucketRateLimiter(default_rate=120.0, default_capacity=120)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware enforcing token-bucket rate limits on all API endpoints.
    Allows exempting /health and static assets.
    """
    def __init__(self, app, limiter_instance: Optional[TokenBucketRateLimiter] = None):
        super().__init__(app)
        self.limiter = limiter_instance or limiter

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Exempt health checks and options requests
        if request.method == "OPTIONS" or path in ("/health", "/api/health", "/docs", "/openapi.json"):
            return await call_next(request)

        # Identifier: authorization token or client IP
        auth_header = request.headers.get("Authorization", "")
        client_ip = request.client.host if request.client else "127.0.0.1"
        key = auth_header if auth_header else client_ip

        allowed, remaining, reset_secs = self.limiter.is_allowed(key)

        if not allowed:
            logger.warning(f"Rate limit exceeded for client {client_ip} on path {path}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Too many forensic query requests.",
                    "retry_after_seconds": reset_secs
                },
                headers={
                    "Retry-After": str(reset_secs),
                    "X-RateLimit-Limit": str(int(self.limiter.capacity)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_secs)
                }
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(int(self.limiter.capacity))
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
