"""Model specifications and benchmark data for routing decisions."""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class QueryType(Enum):
    """Query classification types."""
    CODE = "code"
    SPEED_CRITICAL = "speed_critical"
    GENERATION_HEAVY = "generation_heavy"
    PROMPT_HEAVY = "prompt_heavy"
    BALANCED = "balanced"


@dataclass
class ModelSpec:
    """Model specification with performance characteristics."""

    name: str
    total_time_s: float
    prompt_speed_tps: float
    gen_speed_tps: float
    strength: str
    query_types: List[QueryType]
    memory_mb: int
    prefers_gpu: bool = True
    description: str = ""

    def get_score(self, query_type: QueryType, query_length: int = 0) -> float:
        """
        Calculate routing score for this model based on query type.

        Args:
            query_type: Type of query
            query_length: Length of query in characters

        Returns:
            Score (higher is better)
        """
        # Base score from total time (lower time = higher score)
        time_score = 100.0 / max(self.total_time_s, 1.0)

        # Boost if model specializes in this query type
        specialization_bonus = 50.0 if query_type in self.query_types else 0.0

        # Adjust based on query characteristics
        if query_type == QueryType.PROMPT_HEAVY:
            # Prefer fast prompt processing
            prompt_score = self.prompt_speed_tps / 10.0
            return time_score + specialization_bonus + prompt_score
        elif query_type == QueryType.GENERATION_HEAVY:
            # Prefer fast generation
            gen_score = self.gen_speed_tps / 10.0
            return time_score + specialization_bonus + gen_score
        elif query_type == QueryType.SPEED_CRITICAL:
            # Prefer lowest total time
            return time_score * 2.0 + specialization_bonus
        else:
            # Balanced score
            return time_score + specialization_bonus


class ModelRegistry:
    """Registry of available models with their specifications."""

    MODELS: Dict[str, ModelSpec] = {
        "qwen3:4b": ModelSpec(
            name="qwen3:4b",
            total_time_s=12.5,
            prompt_speed_tps=653,
            gen_speed_tps=73,
            strength="Fastest overall, good for general use",
            query_types=[QueryType.SPEED_CRITICAL, QueryType.BALANCED],
            memory_mb=1500,
            prefers_gpu=True,
            description="4B parameter model with excellent overall speed"
        ),
        "qwen2.5-coder": ModelSpec(
            name="qwen2.5-coder",
            total_time_s=13.0,  # Estimated, will benchmark
            prompt_speed_tps=600,
            gen_speed_tps=75,
            strength="Code specialist",
            query_types=[QueryType.CODE],
            memory_mb=2000,
            prefers_gpu=True,
            description="Specialized code model for programming tasks"
        ),
        "llama3.2": ModelSpec(
            name="llama3.2",
            total_time_s=21.7,
            prompt_speed_tps=3,
            gen_speed_tps=107,
            strength="Fastest generation",
            query_types=[QueryType.GENERATION_HEAVY],
            memory_mb=2000,
            prefers_gpu=True,
            description="Optimized for fast text generation"
        ),
        "llama3.1": ModelSpec(
            name="llama3.1",
            total_time_s=18.9,
            prompt_speed_tps=77,
            gen_speed_tps=15,
            strength="Balanced performance",
            query_types=[QueryType.BALANCED, QueryType.CODE, QueryType.SPEED_CRITICAL],
            memory_mb=3500,
            prefers_gpu=False,
            description="Well-balanced model for general tasks"
        ),
        "ministral-3": ModelSpec(
            name="ministral-3",
            total_time_s=28.9,
            prompt_speed_tps=836,
            gen_speed_tps=9,
            strength="Fastest prompt processing",
            query_types=[QueryType.PROMPT_HEAVY],
            memory_mb=3000,
            prefers_gpu=False,
            description="Excellent for processing large prompts"
        ),
        "phi3:mini": ModelSpec(
            name="phi3:mini",
            total_time_s=43.6,
            prompt_speed_tps=2,
            gen_speed_tps=99,
            strength="Good generation speed",
            query_types=[QueryType.GENERATION_HEAVY, QueryType.BALANCED],
            memory_mb=2500,
            prefers_gpu=False,
            description="Fallback option with good generation"
        ),
        "nemotron-3-nano:4b": ModelSpec(
            name="nemotron-3-nano:4b",
            total_time_s=20.3,
            prompt_speed_tps=448,
            gen_speed_tps=76,
            strength="Balanced fallback",
            query_types=[QueryType.SPEED_CRITICAL, QueryType.BALANCED],
            memory_mb=2000,
            prefers_gpu=False,
            description="Reliable fallback model"
        ),
    }

    # Fallback chains for each query type
    FALLBACK_CHAINS: Dict[QueryType, List[str]] = {
        QueryType.CODE: ["qwen2.5-coder", "qwen3:4b", "llama3.1"],
        QueryType.SPEED_CRITICAL: ["qwen3:4b", "nemotron-3-nano:4b", "llama3.1"],
        QueryType.GENERATION_HEAVY: ["llama3.2", "phi3:mini", "llama3.1"],
        QueryType.PROMPT_HEAVY: ["ministral-3", "qwen3:4b", "nemotron-3-nano:4b"],
        QueryType.BALANCED: ["llama3.1", "qwen3:4b", "llama3.2"],
    }

    @classmethod
    def normalize_model_name(cls, name: str) -> str:
        """
        Normalize model name by removing :latest or other tags.

        Args:
            name: Model name (may include :latest or other tags)

        Returns:
            Normalized model name
        """
        # Remove :latest or other tags
        if ":" in name and name.endswith(":latest"):
            return name.rsplit(":", 1)[0]
        return name

    @classmethod
    def get_model(cls, name: str) -> Optional[ModelSpec]:
        """
        Get model specification by name.

        Args:
            name: Model name

        Returns:
            ModelSpec or None if not found
        """
        # Try exact match first
        if name in cls.MODELS:
            return cls.MODELS[name]

        # Try with normalization
        normalized = cls.normalize_model_name(name)
        if normalized in cls.MODELS:
            return cls.MODELS[normalized]

        # Try adding :latest
        if f"{name}:latest" in cls.MODELS:
            return cls.MODELS[f"{name}:latest"]

        return None

    @classmethod
    def get_all_models(cls) -> Dict[str, ModelSpec]:
        """Get all model specifications."""
        return cls.MODELS.copy()

    @classmethod
    def get_models_for_query_type(cls, query_type: QueryType) -> List[str]:
        """
        Get fallback chain for a query type.

        Args:
            query_type: Type of query

        Returns:
            List of model names in priority order
        """
        return cls.FALLBACK_CHAINS.get(query_type, ["llama3.1"])

    @classmethod
    def get_gpu_models(cls) -> List[str]:
        """Get models that prefer GPU."""
        return [name for name, spec in cls.MODELS.items() if spec.prefers_gpu]

    @classmethod
    def get_ram_models(cls) -> List[str]:
        """Get models that can run in RAM."""
        return [name for name, spec in cls.MODELS.items() if not spec.prefers_gpu]

    @classmethod
    def get_total_memory(cls, model_names: List[str]) -> int:
        """
        Calculate total memory required for models.

        Args:
            model_names: List of model names

        Returns:
            Total memory in MB
        """
        return sum(cls.MODELS.get(name, ModelSpec("", 0, 0, 0, "", [], 0)).memory_mb
                   for name in model_names if name in cls.MODELS)
