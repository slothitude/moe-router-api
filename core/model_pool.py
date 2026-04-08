"""Model pool management for GPU/RAM caching and intelligent swapping."""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta

from models.model_specs import ModelRegistry, ModelSpec
from models.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


@dataclass
class ModelStatus:
    """Status of a model in the pool."""
    name: str
    location: str  # "gpu", "ram", "disk"
    loaded_at: datetime
    last_used: datetime
    use_count: int
    is_loading: bool = False


class ModelPool:
    """
    Manages model pool with GPU/RAM caching and intelligent swapping.

    Memory Strategy:
    - GPU Pool (3.5GB): qwen3:4b (resident) + 1 on-demand
    - RAM Pool (16GB): 5-6 models with LRU eviction
    """

    def __init__(
        self,
        gpu_capacity_mb: int = 3500,
        ram_capacity_mb: int = 20000,
        preload_models: Optional[List[str]] = None
    ):
        """
        Initialize model pool.

        Args:
            gpu_capacity_mb: GPU memory capacity in MB
            ram_capacity_mb: RAM capacity for models in MB
            preload_models: Models to preload on startup
        """
        self.gpu_capacity_mb = gpu_capacity_mb
        self.ram_capacity_mb = ram_capacity_mb
        self.preload_models = preload_models or []

        # Model status tracking
        self.models: Dict[str, ModelStatus] = {}
        self.gpu_models: OrderedDict[str, ModelStatus] = OrderedDict()
        self.ram_models: OrderedDict[str, ModelStatus] = OrderedDict()

        # Memory tracking
        self.current_gpu_mb = 0
        self.current_ram_mb = 0

        # Lock for thread safety
        self._lock = asyncio.Lock()

        # Ollama client (will be set during initialization)
        self.ollama: Optional[OllamaClient] = None

    async def initialize(self, ollama_client: OllamaClient):
        """
        Initialize model pool and preload core models.

        Args:
            ollama_client: Ollama client instance
        """
        self.ollama = ollama_client

        async with self._lock:
            # Check Ollama health
            if not await self.ollama.health_check():
                logger.error("Ollama is not healthy, cannot initialize model pool")
                return

            # Get available models
            available = await self.ollama.list_models()
            # Handle both "model:tag" and "model" formats, normalize to base name
            available_names = []
            for m in available:
                name = m["name"]
                # Remove ":latest" or other tags for normalization
                if ":" in name:
                    base_name = name.rsplit(":", 1)[0]
                    # For models with version in name like qwen3:4b, keep the version
                    if base_name.count(":") > 0:
                        available_names.append(base_name)
                    else:
                        # Check if it has a version tag (e.g., :4b)
                        parts = name.split(":")
                        if len(parts) >= 2:
                            # Keep the base name with version if present
                            available_names.append(name.rsplit(":", 1)[0])
                        else:
                            available_names.append(base_name)
                else:
                    available_names.append(name)

            logger.info(f"Available models: {available_names}")

            # Preload configured models
            for model_name in self.preload_models:
                if model_name in available_names:
                    await self._load_model(model_name, prefer_gpu=ModelRegistry.get_model(model_name).prefers_gpu)
                else:
                    logger.warning(f"Model {model_name} not available, skipping preload")

            logger.info(f"Model pool initialized: {len(self.gpu_models)} GPU, {len(self.ram_models)} RAM")

    async def _load_model(self, model_name: str, prefer_gpu: bool = True) -> bool:
        """
        Load a model into the pool.

        Args:
            model_name: Name of model to load
            prefer_gpu: Whether to prefer GPU (if model supports it)

        Returns:
            True if loaded successfully
        """
        spec = ModelRegistry.get_model(model_name)
        if not spec:
            logger.error(f"Unknown model: {model_name}")
            return False

        # Check if already loaded
        if model_name in self.models:
            logger.debug(f"Model {model_name} already loaded")
            return True

        # Determine where to load
        if spec.prefers_gpu and prefer_gpu:
            # Try to load to GPU
            if self.current_gpu_mb + spec.memory_mb <= self.gpu_capacity_mb:
                location = "gpu"
            elif self.current_ram_mb + spec.memory_mb <= self.ram_capacity_mb:
                location = "ram"
            else:
                # Need to evict
                location = await self._make_space(spec.memory_mb, prefer_gpu=True)
        else:
            # Load to RAM
            if self.current_ram_mb + spec.memory_mb <= self.ram_capacity_mb:
                location = "ram"
            else:
                location = await self._make_space(spec.memory_mb, prefer_gpu=False)

        if location is None:
            logger.error(f"Cannot make space for {model_name}")
            return False

        # Load the model via Ollama (warmup inference)
        logger.info(f"Loading {model_name} to {location}")

        try:
            # Perform a simple inference to load the model
            await self.ollama.generate(
                model=model_name,
                prompt="Hi",
                options={"num_predict": 1}
            )

            # Create status
            now = datetime.now()
            status = ModelStatus(
                name=model_name,
                location=location,
                loaded_at=now,
                last_used=now,
                use_count=0
            )

            self.models[model_name] = status

            if location == "gpu":
                self.gpu_models[model_name] = status
                self.current_gpu_mb += spec.memory_mb
            else:
                self.ram_models[model_name] = status
                self.current_ram_mb += spec.memory_mb

            logger.info(f"Loaded {model_name} to {location} ({spec.memory_mb}MB)")
            return True

        except Exception as e:
            logger.error(f"Failed to load {model_name}: {e}")
            return False

    async def _make_space(self, required_mb: int, prefer_gpu: bool) -> Optional[str]:
        """
        Evict models to make space.

        Args:
            required_mb: Memory required in MB
            prefer_gpu: Whether to prefer GPU space

        Returns:
            Location where space was made ("gpu", "ram", or None)
        """
        if prefer_gpu:
            # Try GPU first
            if await self._evict_from_gpu(required_mb):
                return "gpu"
            # Then try RAM
            if await self._evict_from_ram(required_mb):
                return "ram"
        else:
            # Try RAM first
            if await self._evict_from_ram(required_mb):
                return "ram"
            # Then try GPU
            if await self._evict_from_gpu(required_mb):
                return "gpu"

        return None

    async def _evict_from_gpu(self, required_mb: int) -> bool:
        """
        Evict models from GPU to make space.

        Args:
            required_mb: Memory required in MB

        Returns:
            True if enough space was made
        """
        freed_mb = 0

        # Evict LRU models (keep qwen3:4b if possible)
        for model_name in list(self.gpu_models.keys()):
            if freed_mb >= required_mb:
                break

            # Keep qwen3:4b as last resort
            if model_name == "qwen3:4b" and len(self.gpu_models) > 1:
                continue

            status = self.gpu_models[model_name]
            spec = ModelRegistry.get_model(model_name)

            # Move to RAM if possible
            if spec and not spec.prefers_gpu:
                await self._move_to_ram(model_name)
            else:
                # Unload completely
                await self._unload_model(model_name)

            freed_mb += spec.memory_mb if spec else 0

        return freed_mb >= required_mb

    async def _evict_from_ram(self, required_mb: int) -> bool:
        """
        Evict models from RAM to make space.

        Args:
            required_mb: Memory required in MB

        Returns:
            True if enough space was made
        """
        freed_mb = 0

        # Evict LRU models
        for model_name in list(self.ram_models.keys()):
            if freed_mb >= required_mb:
                break

            status = self.ram_models[model_name]
            spec = ModelRegistry.get_model(model_name)

            await self._unload_model(model_name)
            freed_mb += spec.memory_mb if spec else 0

        return freed_mb >= required_mb

    async def _move_to_ram(self, model_name: str):
        """
        Move a model from GPU to RAM.

        Args:
            model_name: Name of model to move
        """
        if model_name not in self.gpu_models:
            return

        spec = ModelRegistry.get_model(model_name)
        status = self.gpu_models[model_name]

        # Check if RAM has space
        if self.current_ram_mb + spec.memory_mb > self.ram_capacity_mb:
            # Need to evict from RAM first
            await self._evict_from_ram(spec.memory_mb)

        # Update status
        status.location = "ram"
        del self.gpu_models[model_name]
        self.ram_models[model_name] = status

        self.current_gpu_mb -= spec.memory_mb
        self.current_ram_mb += spec.memory_mb

        logger.info(f"Moved {model_name} from GPU to RAM")

    async def _unload_model(self, model_name: str):
        """
        Unload a model completely.

        Args:
            model_name: Name of model to unload
        """
        spec = ModelRegistry.get_model(model_name)

        if model_name in self.gpu_models:
            del self.gpu_models[model_name]
            self.current_gpu_mb -= spec.memory_mb if spec else 0

        if model_name in self.ram_models:
            del self.ram_models[model_name]
            self.current_ram_mb -= spec.memory_mb if spec else 0

        if model_name in self.models:
            del self.models[model_name]

        logger.info(f"Unloaded {model_name}")

    async def get_model(self, model_name: str) -> Optional[str]:
        """
        Get a model, loading it if necessary.

        Args:
            model_name: Name of model to get

        Returns:
            Model name if available, None otherwise
        """
        async with self._lock:
            # Check if already loaded
            if model_name in self.models:
                status = self.models[model_name]
                status.last_used = datetime.now()
                status.use_count += 1

                # Move to end of LRU queue
                if model_name in self.gpu_models:
                    self.gpu_models.move_to_end(model_name)
                elif model_name in self.ram_models:
                    self.ram_models.move_to_end(model_name)

                logger.debug(f"Model {model_name} already loaded in {status.location}")
                return model_name

            # Load the model
            spec = ModelRegistry.get_model(model_name)
            if not spec:
                return None

            success = await self._load_model(model_name, prefer_gpu=spec.prefers_gpu)
            return model_name if success else None

    async def smart_swap(self, target_model: str) -> bool:
        """
        Perform predictive model loading based on usage patterns.

        Args:
            target_model: Model to ensure is loaded

        Returns:
            True if model is ready
        """
        async with self._lock:
            if target_model in self.models:
                return True

            spec = ModelRegistry.get_model(target_model)
            if not spec:
                return False

            # Load with smart placement
            return await self._load_model(target_model, prefer_gpu=spec.prefers_gpu)

    async def warmup_models(self):
        """Warm up loaded models with a test inference."""
        async with self._lock:
            for model_name, status in list(self.models.items()):
                try:
                    await self.ollama.generate(
                        model=model_name,
                        prompt="Hello",
                        options={"num_predict": 1}
                    )
                    logger.debug(f"Warmed up {model_name}")
                except Exception as e:
                    logger.warning(f"Failed to warm up {model_name}: {e}")

    def get_status(self) -> Dict:
        """
        Get pool status.

        Returns:
            Dict with pool information
        """
        return {
            "gpu_models": list(self.gpu_models.keys()),
            "ram_models": list(self.ram_models.keys()),
            "gpu_usage_mb": self.current_gpu_mb,
            "gpu_capacity_mb": self.gpu_capacity_mb,
            "ram_usage_mb": self.current_ram_mb,
            "ram_capacity_mb": self.ram_capacity_mb,
            "total_models": len(self.models)
        }

    def get_model_status(self, model_name: str) -> Optional[Dict]:
        """
        Get status of a specific model.

        Args:
            model_name: Name of model

        Returns:
            Dict with model status or None
        """
        if model_name not in self.models:
            return None

        status = self.models[model_name]
        return {
            "name": status.name,
            "location": status.location,
            "loaded_at": status.loaded_at.isoformat(),
            "last_used": status.last_used.isoformat(),
            "use_count": status.use_count
        }
