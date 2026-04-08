"""WebSocket endpoints for persistent connections."""

import logging
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

from core.router import QueryRouter
from core.executor import QueryExecutor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, connection_id: str, websocket: WebSocket):
        """
        Accept and track a WebSocket connection.

        Args:
            connection_id: Unique connection ID
            websocket: WebSocket instance
        """
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connected: {connection_id}")

    def disconnect(self, connection_id: str):
        """
        Remove a WebSocket connection.

        Args:
            connection_id: Connection ID to remove
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"WebSocket disconnected: {connection_id}")

    async def send_message(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ):
        """
        Send a message to a specific connection.

        Args:
            connection_id: Target connection ID
            message: Message dict to send
        """
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            await websocket.send_json(message)
        else:
            logger.warning(f"Connection not found: {connection_id}")

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connections.

        Args:
            message: Message dict to broadcast
        """
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to {connection_id}: {e}")


# Global connection manager
manager = ConnectionManager()


def get_app_components():
    """Get app components (dependency injection)."""
    from main import app
    return (
        app.state.router,
        app.state.executor,
        app.state.metrics
    )


@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    """
    Persistent chat session over WebSocket.

    Maintains conversation context and streams responses.
    """
    from main import app

    query_router: QueryRouter = app.state.router
    executor: QueryExecutor = app.state.executor
    metrics = app.state.metrics

    connection_id = f"chat-{datetime.now().timestamp()}"

    await manager.connect(connection_id, websocket)

    try:
        # Send welcome message
        await manager.send_message(connection_id, {
            "type": "connected",
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat()
        })

        # Conversation history
        history = []

        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type", "query")

            if message_type == "query":
                query_text = message.get("query", "")
                model_override = message.get("model")
                options = message.get("options")

                if not query_text:
                    await manager.send_message(connection_id, {
                        "type": "error",
                        "error": "Query text is required"
                    })
                    continue

                try:
                    # Route query
                    if model_override:
                        from models.model_specs import QueryType, RoutingDecision
                        decision = RoutingDecision(
                            query_type=QueryType.BALANCED,
                            selected_model=model_override,
                            fallback_chain=[model_override],
                            confidence=1.0,
                            reasoning=f"User specified model: {model_override}"
                        )
                    else:
                        decision = await query_router.route(query_text)

                    # Send routing info
                    await manager.send_message(connection_id, {
                        "type": "routing",
                        "model": decision.selected_model,
                        "query_type": decision.query_type.value,
                        "reasoning": decision.reasoning,
                        "confidence": decision.confidence
                    })

                    # Stream response
                    await manager.send_message(connection_id, {
                        "type": "start",
                        "model": decision.selected_model
                    })

                    response_text = ""

                    async for chunk in executor.execute_stream(
                        query=query_text,
                        model=decision.selected_model,
                        options=options,
                        system=None
                    ):
                        response_text += chunk

                        # Send chunk
                        await manager.send_message(connection_id, {
                            "type": "chunk",
                            "text": chunk
                        })

                    # Send completion
                    await manager.send_message(connection_id, {
                        "type": "done",
                        "model": decision.selected_model,
                        "response_length": len(response_text)
                    })

                    # Add to history
                    history.append({
                        "role": "user",
                        "content": query_text
                    })
                    history.append({
                        "role": "assistant",
                        "content": response_text
                    })

                    # Keep last 10 messages
                    if len(history) > 20:
                        history = history[-20:]

                    # Record metrics
                    metrics.record_query(
                        model=decision.selected_model,
                        query_type=decision.query_type.value,
                        latency=0,  # Streaming, so no single latency
                        status="success"
                    )

                except Exception as e:
                    logger.error(f"Query error: {e}")
                    await manager.send_message(connection_id, {
                        "type": "error",
                        "error": str(e)
                    })

            elif message_type == "clear":
                # Clear history
                history.clear()
                await manager.send_message(connection_id, {
                    "type": "cleared"
                })

            elif message_type == "ping":
                # Respond to ping
                await manager.send_message(connection_id, {
                    "type": "pong"
                })

    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"Chat WebSocket disconnected: {connection_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(connection_id)


@router.websocket("/batch")
async def websocket_batch(websocket: WebSocket):
    """
    Batch processing over WebSocket.

    Handle multiple queries efficiently over a single connection.
    """
    from main import app

    executor: QueryExecutor = app.state.executor
    metrics = app.state.metrics

    connection_id = f"batch-{datetime.now().timestamp()}"

    await manager.connect(connection_id, websocket)

    try:
        await manager.send_message(connection_id, {
            "type": "connected",
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat()
        })

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type", "batch")

            if message_type == "batch":
                queries = message.get("queries", [])

                if not queries:
                    await manager.send_message(connection_id, {
                        "type": "error",
                        "error": "Queries list is required"
                    })
                    continue

                try:
                    # Send start
                    await manager.send_message(connection_id, {
                        "type": "batch_start",
                        "count": len(queries)
                    })

                    # Execute batch
                    results = await executor.execute_batch(queries)

                    # Send results
                    for i, result in enumerate(results):
                        await manager.send_message(connection_id, {
                            "type": "batch_result",
                            "index": i,
                            "response": result.response,
                            "model": result.model_used,
                            "processing_time": result.processing_time,
                            "from_cache": result.from_cache
                        })

                    # Send completion
                    await manager.send_message(connection_id, {
                        "type": "batch_done",
                        "count": len(results)
                    })

                    # Record metrics
                    for result in results:
                        metrics.record_query(
                            model=result.model_used,
                            query_type="batch",
                            latency=result.processing_time,
                            status="success"
                        )

                except Exception as e:
                    logger.error(f"Batch error: {e}")
                    await manager.send_message(connection_id, {
                        "type": "error",
                        "error": str(e)
                    })

            elif message_type == "ping":
                await manager.send_message(connection_id, {
                    "type": "pong"
                })

    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"Batch WebSocket disconnected: {connection_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(connection_id)
