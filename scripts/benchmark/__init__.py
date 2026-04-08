"""MoE Router Benchmark System.

A comprehensive benchmark test system that creates a "router's matrix" -
a detailed performance comparison across all models and query categories.

Includes Pi Agent Boss - autonomous manager of the entire routing stack.
"""

__version__ = "1.0.0"

from .pi_agent_boss import PiAgentBoss, AgentMode, ModelStatus, RoutingMetrics

__all__ = [
    "TestGenerator",
    "MetricsCollector",
    "QualityAnalyzer",
    "MatrixGenerator",
    "PiAgentBoss",
    "AgentMode",
    "ModelStatus",
    "RoutingMetrics",
]
