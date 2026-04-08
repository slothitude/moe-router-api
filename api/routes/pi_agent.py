"""Pi Agent Admin API endpoints.

These endpoints are used by the Pi Agent Boss to manage the routing system.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.model_specs import ModelRegistry, QueryType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# Request/Response Models
class RoutingUpdate(BaseModel):
    """Request to update routing configuration."""
    category: str
    model: str
    score: Optional[float] = None
    priority: Optional[int] = None


class ModelScoreUpdate(BaseModel):
    """Request to update model benchmark scores."""
    model: str
    scores: Dict[str, float]  # category -> score


class RoutingConfig(BaseModel):
    """Current routing configuration."""
    fallback_chains: Dict[str, list]
    model_scores: Dict[str, Dict[str, float]]
    recommendations: Dict[str, str]


def get_app_state():
    """Get app state (dependency injection)."""
    from main import app
    return app


@router.get("/routing", response_model=RoutingConfig)
async def get_routing_config():
    """
    Get current routing configuration.

    Returns fallback chains and model scores.
    """
    try:
        # Get fallback chains
        fallback_chains = {
            qt.value: chain
            for qt, chain in ModelRegistry.FALLBACK_CHAINS.items()
        }

        # Get model scores (from specs)
        model_scores = {}
        for name, spec in ModelRegistry.get_all_models().items():
            model_scores[name] = {
                qt.value: spec.get_score(qt)
                for qt in QueryType
            }

        return RoutingConfig(
            fallback_chains=fallback_chains,
            model_scores=model_scores,
            recommendations={}
        )

    except Exception as e:
        logger.error(f"Failed to get routing config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/routing/recommendations")
async def update_routing_recommendations(recommendations: Dict[str, str]):
    """
    Update routing recommendations from Pi Agent.

    The Pi Agent provides optimal model per category based on benchmarks.
    """
    try:
        # In a full implementation, this would update the router's
        # fallback chains or scoring system

        # For now, we'll log and acknowledge
        logger.info(f"Updated routing recommendations: {recommendations}")

        # Store recommendations (could be persisted or used to update ModelRegistry)
        from main import app
        if not hasattr(app.state, 'pi_recommendations'):
            app.state.pi_recommendations = {}
        app.state.pi_recommendations.update(recommendations)

        return {
            "message": "Routing recommendations updated",
            "recommendations": recommendations,
            "categories_updated": len(recommendations)
        }

    except Exception as e:
        logger.error(f"Failed to update recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/routing/update-fallback")
async def update_fallback_chain(category: str, chain: list):
    """
    Update fallback chain for a category.

    Pi Agent can use this to optimize routing based on benchmark results.
    """
    try:
        # Convert string to QueryType
        query_type = QueryType(category)

        # Validate all models exist
        for model in chain:
            if not ModelRegistry.get_model(model):
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown model: {model}"
                )

        # Update the fallback chain (this modifies ModelRegistry)
        ModelRegistry.FALLBACK_CHAINS[query_type] = chain

        logger.info(f"Updated fallback chain for {category}: {' -> '.join(chain)}")

        return {
            "message": f"Fallback chain updated for {category}",
            "category": category,
            "chain": chain
        }

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {category}"
        )
    except Exception as e:
        logger.error(f"Failed to update fallback chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model/benchmark-score")
async def update_model_benchmark_score(update: ModelScoreUpdate):
    """
    Update a model's benchmark scores.

    Pi Agent provides scores from running benchmarks.
    """
    try:
        spec = ModelRegistry.get_model(update.model)
        if not spec:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown model: {update.model}"
            )

        # Store benchmark scores
        # In a full implementation, this might update the ModelSpec
        # or be used in routing decisions

        from main import app
        if not hasattr(app.state, 'benchmark_scores'):
            app.state.benchmark_scores = {}
        app.state.benchmark_scores[update.model] = update.scores

        logger.info(f"Updated benchmark scores for {update.model}: {update.scores}")

        return {
            "message": f"Benchmark scores updated for {update.model}",
            "model": update.model,
            "scores": update.scores
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update benchmark scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pi-status")
async def get_pi_agent_status():
    """
    Get Pi Agent status and recommendations.

    Returns what the Pi Agent has configured.
    """
    try:
        from main import app

        status = {
            "enabled": hasattr(app.state, 'pi_agent_active') and app.state.pi_agent_active,
            "recommendations": getattr(app.state, 'pi_recommendations', {}),
            "benchmark_scores": getattr(app.state, 'benchmark_scores', {}),
            "last_update": getattr(app.state, 'pi_last_update', None),
        }

        return status

    except Exception as e:
        logger.error(f"Failed to get Pi Agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload-models")
async def reload_model_registry():
    """
    Reload model registry.

    Pi Agent can call this when it discovers new models.
    """
    try:
        # In a full implementation, this would reload the model specs
        # from a config file or database

        logger.info("Model registry reload requested by Pi Agent")

        return {
            "message": "Model registry reload initiated",
            "models_count": len(ModelRegistry.get_all_models())
        }

    except Exception as e:
        logger.error(f"Failed to reload model registry: {e}")
        raise HTTPException(status_code=500, detail=str(e))
