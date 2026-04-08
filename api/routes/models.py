"""Model management API endpoints."""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

from models.model_specs import ModelRegistry
from core.model_pool import ModelPool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/models", tags=["models"])


# Request/Response Models
class ModelInfo(BaseModel):
    """Model information."""
    name: str
    total_time_s: float
    prompt_speed_tps: float
    gen_speed_tps: float
    strength: str
    query_types: List[str]
    memory_mb: int
    prefers_gpu: bool
    description: str


class ModelStatus(BaseModel):
    """Model status in pool."""
    name: str
    location: Optional[str] = None  # "gpu", "ram", or None if not loaded
    loaded_at: Optional[str] = None
    last_used: Optional[str] = None
    use_count: int = 0
    is_available: bool = True


class ModelListResponse(BaseModel):
    """Response for model list endpoint."""
    models: List[ModelInfo]
    total: int


class ModelPoolStatus(BaseModel):
    """Model pool status."""
    gpu_models: List[str]
    ram_models: List[str]
    gpu_usage_mb: int
    gpu_capacity_mb: int
    ram_usage_mb: int
    ram_capacity_mb: int
    total_models: int


class LoadRequest(BaseModel):
    """Request to load a model."""
    force: bool = Field(False, description="Force reload even if already loaded")


def get_app_state():
    """Get app state (dependency injection)."""
    from main import app
    return app


@router.get("", response_model=ModelListResponse)
async def list_models():
    """
    List all available models with specifications.

    Returns benchmark data and capabilities for all models.
    """
    try:
        all_models = ModelRegistry.get_all_models()

        model_infos = []
        for name, spec in all_models.items():
            model_infos.append(ModelInfo(
                name=spec.name,
                total_time_s=spec.total_time_s,
                prompt_speed_tps=spec.prompt_speed_tps,
                gen_speed_tps=spec.gen_speed_tps,
                strength=spec.strength,
                query_types=[qt.value for qt in spec.query_types],
                memory_mb=spec.memory_mb,
                prefers_gpu=spec.prefers_gpu,
                description=spec.description
            ))

        return ModelListResponse(
            models=model_infos,
            total=len(model_infos)
        )

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pool", response_model=ModelPoolStatus)
async def get_pool_status():
    """
    Get current model pool status.

    Shows which models are loaded in GPU vs RAM.
    """
    from main import app

    model_pool: ModelPool = app.state.model_pool

    try:
        status = model_pool.get_status()

        return ModelPoolStatus(
            gpu_models=status["gpu_models"],
            ram_models=status["ram_models"],
            gpu_usage_mb=status["gpu_usage_mb"],
            gpu_capacity_mb=status["gpu_capacity_mb"],
            ram_usage_mb=status["ram_usage_mb"],
            ram_capacity_mb=status["ram_capacity_mb"],
            total_models=status["total_models"]
        )

    except Exception as e:
        logger.error(f"Failed to get pool status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_name}", response_model=ModelStatus)
async def get_model_status(model_name: str):
    """
    Get status of a specific model.

    Shows if model is loaded, location, and usage stats.
    """
    from main import app

    model_pool: ModelPool = app.state.model_pool
    ollama_client = app.state.ollama_client

    try:
        # Get pool status
        pool_status = model_pool.get_model_status(model_name)

        # Check if available in Ollama
        is_available = False
        try:
            available_models = await ollama_client.list_models()
            available_names = [m["name"] for m in available_models]
            is_available = model_name in available_names
        except Exception as e:
            logger.warning(f"Failed to check Ollama availability: {e}")

        if pool_status:
            return ModelStatus(
                name=pool_status["name"],
                location=pool_status["location"],
                loaded_at=pool_status["loaded_at"],
                last_used=pool_status["last_used"],
                use_count=pool_status["use_count"],
                is_available=is_available
            )
        else:
            # Model not loaded in pool
            spec = ModelRegistry.get_model(model_name)
            if spec:
                return ModelStatus(
                    name=model_name,
                    location=None,
                    loaded_at=None,
                    last_used=None,
                    use_count=0,
                    is_available=is_available
                )
            else:
                raise HTTPException(status_code=404, detail=f"Unknown model: {model_name}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_name}/load")
async def load_model(model_name: str, request: LoadRequest = None):
    """
    Preload a model into the pool.

    Loads the model into GPU or RAM based on its preferences.
    """
    from main import app

    model_pool: ModelPool = app.state.model_pool

    try:
        # Check if model exists
        spec = ModelRegistry.get_model(model_name)
        if not spec:
            raise HTTPException(status_code=404, detail=f"Unknown model: {model_name}")

        # Check if already loaded
        if model_name in model_pool.models and not (request and request.force):
            return {
                "message": f"Model {model_name} already loaded",
                "location": model_pool.models[model_name].location
            }

        # Load model
        success = await model_pool.smart_swap(model_name)

        if success:
            status = model_pool.get_model_status(model_name)
            return {
                "message": f"Model {model_name} loaded successfully",
                "location": status["location"] if status else None,
                "memory_mb": spec.memory_mb
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load model {model_name}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_name}/unload")
async def unload_model(model_name: str):
    """
    Unload a model from the pool.

    Frees up GPU/RAM memory.
    """
    from main import app

    model_pool: ModelPool = app.state.model_pool

    try:
        # Check if model is loaded
        if model_name not in model_pool.models:
            raise HTTPException(
                status_code=404,
                detail=f"Model {model_name} is not loaded"
            )

        # Get memory info before unloading
        spec = ModelRegistry.get_model(model_name)
        memory_mb = spec.memory_mb if spec else 0
        location = model_pool.models[model_name].location

        # Unload
        await model_pool._unload_model(model_name)

        return {
            "message": f"Model {model_name} unloaded",
            "freed_memory_mb": memory_mb,
            "was_in": location
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unload model: {e}")
        raise HTTPException(status_code=500, detail=str(e))
