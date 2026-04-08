#!/usr/bin/env python3
"""Router's Matrix - Main CLI orchestrator for benchmark system.

A comprehensive benchmark test system for the MoE Router API that creates
a "router's matrix" - a detailed performance comparison across all models
and query categories.
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path
from typing import Optional, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark.test_generator import TestGenerator
from benchmark.metrics_collector import MetricsCollector
from benchmark.quality_analyzer import QualityAnalyzer
from benchmark.matrix_generator import MatrixGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RouterMatrixBenchmark:
    """Main benchmark orchestrator."""

    def __init__(
        self,
        api_base_url: str = "http://localhost:8000",
        output_dir: Optional[str] = None,
        concurrent: int = 5,
        timeout: int = 120,
        iterations: int = 1
    ):
        """
        Initialize benchmark orchestrator.

        Args:
            api_base_url: MoE Router API base URL
            output_dir: Output directory for results
            concurrent: Number of concurrent tests
            timeout: Timeout per test (seconds)
            iterations: Number of iterations per test
        """
        self.api_base_url = api_base_url
        self.output_dir = output_dir
        self.concurrent = concurrent
        self.timeout = timeout
        self.iterations = iterations

        self.test_generator = TestGenerator()
        self.matrix_generator = MatrixGenerator(output_dir)

    async def run_benchmark(
        self,
        tests: Optional[List[dict]] = None,
        models: Optional[List[str]] = None,
        category: Optional[str] = None
    ) -> str:
        """
        Run the full benchmark suite.

        Args:
            tests: Specific tests to run (None for all)
            models: Specific models to test (None for all)
            category: Specific category to test (None for all)

        Returns:
            Path to output directory
        """
        # Select tests
        if tests is None:
            if category:
                tests = self.test_generator.get_tests_by_category(category)
                logger.info(f"Running {len(tests)} tests from category: {category}")
            else:
                tests = self.test_generator.get_all_tests()
                logger.info(f"Running all {len(tests)} tests")
        else:
            logger.info(f"Running {len(tests)} specified tests")

        if not tests:
            logger.error("No tests to run!")
            return ""

        # Get available models
        available_models = await self._get_available_models()
        if models:
            models = [m for m in models if m in available_models]
        else:
            models = available_models

        if not models:
            logger.error("No models available!")
            return ""

        logger.info(f"Testing against models: {', '.join(models)}")

        # Run benchmarks
        all_metrics = []
        all_quality_scores = []

        async with MetricsCollector(
            api_base_url=self.api_base_url,
            timeout_seconds=self.timeout
        ) as collector:
            quality_analyzer = QualityAnalyzer()

            # Test each model
            for model in models:
                logger.info(f"\n{'='*60}")
                logger.info(f"Benchmarking model: {model}")
                logger.info(f"{'='*60}")

                # Collect metrics
                metrics = await collector.collect_batch(
                    tests,
                    model=model,
                    concurrent=self.concurrent
                )

                # Analyze quality
                quality_scores = await quality_analyzer.analyze_batch(
                    metrics,
                    tests
                )

                all_metrics.extend(metrics)
                all_quality_scores.extend(quality_scores)

                # Report progress
                successful = sum(1 for m in metrics if not m.error)
                failed = len(metrics) - successful
                avg_latency = sum(
                    m.total_latency_ms for m in metrics
                    if not m.error
                ) / max(1, successful)

                logger.info(f"Completed: {successful}/{len(tests)} successful")
                logger.info(f"Failed: {failed}")
                logger.info(f"Average latency: {avg_latency/1000:.2f}s")

        # Generate matrices
        logger.info("\n" + "="*60)
        logger.info("Generating performance matrices...")
        logger.info("="*60)

        # Convert metrics to dicts for matrix generator
        metrics_dicts = [m.to_dict() for m in all_metrics]

        speed_matrix, accuracy_matrix, recommendations = \
            self.matrix_generator.calculate_matrices(
                all_metrics,
                all_quality_scores
            )

        # Generate outputs
        output_path = self.matrix_generator.generate_all(
            speed_matrix,
            accuracy_matrix,
            recommendations,
            metrics_dicts
        )

        # Print summary
        self._print_summary(
            speed_matrix,
            accuracy_matrix,
            recommendations,
            len(tests),
            len(models)
        )

        return output_path

    async def _get_available_models(self) -> List[str]:
        """Get list of available models from API."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.api_base_url}/api/v1/models")
                if response.status_code == 200:
                    data = response.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.warning(f"Could not fetch models from API: {e}")

        # Fallback to default models
        return [
            "qwen3:4b",
            "qwen2.5-coder",
            "llama3.2",
            "llama3.1",
            "ministral-3",
            "phi3:mini",
            "nemotron-3-nano:4b"
        ]

    def _print_summary(
        self,
        speed_matrix: dict,
        accuracy_matrix: dict,
        recommendations: dict,
        num_tests: int,
        num_models: int
    ):
        """Print benchmark summary."""
        logger.info("\n" + "="*60)
        logger.info("BENCHMARK SUMMARY")
        logger.info("="*60)
        logger.info(f"Tests run: {num_tests}")
        logger.info(f"Models tested: {num_models}")
        logger.info(f"\nOutput directory: {self.matrix_generator.run_dir}")

        logger.info("\nROUTING RECOMMENDATIONS:")
        logger.info("-" * 40)
        for category, model in recommendations.items():
            speed = speed_matrix.get(model, {}).get(category, 0)
            accuracy = accuracy_matrix.get(model, {}).get(category, 0)
            logger.info(f"  {category:15} -> {model:20} "
                       f"({speed:.2f}s, {accuracy:.1%} accuracy)")

        logger.info("\n" + "="*60)


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Router's Matrix - MoE Router Benchmark System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full benchmark (130 tests, all models)
  python scripts/router_matrix.py --full

  # Quick benchmark (20 tests)
  python scripts/router_matrix.py --quick

  # Specific category
  python scripts/router_matrix.py --category code

  # Specific models
  python scripts/router_matrix.py --models qwen3:4b,llama3.1

  # Custom API URL
  python scripts/router_matrix.py --api-url http://localhost:9000

  # HTML output only
  python scripts/router_matrix.py --format html
        """
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full benchmark (130 tests)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick benchmark (20 tests)"
    )
    parser.add_argument(
        "--category",
        choices=["agentic", "document", "code", "creative", "factual"],
        help="Run tests for specific category only"
    )
    parser.add_argument(
        "--models",
        help="Comma-separated list of models to test"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="MoE Router API base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for results (default: benchmark_output/)"
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=5,
        help="Number of concurrent tests (default: 5)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout per test in seconds (default: 120)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "html", "csv", "all"],
        default="all",
        help="Output format (default: all)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse models
    models = None
    if args.models:
        models = [m.strip() for m in args.models.split(",")]

    # Create orchestrator
    orchestrator = RouterMatrixBenchmark(
        api_base_url=args.api_url,
        output_dir=args.output_dir,
        concurrent=args.concurrent,
        timeout=args.timeout
    )

    # Select tests
    tests = None
    test_generator = TestGenerator()

    if args.quick:
        tests = test_generator.get_quick_tests(20)
    elif args.category:
        tests = test_generator.get_tests_by_category(args.category)
    elif not args.full:
        # Default to quick run
        logger.info("No test selection specified. Running quick benchmark (20 tests).")
        logger.info("Use --full for all 130 tests or --category for specific categories.")
        tests = test_generator.get_quick_tests(20)

    # Run benchmark
    try:
        output_path = await orchestrator.run_benchmark(
            tests=tests,
            models=models
        )

        if output_path:
            logger.info(f"\n✓ Benchmark complete!")
            logger.info(f"✓ Results saved to: {output_path}")
            logger.info(f"\nOpen in your browser:")
            logger.info(f"  file://{output_path}/speed_matrix.html")
            logger.info(f"  file://{output_path}/accuracy_matrix.html")
        else:
            logger.error("Benchmark failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nBenchmark interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Benchmark error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
