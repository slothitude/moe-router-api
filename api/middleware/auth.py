"""API key authentication middleware."""

import os
from typing import List, Optional
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging

logger = logging.getLogger(__name__)

# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to check API keys for protected endpoints."""

    def __init__(
        self,
        app,
        api_keys: Optional[List[str]] = None,
        excluded_paths: Optional[List[str]] = None
    ):
        """
        Initialize API key middleware.

        Args:
            app: ASGI application
            api_keys: List of valid API keys (if None, uses API_KEYS env var)
            excluded_paths: Paths that don't require authentication
        """
        super().__init__(app)

        # Load API keys from environment if not provided
        if api_keys is None:
            env_keys = os.getenv("API_KEYS", "")
            api_keys = [k.strip() for k in env_keys.split(",") if k.strip()]

        self.api_keys = set(api_keys) if api_keys else set()

        # Paths that don't require authentication
        self.excluded_paths = excluded_paths or [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health",
            "/api/v1/metrics/prometheus",
            "/ws"  # WebSocket endpoints
        ]

        # Log configuration
        if self.api_keys:
            logger.info(f"API key authentication enabled for {len(self.api_keys)} keys")
        else:
            logger.warning("API key authentication DISABLED - no keys configured")

    async def dispatch(self, request: Request, call_next):
        """
        Process request and check API key.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response from handler or 401 if unauthorized
        """
        # Check if path is excluded
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # If no API keys configured, allow all requests (development mode)
        if not self.api_keys:
            return await call_next(request)

        # Check API key
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            logger.warning(f"Unauthorized request to {request.url.path}: No API key")
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required. Include X-API-Key header."
            )

        if api_key not in self.api_keys:
            logger.warning(f"Unauthorized request to {request.url.path}: Invalid API key")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key"
            )

        # API key is valid
        return await call_next(request)


async def verify_api_key(api_key: str = Security(api_key_header)) -> bool:
    """
    Verify API key for endpoint-level security.

    Args:
        api_key: API key from header

    Returns:
        True if valid

    Raises:
        HTTPException: If API key is invalid
    """
    # Load API keys from environment
    env_keys = os.getenv("API_KEYS", "")
    valid_keys = set(k.strip() for k in env_keys.split(",") if k.strip())

    # If no keys configured, allow all (development mode)
    if not valid_keys:
        return True

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )

    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )

    return True
