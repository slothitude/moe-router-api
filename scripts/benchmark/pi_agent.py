"""Pi Agent - The boss of the Router's Matrix benchmark system.

The Pi Agent is an autonomous agent that:
- Automatically discovers new Ollama models
- Manages mandatory testing for all models
- Coordinates the entire benchmark workflow
- Provides continuous monitoring and reporting
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import httpx
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ModelStatus:
    """Status of a model in the benchmark system."""
    name: str
    discovered_at: str
    last_benchmarked: Optional[str]
    benchmark_count: int
    is_benchmarked: bool
    mandatory_tests_passed: Optional[bool]
    overall_score: Optional[float]
    categories_tested: List[str]


@dataclass
class BenchmarkJob:
    """A benchmark job managed by Pi Agent."""
    job_id: str
    model: str
    status: str  # pending, running, completed, failed
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    test_count: int
    results: Optional[Dict[str, Any]]


class PiAgent:
    """
    The Pi Agent - Boss of the Router's Matrix benchmark system.

    Features:
    - Automatic model discovery from Ollama
    - Mandatory testing enforcement
    - Continuous monitoring mode
    - Benchmark job scheduling
    - Performance tracking and reporting
    """

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        router_api_url: str = "http://localhost:8000",
        benchmark_dir: str = "benchmark_output",
        state_file: str = "pi_agent_state.json",
        mandatory_categories: Optional[List[str]] = None,
        discovery_interval: int = 300,  # 5 minutes
        auto_benchmark_new: bool = True,
    ):
        """
        Initialize Pi Agent.

        Args:
            ollama_base_url: Ollama API base URL
            router_api_url: MoE Router API base URL
            benchmark_dir: Directory for benchmark outputs
            state_file: File to persist agent state
            mandatory_categories: Categories that MUST be tested
            discovery_interval: Seconds between model discovery checks
            auto_benchmark_new: Automatically benchmark new models
        """
        self.ollama_base_url = ollama_base_url
        self.router_api_url = router_api_url
        self.benchmark_dir = Path(benchmark_dir)
        self.benchmark_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = Path(state_file)

        # Mandatory testing configuration
        self.mandatory_categories = mandatory_categories or [
            "agentic",    # Multi-step reasoning is critical
            "code",       # Code generation is critical
            "factual",    # Accuracy on facts is critical
        ]

        self.discovery_interval = discovery_interval
        self.auto_benchmark_new = auto_benchmark_new

        # Agent state
        self.known_models: Dict[str, ModelStatus] = {}
        self.benchmark_jobs: List[BenchmarkJob] = []
        self.running = False

        # Load previous state
        self._load_state()

    async def start(self):
        """Start the Pi Agent in monitoring mode."""
        logger.info("="*60)
        logger.info("PI AGENT - Boss of Router's Matrix")
        logger.info("="*60)
        logger.info(f"Ollama URL: {self.ollama_base_url}")
        logger.info(f"Router API: {self.router_api_url}")
        logger.info(f"Mandatory categories: {', '.join(self.mandatory_categories)}")
        logger.info(f"Auto-benchmark new models: {self.auto_benchmark_new}")
        logger.info("="*60)

        self.running = True

        # Initial discovery
        await self._discover_models()

        # Main monitoring loop
        while self.running:
            try:
                # Check for new models
                await self._discover_models()

                # Process pending jobs
                await self._process_jobs()

                # Save state
                self._save_state()

                # Wait before next cycle
                logger.debug(f"Sleeping {self.discovery_interval}s...")
                await asyncio.sleep(self.discovery_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(60)

    def stop(self):
        """Stop the Pi Agent."""
        logger.info("Stopping Pi Agent...")
        self.running = False
        self._save_state()

    async def _discover_models(self):
        """Discover models from Ollama and update known models."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.ollama_base_url}/api/tags")
                response.raise_for_status()
                data = response.json()

            ollama_models = data.get("models", [])
            current_models = {m["name"] for m in ollama_models}

            # Check for new models
            new_models = current_models - set(self.known_models.keys())

            if new_models:
                logger.info(f"🎉 Discovered {len(new_models)} new model(s): {', '.join(new_models)}")

                for model_name in new_models:
                    await self._register_new_model(model_name)

                    if self.auto_benchmark_new:
                        await self._schedule_mandatory_benchmark(model_name)

            # Check for removed models
            removed_models = set(self.known_models.keys()) - current_models
            if removed_models:
                logger.warning(f"⚠️  Models no longer available: {', '.join(removed_models)}")
                for model_name in removed_models:
                    del self.known_models[model_name]

        except Exception as e:
            logger.error(f"Error discovering models: {e}")

    async def _register_new_model(self, model_name: str):
        """Register a new model in the system."""
        now = datetime.now().isoformat()
        self.known_models[model_name] = ModelStatus(
            name=model_name,
            discovered_at=now,
            last_benchmarked=None,
            benchmark_count=0,
            is_benchmarked=False,
            mandatory_tests_passed=None,
            overall_score=None,
            categories_tested=[],
        )
        logger.info(f"✓ Registered new model: {model_name}")

    async def _schedule_mandatory_benchmark(self, model_name: str):
        """Schedule mandatory benchmark tests for a model."""
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{model_name.replace(':', '_')}"

        job = BenchmarkJob(
            job_id=job_id,
            model=model_name,
            status="pending",
            created_at=datetime.now().isoformat(),
            started_at=None,
            completed_at=None,
            test_count=0,
            results=None,
        )

        self.benchmark_jobs.append(job)
        logger.info(f"📋 Scheduled mandatory benchmark for: {model_name} (job: {job_id})")

    async def _process_jobs(self):
        """Process pending benchmark jobs."""
        pending_jobs = [j for j in self.benchmark_jobs if j.status == "pending"]

        # Process jobs one at a time (can be parallelized)
        for job in pending_jobs:
            logger.info(f"🚀 Processing job: {job.job_id} (model: {job.model})")
            await self._run_benchmark_job(job)

    async def _run_benchmark_job(self, job: BenchmarkJob):
        """Run a benchmark job."""
        job.status = "running"
        job.started_at = datetime.now().isoformat()
        self._save_state()

        try:
            # Import here to avoid circular dependency
            from test_generator import TestGenerator
            from metrics_collector import MetricsCollector
            from quality_analyzer import QualityAnalyzer
            from matrix_generator import MatrixGenerator

            # Run mandatory category tests
            test_gen = TestGenerator()
            all_metrics = []
            all_quality = []
            categories_tested = []

            for category in self.mandatory_categories:
                logger.info(f"  Testing category: {category}")
                tests = test_gen.get_tests_by_category(category)

                async with MetricsCollector(
                    api_base_url=self.router_api_url,
                    timeout_seconds=120
                ) as collector:
                    metrics = await collector.collect_batch(
                        tests,
                        model=job.model,
                        concurrent=3
                    )

                    # Analyze quality
                    quality_analyzer = QualityAnalyzer()
                    quality_scores = await quality_analyzer.analyze_batch(metrics, tests)

                    all_metrics.extend(metrics)
                    all_quality.extend(quality_scores)
                    categories_tested.append(category)

            # Generate matrices
            matrix_gen = MatrixGenerator(output_dir=str(self.benchmark_dir))
            speed_matrix, accuracy_matrix, recommendations = \
                matrix_gen.calculate_matrices(all_metrics, all_quality)

            # Update job results
            job.status = "completed"
            job.completed_at = datetime.now().isoformat()
            job.test_count = len(all_metrics)
            job.results = {
                "speed_matrix": speed_matrix,
                "accuracy_matrix": accuracy_matrix,
                "categories_tested": categories_tested,
                "model": job.model,
            }

            # Update model status
            model_status = self.known_models.get(job.model)
            if model_status:
                model_status.last_benchmarked = job.completed_at
                model_status.benchmark_count += 1
                model_status.is_benchmarked = True
                model_status.categories_tested = categories_tested

                # Calculate overall score
                if job.model in accuracy_matrix:
                    scores = [
                        acc for acc in accuracy_matrix[job.model].values()
                        if acc > 0
                    ]
                    if scores:
                        model_status.overall_score = sum(scores) / len(scores)

                # Check if mandatory tests passed
                model_status.mandatory_tests_passed = (
                    set(categories_tested) >= set(self.mandatory_categories)
                    and model_status.overall_score and model_status.overall_score > 0.5
                )

            # Save results to file
            results_file = self.benchmark_dir / f"job_{job.job_id}_results.json"
            with open(results_file, 'w') as f:
                json.dump({
                    "job": asdict(job),
                    "speed_matrix": speed_matrix,
                    "accuracy_matrix": accuracy_matrix,
                }, f, indent=2)

            logger.info(f"✓ Job completed: {job.job_id}")
            logger.info(f"  Categories tested: {', '.join(categories_tested)}")
            logger.info(f"  Overall score: {model_status.overall_score:.2%}" if model_status.overall_score else "  Overall score: N/A")
            logger.info(f"  Results saved to: {results_file}")

        except Exception as e:
            logger.error(f"✗ Job failed: {job.job_id} - {e}", exc_info=True)
            job.status = "failed"
            job.completed_at = datetime.now().isoformat()

        self._save_state()

    def _load_state(self):
        """Load agent state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)

                # Restore known models
                for name, status_data in data.get("known_models", {}).items():
                    self.known_models[name] = ModelStatus(**status_data)

                # Restore jobs
                for job_data in data.get("benchmark_jobs", []):
                    self.benchmark_jobs.append(BenchmarkJob(**job_data))

                logger.info(f"Loaded state: {len(self.known_models)} models, {len(self.benchmark_jobs)} jobs")

            except Exception as e:
                logger.warning(f"Could not load state: {e}")

    def _save_state(self):
        """Save agent state to file."""
        try:
            state = {
                "known_models": {
                    name: asdict(status)
                    for name, status in self.known_models.items()
                },
                "benchmark_jobs": [asdict(job) for job in self.benchmark_jobs],
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            logger.error(f"Could not save state: {e}")

    async def get_status_report(self) -> Dict[str, Any]:
        """Generate a comprehensive status report."""
        # Calculate stats
        total_models = len(self.known_models)
        benchmarked_models = sum(
            1 for m in self.known_models.values()
            if m.is_benchmarked
        )
        passed_mandatory = sum(
            1 for m in self.known_models.values()
            if m.mandatory_tests_passed
        )

        # Recent jobs
        recent_jobs = sorted(
            [j for j in self.benchmark_jobs if j.status == "completed"],
            key=lambda j: j.completed_at or "",
            reverse=True
        )[:5]

        return {
            "agent_status": "running" if self.running else "stopped",
            "models": {
                "total": total_models,
                "benchmarked": benchmarked_models,
                "pending": total_models - benchmarked,
                "passed_mandatory": passed_mandatory,
            },
            "known_models": {
                name: {
                    "discovered": status.discovered_at,
                    "benchmarked": status.is_benchmarked,
                    "score": f"{status.overall_score:.2%}" if status.overall_score else "N/A",
                    "categories": status.categories_tested,
                }
                for name, status in self.known_models.items()
            },
            "recent_jobs": [
                {
                    "id": job.job_id,
                    "model": job.model,
                    "status": job.status,
                    "completed": job.completed_at,
                }
                for job in recent_jobs
            ],
            "mandatory_categories": self.mandatory_categories,
        }

    async def force_benchmark_model(self, model_name: str, categories: Optional[List[str]] = None):
        """Force a benchmark run for a specific model."""
        if model_name not in self.known_models:
            logger.warning(f"Model {model_name} not known, registering...")
            await self._register_new_model(model_name)

        # Override mandatory categories if specified
        original_mandatory = self.mandatory_categories
        if categories:
            self.mandatory_categories = categories

        await self._schedule_mandatory_benchmark(model_name)

        # Wait for job to complete
        job = self.benchmark_jobs[-1]
        while job.status == "pending":
            await asyncio.sleep(1)
        while job.status == "running":
            await asyncio.sleep(5)

        # Restore original categories
        self.mandatory_categories = original_mandatory

        return job.results

    async def get_recommended_routing(self) -> Dict[str, str]:
        """Get routing recommendations based on all benchmark results."""
        # Collect all job results
        all_speed = {}
        all_accuracy = {}

        for job in self.benchmark_jobs:
            if job.status == "completed" and job.results:
                model = job.model
                speed = job.results.get("speed_matrix", {}).get(model, {})
                accuracy = job.results.get("accuracy_matrix", {}).get(model, {})

                if model not in all_speed:
                    all_speed[model] = {}
                    all_accuracy[model] = {}

                all_speed[model].update(speed)
                all_accuracy[model].update(accuracy)

        # Calculate best model per category
        recommendations = {}

        categories = set()
        for model_scores in all_speed.values():
            categories.update(model_scores.keys())

        for category in categories:
            best_model = None
            best_score = -1

            for model in all_speed:
                if category not in all_speed[model]:
                    continue

                speed = all_speed[model][category]
                accuracy = all_accuracy.get(model, {}).get(category, 0)

                # Normalize and combine
                # Lower speed is better
                max_speed = max(
                    all_speed[m][category]
                    for m in all_speed
                    if category in all_speed[m]
                )
                norm_speed = 1 - (speed / max_speed) if max_speed > 0 else 0

                combined = (accuracy * 0.6) + (norm_speed * 0.4)

                if combined > best_score:
                    best_score = combined
                    best_model = model

            if best_model:
                recommendations[category] = best_model

        return recommendations


__all__ = ["PiAgent", "ModelStatus", "BenchmarkJob"]
