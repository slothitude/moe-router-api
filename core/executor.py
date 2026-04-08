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
        default_timeout: Optional[float] = None,  # No timeout - let queries complete
        model_limits: Optional[Dict[str, int]] = None,
        external_api_client: Optional['ExternalAPIClient'] = None
    ):
        """
        Initialize query executor.

        Args:
            ollama_client: Ollama client instance
            model_pool: Model pool instance
            cache: Response cache instance
            fallback_manager: Fallback manager instance
            default_timeout: Default timeout in seconds (increased for benchmarks)
            model_limits: Concurrent request limit per model
            external_api_client: Optional external API client for cloud models
        """
        self.ollama = ollama_client
        self.model_pool = model_pool
        self.cache = cache
        self.fallback_manager = fallback_manager
        self.default_timeout = default_timeout
        self.external_api_client = external_api_client

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
        # Check if this is an external model
        if model.startswith("external/") and self.external_api_client:
            return await self._execute_external(query, model, options, timeout, use_cache)

        # Check cache first for local models
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

        # Attempt execution without timeout or fallback
        start_time = time.time()

        try:
            # Execute with semaphore (no timeout)
            if timeout is None:
                # No timeout - let query complete naturally
                result = await self._execute_with_semaphore(query, model, options, system)
            else:
                # Use timeout if specified
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
                routing_attempted=1
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Query failed for {model}: {str(e)}")
            await self.fallback_manager.record_failure(model)
            raise Exception(f"Query failed: {str(e)}")

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

    async def _execute_external(
        self,
        query: str,
        model: str,
        options: Optional[Dict[str, Any]],
        timeout: Optional[float],
        use_cache: bool
    ) -> ExecutionResult:
        """
        Execute query on external API model.

        Args:
            query: Query string
            model: External model ID
            options: Generation options
            timeout: Request timeout
            use_cache: Whether to check cache

        Returns:
            ExecutionResult with response and metadata
        """
        if not self.external_api_client:
            raise ValueError("External API client not configured")

        # Check cache first
        if use_cache:
            cached = await self.cache.get(query, model, options)
            if cached is not None:
                logger.info(f"Cache hit for external model {model}")
                return ExecutionResult(
                    response=cached.get("response", ""),
                    model_used=model,
                    tokens_generated=cached.get("tokens_generated", 0),
                    processing_time=cached.get("processing_time", 0.0),
                    from_cache=True
                )

        # Prepare messages for external API
        messages = [{"role": "user", "content": query}]

        # Execute query
        start_time = time.time()
        timeout = timeout or self.default_timeout

        try:
            # Execute with or without timeout
            if timeout is None:
                result = await self.external_api_client.query(
                    model,
                    messages,
                    temperature=options.get("temperature", 0.7) if options else 0.7,
                    max_tokens=options.get("num_predict", 1024) if options else 1024
                )
            else:
                result = await asyncio.wait_for(
                    self.external_api_client.query(
                        model,
                        messages,
                        temperature=options.get("temperature", 0.7) if options else 0.7,
                        max_tokens=options.get("num_predict", 1024) if options else 1024
                    ),
                    timeout=timeout
                )

            processing_time = time.time() - start_time

            # Cache the result
            await self.cache.set(
                query, model,
                {
                    "response": result["content"],
                    "tokens_generated": result.get("usage", {}).get("completion_tokens", 0),
                    "processing_time": processing_time
                },
                options
            )

            return ExecutionResult(
                response=result["content"],
                model_used=model,
                tokens_generated=result.get("usage", {}).get("completion_tokens", 0),
                processing_time=processing_time,
                routing_attempted=1
            )

        except asyncio.TimeoutError:
            raise Exception(f"External API timeout after {timeout}s")
        except Exception as e:
            raise Exception(f"External API error: {str(e)}")

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
