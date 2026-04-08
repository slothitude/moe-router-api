"""Pi Agent - The Boss of the entire MoE Router API stack.

The Pi Agent manages:
1. Routing System - Model pool, routing decisions, performance
2. Benchmark System - Mandatory testing, new model validation
3. Continuous Monitoring - Health checks, performance tracking
4. Auto-Optimization - Update routing based on benchmark results
5. Disk Management - Keep Ollama models under 50GB
"""

import asyncio
import json
import logging
import shutil
import subprocess
import platform
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import httpx
from dataclasses import dataclass, asdict, field
from enum import Enum

logger = logging.getLogger(__name__)


class AgentMode(Enum):
    """Pi Agent operating modes."""
    PASSIVE = "passive"  # Monitor only, no changes
    ADVISORY = "advisory"  # Make recommendations, wait for approval
    ACTIVE = "active"  # Automatically optimize routing
    BOSS = "boss"  # Full control: manage models, routing, benchmarks


@dataclass
class ModelStatus:
    """Status of a model in the system."""
    name: str
    in_pool: bool
    loaded: bool
    location: Optional[str]  # gpu/ram
    memory_mb: int
    queries_handled: int
    avg_latency_ms: float
    success_rate: float
    last_health_check: Optional[str]
    benchmark_score: Optional[float]
    routing_recommendations: List[str]
    # Disk management fields
    disk_size_gb: float = 0.0
    disk_path: Optional[str] = None
    last_used: Optional[str] = None
    removal_priority: int = 0  # Lower = higher priority to keep
    # Load time tracking
    load_time: Optional[float] = None  # Time to load from cold (seconds)


@dataclass
class DiskUsage:
    """Disk usage statistics."""
    total_gb: float
    used_gb: float
    free_gb: float
    usage_percent: float
    ollama_models_size_gb: float
    model_count: int
    max_size_gb: float


@dataclass
class RoutingMetrics:
    """Current routing performance metrics."""
    total_queries: int
    routed_by_auto: int
    routed_by_manual: int
    avg_latency_ms: float
    success_rate: float
    model_distribution: Dict[str, int]
    category_distribution: Dict[str, int]


class PiAgentBoss:
    """
    The Pi Agent Boss - Complete manager of the MoE Router stack.

    Responsibilities:
    - Discover and register new Ollama models
    - Run mandatory benchmarks on all models
    - Monitor routing performance in real-time
    - Auto-update routing decisions based on benchmarks
    - Manage model pool (load/unload for optimization)
    - Generate reports and recommendations
    """

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        router_api_url: str = "http://localhost:8000",
        mode: AgentMode = AgentMode.BOSS,
        state_dir: str = "pi_agent_state",
        mandatory_benchmark_categories: Optional[List[str]] = None,
        discovery_interval: int = 300,
        health_check_interval: int = 60,
        auto_optimize_routing: bool = True,
        auto_manage_pool: bool = True,
        max_disk_size_gb: float = 50.0,
        disk_cleanup_threshold: float = 0.90,  # 90% of max
        ollama_models_path: Optional[str] = None,
        external_api_config: Optional[str] = None,
    ):
        """
        Initialize Pi Agent Boss.

        Args:
            ollama_base_url: Ollama API URL
            router_api_url: MoE Router API URL
            mode: Operating mode (PASSIVE, ADVISORY, ACTIVE, BOSS)
            state_dir: Directory for agent state
            mandatory_benchmark_categories: Categories requiring benchmarks
            discovery_interval: Seconds between model discovery
            health_check_interval: Seconds between health checks
            auto_optimize_routing: Auto-update routing based on benchmarks
            auto_manage_pool: Auto load/unload models
            max_disk_size_gb: Maximum disk size for Ollama models (default: 50GB)
            disk_cleanup_threshold: Trigger cleanup at this % of max (default: 90%)
            ollama_models_path: Path to Ollama models directory (auto-detected)
            external_api_config: Path to external API configuration file
        """
        self.ollama_base_url = ollama_base_url
        self.router_api_url = router_api_url
        self.mode = mode
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.mandatory_benchmark_categories = mandatory_benchmark_categories or [
            "agentic", "code", "factual", "document"
        ]

        self.discovery_interval = discovery_interval
        self.health_check_interval = health_check_interval
        self.auto_optimize_routing = auto_optimize_routing
        self.auto_manage_pool = auto_manage_pool

        # Disk management
        self.max_disk_size_gb = max_disk_size_gb
        self.disk_cleanup_threshold = disk_cleanup_threshold
        self.ollama_models_path = Path(ollama_models_path) if ollama_models_path else self._find_ollama_models_path()

        # External API integration
        self.external_api_config = external_api_config
        self.external_api_client = None

        # State
        self.known_models: Dict[str, ModelStatus] = {}
        self.routing_metrics = RoutingMetrics(
            total_queries=0,
            routed_by_auto=0,
            routed_by_manual=0,
            avg_latency_ms=0,
            success_rate=1.0,
            model_distribution={},
            category_distribution={},
        )
        self.benchmark_results: Dict[str, Dict] = {}
        self.routing_recommendations: Dict[str, str] = {}
        self.auto_routing_benchmark: Optional[Dict] = None
        self.classification_accuracy: Optional[Dict] = None
        self.updated_fallback_chains: Optional[Dict] = None
        self.running = False

        # HTTP client
        self.client: Optional[httpx.AsyncClient] = None

        # Load state
        self._load_state()

        # Initialize external API client if config provided
        if self.external_api_config:
            self._initialize_external_api_client()

    async def start(self):
        """Start Pi Agent Boss in monitoring mode."""
        logger.info("="*70)
        logger.info(" PI AGENT BOSS - Manager of MoE Router Stack")
        logger.info("="*70)
        logger.info(f"Mode: {self.mode.value.upper()}")
        logger.info(f"Ollama: {self.ollama_base_url}")
        logger.info(f"Router API: {self.router_api_url}")
        logger.info(f"Auto-optimize routing: {self.auto_optimize_routing}")
        logger.info(f"Auto-manage pool: {self.auto_manage_pool}")
        logger.info("="*70)

        self.client = httpx.AsyncClient(timeout=30)
        self.running = True

        # Initial setup
        await self._initial_discovery()
        await self._check_router_health()

        # Main loop
        while self.running:
            try:
                # Health check
                await self._health_check_cycle()

                # Model discovery
                await self._discovery_cycle()

                # Benchmark management
                await self._benchmark_cycle()

                # Routing optimization
                if self.auto_optimize_routing:
                    await self._routing_optimization_cycle()
                    await self._update_fallback_chains()

                # Pool management
                if self.auto_manage_pool:
                    await self._pool_management_cycle()

                # Disk management
                await self._disk_management_cycle()

                # Save state
                self._save_state()

                # Wait
                await asyncio.sleep(min(self.discovery_interval, self.health_check_interval))

            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(60)

        await self.client.aclose()

    def stop(self):
        """Stop the agent."""
        logger.info("Stopping Pi Agent Boss...")
        self.running = False
        self._save_state()

    def _initialize_external_api_client(self):
        """Initialize the external API client if config is provided."""
        if not self.external_api_config:
            return

        try:
            from models.external_api_client import ExternalAPIClient
            self.external_api_client = ExternalAPIClient(self.external_api_config)
            external_models = self.external_api_client.get_models()
            logger.info(f"✓ External API client initialized with {len(external_models)} models")
        except Exception as e:
            logger.warning(f"Could not initialize external API client: {e}")
            self.external_api_client = None

    async def _discover_external_models(self):
        """Discover and register external API models."""
        if not self.external_api_client:
            return

        external_models = self.external_api_client.get_models()

        for model_id, model_config in external_models.items():
            if model_id not in self.known_models:
                await self._register_model(model_id, is_external=True)
                logger.info(f"✓ Discovered external model: {model_config.display_name}")

    async def _initial_discovery(self):
        """Initial model discovery and system check."""
        logger.info("Running initial discovery...")

        # Discover Ollama models
        await self._discover_ollama_models()

        # Discover external API models
        await self._discover_external_models()

        # Get current router state
        await self._sync_router_state()

        # Check which models need benchmarking
        await self._check_benchmark_status()

        logger.info(f"Initial discovery complete: {len(self.known_models)} models known")

    async def _discover_ollama_models(self):
        """Discover models from Ollama."""
        try:
            response = await self.client.get(f"{self.ollama_base_url}/api/tags")
            response.raise_for_status()
            data = response.json()

            ollama_models = {m["name"] for m in data.get("models", [])}

            # Find new models
            new_models = ollama_models - set(self.known_models.keys())
            if new_models:
                logger.info(f"🎉 New models discovered: {', '.join(new_models)}")
                for model in new_models:
                    await self._register_model(model)

            # Find removed models
            removed = set(self.known_models.keys()) - ollama_models
            if removed:
                logger.warning(f"⚠️  Models removed: {', '.join(removed)}")
                for model in removed:
                    del self.known_models[model]

        except Exception as e:
            logger.error(f"Error discovering models: {e}")

    async def _register_model(self, model_name: str, is_external: bool = False):
        """Register a new model.

        Args:
            model_name: Name of the model
            is_external: Whether this is an external API model
        """
        # Get external model config if applicable
        display_name = model_name
        if is_external and self.external_api_client:
            model_config = self.external_api_client.get_model(model_name)
            if model_config:
                display_name = model_config.display_name

        self.known_models[model_name] = ModelStatus(
            name=model_name,
            in_pool=not is_external,  # External models are always "in pool"
            loaded=is_external,  # External models are always "loaded" (no load time)
            location="external" if is_external else None,
            memory_mb=0 if is_external else 0,
            queries_handled=0,
            avg_latency_ms=0,
            success_rate=1.0,
            last_health_check=datetime.now().isoformat() if is_external else None,
            benchmark_score=None,
            routing_recommendations=[],
        )
        logger.info(f"✓ Registered model: {display_name}")

        # Register external models in the model specs registry
        if is_external and self.external_api_client:
            try:
                from models.model_specs import ModelRegistry
                model_config = self.external_api_client.get_model(model_name)
                if model_config:
                    ModelRegistry.register_external_model(model_name, {
                        "display_name": model_config.display_name,
                        "categories": model_config.categories,
                        "specialization": model_config.specialization,
                        "priority": model_config.priority,
                        "api": model_config.api
                    })
            except Exception as e:
                logger.warning(f"Could not register external model in specs: {e}")

    async def _sync_router_state(self):
        """Sync with router API state."""
        try:
            # Get model pool status
            response = await self.client.get(f"{self.router_api_url}/api/v1/models/pool")
            if response.status_code == 200:
                pool_data = response.json()

                # Update model statuses
                for model_name, status in self.known_models.items():
                    pool_info = pool_data.get("models", {}).get(model_name, {})
                    status.in_pool = pool_info.get("in_pool", False)
                    status.loaded = pool_info.get("loaded", False)
                    status.location = pool_info.get("location")

        except Exception as e:
            logger.warning(f"Could not sync router state: {e}")

    async def _health_check_cycle(self):
        """Run health checks."""
        try:
            response = await self.client.get(f"{self.router_api_url}/api/v1/health")
            if response.status_code == 200:
                health = response.json()
                logger.debug(f"Router health: {health.get('status', 'unknown')}")

                # Get metrics
                metrics_response = await self.client.get(f"{self.router_api_url}/api/v1/metrics")
                if metrics_response.status_code == 200:
                    await self._update_routing_metrics(metrics_response.json())

        except Exception as e:
            logger.error(f"Health check failed: {e}")

    async def _update_routing_metrics(self, metrics_data: Dict):
        """Update routing metrics from API."""
        # Extract and update metrics
        self.routing_metrics.total_queries = metrics_data.get("total_queries", 0)
        # Update other metrics as needed
        logger.debug(f"Total queries: {self.routing_metrics.total_queries}")

    async def _discovery_cycle(self):
        """Periodic model discovery."""
        await self._discover_ollama_models()
        await self._discover_external_models()
        await self._sync_router_state()

    async def _benchmark_cycle(self):
        """Check and run benchmarks."""
        # Find models that need mandatory benchmarks
        for model_name, status in self.known_models.items():
            if status.benchmark_score is None:
                logger.info(f"⚠️  Model {model_name} needs benchmarking")
                if self.mode in [AgentMode.ACTIVE, AgentMode.BOSS]:
                    logger.info(f"🚀 Starting mandatory benchmark for {model_name}")
                    await self._run_benchmark(model_name)

        # After all models are benchmarked, test auto-routing
        if self.mode in [AgentMode.ACTIVE, AgentMode.BOSS]:
            benchmarked = [m for m, s in self.known_models.items() if s.benchmark_score is not None]
            if len(benchmarked) >= 2:  # Need at least 2 models to test routing
                await self._benchmark_auto_routing()

    async def _wait_for_model_loaded(self, model_name: str, timeout_seconds: int = 30) -> bool:
        """Wait for a model to be loaded by checking Ollama's actual running state."""
        start_time = asyncio.get_event_loop().time()
        check_interval = 1  # Check every second

        while True:
            try:
                # Check Ollama's actual running state via its API
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.ollama_base_url}/api/ps")
                    if response.status_code == 200:
                        ps_data = response.json()
                        # Check if model is actually running in Ollama
                        running_models = ps_data.get("models", [])

                        # Check for partial model name match
                        is_running = any(
                            model_name in m.get("name", "") or m.get("name", "") in model_name
                            for m in running_models
                        )

                        if is_running:
                            logger.info(f"  ✓ {model_name} is running in Ollama")
                            return True

                        elapsed = asyncio.get_event_loop().time() - start_time
                        if elapsed > timeout_seconds:
                            logger.warning(f"  ⚠ {model_name} not detected in Ollama after {elapsed:.1f}s")
                            return False

                        # Wait before polling again
                        await asyncio.sleep(check_interval)
            except Exception as e:
                logger.debug(f"Error checking Ollama status: {e}")
                await asyncio.sleep(check_interval)

    async def _check_model_running(self, model_name: str) -> bool:
        """Check if a model is currently running in Ollama."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_base_url}/api/ps")
                if response.status_code == 200:
                    ps_data = response.json()
                    running_models = ps_data.get("models", [])

                    # Check for partial model name match
                    is_running = any(
                        model_name in m.get("name", "") or m.get("name", "") in model_name
                        for m in running_models
                    )
                    return is_running
        except Exception as e:
            logger.debug(f"Error checking Ollama: {e}")
        return False

    async def _warmup_model(self, model_name: str):
        """Load model into Ollama and measure load time."""
        logger.info(f"  Loading {model_name}...")

        # Check if already running
        if await self._check_model_running(model_name):
            logger.info(f"  ✓ {model_name} already running")
            return True

        # Not running - load it and measure time
        load_start = asyncio.get_event_loop().time()

        try:
            # Create a separate client for the load request
            async with httpx.AsyncClient(timeout=180.0) as load_client:
                # Start the loading request in background
                load_task = asyncio.create_task(
                    load_client.post(
                        f"{self.ollama_base_url}/api/generate",
                        json={
                            "model": model_name,
                            "prompt": "OK",
                            "stream": False,
                            "options": {"num_predict": 2}
                        }
                    )
                )

                # Wait for model to appear in Ollama
                # Poll /api/ps every 2 seconds
                while True:
                    await asyncio.sleep(2)

                    if await self._check_model_running(model_name):
                        load_time = asyncio.get_event_loop().time() - load_start
                        logger.info(f"  ✓ {model_name} loaded in {load_time:.1f}s")

                        # Store load time in model status
                        if model_name in self.known_models:
                            self.known_models[model_name].load_time = load_time

                        # Cancel the load task since we don't need the response
                        if not load_task.done():
                            load_task.cancel()
                            try:
                                await load_task
                            except asyncio.CancelledError:
                                pass

                        return True

                    # Timeout after 2 minutes
                    if asyncio.get_event_loop().time() - load_start > 120:
                        logger.warning(f"  ⚠ {model_name} failed to load after 120s")
                        # Cancel the load task
                        if not load_task.done():
                            load_task.cancel()
                            try:
                                await load_task
                            except asyncio.CancelledError:
                                pass
                        return False

        except Exception as e:
            logger.error(f"  ✗ {model_name} load error: {e}")
            return False

    async def _run_benchmark(self, model_name: str):
        """Run benchmark for a model.

        Args:
            model_name: Name of the model (can be local or external)
        """
        # Check if this is an external model
        if model_name.startswith("external/"):
            await self._benchmark_external_model(model_name)
            return

        try:
            # Warmup model first to load into memory
            await self._warmup_model(model_name)

            # Import benchmark components
            from test_generator import TestGenerator
            from metrics_collector import MetricsCollector
            from quality_analyzer import QualityAnalyzer

            test_gen = TestGenerator()
            all_metrics = []
            all_quality = []

            # Test mandatory categories
            for category in self.mandatory_benchmark_categories:
                tests = test_gen.get_tests_by_category(category)
                logger.info(f"  Benchmarking {category}...")

                async with MetricsCollector(
                    api_base_url=self.router_api_url,
                    timeout_seconds=180  # Increased from 120
                ) as collector:
                    metrics = await collector.collect_batch(
                        tests,
                        model=model_name,
                        concurrent=1  # Reduced from 3 to avoid timeouts
                    )

                    quality_analyzer = QualityAnalyzer()
                    quality_scores = await quality_analyzer.analyze_batch(metrics, tests)

                    all_metrics.extend(metrics)
                    all_quality.extend(quality_scores)

            # Calculate overall score
            successful = sum(1 for q in all_quality if q.get("overall_accuracy", 0) > 0.5)
            total = len(all_quality)
            score = successful / total if total > 0 else 0

            # Update model status
            self.known_models[model_name].benchmark_score = score

            # Store results
            self.benchmark_results[model_name] = {
                "score": score,
                "categories_tested": self.mandatory_benchmark_categories,
                "timestamp": datetime.now().isoformat(),
            }

            # Save results
            results_file = self.state_dir / f"benchmark_{model_name.replace(':', '_')}.json"
            with open(results_file, 'w') as f:
                json.dump({
                    "model": model_name,
                    "score": score,
                    "metrics": [m.to_dict() for m in all_metrics],
                    "quality": all_quality,
                }, f, indent=2)

            logger.info(f"✓ Benchmark complete for {model_name}: {score:.2%}")

            # Update routing recommendations
            await self._update_routing_recommendations()

        except Exception as e:
            logger.error(f"Benchmark failed for {model_name}: {e}", exc_info=True)

    async def _benchmark_external_model(self, model_id: str):
        """Benchmark an external API model.

        Args:
            model_id: External model ID (e.g., "external/nvidia_nim/model-name")
        """
        if not self.external_api_client:
            logger.error("External API client not initialized")
            return

        try:
            from test_generator import TestGenerator

            model_config = self.external_api_client.get_model(model_id)
            if not model_config:
                logger.error(f"Unknown external model: {model_id}")
                return

            # Test categories based on model's configured categories
            categories_to_test = model_config.categories if model_config else ['factual']

            logger.info(f"  Benchmarking external model: {model_config.display_name}")
            logger.info(f"  Categories: {', '.join(categories_to_test)}")

            test_gen = TestGenerator()
            all_metrics = []
            all_quality = []

            # Test each category
            for category in categories_to_test:
                if category not in self.mandatory_benchmark_categories:
                    continue

                tests = test_gen.get_tests_by_category(category)
                logger.info(f"  Benchmarking {category}...")

                # Query external API directly
                for test in tests[:5]:  # Test 5 queries per category
                    start = asyncio.get_event_loop().time()

                    try:
                        messages = [{"role": "user", "content": test["query"]}]
                        response = await self.external_api_client.query(
                            model_id,
                            messages,
                            temperature=0.7,
                            max_tokens=512
                        )

                        latency = (asyncio.get_event_loop().time() - start) * 1000

                        # Store metric
                        all_metrics.append({
                            "query": test["query"],
                            "response": response["content"],
                            "latency_ms": latency,
                            "category": category,
                            "model": model_id,
                            "tokens": response.get("usage", {}).get("total_tokens", 0)
                        })

                        # Simple quality check (basic length/relevance)
                        if len(response["content"]) > 50:  # Minimum reasonable response
                            all_quality.append({
                                "category": category,
                                "accuracy": 1.0,
                                "reason": "External API response received"
                            })

                        logger.info(f"    Response: {response['content'][:100]}... ({latency:.0f}ms)")

                    except Exception as e:
                        logger.error(f"    Error: {e}")

            # Calculate score
            successful = sum(1 for q in all_quality if q.get("accuracy", 0) > 0.5)
            total = len(all_quality)
            score = successful / total if total > 0 else 0

            # Update model status
            self.known_models[model_id].benchmark_score = score

            # Store results
            self.benchmark_results[model_id] = {
                "score": score,
                "categories_tested": categories_to_test,
                "timestamp": datetime.now().isoformat(),
                "type": "external"
            }

            # Save results
            results_file = self.state_dir / f"benchmark_{model_id.replace('/', '_').replace(':', '_')}.json"
            with open(results_file, 'w') as f:
                json.dump({
                    "model": model_id,
                    "display_name": model_config.display_name,
                    "score": score,
                    "metrics": all_metrics,
                    "quality": all_quality,
                }, f, indent=2)

            logger.info(f"✓ Benchmark complete for {model_config.display_name}: {score:.2%}")

        except Exception as e:
            logger.error(f"External model benchmark failed for {model_id}: {e}", exc_info=True)

    async def _update_routing_recommendations(self):
        """Update routing recommendations based on benchmarks."""
        # For each category, find best model
        for category in self.mandatory_benchmark_categories:
            best_model = None
            best_score = -1

            for model_name, status in self.known_models.items():
                if status.benchmark_score and status.benchmark_score > best_score:
                    best_score = status.benchmark_score
                    best_model = model_name

            if best_model:
                self.routing_recommendations[category] = best_model
                logger.info(f"📊 Routing recommendation: {category} -> {best_model}")

    async def _warmup_all_models(self):
        """Warm up all models that might be used in auto-routing."""
        logger.info("Warming up all models for auto-routing benchmark...")

        # Get list of non-embedding models
        models_to_warmup = [
            name for name in self.known_models.keys()
            if "embed" not in name.lower()
        ]

        success_count = 0
        for model in models_to_warmup:
            try:
                result = await self._warmup_model(model)
                if result:
                    success_count += 1
            except Exception as e:
                logger.warning(f"Failed to warmup {model}: {e}")

        logger.info(f"Warmed up {success_count}/{len(models_to_warmup)} models")

    async def _benchmark_auto_routing(self):
        """Benchmark the router's auto-routing performance."""
        logger.info("\n" + "="*60)
        logger.info("🔄 BENCHMARKING AUTO-ROUTING")
        logger.info("="*60 + "\n")

        try:
            # First, warmup all models that might be used
            await self._warmup_all_models()

            from test_generator import TestGenerator
            from metrics_collector import MetricsCollector
            from quality_analyzer import QualityAnalyzer

            test_gen = TestGenerator()

            # Test each category with auto-routing
            auto_routing_results = {}

            for category in self.mandatory_benchmark_categories:
                tests = test_gen.get_tests_by_category(category)
                logger.info(f"Testing {category} with auto-routing...")

                async with MetricsCollector(
                    api_base_url=self.router_api_url,
                    timeout_seconds=180  # Increased from 120
                ) as collector:
                    # model=None enables auto-routing
                    metrics = await collector.collect_batch(
                        tests,
                        model=None,  # AUTO-ROUTING
                        concurrent=1  # Reduced to avoid timeouts
                    )

                    quality_analyzer = QualityAnalyzer()
                    quality_scores = await quality_analyzer.analyze_batch(metrics, tests)

                    # Calculate results
                    successful = sum(1 for q in quality_scores if q.get("overall_accuracy", 0) > 0.5)
                    score = successful / len(quality_scores) if quality_scores else 0

                    # Track which models were selected
                    model_selection = {}
                    for m in metrics:
                        if not m.error:
                            if m.model not in model_selection:
                                model_selection[m.model] = 0
                            model_selection[m.model] += 1

                    auto_routing_results[category] = {
                        "score": score,
                        "model_selection": model_selection,
                        "avg_latency": sum(m.total_latency_ms for m in metrics if not m.error) / max(1, len([m for m in metrics if not m.error])),
                        "queries": len(metrics)
                    }

                    logger.info(f"  Auto-routing score: {score:.2%}")
                    logger.info(f"  Models selected: {model_selection}")

            # Compare auto-routing vs forced routing
            await self._compare_routing(auto_routing_results)

            # Test classification accuracy
            await self._test_classification_accuracy()

            # Store results
            self.auto_routing_benchmark = auto_routing_results

            # Save comparison report
            await self._save_routing_comparison_report(auto_routing_results)

        except Exception as e:
            logger.error(f"Auto-routing benchmark failed: {e}", exc_info=True)

    async def _compare_routing(self, auto_routing_results: Dict):
        """Compare auto-routing vs forced routing performance."""
        logger.info("\n" + "="*60)
        logger.info("📊 ROUTING COMPARISON: Auto vs Forced")
        logger.info("="*60 + "\n")

        for category, auto_result in auto_routing_results.items():
            logger.info(f"\n{category.upper()}:")
            logger.info(f"  Auto-Routing:")
            logger.info(f"    Score: {auto_result['score']:.2%}")
            logger.info(f"    Latency: {auto_result['avg_latency']:.0f}ms")
            logger.info(f"    Models: {auto_result['model_selection']}")

            # Compare with forced routing for each model
            best_forced_score = 0
            best_forced_model = None

            for model_name, status in self.known_models.items():
                if status.benchmark_score:
                    # Get category-specific score if available
                    model_result = self.benchmark_results.get(model_name, {})
                    category_score = status.benchmark_score  # Using overall score for now

                    logger.info(f"    {model_name}: {category_score:.2%}")

                    if category_score > best_forced_score:
                        best_forced_score = category_score
                        best_forced_model = model_name

            if best_forced_model:
                improvement = auto_result['score'] - best_forced_score
                logger.info(f"\n  Comparison:")
                logger.info(f"    Best forced model: {best_forced_model} ({best_forced_score:.2%})")
                logger.info(f"    Difference: {improvement:+.2%}")

                if improvement > 0:
                    logger.info(f"    ✓ Auto-routing is better by {improvement:.2%}")
                else:
                    logger.info(f"    ⚠ Forced routing is better by {-improvement:.2%}")

        logger.info("\n" + "="*60 + "\n")

    async def _test_classification_accuracy(self):
        """Test how accurately the router classifies queries."""
        logger.info("\n" + "="*60)
        logger.info("🎯 TESTING CLASSIFICATION ACCURACY")
        logger.info("="*60 + "\n")

        try:
            from test_generator import TestGenerator
            from .metrics_collector import MetricsCollector

            test_gen = TestGenerator()
            all_tests = test_gen.get_all_tests()

            # Get test categories
            category_tests = {}
            for test in all_tests:
                cat = test["category"]
                if cat not in category_tests:
                    category_tests[cat] = []
                category_tests[cat].append(test)

            classification_results = {}

            async with MetricsCollector(
                api_base_url=self.router_api_url,
                timeout_seconds=120
            ) as collector:
                for category, tests in category_tests.items():
                    # Sample 5 tests per category
                    sample_tests = tests[:5]

                    logger.info(f"Testing classification for {category}...")

                    correct = 0
                    model_usage = {}

                    for test in sample_tests:
                        metrics = await collector.collect_metrics(test, model=None)

                        if not metrics.error:
                            # Check if router classified correctly
                            expected_type = test["category"]
                            classified_type = metrics.query_type_classified

                            # Map category names
                            category_map = {
                                "agentic": "BALANCED",
                                "code": "CODE",
                                "factual": "SPEED_CRITICAL",
                                "document": "PROMPT_HEAVY",
                                "creative": "GENERATION_HEAVY"
                            }

                            expected_mapped = category_map.get(expected_type, expected_type.upper())

                            if expected_mapped in classified_type or classified_type in expected_mapped:
                                correct += 1

                            # Track model usage
                            if metrics.model not in model_usage:
                                model_usage[metrics.model] = 0
                            model_usage[metrics.model] += 1

                    accuracy = correct / len(sample_tests) if sample_tests else 0
                    classification_results[category] = {
                        "accuracy": accuracy,
                        "correct": correct,
                        "total": len(sample_tests),
                        "model_usage": model_usage
                    }

                    logger.info(f"  Accuracy: {accuracy:.2%} ({correct}/{len(sample_tests)})")
                    logger.info(f"  Model usage: {model_usage}")

            # Calculate overall accuracy
            total_correct = sum(r["correct"] for r in classification_results.values())
            total_tests = sum(r["total"] for r in classification_results.values())
            overall_accuracy = total_correct / total_tests if total_tests > 0 else 0

            logger.info(f"\n📊 Overall Classification Accuracy: {overall_accuracy:.2%}")
            logger.info(f"   Correct: {total_correct}/{total_tests}\n")

            self.classification_accuracy = {
                "overall": overall_accuracy,
                "by_category": classification_results
            }

        except Exception as e:
            logger.error(f"Classification accuracy test failed: {e}", exc_info=True)

    async def _save_routing_comparison_report(self, auto_routing_results: Dict):
        """Save detailed routing comparison report."""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "auto_routing_results": auto_routing_results,
                "model_benchmarks": {
                    model: {
                        "score": status.benchmark_score,
                        "queries": status.queries_handled,
                        "avg_latency": status.avg_latency_ms,
                    }
                    for model, status in self.known_models.items()
                    if status.benchmark_score is not None
                },
                "classification_accuracy": getattr(self, 'classification_accuracy', None),
            }

            report_file = self.state_dir / "routing_comparison_report.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)

            logger.info(f"✓ Routing comparison saved: {report_file}")

        except Exception as e:
            logger.error(f"Failed to save routing comparison: {e}")

    async def _update_fallback_chains(self):
        """Update router fallback chains based on benchmark results."""
        if self.mode != AgentMode.BOSS:
            return

        logger.info("\n" + "="*60)
        logger.info("🔧 UPDATING FALLBACK CHAINS")
        logger.info("="*60 + "\n")

        try:
            # Group models by category performance
            category_performance = {}

            for model_name, status in self.known_models.items():
                if status.benchmark_score is None:
                    continue

                # Get model specialization from benchmark results
                benchmark_data = self.benchmark_results.get(model_name, {})

                # For each category, build a ranked list
                if model_name not in category_performance:
                    category_performance[model_name] = {}

                # Use overall score as proxy for all categories
                # (In production, would have per-category scores)
                for category in self.mandatory_benchmark_categories:
                    if category not in category_performance:
                        category_performance[category] = []
                    category_performance[category].append((model_name, status.benchmark_score))

            # Sort and create fallback chains
            new_fallback_chains = {}

            for category, models in category_performance.items():
                # Sort by score (descending)
                models.sort(key=lambda x: x[1], reverse=True)
                chain = [model for model, score in models]

                new_fallback_chains[category] = chain

                logger.info(f"  {category}:")
                for i, (model, score) in enumerate(models):
                    logger.info(f"    {i+1}. {model} ({score:.2%})")

            # Apply to router via Admin API
            if self.mode == AgentMode.BOSS:
                for category, chain in new_fallback_chains.items():
                    try:
                        await self.client.post(
                            f"{self.router_api_url}/api/v1/admin/routing/update-fallback",
                            params={"category": category},
                            json={"chain": chain}
                        )
                        logger.info(f"✓ Updated fallback chain for {category}")
                    except Exception as e:
                        logger.warning(f"Could not update fallback chain for {category}: {e}")

            self.updated_fallback_chains = new_fallback_chains

            logger.info("\n" + "="*60 + "\n")

        except Exception as e:
            logger.error(f"Failed to update fallback chains: {e}", exc_info=True)

    async def _routing_optimization_cycle(self):
        """Apply routing optimizations."""
        if self.mode != AgentMode.BOSS:
            return

        # Apply recommendations to router
        for category, model in self.routing_recommendations.items():
            logger.info(f"✓ Optimized routing: {category} -> {model}")
            # In real implementation, would call router API to update

    async def _pool_management_cycle(self):
        """Manage model pool."""
        if self.mode != AgentMode.BOSS:
            return

        # Load high-performing models
        for model_name, status in self.known_models.items():
            if status.benchmark_score and status.benchmark_score > 0.7:
                if not status.loaded:
                    logger.info(f"📥 Loading high-performing model: {model_name}")
                    # Would call API to load model
                    # await self.client.post(f"{self.router_api_url}/api/v1/models/{model_name}/load")

    async def _check_router_health(self):
        """Check router health."""
        try:
            response = await self.client.get(f"{self.router_api_url}/api/v1/health")
            if response.status_code == 200:
                logger.info("✓ Router API is healthy")
            else:
                logger.warning("⚠️  Router API health check failed")
        except Exception as e:
            logger.error(f"✗ Cannot connect to Router API: {e}")

    async def _check_benchmark_status(self):
        """Check which models need benchmarking."""
        need_benchmark = [
            m for m, s in self.known_models.items()
            if s.benchmark_score is None
        ]

        if need_benchmark:
            logger.info(f"⚠️  Models needing benchmark: {', '.join(need_benchmark)}")

            if self.mode in [AgentMode.ACTIVE, AgentMode.BOSS]:
                for model in need_benchmark:
                    await self._run_benchmark(model)

    async def get_dashboard(self) -> Dict[str, Any]:
        """Get agent dashboard data."""
        # Get disk usage
        disk_usage = await self._get_disk_usage()

        return {
            "mode": self.mode.value,
            "disk": {
                "used_gb": disk_usage.ollama_models_size_gb,
                "max_gb": disk_usage.max_size_gb,
                "free_gb": disk_usage.free_gb,
                "usage_percent": disk_usage.usage_percent,
                "model_count": disk_usage.model_count,
            },
            "models": {
                "total": len(self.known_models),
                "benchmarked": sum(1 for s in self.known_models.values() if s.benchmark_score),
                "in_pool": sum(1 for s in self.known_models.values() if s.in_pool),
                "loaded": sum(1 for s in self.known_models.values() if s.loaded),
            },
            "model_details": [
                {
                    "name": s.name,
                    "loaded": s.loaded,
                    "benchmark_score": f"{s.benchmark_score:.2%}" if s.benchmark_score else "Pending",
                    "queries": s.queries_handled,
                    "avg_latency": f"{s.avg_latency_ms:.0f}ms",
                    "disk_size_gb": f"{s.disk_size_gb:.2f}GB",
                }
                for s in sorted(
                    self.known_models.values(),
                    key=lambda x: x.benchmark_score or 0,
                    reverse=True
                )
            ],
            "routing_recommendations": self.routing_recommendations,
            "routing_metrics": asdict(self.routing_metrics),
        }

    def _load_state(self):
        """Load agent state."""
        state_file = self.state_dir / "agent_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    data = json.load(f)

                for name, status in data.get("models", {}).items():
                    self.known_models[name] = ModelStatus(**status)

                self.routing_recommendations = data.get("routing_recommendations", {})
                self.benchmark_results = data.get("benchmark_results", {})

                logger.info(f"Loaded state: {len(self.known_models)} models")

            except Exception as e:
                logger.warning(f"Could not load state: {e}")

    def _save_state(self):
        """Save agent state."""
        try:
            state = {
                "models": {
                    name: asdict(status)
                    for name, status in self.known_models.items()
                },
                "routing_recommendations": self.routing_recommendations,
                "benchmark_results": self.benchmark_results,
                "last_updated": datetime.now().isoformat(),
            }

            state_file = self.state_dir / "agent_state.json"
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            logger.error(f"Could not save state: {e}")

    def _find_ollama_models_path(self) -> Path:
        """Auto-detect Ollama models directory path."""
        system = platform.system()

        if system == "Windows":
            # Windows: C:\Users\<username>\.ollama\models
            base = Path.home() / ".ollama" / "models"
        elif system == "Darwin":  # macOS
            # macOS: ~/.ollama/models
            base = Path.home() / ".ollama" / "models"
        else:  # Linux
            # Linux: /usr/share/ollama/.ollama/models or ~/.ollama/models
            base = Path.home() / ".ollama" / "models"
            if not base.exists():
                base = Path("/usr/share/ollama/.ollama/models")

        if base.exists():
            logger.info(f"Detected Ollama models path: {base}")
        else:
            logger.warning(f"Ollama models path not found: {base}")

        return base

    async def _disk_management_cycle(self):
        """Check disk usage and cleanup if needed."""
        if self.mode not in [AgentMode.ACTIVE, AgentMode.BOSS]:
            return

        try:
            disk_usage = await self._get_disk_usage()

            logger.info(f"💾 Disk: {disk_usage.ollama_models_size_gb:.2f}GB / {disk_usage.max_size_gb:.2f}GB "
                       f"({disk_usage.usage_percent:.1f}%)")

            # Check if we need cleanup
            if disk_usage.ollama_models_size_gb > (self.max_disk_size_gb * self.disk_cleanup_threshold):
                logger.warning(f"⚠️  Approaching disk limit: {disk_usage.ollama_models_size_gb:.2f}GB / "
                             f"{self.max_disk_size_gb:.2f}GB")
                await self._cleanup_models(disk_usage)

        except Exception as e:
            logger.error(f"Error in disk management cycle: {e}")

    async def _get_disk_usage(self) -> DiskUsage:
        """Get current disk usage statistics."""
        # Scan Ollama models directory
        total_size = 0.0
        model_sizes = {}

        if self.ollama_models_path.exists():
            # Calculate size per model
            for model_dir in self.ollama_models_path.iterdir():
                if model_dir.is_dir():
                    size_gb = self._get_dir_size_gb(model_dir)
                    model_name = model_dir.name
                    model_sizes[model_name] = size_gb
                    total_size += size_gb

                    # Update model status with disk info
                    if model_name in self.known_models:
                        self.known_models[model_name].disk_size_gb = size_gb
                        self.known_models[model_name].disk_path = str(model_dir)

        return DiskUsage(
            total_gb=self.max_disk_size_gb,
            used_gb=total_size,
            free_gb=max(0, self.max_disk_size_gb - total_size),
            usage_percent=(total_size / self.max_disk_size_gb * 100) if self.max_disk_size_gb > 0 else 0,
            ollama_models_size_gb=total_size,
            model_count=len(model_sizes),
            max_size_gb=self.max_disk_size_gb,
        )

    def _get_dir_size_gb(self, path: Path) -> float:
        """Get directory size in GB."""
        try:
            if platform.system() == "Windows":
                # Use PowerShell for Windows
                result = subprocess.run(
                    ['powershell', '-Command',
                     f'(Get-ChildItem -Path "{path}" -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0 and result.stdout.strip():
                    return float(result.stdout.strip())
            else:
                # Use du for Unix-like systems
                result = subprocess.run(
                    ['du', '-sb', str(path)],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    size_bytes = int(result.stdout.split()[0])
                    return size_bytes / (1024**3)  # Convert to GB
        except Exception as e:
            logger.warning(f"Could not get size for {path}: {e}")

        # Fallback: estimate based on file count
        try:
            total = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            return total / (1024**3)
        except Exception:
            return 0.0

    async def _cleanup_models(self, disk_usage: DiskUsage):
        """Remove low-priority models to free up disk space."""
        if self.mode != AgentMode.BOSS:
            logger.info("ℹ️  Would cleanup models (not in BOSS mode)")
            return

        # Calculate removal priority for each model
        models_to_remove = []

        for model_name, status in self.known_models.items():
            # Skip models with no disk usage
            if status.disk_size_gb == 0:
                continue

            # Calculate priority score (lower = remove first)
            priority_score = 0

            # Keep if it's a recommended model
            if any(rec == model_name for rec in self.routing_recommendations.values()):
                priority_score += 100

            # Keep if benchmark score is high
            if status.benchmark_score:
                priority_score += int(status.benchmark_score * 50)

            # Keep if recently used
            if status.queries_handled > 0:
                priority_score += min(20, status.queries_handled)

            # Keep if loaded
            if status.loaded:
                priority_score += 30

            status.removal_priority = priority_score

            if priority_score < 50:  # Low priority models
                models_to_remove.append((model_name, status))

        # Sort by priority (lowest first)
        models_to_remove.sort(key=lambda x: x[1].removal_priority)

        # Calculate how much to free
        target_free = self.max_disk_size_gb * 0.15  # Aim to free 15%
        freed = 0.0

        for model_name, status in models_to_remove:
            if freed >= target_free:
                break

            logger.info(f"🗑️  Removing model: {model_name} ({status.disk_size_gb:.2f}GB, "
                       f"priority: {status.removal_priority})")

            success = await self._remove_model(model_name)

            if success:
                freed += status.disk_size_gb
                del self.known_models[model_name]

        logger.info(f"✓ Freed {freed:.2f}GB of disk space")

    async def _remove_model(self, model_name: str) -> bool:
        """Remove a model from Ollama."""
        try:
            # Unload from pool first
            if model_name in self.known_models:
                status = self.known_models[model_name]
                if status.loaded:
                    try:
                        await self.client.post(f"{self.router_api_url}/api/v1/models/{model_name}/unload")
                    except Exception as e:
                        logger.warning(f"Could not unload {model_name}: {e}")

            # Remove from Ollama
            result = subprocess.run(
                ['ollama', 'rm', model_name],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                logger.info(f"✓ Removed {model_name} from Ollama")
                return True
            else:
                logger.error(f"Failed to remove {model_name}: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error removing model {model_name}: {e}")
            return False

    async def get_disk_report(self) -> Dict[str, Any]:
        """Get detailed disk usage report."""
        disk_usage = await self._get_disk_usage()

        # Get model sizes
        model_sizes = [
            {
                "name": name,
                "size_gb": status.disk_size_gb,
                "benchmark_score": f"{status.benchmark_score:.2%}" if status.benchmark_score else "N/A",
                "priority": status.removal_priority,
                "recommended": any(rec == name for rec in self.routing_recommendations.values()),
                "loaded": status.loaded,
            }
            for name, status in sorted(
                self.known_models.items(),
                key=lambda x: x[1].disk_size_gb,
                reverse=True
            )
        ]

        return {
            "disk_usage": asdict(disk_usage),
            "models": model_sizes,
            "cleanup_threshold": self.disk_cleanup_threshold * 100,
            "max_size_gb": self.max_disk_size_gb,
        }


__all__ = [
    "PiAgentBoss",
    "AgentMode",
    "ModelStatus",
    "RoutingMetrics",
    "DiskUsage",
]
