"""Query classification and routing engine."""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from models.model_specs import ModelRegistry, QueryType
from models.query_classifier import QueryClassifier
from core.model_pool import ModelPool
from core.fallback import FallbackManager

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """Result of routing decision."""
    query_type: QueryType
    selected_model: str
    fallback_chain: List[str]
    confidence: float
    reasoning: str


class QueryRouter:
    """
    Analyze queries and select optimal model.

    Uses query classification + model selection + current load
    to make intelligent routing decisions.
    """

    def __init__(
        self,
        classifier: QueryClassifier,
        model_pool: ModelPool,
        fallback_manager: FallbackManager
    ):
        """
        Initialize query router.

        Args:
            classifier: Query classifier instance
            model_pool: Model pool instance
            fallback_manager: Fallback manager instance
        """
        self.classifier = classifier
        self.model_pool = model_pool
        self.fallback_manager = fallback_manager

    async def route(
        self,
        query: str,
        preferred_model: Optional[str] = None,
        exclude_models: Optional[List[str]] = None
    ) -> RoutingDecision:
        """
        Route a query to the optimal model.

        Args:
            query: Query string
            preferred_model: Optional specific model to use
            exclude_models: Models to exclude from selection

        Returns:
            RoutingDecision with selected model and reasoning
        """
        # Classify query
        query_type = await self.classifier.classify(query)

        # Get fallback chain for query type
        fallback_chain = ModelRegistry.get_models_for_query_type(query_type)

        # Filter out excluded models and models with open circuits
        available_models = [
            model for model in fallback_chain
            if (exclude_models is None or model not in exclude_models)
            and not self.fallback_manager.is_circuit_open(model)
        ]

        if not available_models:
            # All models excluded or have open circuits, try to reset
            logger.warning("All models excluded or unavailable, attempting circuit reset")
            available_models = [model for model in fallback_chain
                              if exclude_models is None or model not in exclude_models]

        if preferred_model and preferred_model not in available_models:
            # Check if preferred model is available
            if not self.fallback_manager.is_circuit_open(preferred_model):
                available_models.insert(0, preferred_model)

        if not available_models:
            # Last resort: use any model
            all_models = list(ModelRegistry.get_all_models().keys())
            available_models = [m for m in all_models
                              if not self.fallback_manager.is_circuit_open(m)]

        if not available_models:
            raise Exception("No models available")

        # Select best model from chain
        selected_model = await self._select_best_model(
            available_models,
            query_type,
            query
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            query_type,
            selected_model,
            query
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            query_type,
            selected_model,
            fallback_chain
        )

        return RoutingDecision(
            query_type=query_type,
            selected_model=selected_model,
            fallback_chain=available_models,
            confidence=confidence,
            reasoning=reasoning
        )

    async def _select_best_model(
        self,
        candidate_models: List[str],
        query_type: QueryType,
        query: str
    ) -> str:
        """
        Select best model from candidates.

        Args:
            candidate_models: List of model names to consider
            query_type: Classified query type
            query: Query string

        Returns:
            Selected model name
        """
        # Score each model
        scores = {}
        for model_name in candidate_models:
            spec = ModelRegistry.get_model(model_name)
            if not spec:
                continue

            # Base score from model spec
            base_score = spec.get_score(query_type)

            # Check if model is loaded (bonus for loaded models)
            is_loaded = model_name in self.model_pool.models
            load_bonus = 10.0 if is_loaded else 0.0

            # Check model location (GPU bonus)
            if is_loaded:
                status = self.model_pool.models[model_name]
                location_bonus = 5.0 if status.location == "gpu" else 0.0
            else:
                location_bonus = 0.0

            # Check circuit breaker state
            if self.fallback_manager.is_circuit_open(model_name):
                # Heavily penalize models with open circuits
                circuit_penalty = -1000.0
            else:
                # Consider failure rate
                failure_rate = self.fallback_manager.get_failure_rate(model_name)
                circuit_penalty = -failure_rate * 50.0

            scores[model_name] = base_score + load_bonus + location_bonus + circuit_penalty

        # Select model with highest score
        best_model = max(scores.items(), key=lambda x: x[1])[0]
        logger.debug(f"Model scores: {scores}, selected: {best_model}")

        return best_model

    def _calculate_confidence(
        self,
        query_type: QueryType,
        selected_model: str,
        query: str
    ) -> float:
        """
        Calculate confidence in routing decision.

        Args:
            query_type: Classified query type
            selected_model: Model that was selected
            query: Query string

        Returns:
            Confidence score (0.0 to 1.0)
        """
        spec = ModelRegistry.get_model(selected_model)
        if not spec:
            return 0.5

        # High confidence if model specializes in query type
        if query_type in spec.query_types:
            return 0.9

        # Medium confidence if model is in fallback chain
        if query_type in ModelRegistry.FALLBACK_CHAINS:
            chain = ModelRegistry.FALLBACK_CHAINS[query_type]
            if selected_model in chain:
                position = chain.index(selected_model)
                # Decrease confidence based on position in chain
                return max(0.5, 0.8 - position * 0.15)

        # Low confidence for fallback
        return 0.5

    def _generate_reasoning(
        self,
        query_type: QueryType,
        selected_model: str,
        fallback_chain: List[str]
    ) -> str:
        """
        Generate human-readable reasoning for routing decision.

        Args:
            query_type: Classified query type
            selected_model: Model that was selected
            fallback_chain: Available fallback chain

        Returns:
            Reasoning string
        """
        spec = ModelRegistry.get_model(selected_model)
        if not spec:
            return f"Selected {selected_model} (unknown spec)"

        reasoning = [
            f"Query type: {query_type.value}",
            f"Selected: {selected_model}",
            f"Strength: {spec.strength}",
            f"Performance: {spec.total_time_s}s total, "
            f"{spec.prompt_speed_tps} t/s prompt, {spec.gen_speed_tps} t/s gen"
        ]

        if query_type in spec.query_types:
            reasoning.append("Model specializes in this query type")
        else:
            reasoning.append(f"Model is in fallback chain for {query_type.value}")

        # Add fallback info
        if len(fallback_chain) > 1:
            reasoning.append(f"Fallback chain: {' → '.join(fallback_chain[:3])}")

        return ". ".join(reasoning)

    async def get_routing_stats(self) -> Dict[str, Any]:
        """
        Get routing statistics.

        Returns:
            Dict with routing stats
        """
        pool_status = self.model_pool.get_status()
        circuit_states = self.fallback_manager.get_all_states()

        return {
            "model_pool": pool_status,
            "circuit_breakers": circuit_states,
            "available_models": list(ModelRegistry.get_all_models().keys())
        }
