"""Query API endpoints for routing and execution."""

import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from datetime import datetime

from core.router import QueryRouter, RoutingDecision
from core.executor import QueryExecutor, ExecutionResult
from models.model_specs import QueryType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["query"])


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str = Field(..., description="Query text", min_length=1)
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    priority: str = Field("normal", description="Priority level")
    model: Optional[str] = Field(None, description="Specific model to use (overrides routing)")
    options: Optional[Dict[str, Any]] = Field(None, description="Generation options")
    system: Optional[str] = Field(None, description="System prompt")
    use_cache: bool = Field(True, description="Whether to use cache")


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    response: str
    model_used: str
    routing_decision: Dict[str, Any]
    tokens_generated: int
    processing_time: float
    from_cache: bool
    timestamp: str


class BatchRequest(BaseModel):
    """Request model for batch endpoint."""
    queries: List[QueryRequest] = Field(..., description="List of queries")


class BatchResponse(BaseModel):
    """Response model for batch endpoint."""
    responses: List[QueryResponse]
    total_time: float


async def get_router_executor() -> tuple[QueryRouter, QueryExecutor]:
    """Get router and executor instances (dependency injection)."""
    # This will be injected by the main app
    from main import app
    return app.state.router, app.state.executor


@router.post("/query", response_model=QueryResponse)
async def query_route(request: QueryRequest):
    """
    Execute a single query with automatic routing.

    The system will:
    1. Classify the query type
    2. Select the optimal model
    3. Execute with fallback support
    4. Cache the result

    Returns the response along with routing metadata.
    """
    from main import app

    router: QueryRouter = app.state.router
    executor: QueryExecutor = app.state.executor
    metrics = app.state.metrics

    start_time = datetime.now()

    try:
        # Route the query
        if request.model:
            # Use specific model
            decision = RoutingDecision(
                query_type=QueryType.BALANCED,
                selected_model=request.model,
                fallback_chain=[request.model],
                confidence=1.0,
                reasoning=f"User specified model: {request.model}"
            )
        else:
            # Auto-route
            decision = await router.route(request.query)

        logger.info(f"Routing decision: {decision.selected_model} "
                   f"({decision.query_type.value}) - {decision.reasoning}")

        # Execute query
        result: ExecutionResult = await executor.execute(
            query=request.query,
            model=decision.selected_model,
            options=request.options,
            use_cache=request.use_cache,
            system=request.system
        )

        # Record metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        metrics.record_query(
            model=result.model_used,
            query_type=decision.query_type.value,
            latency=result.processing_time,
            status="success"
        )

        if result.from_cache:
            metrics.record_cache_hit()
        else:
            metrics.record_cache_miss()

        # Return response
        return QueryResponse(
            response=result.response,
            model_used=result.model_used,
            routing_decision={
                "query_type": decision.query_type.value,
                "selected_model": decision.selected_model,
                "fallback_chain": decision.fallback_chain,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning
            },
            tokens_generated=result.tokens_generated,
            processing_time=result.processing_time,
            from_cache=result.from_cache,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Query failed: {e}")
        metrics.record_query(
            model=request.model or "unknown",
            query_type="unknown",
            latency=(datetime.now() - start_time).total_seconds(),
            status="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def query_stream_route(request: QueryRequest):
    """
    Execute a query with streaming response.

    Returns Server-Sent Events (SSE) stream of response chunks.
    """
    from main import app

    router: QueryRouter = app.state.router
    executor: QueryExecutor = app.state.executor

    try:
        # Route the query
        if request.model:
            decision = RoutingDecision(
                query_type=QueryType.BALANCED,
                selected_model=request.model,
                fallback_chain=[request.model],
                confidence=1.0,
                reasoning=f"User specified model: {request.model}"
            )
        else:
            decision = await router.route(request.query)

        logger.info(f"Streaming with model: {decision.selected_model}")

        async def generate():
            """Generate SSE stream."""
            try:
                # Send metadata event
                yield f"event: metadata\n"
                yield f"data: {{"
                yield f"\"model\": \"{decision.selected_model}\", "
                yield f"\"query_type\": \"{decision.query_type.value}\", "
                yield f"\"reasoning\": \"{decision.reasoning}\""
                yield f"}}\n\n"

                # Stream response
                async for chunk in executor.execute_stream(
                    query=request.query,
                    model=decision.selected_model,
                    options=request.options,
                    system=request.system
                ):
                    # Send chunk event
                    yield f"event: chunk\n"
                    yield f"data: {{\"text\": {repr(chunk)}}}\n\n"

                # Send done event
                yield f"event: done\n"
                yield f"data: {{}}\n\n"

            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield f"event: error\n"
                yield f"data: {{\"error\": {repr(str(e))}}}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        logger.error(f"Stream setup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=BatchResponse)
async def batch_route(request: BatchRequest):
    """
    Execute multiple queries in batch.

    Queries are executed concurrently for better performance.
    """
    from main import app

    executor: QueryExecutor = app.state.executor
    metrics = app.state.metrics

    start_time = datetime.now()

    try:
        # Convert to list of dicts
        queries_data = [
            {
                "query": q.query,
                "model": q.model,
                "options": q.options,
                "system": q.system,
                "use_cache": q.use_cache
            }
            for q in request.queries
        ]

        # Execute batch
        results = await executor.execute_batch(queries_data)

        # Record metrics
        for result in results:
            metrics.record_query(
                model=result.model_used,
                query_type="batch",
                latency=result.processing_time,
                status="success"
            )

        total_time = (datetime.now() - start_time).total_seconds()

        # Create response (simplified routing decision for batch)
        return BatchResponse(
            responses=[
                QueryResponse(
                    response=r.response,
                    model_used=r.model_used,
                    routing_decision={
                        "query_type": "batch",
                        "selected_model": r.model_used,
                        "fallback_chain": [],
                        "confidence": 1.0,
                        "reasoning": "Batch execution"
                    },
                    tokens_generated=r.tokens_generated,
                    processing_time=r.processing_time,
                    from_cache=r.from_cache,
                    timestamp=datetime.now().isoformat()
                )
                for r in results
            ],
            total_time=total_time
        )

    except Exception as e:
        logger.error(f"Batch query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
