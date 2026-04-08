"""Test suites for benchmark system.

Each module contains test cases for a specific query category.
"""

from .agentic import AGENTIC_TESTS
from .document import DOCUMENT_TESTS
from .code import CODE_TESTS
from .creative import CREATIVE_TESTS
from .factual import FACTUAL_TESTS

__all__ = [
    "AGENTIC_TESTS",
    "DOCUMENT_TESTS",
    "CODE_TESTS",
    "CREATIVE_TESTS",
    "FACTUAL_TESTS",
]
