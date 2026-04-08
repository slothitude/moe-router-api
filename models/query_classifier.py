"""Query classification using embeddings and heuristic analysis."""

import re
import logging
from typing import List, Dict, Optional, Tuple
import numpy as np

from models.model_specs import QueryType
from models.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class QueryClassifier:
    """
    Classify queries into types for routing decisions.

    Uses a combination of:
    1. Keyword/regex patterns for fast classification
    2. Embedding-based semantic similarity for nuanced cases
    """

    # Patterns for code detection
    CODE_PATTERNS = [
        r'\bdef\s+\w+\s*\(',  # Python function
        r'\bclass\s+\w+\s*:',  # Python class
        r'\bfunction\s+\w+\s*\(',  # JavaScript function
        r'\bpublic\s+(static\s+)?void\s+\w+',  # Java method
        r'#include\s*[<"]',  # C/C++ include
        r'\bimport\s+\w+',  # Python/JS import
        r'\bfrom\s+\w+\s+import',  # Python import
        r'console\.log\(',  # JS console
        r'print\s*\(',  # Python print
        r'=\s*function\s*\(',  # JS function
        r'=>\s*{',  # Arrow function
        r'<[\w\s]*>',  # HTML/XML tags
    ]

    # Keywords for different query types
    QUERY_KEYWORDS = {
        QueryType.CODE: [
            'debug', 'fix', 'error', 'bug', 'code', 'function', 'implement',
            'refactor', 'optimize', 'algorithm', 'programming', 'developer',
            'syntax', 'compile', 'runtime', 'exception', 'stack trace'
        ],
        QueryType.SPEED_CRITICAL: [
            'quick', 'fast', 'short', 'brief', 'simple', 'quickly', 'what is',
            'define', 'explain', 'summarize'
        ],
        QueryType.GENERATION_HEAVY: [
            'write', 'generate', 'create', 'story', 'essay', 'article', 'poem',
            'creative', 'compose', 'draft', 'long', 'detailed'
        ],
        QueryType.PROMPT_HEAVY: [
            'analyze', 'review', 'summarize this', 'process', 'document',
            'file', 'text', 'conversation', 'history', 'log'
        ],
    }

    # Semantic query examples for embedding similarity
    SEMANTIC_EXAMPLES = {
        QueryType.CODE: [
            "How do I fix this bug in my code?",
            "Write a function to sort an array",
            "Debug this Python script",
            "What's wrong with this code?",
            "Implement a binary search algorithm"
        ],
        QueryType.SPEED_CRITICAL: [
            "What's the capital of France?",
            "Quick answer needed",
            "Simple explanation",
            "Brief summary",
            "Basic question"
        ],
        QueryType.GENERATION_HEAVY: [
            "Write a creative story about",
            "Generate a long essay on",
            "Create a detailed report",
            "Compose a poem about",
            "Write an article discussing"
        ],
        QueryType.PROMPT_HEAVY: [
            "Analyze this document",
            "Process this conversation",
            "Review this codebase",
            "Summarize these logs",
            "Parse this file"
        ],
    }

    def __init__(
        self,
        ollama_client: OllamaClient,
        embedding_model: str = "nomic-embed-text",
        enable_embeddings: bool = True,
        semantic_threshold: float = 0.85
    ):
        """
        Initialize query classifier.

        Args:
            ollama_client: Ollama client for embeddings
            embedding_model: Model to use for embeddings
            enable_embeddings: Whether to use embedding-based classification
            semantic_threshold: Threshold for semantic similarity
        """
        self.ollama = ollama_client
        self.embedding_model = embedding_model
        self.enable_embeddings = enable_embeddings
        self.semantic_threshold = semantic_threshold

        # Cached embeddings for semantic examples
        self._semantic_embeddings: Optional[Dict[QueryType, List[np.ndarray]]] = None

    async def _initialize_semantic_embeddings(self):
        """Initialize embeddings for semantic examples."""
        if self._semantic_embeddings is not None:
            return

        self._semantic_embeddings = {qt: [] for qt in QueryType}

        if not self.enable_embeddings:
            return

        for query_type, examples in self.SEMANTIC_EXAMPLES.items():
            for example in examples:
                try:
                    embedding = await self.ollama.embeddings(
                        model=self.embedding_model,
                        text=example
                    )
                    self._semantic_embeddings[query_type].append(np.array(embedding))
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for example: {e}")

        logger.info("Semantic embeddings initialized")

    def _has_code_patterns(self, query: str) -> bool:
        """
        Check if query contains code patterns.

        Args:
            query: Query string

        Returns:
            True if code patterns detected
        """
        for pattern in self.CODE_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False

    def _keyword_score(self, query: str) -> Dict[QueryType, float]:
        """
        Calculate keyword-based scores for each query type.

        Args:
            query: Query string

        Returns:
            Dict of query type to score
        """
        query_lower = query.lower()
        scores = {}

        for query_type, keywords in self.QUERY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            scores[query_type] = score

        return scores

    async def _semantic_score(self, query: str) -> Dict[QueryType, float]:
        """
        Calculate semantic similarity scores.

        Args:
            query: Query string

        Returns:
            Dict of query type to similarity score
        """
        if not self.enable_embeddings or self._semantic_embeddings is None:
            return {}

        try:
            query_embedding = np.array(
                await self.ollama.embeddings(
                    model=self.embedding_model,
                    text=query
                )
            )

            scores = {}
            for query_type, embeddings in self._semantic_embeddings.items():
                if not embeddings:
                    continue

                # Calculate cosine similarity with each example
                similarities = []
                for example_emb in embeddings:
                    # Cosine similarity
                    dot_product = np.dot(query_embedding, example_emb)
                    norm_product = np.linalg.norm(query_embedding) * np.linalg.norm(example_emb)
                    similarity = dot_product / (norm_product + 1e-8)
                    similarities.append(similarity)

                # Take maximum similarity
                scores[query_type] = max(similarities) if similarities else 0.0

            return scores

        except Exception as e:
            logger.warning(f"Failed to calculate semantic scores: {e}")
            return {}

    def _analyze_query_characteristics(self, query: str) -> Dict[str, float]:
        """
        Analyze query characteristics for routing.

        Args:
            query: Query string

        Returns:
            Dict of characteristic scores
        """
        return {
            'length': len(query),
            'has_code': float(self._has_code_patterns(query)),
            'line_count': len(query.split('\n')),
            'avg_line_length': len(query) / max(len(query.split('\n')), 1)
        }

    async def classify(self, query: str) -> QueryType:
        """
        Classify query into type.

        Args:
            query: Query string

        Returns:
            QueryType classification
        """
        # Initialize semantic embeddings if needed
        await self._initialize_semantic_embeddings()

        # Fast path: code detection
        if self._has_code_patterns(query):
            logger.debug("Classified as CODE (pattern match)")
            return QueryType.CODE

        # Keyword-based classification
        keyword_scores = self._keyword_score(query)

        # Semantic-based classification
        semantic_scores = await self._semantic_score(query)

        # Analyze query characteristics
        characteristics = self._analyze_query_characteristics(query)

        # Combine scores
        combined_scores = {qt: 0.0 for qt in QueryType}

        # Add keyword scores (weight: 1.0)
        for qt, score in keyword_scores.items():
            combined_scores[qt] += score * 1.0

        # Add semantic scores (weight: 2.0 if above threshold)
        for qt, score in semantic_scores.items():
            if score >= self.semantic_threshold:
                combined_scores[qt] += score * 2.0

        # Boost based on characteristics
        if characteristics['has_code'] > 0:
            combined_scores[QueryType.CODE] += 5.0

        if characteristics['length'] > 1000:
            combined_scores[QueryType.PROMPT_HEAVY] += 2.0

        if characteristics['line_count'] > 50:
            combined_scores[QueryType.PROMPT_HEAVY] += 2.0

        # Find best match
        best_type = QueryType.BALANCED  # Default
        best_score = -1.0

        for qt, score in combined_scores.items():
            if score > best_score:
                best_score = score
                best_type = qt

        logger.debug(f"Classified as {best_type} (scores: {combined_scores})")
        return best_type

    async def classify_with_scores(self, query: str) -> Tuple[QueryType, Dict[str, float]]:
        """
        Classify query and return detailed scores.

        Args:
            query: Query string

        Returns:
            Tuple of (QueryType, scores dict)
        """
        # Initialize semantic embeddings if needed
        await self._initialize_semantic_embeddings()

        query_type = await self.classify(query)

        # Get all scores for transparency
        keyword_scores = self._keyword_score(query)
        semantic_scores = await self._semantic_score(query)
        characteristics = self._analyze_query_characteristics(query)

        return query_type, {
            'keyword_scores': {qt.name: score for qt, score in keyword_scores.items()},
            'semantic_scores': {qt.name: score for qt, score in semantic_scores.items()},
            'characteristics': characteristics
        }
