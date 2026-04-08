"""CORS middleware configuration."""

from fastapi.middleware.cors import CORSMiddleware
from typing import List


def add_cors_middleware(app, allowed_origins: List[str] = None):
    """
    Add CORS middleware to the FastAPI app.

    Args:
        app: FastAPI application instance
        allowed_origins: List of allowed origins (None allows all)
    """
    if allowed_origins is None:
        # Default: allow localhost for development
        allowed_origins = [
            "http://localhost:8000",
            "http://localhost:3000",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:3000",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
