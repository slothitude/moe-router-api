"""MoE Router API - Main application entry point."""

import asyncio
import logging
import yaml
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from models.ollama_client import OllamaClient
from models.model_specs import ModelRegistry
from models.query_classifier import QueryClassifier
from core.model_pool import ModelPool
from core.router import QueryRouter
from core.executor import QueryExecutor
from core.cache import ResponseCache
from core.fallback import FallbackManager
from utils.metrics import MetricsCollector
from utils.monitoring import HealthMonitor, health_check_task

from api.routes.query import router as query_router
from api.routes.models import router as models_router
from api.routes.health import router as health_router
from api.routes.websocket import router as websocket_router
from api.middleware.cors import add_cors_middleware
from api.middleware.logging import RequestLoggingMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config() -> dict:
    """Load configuration from YAML file."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    else:
        logger.warning(f"Config file not found: {CONFIG_PATH}")
        return {
            "server": {"host": "0.0.0.0", "port": 8000, "log_level": "info"},
            "models": {
                "ollama_base_url": "http://localhost:11434",
                "pool": {"gpu_capacity_mb": 3500, "ram_capacity_mb": 20000},
                "preload": ["qwen3:4b", "llama3.1"]
            },
            "cache": {"enabled": True, "max_size": 1000, "ttl_seconds": 3600},
            "concurrency": {
                "default_limit": 3,
                "model_limits": {
                    'qwen3:4b': 3,
                    'qwen2.5-coder': 3,
                    'llama3.2': 2,
                    'llama3.1': 4,
                    'ministral-3': 3,
                    'phi3:mini': 4,
                    'nemotron-3-nano:4b': 4
                }
            },
            "fallback": {
                "max_attempts": 3,
                "circuit_breaker_threshold": 3,
                "circuit_breaker_cooldown": 60
            },
            "routing": {
                "enable_embeddings": True,
                "embedding_model": "nomic-embed-text",
                "semantic_threshold": 0.85
            }
        }


config = load_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting MoE Router API...")

    # Initialize Ollama client
    ollama_base_url = os.getenv(
        "OLLAMA_BASE_URL",
        config["models"]["ollama_base_url"]
    )
    app.state.ollama_client = OllamaClient(base_url=ollama_base_url)

    # Check Ollama health
    logger.info("Checking Ollama connectivity...")
    if await app.state.ollama_client.health_check():
        logger.info("Ollama is healthy")
    else:
        logger.warning("Ollama is not responding - some features may not work")

    # Get available models
    try:
        available = await app.state.ollama_client.list_models()
        logger.info(f"Available models: {[m['name'] for m in available]}")
    except Exception as e:
        logger.error(f"Failed to list models: {e}")

    # Initialize core components
    logger.info("Initializing core components...")

    # Model pool
    app.state.model_pool = ModelPool(
        gpu_capacity_mb=config["models"]["pool"]["gpu_capacity_mb"],
        ram_capacity_mb=config["models"]["pool"]["ram_capacity_mb"],
        preload_models=config["models"]["preload"]
    )
    await app.state.model_pool.initialize(app.state.ollama_client)

    # Query classifier
    app.state.classifier = QueryClassifier(
        ollama_client=app.state.ollama_client,
        embedding_model=config["routing"]["embedding_model"],
        enable_embeddings=config["routing"]["enable_embeddings"],
        semantic_threshold=config["routing"]["semantic_threshold"]
    )

    # Fallback manager
    app.state.fallback_manager = FallbackManager(
        failure_threshold=config["fallback"]["circuit_breaker_threshold"],
        cooldown_seconds=config["fallback"]["circuit_breaker_cooldown"]
    )

    # Query router
    app.state.router = QueryRouter(
        classifier=app.state.classifier,
        model_pool=app.state.model_pool,
        fallback_manager=app.state.fallback_manager
    )

    # Response cache
    app.state.cache = ResponseCache(
        max_size=config["cache"]["max_size"],
        ttl_seconds=config["cache"]["ttl_seconds"]
    )
    await app.state.cache.start()

    # Query executor
    app.state.executor = QueryExecutor(
        ollama_client=app.state.ollama_client,
        model_pool=app.state.model_pool,
        cache=app.state.cache,
        fallback_manager=app.state.fallback_manager,
        model_limits=config["concurrency"]["model_limits"]
    )

    # Metrics collector
    app.state.metrics = MetricsCollector()

    # Health monitor
    app.state.health_monitor = HealthMonitor(check_interval=30)

    # Start background tasks
    app.state.health_check_task = asyncio.create_task(
        health_check_task(
            app.state.health_monitor,
            app.state.ollama_client,
            app.state.metrics
        )
    )

    logger.info("All components initialized successfully")
    logger.info(f"Model pool status: {app.state.model_pool.get_status()}")

    yield

    # Shutdown
    logger.info("Shutting down MoE Router API...")

    # Stop background tasks
    if hasattr(app.state, 'health_check_task'):
        app.state.health_check_task.cancel()
        try:
            await app.state.health_check_task
        except asyncio.CancelledError:
            pass

    # Stop cache
    if hasattr(app.state, 'cache'):
        await app.state.cache.stop()

    # Close Ollama client
    if hasattr(app.state, 'ollama_client'):
        await app.state.ollama_client.__aexit__(None, None, None)

    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="MoE Router API",
    description="Intelligent Mixture of Experts routing for Ollama models",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
add_cors_middleware(app)
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(query_router)
app.include_router(models_router)
app.include_router(health_router)
app.include_router(websocket_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "MoE Router API",
        "version": "1.0.0",
        "description": "Intelligent Mixture of Experts routing for Ollama models",
        "endpoints": {
            "query": "/api/v1/query",
            "stream": "/api/v1/query/stream",
            "batch": "/api/v1/batch",
            "models": "/api/v1/models",
            "health": "/api/v1/health",
            "metrics": "/api/v1/metrics",
            "websocket_chat": "/ws/chat",
            "websocket_batch": "/ws/batch"
        },
        "docs": "/docs",
        "models": list(ModelRegistry.get_all_models().keys())
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", config["server"]["host"])
    port = int(os.getenv("PORT", config["server"]["port"]))
    log_level = os.getenv("LOG_LEVEL", config["server"]["log_level"])

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=True
    )
