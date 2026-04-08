"""Test generator for Router's Matrix benchmark system."""

from typing import List, Dict, Any
from test_suites import (
    AGENTIC_TESTS,
    DOCUMENT_TESTS,
    CODE_TESTS,
    CREATIVE_TESTS,
    FACTUAL_TESTS,
)


class TestGenerator:
    """Generate test cases for benchmarking."""

    ALL_TESTS = (
        AGENTIC_TESTS +
        DOCUMENT_TESTS +
        CODE_TESTS +
        CREATIVE_TESTS +
        FACTUAL_TESTS
    )

    CATEGORIES = {
        "agentic": AGENTIC_TESTS,
        "document": DOCUMENT_TESTS,
        "code": CODE_TESTS,
        "creative": CREATIVE_TESTS,
        "factual": FACTUAL_TESTS,
    }

    SUBCATEGORIES = {
        "agentic": ["planning", "reasoning", "tool_use"],
        "document": ["writing", "editing", "summarization"],
        "code": ["generation", "debugging", "optimization"],
        "creative": ["story", "poetry", "dialogue", "content"],
        "factual": ["definition", "fact", "comparison", "answer"],
    }

    @classmethod
    def get_all_tests(cls) -> List[Dict[str, Any]]:
        """Get all 130 test cases."""
        return cls.ALL_TESTS

    @classmethod
    def get_tests_by_category(cls, category: str) -> List[Dict[str, Any]]:
        """
        Get tests for a specific category.

        Args:
            category: One of: agentic, document, code, creative, factual

        Returns:
            List of test cases for the category
        """
        return cls.CATEGORIES.get(category, [])

    @classmethod
    def get_tests_by_subcategory(
        cls,
        category: str,
        subcategory: str
    ) -> List[Dict[str, Any]]:
        """
        Get tests for a specific subcategory.

        Args:
            category: Main category
            subcategory: Subcategory within the main category

        Returns:
            List of filtered test cases
        """
        tests = cls.get_tests_by_category(category)
        return [
            t for t in tests
            if t.get("subcategory") == subcategory
        ]

    @classmethod
    def get_quick_tests(cls, count: int = 20) -> List[Dict[str, Any]]:
        """
        Get a quick subset of tests for rapid benchmarking.

        Distributes evenly across categories.

        Args:
            count: Number of tests to return (default 20)

        Returns:
            List of test cases
        """
        per_category = count // len(cls.CATEGORIES)
        selected = []

        for category_tests in cls.CATEGORIES.values():
            # Take tests evenly from subcategories
            subcategories = {}
            for test in category_tests:
                subcat = test.get("subcategory", "general")
                if subcat not in subcategories:
                    subcategories[subcat] = []
                subcategories[subcat].append(test)

            # Select from each subcategory
            for subcat_tests in subcategories.values():
                take = min(len(subcat_tests), max(1, per_category // len(subcategories)))
                selected.extend(subcat_tests[:take])

            if len(selected) >= per_category * (len(cls.CATEGORIES) - 1):
                # We have enough from previous categories
                pass

        return selected[:count]

    @classmethod
    def get_test_count(cls) -> Dict[str, int]:
        """Get count of tests by category."""
        return {
            category: len(tests)
            for category, tests in cls.CATEGORIES.items()
        }

    @classmethod
    def get_test_by_id(cls, test_id: str) -> Dict[str, Any]:
        """
        Get a specific test by ID.

        Args:
            test_id: Test identifier (e.g., "agentic_001")

        Returns:
            Test case dict or None if not found
        """
        for test in cls.ALL_TESTS:
            if test.get("id") == test_id:
                return test
        return None

    @classmethod
    def validate_test(cls, test: Dict[str, Any]) -> bool:
        """
        Validate that a test case has all required fields.

        Args:
            test: Test case dict

        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            "id",
            "category",
            "subcategory",
            "query",
            "expected_elements",
            "complexity"
        ]

        return all(field in test for field in required_fields)

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """Get summary statistics about all test cases."""
        total = len(cls.ALL_TESTS)

        complexity_distribution = {}
        category_distribution = {}

        for test in cls.ALL_TESTS:
            # Count by complexity
            complexity = test.get("complexity", "unknown")
            complexity_distribution[complexity] = (
                complexity_distribution.get(complexity, 0) + 1
            )

            # Count by category
            category = test.get("category", "unknown")
            if category not in category_distribution:
                category_distribution[category] = {
                    "total": 0,
                    "subcategories": set()
                }
            category_distribution[category]["total"] += 1
            category_distribution[category]["subcategories"].add(
                test.get("subcategory", "general")
            )

        # Convert subcategories sets to counts
        for cat_data in category_distribution.values():
            cat_data["subcategories"] = len(cat_data["subcategories"])

        return {
            "total_tests": total,
            "categories": category_distribution,
            "complexity": complexity_distribution,
        }


__all__ = ["TestGenerator"]
