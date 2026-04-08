"""Prometheus metrics collection for monitoring."""

import time
import logging
from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    CollectorRegistry,
    generate_latest
)

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collect and expose Prometheus metrics.

    Metrics:
    - Query latency histogram
    - Model usage counter
    - Cache hit/miss counters
    - Circuit breaker state gauges
    - Active requests gauge
    """

    def __init__(self):
        """Initialize metrics collector."""
        self.registry = CollectorRegistry()

        # Query metrics
        self.query_latency = Histogram(
            'moe_query_latency_seconds',
            'Query latency in seconds',
            ['model', 'query_type', 'status'],
            registry=self.registry
        )

        self.query_counter = Counter(
            'moe_queries_total',
            'Total number of queries',
            ['model', 'query_type', 'status'],
            registry=self.registry
        )

        # Model metrics
        self.model_usage = Counter(
            'moe_model_usage_total',
            'Total model usage',
            ['model'],
            registry=self.registry
        )

        # Cache metrics
        self.cache_hits = Counter(
            'moe_cache_hits_total',
            'Total cache hits',
            registry=self.registry
        )

        self.cache_misses = Counter(
            'moe_cache_misses_total',
            'Total cache misses',
            registry=self.registry
        )

        self.cache_size = Gauge(
            'moe_cache_size',
            'Current cache size',
            registry=self.registry
        )

        # Circuit breaker metrics
        self.circuit_state = Gauge(
            'moe_circuit_state',
            'Circuit breaker state (0=closed, 1=open)',
            ['model'],
            registry=self.registry
        )

        self.circuit_failures = Counter(
            'moe_circuit_failures_total',
            'Total circuit breaker failures',
            ['model'],
            registry=self.registry
        )

        # Concurrency metrics
        self.active_requests = Gauge(
            'moe_active_requests',
            'Number of active requests',
            ['model'],
            registry=self.registry
        )

        # Memory metrics
        self.gpu_memory_usage = Gauge(
            'moe_gpu_memory_mb',
            'GPU memory usage in MB',
            registry=self.registry
        )

        self.ram_memory_usage = Gauge(
            'moe_ram_memory_mb',
            'RAM memory usage for models in MB',
            registry=self.registry
        )

        # Internal stats
        self._query_times: Dict[str, list] = defaultdict(list)
        self._last_update = datetime.now()

    def record_query(
        self,
        model: str,
        query_type: str,
        latency: float,
        status: str = "success"
    ):
        """
        Record a query execution.

        Args:
            model: Model name
            query_type: Query type (code, speed_critical, etc.)
            latency: Query latency in seconds
            status: Execution status (success, error, timeout)
        """
        self.query_latency.labels(
            model=model,
            query_type=query_type,
            status=status
        ).observe(latency)

        self.query_counter.labels(
            model=model,
            query_type=query_type,
            status=status
        ).inc()

        self.model_usage.labels(model=model).inc()

        # Track for adaptive concurrency
        self._query_times[model].append(latency)
        self._cleanup_old_times(model)

    def record_cache_hit(self):
        """Record a cache hit."""
        self.cache_hits.inc()

    def record_cache_miss(self):
        """Record a cache miss."""
        self.cache_misses.inc()

    def update_cache_size(self, size: int):
        """
        Update cache size gauge.

        Args:
            size: Current cache size
        """
        self.cache_size.set(size)

    def update_circuit_state(self, model: str, is_open: bool):
        """
        Update circuit breaker state.

        Args:
            model: Model name
            is_open: Whether circuit is open
        """
        self.circuit_state.labels(model=model).set(1 if is_open else 0)

    def record_circuit_failure(self, model: str):
        """
        Record a circuit breaker failure.

        Args:
            model: Model name
        """
        self.circuit_failures.labels(model=model).inc()

    def update_active_requests(self, active_count: Dict[str, int]):
        """
        Update active requests gauge.

        Args:
            active_count: Dict of model to active request count
        """
        # Reset all gauges first
        for model in list(active_count.keys()):
            self.active_requests.labels(model=model).set(active_count[model])

    def update_memory_usage(self, gpu_mb: int, ram_mb: int):
        """
        Update memory usage gauges.

        Args:
            gpu_mb: GPU memory usage in MB
            ram_mb: RAM usage for models in MB
        """
        self.gpu_memory_usage.set(gpu_mb)
        self.ram_memory_usage.set(ram_mb)

    def get_avg_query_time(self, model: str, window_seconds: int = 60) -> Optional[float]:
        """
        Get average query time for a model.

        Args:
            model: Model name
            window_seconds: Time window in seconds

        Returns:
            Average query time or None if no data
        """
        self._cleanup_old_times(model, window_seconds)

        times = self._query_times.get(model, [])
        if not times:
            return None

        return sum(times) / len(times)

    def _cleanup_old_times(self, model: str, window_seconds: int = 60):
        """
        Remove old query time data.

        Args:
            model: Model name
            window_seconds: Time window in seconds
        """
        cutoff = datetime.now() - timedelta(seconds=window_seconds)

        # Keep only recent data (simplified - should use timestamps in production)
        if len(self._query_times[model]) > 100:
            # Keep only last 100 entries
            self._query_times[model] = self._query_times[model][-100:]

    def get_metrics_text(self) -> bytes:
        """
        Get metrics in Prometheus text format.

        Returns:
            Metrics as bytes
        """
        return generate_latest(self.registry)

    def get_summary(self) -> Dict:
        """
        Get metrics summary.

        Returns:
            Dict with key metrics
        """
        # Get cache metrics using _metrics dict
        cache_hits_value = 0
        cache_misses_value = 0

        # Extract values from Prometheus metrics
        for metric in [self.cache_hits, self.cache_misses]:
            for sample in metric.collect()[0].samples:
                if metric.name == "moe_cache_hits_total":
                    cache_hits_value = sample.value or 0
                elif metric.name == "moe_cache_misses_total":
                    cache_misses_value = sample.value or 0

        # Get total queries
        total_queries = 0
        try:
            for metric in self.query_counter.collect():
                for sample in metric.samples:
                    total_queries += sample.value or 0
        except Exception:
            total_queries = 0

        # Get active models
        active_models = set()
        try:
            for metric in self.model_usage.collect():
                for sample in metric.samples:
                    if sample.name == "moe_model_usage_total":
                        active_models.add(sample.labels.get('model', ''))
        except Exception:
            pass

        return {
            "cache_hits": int(cache_hits_value),
            "cache_misses": int(cache_misses_value),
            "total_queries": int(total_queries),
            "active_models": len(active_models),
            "avg_query_times": {
                model: self.get_avg_query_time(model)
                for model in self._query_times.keys()
            }
        }
