"""Health check and monitoring endpoints."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["health"])


# Response Models
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    ollama: bool
    memory: bool
    disk: bool
    timestamp: str


class MetricsResponse(BaseModel):
    """Metrics response."""
    cache_hits: int
    cache_misses: int
    total_queries: int
    active_models: int
    cache_size: int
    circuit_breakers: Dict[str, Any]


class CacheStatsResponse(BaseModel):
    """Cache statistics response."""
    size: int
    max_size: int
    hits: int
    misses: int
    hit_rate: str
    evictions: int
    expirations: int


def get_app_state():
    """Get app state (dependency injection)."""
    from main import app
    return app


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Checks Ollama connectivity and system resources.
    """
    from main import app

    health_monitor = app.state.health_monitor
    ollama_client = app.state.ollama_client

    try:
        # Run health checks
        await health_monitor.check_ollama(ollama_client)
        health_monitor.check_memory()
        health_monitor.check_disk()

        health_status = health_monitor.get_health_status()

        return HealthResponse(
            status="healthy" if health_status["overall"] else "unhealthy",
            ollama=health_status["ollama"],
            memory=health_status["memory"],
            disk=health_status["disk"],
            timestamp=health_status["last_check"] or "now"
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get performance metrics.

    Returns query statistics, cache stats, and system info.
    """
    from main import app

    metrics_collector = app.state.metrics
    cache = app.state.cache
    fallback_manager = app.state.fallback_manager
    model_pool = app.state.model_pool
    executor = app.state.executor

    try:
        # Get metrics summary
        metrics_summary = metrics_collector.get_summary()

        # Get cache stats
        cache_stats = await cache.get_status()

        # Get circuit breaker states
        circuit_states = fallback_manager.get_all_states()

        # Update gauges
        metrics_collector.update_cache_size(cache_stats["size"])

        pool_status = model_pool.get_status()
        metrics_collector.update_memory_usage(
            pool_status["gpu_usage_mb"],
            pool_status["ram_usage_mb"]
        )

        active_jobs = executor.get_active_jobs()
        metrics_collector.update_active_requests(active_jobs)

        return MetricsResponse(
            cache_hits=metrics_summary["cache_hits"],
            cache_misses=metrics_summary["cache_misses"],
            total_queries=metrics_summary["total_queries"],
            active_models=metrics_summary["active_models"],
            cache_size=cache_stats["size"],
            circuit_breakers=circuit_states
        )

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """
    Get metrics in Prometheus text format.

    Returns metrics that can be scraped by Prometheus.
    """
    from main import app

    metrics_collector = app.state.metrics

    try:
        metrics_text = metrics_collector.get_metrics_text()

        from fastapi.responses import Response
        return Response(
            content=metrics_text,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )

    except Exception as e:
        logger.error(f"Failed to get Prometheus metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """
    Get detailed cache statistics.

    Shows cache size, hit rate, and eviction info.
    """
    from main import app

    cache = app.state.cache

    try:
        stats = await cache.get_status()

        return CacheStatsResponse(
            size=stats["size"],
            max_size=stats["max_size"],
            hits=stats["hits"],
            misses=stats["misses"],
            hit_rate=stats["hit_rate"],
            evictions=stats["evictions"],
            expirations=stats["expirations"]
        )

    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache():
    """
    Clear all cached responses.

    Frees memory and resets cache statistics.
    """
    from main import app

    cache = app.state.cache

    try:
        await cache.clear()

        return {
            "message": "Cache cleared successfully"
        }

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/info")
async def get_system_info():
    """
    Get system information.

    Returns CPU, memory, and disk usage stats.
    """
    from main import app

    health_monitor = app.state.health_monitor

    try:
        system_info = health_monitor.get_system_info()

        return system_info

    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routing/stats")
async def get_routing_stats():
    """
    Get routing statistics.

    Shows model pool status and circuit breaker states.
    """
    from main import app

    router = app.state.router

    try:
        stats = await router.get_routing_stats()

        return stats

    except Exception as e:
        logger.error(f"Failed to get routing stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
