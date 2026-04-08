"""Query execution engine with concurrency control."""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass

from models.ollama_client import OllamaClient
from core.model_pool import ModelPool
from core.cache import ResponseCache
from core.fallback import FallbackManager
from models.model_specs import QueryType

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of query execution."""
    response: str
    model_used: str
    tokens_generated: int
    processing_time: float
    from_cache: bool = False
    routing_attempted: int = 1


class QueryExecutor:
    """
    Execute queries with concurrency control and fallback logic.

    Features:
    - Semaphore-based throttling per model
    - Circuit breaker integration
    - Timeout handling
    - Automatic fallback on failure
    """

    def __init__(
        self,
        ollama_client: OllamaClient,
        model_pool: ModelPool,
        cache: ResponseCache,
        fallback_manager: FallbackManager,
        default_timeout: float = 30.0,
        model_limits: Optional[Dict[str, int]] = None
    ):
        """
        Initialize query executor.

        Args:
            ollama_client: Ollama client instance
            model_pool: Model pool instance
            cache: Response cache instance
            fallback_manager: Fallback manager instance
            default_timeout: Default timeout in seconds
            model_limits: Concurrent request limit per model
        """
        self.ollama = ollama_client
        self.model_pool = model_pool
        self.cache = cache
        self.fallback_manager = fallback_manager
        self.default_timeout = default_timeout

        # Default model limits (based on benchmark speeds)
        self.model_limits = model_limits or {
            'qwen3:4b': 3,
            'qwen2.5-coder': 3,
            'llama3.2': 2,
            'llama3.1': 4,
            'ministral-3': 3,
            'phi3:mini': 4,
            'nemotron-3-nano:4b': 4
        }

        # Semaphores for each model
        self.semaphores: Dict[str, asyncio.Semaphore] = {}

        # Active job tracking
        self.active_jobs: Dict[str, List[str]] = {}

        self._initialize_semaphores()

    def _initialize_semaphores(self):
        """Initialize semaphores for all models."""
        for model_name, limit in self.model_limits.items():
            self.semaphores[model_name] = asyncio.Semaphore(limit)
            self.active_jobs[model_name] = []
        logger.info(f"Initialized semaphores for {len(self.semaphores)} models")

    async def execute(
        self,
        query: str,
        model: str,
        options: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        use_cache: bool = True,
        system: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute a query with automatic fallback.

        Args:
            query: Query string
            model: Model to use
            options: Generation options
            timeout: Request timeout in seconds
            use_cache: Whether to check cache
            system: System prompt

        Returns:
            ExecutionResult with response and metadata
        """
        # Check cache first
        if use_cache:
            cached = await self.cache.get(query, model, options)
            if cached is not None:
                logger.info(f"Cache hit for query with {model}")
                return ExecutionResult(
                    response=cached.get("response", ""),
                    model_used=model,
                    tokens_generated=cached.get("tokens_generated", 0),
                    processing_time=cached.get("processing_time", 0.0),
                    from_cache=True
                )

        # Attempt execution with fallback
        timeout = timeout or self.default_timeout
        start_time = time.time()
        attempt = 0
        last_error = None

        while attempt < 3:  # Max 3 attempts
            try:
                # Check if model can be attempted
                if not await self.fallback_manager.can_attempt(model):
                    logger.warning(f"Circuit open for {model}, skipping to next attempt")
                    attempt += 1
                    continue

                # Execute with semaphore and timeout
                result = await asyncio.wait_for(
                    self._execute_with_semaphore(query, model, options, system),
                    timeout=timeout
                )

                # Record success
                await self.fallback_manager.record_success(model)

                processing_time = time.time() - start_time

                # Cache the result
                await self.cache.set(
                    query, model,
                    {
                        "response": result["response"],
                        "tokens_generated": result.get("eval_count", 0),
                        "processing_time": processing_time
                    },
                    options
                )

                return ExecutionResult(
                    response=result["response"],
                    model_used=model,
                    tokens_generated=result.get("eval_count", 0),
                    processing_time=processing_time,
                    routing_attempted=attempt + 1
                )

            except asyncio.TimeoutError:
                last_error = f"Timeout after {timeout}s"
                logger.warning(f"Query timed out for {model}: {last_error}")
                await self.fallback_manager.record_failure(model)

            except Exception as e:
                last_error = str(e)
                logger.error(f"Query failed for {model}: {last_error}")
                await self.fallback_manager.record_failure(model)

            attempt += 1

        # All attempts failed
        processing_time = time.time() - start_time
        raise Exception(
            f"Query failed after {attempt} attempts. Last error: {last_error}"
        )

    async def _execute_with_semaphore(
        self,
        query: str,
        model: str,
        options: Optional[Dict[str, Any]],
        system: Optional[str]
    ) -> Dict[str, Any]:
        """
        Execute query with semaphore control.

        Args:
            query: Query string
            model: Model name
            options: Generation options
            system: System prompt

        Returns:
            Response dict from Ollama
        """
        # Get or create semaphore for model
        if model not in self.semaphores:
            self.semaphores[model] = asyncio.Semaphore(self.model_limits.get(model, 3))
            self.active_jobs[model] = []

        semaphore = self.semaphores[model]
        job_id = f"{model}-{time.time()}"

        async with semaphore:
            # Track active job
            self.active_jobs[model].append(job_id)
            logger.debug(f"Acquired semaphore for {model} (active: {len(self.active_jobs[model])})")

            try:
                # Ensure model is loaded
                loaded_model = await self.model_pool.get_model(model)
                if not loaded_model:
                    raise Exception(f"Failed to load model {model}")

                # Execute query
                result = await self.ollama.generate(
                    model=model,
                    prompt=query,
                    options=options,
                    system=system
                )

                return result

            finally:
                # Remove job from tracking
                if job_id in self.active_jobs[model]:
                    self.active_jobs[model].remove(job_id)
                logger.debug(f"Released semaphore for {model}")

    async def execute_stream(
        self,
        query: str,
        model: str,
        options: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute a query with streaming response.

        Args:
            query: Query string
            model: Model to use
            options: Generation options
            system: System prompt

        Yields:
            Response chunks as they arrive
        """
        # Get semaphore for model
        if model not in self.semaphores:
            self.semaphores[model] = asyncio.Semaphore(self.model_limits.get(model, 3))
            self.active_jobs[model] = []

        semaphore = self.semaphores[model]
        job_id = f"{model}-{time.time()}-stream"

        async with semaphore:
            # Track active job
            self.active_jobs[model].append(job_id)
            logger.debug(f"Acquired semaphore for {model} stream")

            try:
                # Ensure model is loaded
                loaded_model = await self.model_pool.get_model(model)
                if not loaded_model:
                    raise Exception(f"Failed to load model {model}")

                # Execute streaming query
                async for chunk in self.ollama.generate_stream(
                    model=model,
                    prompt=query,
                    options=options,
                    system=system
                ):
                    yield chunk

            finally:
                # Remove job from tracking
                if job_id in self.active_jobs[model]:
                    self.active_jobs[model].remove(job_id)
                logger.debug(f"Released semaphore for {model} stream")

    async def execute_batch(
        self,
        queries: List[Dict[str, Any]],
        timeout: Optional[float] = None
    ) -> List[ExecutionResult]:
        """
        Execute multiple queries concurrently.

        Args:
            queries: List of query dicts with 'query', 'model', 'options', etc.
            timeout: Per-query timeout in seconds

        Returns:
            List of ExecutionResult objects
        """
        tasks = []

        for query_data in queries:
            task = self.execute(
                query=query_data["query"],
                model=query_data.get("model", query_data.get("model_name", "qwen3:4b")),
                options=query_data.get("options"),
                timeout=timeout,
                use_cache=query_data.get("use_cache", True),
                system=query_data.get("system")
            )
            tasks.append(task)

        # Execute all concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch query {i} failed: {result}")
                processed_results.append(ExecutionResult(
                    response=f"Error: {str(result)}",
                    model_used=queries[i].get("model", "unknown"),
                    tokens_generated=0,
                    processing_time=0.0,
                    routing_attempted=1
                ))
            else:
                processed_results.append(result)

        return processed_results

    def get_active_jobs(self) -> Dict[str, int]:
        """
        Get count of active jobs per model.

        Returns:
            Dict of model name to active job count
        """
        return {
            model: len(jobs)
            for model, jobs in self.active_jobs.items()
        }

    def get_semaphore_status(self) -> Dict[str, Dict[str, int]]:
        """
        Get semaphore status for all models.

        Returns:
            Dict of model name to status dict
        """
        return {
            model: {
                "limit": self.model_limits.get(model, 3),
                "active": len(jobs),
                "available": self.semaphores[model]._value  # Internal semaphore value
            }
            for model, jobs in self.active_jobs.items()
        }
