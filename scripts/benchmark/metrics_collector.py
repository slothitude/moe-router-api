"""Metrics collector for Router's Matrix benchmark system."""

import time
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import httpx


@dataclass
class BenchmarkMetrics:
    """Metrics collected from a single benchmark run."""

    # Test identification
    test_id: str
    category: str
    subcategory: str
    model: str

    # Speed metrics
    total_latency_ms: float
    first_token_time_ms: Optional[float]
    prompt_speed_tps: float
    generation_speed_tps: float

    # Response details
    response_text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    # Routing info
    query_type_classified: str
    confidence: float
    was_optimal: bool

    # Error handling
    error: Optional[str] = None
    timeout: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling None values."""
        data = asdict(self)
        # Convert None to empty string for JSON serialization
        return {
            k: v if v is not None else ""
            for k, v in data.items()
        }


class MetricsCollector:
    """Collect metrics from benchmark runs."""

    def __init__(
        self,
        api_base_url: str = "http://localhost:8000",
        timeout_seconds: int = 120
    ):
        """
        Initialize metrics collector.

        Args:
            api_base_url: Base URL of the MoE Router API
            timeout_seconds: Timeout for each query
        """
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout = timeout_seconds
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    async def collect_metrics(
        self,
        test: Dict[str, Any],
        model: Optional[str] = None
    ) -> BenchmarkMetrics:
        """
        Collect metrics for a single test case.

        Args:
            test: Test case dict with query and metadata
            model: Specific model to use (None for auto-routing)

        Returns:
            BenchmarkMetrics with collected data

        Raises:
            httpx.HTTPError: If API request fails
            asyncio.TimeoutError: If query times out
        """
        if not self.client:
            raise RuntimeError("MetricsCollector must be used as async context manager")

        query = test["query"]
        test_id = test["id"]
        category = test["category"]
        subcategory = test.get("subcategory", "general")

        # Prepare request
        start_time = time.time()
        first_token_time = None
        response_text = ""

        try:
            # Make request to router API
            endpoint = f"{self.api_base_url}/api/v1/query"
            payload = {
                "query": query,
            }

            if model:
                payload["model"] = model

            # Track first token time
            request_start = time.time()

            response = await self.client.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )

            request_end = time.time()
            total_latency_ms = (request_end - request_start) * 1000

            if response.status_code != 200:
                return BenchmarkMetrics(
                    test_id=test_id,
                    category=category,
                    subcategory=subcategory,
                    model=model or "auto",
                    total_latency_ms=total_latency_ms,
                    first_token_time_ms=None,
                    prompt_speed_tps=0.0,
                    generation_speed_tps=0.0,
                    response_text="",
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    query_type_classified="unknown",
                    confidence=0.0,
                    was_optimal=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                )

            data = response.json()

            # Extract response data
            response_text = data.get("response", "")
            model_used = data.get("model", model or "unknown")

            # Extract timing information
            timing = data.get("timing", {})
            first_token_time = timing.get("first_token_ms")
            if first_token_time is None:
                # Estimate from total latency if not provided
                first_token_time = total_latency_ms * 0.3

            # Extract token counts
            prompt_tokens = data.get("prompt_tokens", 0)
            completion_tokens = data.get("completion_tokens", len(response_text.split()))
            total_tokens = data.get("total_tokens", prompt_tokens + completion_tokens)

            # Calculate speeds
            prompt_time_s = timing.get("prompt_processing_ms", total_latency_ms * 0.4) / 1000
            generation_time_s = timing.get("generation_ms", total_latency_ms * 0.6) / 1000

            prompt_speed_tps = (
                prompt_tokens / prompt_time_s
                if prompt_time_s > 0 else 0.0
            )
            generation_speed_tps = (
                completion_tokens / generation_time_s
                if generation_time_s > 0 else 0.0
            )

            # Extract routing info
            routing_info = data.get("routing", {})
            query_type_classified = routing_info.get("query_type", "unknown")
            confidence = routing_info.get("confidence", 0.0)
            was_optimal = routing_info.get("was_optimal", False)

            return BenchmarkMetrics(
                test_id=test_id,
                category=category,
                subcategory=subcategory,
                model=model_used,
                total_latency_ms=total_latency_ms,
                first_token_time_ms=first_token_time,
                prompt_speed_tps=prompt_speed_tps,
                generation_speed_tps=generation_speed_tps,
                response_text=response_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                query_type_classified=query_type_classified,
                confidence=confidence,
                was_optimal=was_optimal,
            )

        except asyncio.TimeoutError:
            return BenchmarkMetrics(
                test_id=test_id,
                category=category,
                subcategory=subcategory,
                model=model or "auto",
                total_latency_ms=self.timeout * 1000,
                first_token_time_ms=None,
                prompt_speed_tps=0.0,
                generation_speed_tps=0.0,
                response_text="",
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                query_type_classified="unknown",
                confidence=0.0,
                was_optimal=False,
                error="Timeout",
                timeout=True,
            )

        except Exception as e:
            total_latency_ms = (time.time() - start_time) * 1000
            return BenchmarkMetrics(
                test_id=test_id,
                category=category,
                subcategory=subcategory,
                model=model or "auto",
                total_latency_ms=total_latency_ms,
                first_token_time_ms=None,
                prompt_speed_tps=0.0,
                generation_speed_tps=0.0,
                response_text="",
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                query_type_classified="unknown",
                confidence=0.0,
                was_optimal=False,
                error=str(e),
            )

    async def collect_batch(
        self,
        tests: list[Dict[str, Any]],
        model: Optional[str] = None,
        concurrent: int = 5
    ) -> list[BenchmarkMetrics]:
        """
        Collect metrics for multiple tests concurrently.

        Args:
            tests: List of test cases
            model: Specific model to use (None for auto-routing)
            concurrent: Number of concurrent requests

        Returns:
            List of BenchmarkMetrics
        """
        semaphore = asyncio.Semaphore(concurrent)

        async def collect_with_semaphore(test: Dict[str, Any]) -> BenchmarkMetrics:
            async with semaphore:
                return await self.collect_metrics(test, model)

        tasks = [collect_with_semaphore(test) for test in tests]
        return await asyncio.gather(*tasks)

    def aggregate_metrics(
        self,
        metrics_list: list[BenchmarkMetrics]
    ) -> Dict[str, Any]:
        """
        Aggregate metrics by model and category.

        Args:
            metrics_list: List of BenchmarkMetrics

        Returns:
            Aggregated metrics dict
        """
        aggregated = {}

        for metrics in metrics_list:
            if metrics.error:
                continue

            model = metrics.model
            category = metrics.category

            if model not in aggregated:
                aggregated[model] = {}

            if category not in aggregated[model]:
                aggregated[model][category] = {
                    "count": 0,
                    "total_latency_ms": 0.0,
                    "total_first_token_ms": 0.0,
                    "total_prompt_speed": 0.0,
                    "total_generation_speed": 0.0,
                    "optimal_count": 0,
                }

            agg = aggregated[model][category]
            agg["count"] += 1
            agg["total_latency_ms"] += metrics.total_latency_ms
            if metrics.first_token_time_ms:
                agg["total_first_token_ms"] += metrics.first_token_time_ms
            agg["total_prompt_speed"] += metrics.prompt_speed_tps
            agg["total_generation_speed"] += metrics.generation_speed_tps
            if metrics.was_optimal:
                agg["optimal_count"] += 1

        # Calculate averages
        for model in aggregated:
            for category in aggregated[model]:
                agg = aggregated[model][category]
                count = agg["count"]

                if count > 0:
                    agg["avg_latency_ms"] = agg["total_latency_ms"] / count
                    agg["avg_first_token_ms"] = (
                        agg["total_first_token_ms"] / count
                        if agg["total_first_token_ms"] > 0 else 0
                    )
                    agg["avg_prompt_speed_tps"] = agg["total_prompt_speed"] / count
                    agg["avg_generation_speed_tps"] = (
                        agg["total_generation_speed"] / count
                    )
                    agg["optimal_rate"] = agg["optimal_count"] / count

        return aggregated


__all__ = ["MetricsCollector", "BenchmarkMetrics"]
