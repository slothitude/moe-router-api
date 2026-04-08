"""Quality analyzer for Router's Matrix benchmark system.

Measures response accuracy through multiple methods:
- Semantic similarity using embeddings
- Keyword matching
- Code validity
- Factual correctness
- Completeness scoring
"""

import re
import ast
import logging
from typing import Dict, Any, List, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from metrics_collector import BenchmarkMetrics

logger = logging.getLogger(__name__)


class QualityAnalyzer:
    """Analyze response quality and accuracy."""

    def __init__(
        self,
        embedding_model: str = "nomic-embed-text",
        ollama_base_url: str = "http://localhost:11434"
    ):
        """
        Initialize quality analyzer.

        Args:
            embedding_model: Model name for embeddings
            ollama_base_url: Ollama API base URL
        """
        self.embedding_model_name = embedding_model
        self.ollama_base_url = ollama_base_url
        self.embedding_model: Optional[SentenceTransformer] = None
        self._load_embedding_model()

    def _load_embedding_model(self):
        """Load sentence transformer model."""
        try:
            # Try to load from sentence-transformers
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Loaded embedding model: {self.embedding_model_name}")
        except Exception as e:
            logger.warning(f"Could not load sentence transformer: {e}")
            self.embedding_model = None

    async def analyze_response(
        self,
        metrics: BenchmarkMetrics,
        test: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Analyze response quality across multiple dimensions.

        Args:
            metrics: Benchmark metrics with response
            test: Original test case with expected elements

        Returns:
            Dict with quality scores
        """
        scores = {
            "semantic_similarity": 0.0,
            "keyword_match": 0.0,
            "code_validity": 0.0,
            "factual_correctness": 0.0,
            "completeness": 0.0,
        }

        if metrics.error or not metrics.response_text:
            return scores

        # Semantic similarity
        scores["semantic_similarity"] = await self._semantic_similarity(
            metrics.response_text,
            test
        )

        # Keyword matching
        scores["keyword_match"] = self._keyword_match(
            metrics.response_text,
            test.get("expected_elements", [])
        )

        # Code validity (for code tests)
        if metrics.category == "code":
            scores["code_validity"] = self._check_code_validity(
                metrics.response_text,
                test.get("language", "python")
            )

        # Factual correctness (for factual tests)
        if metrics.category == "factual":
            scores["factual_correctness"] = self._check_factual_correctness(
                metrics.response_text,
                test
            )

        # Completeness
        scores["completeness"] = self._check_completeness(
            metrics.response_text,
            test
        )

        return scores

    async def _semantic_similarity(
        self,
        response: str,
        test: Dict[str, Any]
    ) -> float:
        """
        Calculate semantic similarity between response and expected content.

        Args:
            response: Model response text
            test: Test case with query and expected elements

        Returns:
            Similarity score 0.0 to 1.0
        """
        if not self.embedding_model:
            # Fallback: use keyword overlap
            return self._keyword_overlap(response, test["query"])

        try:
            # Create embeddings
            response_embedding = self.embedding_model.encode([response])
            query_embedding = self.embedding_model.encode([test["query"]])

            # Calculate cosine similarity
            similarity = cosine_similarity(response_embedding, query_embedding)[0][0]

            # Normalize to 0-1 range (cosine similarity can be -1 to 1)
            return max(0.0, min(1.0, (similarity + 1) / 2))

        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0

    def _keyword_match(
        self,
        response: str,
        expected_elements: List[str]
    ) -> float:
        """
        Check how many expected keywords appear in response.

        Args:
            response: Model response text
            expected_elements: List of expected keywords

        Returns:
            Match score 0.0 to 1.0
        """
        if not expected_elements:
            return 1.0

        response_lower = response.lower()
        matches = 0

        for element in expected_elements:
            # Check for whole word or phrase match
            pattern = r'\b' + re.escape(element.lower()) + r'\b'
            if re.search(pattern, response_lower):
                matches += 1

        return matches / len(expected_elements)

    def _keyword_overlap(self, response: str, query: str) -> float:
        """
        Calculate keyword overlap between response and query.

        Args:
            response: Model response
            query: Original query

        Returns:
            Overlap score 0.0 to 1.0
        """
        response_words = set(response.lower().split())
        query_words = set(query.lower().split())

        if not query_words:
            return 0.0

        overlap = response_words & query_words
        return len(overlap) / len(query_words)

    def _check_code_validity(
        self,
        response: str,
        language: str
    ) -> float:
        """
        Check if code in response is syntactically valid.

        Args:
            response: Model response (may contain code)
            language: Programming language

        Returns:
            Validity score 0.0 to 1.0
        """
        # Extract code blocks (markdown format)
        code_pattern = r'```(?:' + language + r')?\n(.*?)```'
        code_blocks = re.findall(code_pattern, response, re.DOTALL)

        if not code_blocks:
            # Try to find code without language spec
            code_pattern = r'```\n(.*?)```'
            code_blocks = re.findall(code_pattern, response, re.DOTALL)

        if not code_blocks:
            # No code blocks found
            return 0.5

        valid_count = 0
        for code in code_blocks:
            if self._validate_code_syntax(code, language):
                valid_count += 1

        return valid_count / len(code_blocks) if code_blocks else 0.0

    def _validate_code_syntax(self, code: str, language: str) -> bool:
        """
        Validate syntax of code snippet.

        Args:
            code: Code string
            language: Programming language

        Returns:
            True if syntax is valid
        """
        try:
            if language == "python":
                ast.parse(code)
                return True
            elif language in ["javascript", "js", "tsx"]:
                # Basic syntax check for JS
                # (more thorough validation would require a JS parser)
                return bool(code.strip() and not code.count('{') != code.count('}'))
            elif language == "sql":
                # Basic SQL syntax check
                sql_keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE']
                return any(keyword in code.upper() for keyword in sql_keywords)
            elif language == "html":
                return bool(re.search(r'<[^>]+>', code))
            elif language == "css":
                return bool(re.search(r'\{[^}]*\}', code))
            elif language == "bash":
                # Check for common bash commands
                bash_commands = ['if', 'for', 'while', 'do', 'done', 'fi', 'then']
                return any(cmd in code for cmd in bash_commands) or '=' in code
            else:
                # Unknown language, assume valid
                return True

        except Exception:
            return False

    def _check_factual_correctness(
        self,
        response: str,
        test: Dict[str, Any]
    ) -> float:
        """
        Check factual correctness for factual queries.

        Args:
            response: Model response
            test: Test case

        Returns:
            Correctness score 0.0 to 1.0
        """
        # For factual tests, check if expected elements are present
        expected_elements = test.get("expected_elements", [])

        if not expected_elements:
            return 1.0

        # Simple keyword matching for factual correctness
        # A more sophisticated approach would use a knowledge base
        return self._keyword_match(response, expected_elements)

    def _check_completeness(
        self,
        response: str,
        test: Dict[str, Any]
    ) -> float:
        """
        Check if response addresses all aspects of the query.

        Args:
            response: Model response
            test: Test case

        Returns:
            Completeness score 0.0 to 1.0
        """
        # Check based on expected elements
        expected_elements = test.get("expected_elements", [])

        if not expected_elements:
            # Check response length relative to query complexity
            complexity = test.get("complexity", "medium")
            min_length = {
                "low": 50,
                "medium": 150,
                "high": 300
            }.get(complexity, 100)

            return min(1.0, len(response) / min_length)

        # Check how many expected elements are addressed
        response_lower = response.lower()
        addressed = 0

        for element in expected_elements:
            if element.lower() in response_lower:
                addressed += 1

        return addressed / len(expected_elements)

    def calculate_overall_accuracy(
        self,
        scores: Dict[str, float],
        category: str
    ) -> float:
        """
        Calculate overall accuracy score from component scores.

        Args:
            scores: Individual quality scores
            category: Test category

        Returns:
            Overall accuracy 0.0 to 1.0
        """
        # Weight components based on category
        weights = {
            "agentic": {
                "semantic_similarity": 0.3,
                "keyword_match": 0.2,
                "completeness": 0.5,
            },
            "document": {
                "semantic_similarity": 0.3,
                "keyword_match": 0.3,
                "completeness": 0.4,
            },
            "code": {
                "code_validity": 0.5,
                "keyword_match": 0.3,
                "completeness": 0.2,
            },
            "creative": {
                "semantic_similarity": 0.4,
                "completeness": 0.6,
            },
            "factual": {
                "keyword_match": 0.6,
                "factual_correctness": 0.4,
            },
        }

        category_weights = weights.get(category, {
            "semantic_similarity": 0.3,
            "keyword_match": 0.3,
            "completeness": 0.4,
        })

        overall = 0.0
        total_weight = 0.0

        for component, weight in category_weights.items():
            if component in scores:
                overall += scores[component] * weight
                total_weight += weight

        return overall / total_weight if total_weight > 0 else 0.0

    async def analyze_batch(
        self,
        metrics_list: List[BenchmarkMetrics],
        tests: List[Dict[str, Any]]
    ) -> List[Dict[str, float]]:
        """
        Analyze quality for a batch of responses.

        Args:
            metrics_list: List of benchmark metrics
            tests: Corresponding test cases

        Returns:
            List of quality score dicts
        """
        results = []

        for metrics, test in zip(metrics_list, tests):
            scores = await self.analyze_response(metrics, test)
            overall = self.calculate_overall_accuracy(
                scores,
                metrics.category
            )
            scores["overall_accuracy"] = overall
            results.append(scores)

        return results


__all__ = ["QualityAnalyzer"]
