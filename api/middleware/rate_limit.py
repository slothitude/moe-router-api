"""Rate limiting middleware."""

import os
from typing import Optional
from fastapi import Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import logging

logger = logging.getLogger(__name__)

# Initialize rate limiter
# Use IP address by default, but can use API key if provided
def _get_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.

    Prioritizes API key over IP address for more accurate per-client limiting.

    Args:
        request: FastAPI request

    Returns:
        Identifier string (API key or IP address)
    """
    # If API key authentication is enabled, use that for rate limiting
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key}"

    # Otherwise use IP address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=_get_identifier,
    default_limits=["60/minute"],  # Default: 60 requests per minute
    storage_uri="memory://",  # Use in-memory storage
    headers_enabled=True  # Include rate limit headers in response
)


def setup_rate_limits(app, enabled: bool = True):
    """
    Set up rate limiting for the application.

    Args:
        app: FastAPI application
        enabled: Whether to enable rate limiting
    """
    if not enabled:
        logger.info("Rate limiting disabled")
        return

    # Check if rate limiting is disabled via environment
    if os.getenv("RATE_LIMIT_DISABLED", "false").lower() == "true":
        logger.info("Rate limiting disabled via environment variable")
        return

    # Add rate limiting to app
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    logger.info("Rate limiting enabled (default: 60 requests/minute)")
