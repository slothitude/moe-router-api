"""Models package for Ollama client and model specifications."""

from .ollama_client import OllamaClient
from .model_specs import ModelSpec, ModelRegistry, QueryType
from .query_classifier import QueryClassifier

__all__ = [
    "OllamaClient",
    "ModelSpec",
    "ModelRegistry",
    "QueryType",
    "QueryClassifier",
]
