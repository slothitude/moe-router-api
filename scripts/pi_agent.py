#!/usr/bin/env python3
"""Pi Agent Boss CLI - Start and manage the Pi Agent."""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Set UTF-8 for Windows
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark.pi_agent_boss import PiAgentBoss, AgentMode
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_agent(args):
    """Run Pi Agent in boss mode."""
    mode = AgentMode(args.mode)

    agent = PiAgentBoss(
        ollama_base_url=args.ollama_url,
        router_api_url=args.router_url,
        mode=mode,
        state_dir=args.state_dir,
        mandatory_benchmark_categories=args.categories.split(',') if args.categories else None,
        discovery_interval=args.discovery_interval,
        health_check_interval=args.health_interval,
        auto_optimize_routing=args.auto_optimize,
        auto_manage_pool=args.auto_manage,
        max_disk_size_gb=args.max_disk_size,
        disk_cleanup_threshold=args.cleanup_threshold,
        external_api_config=args.external_api_config,
    )

    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("\nShutting down Pi Agent...")
        agent.stop()
    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        sys.exit(1)


async def show_dashboard(args):
    """Show current agent dashboard."""
    agent = PiAgentBoss(
        ollama_base_url=args.ollama_url,
        router_api_url=args.router_url,
        state_dir=args.state_dir,
    )

    # Load state
    agent._load_state()

    dashboard = await agent.get_dashboard()

    print("\n" + "="*70)
    print(" PI AGENT BOSS - DASHBOARD")
    print("="*70)

    print(f"\n📊 MODE: {dashboard['mode'].upper()}")

    # Disk usage
    disk = dashboard['disk']
    usage_bar = "█" * int(disk['usage_percent'] / 5) + "░" * (20 - int(disk['usage_percent'] / 5))
    print(f"\n💾 Disk Usage:")
    print(f"   {disk['used_gb']:.2f}GB / {disk['max_gb']:.0f}GB ({disk['usage_percent']:.1f}%)")
    print(f"   [{usage_bar}]")
    print(f"   Free: {disk['free_gb']:.2f}GB | Models: {disk['model_count']}")

    models = dashboard['models']
    print(f"\n🤖 Models:")
    print(f"   Total: {models['total']}")
    print(f"   Benchmarked: {models['benchmarked']}")
    print(f"   In Pool: {models['in_pool']}")
    print(f"   Loaded: {models['loaded']}")

    print(f"\n📈 Model Performance:")
    for detail in dashboard['model_details']:
        print(f"   {detail['name']:25} | Score: {detail['benchmark_score']:8} | "
              f"Queries: {detail['queries']:4} | Latency: {detail['avg_latency']:8} | "
              f"Size: {detail['disk_size_gb']}")

    print(f"\n🎯 Routing Recommendations:")
    for category, model in dashboard['routing_recommendations'].items():
        print(f"   {category:15} → {model}")

    metrics = dashboard['routing_metrics']
    print(f"\n📊 Routing Metrics:")
    print(f"   Total Queries: {metrics['total_queries']}")
    print(f"   Auto-Routed: {metrics['routed_by_auto']}")
    print(f"   Manual Routes: {metrics['routed_by_manual']}")
    print(f"   Avg Latency: {metrics['avg_latency_ms']:.0f}ms")
    print(f"   Success Rate: {metrics['success_rate']:.1%}")

    print("\n" + "="*70 + "\n")


async def benchmark_model(args):
    """Force benchmark a specific model."""
    agent = PiAgentBoss(
        ollama_base_url=args.ollama_url,
        router_api_url=args.router_url,
        state_dir=args.state_dir,
        mode=AgentMode.BOSS,
    )

    # Load state
    agent._load_state()

    # Register model if not known
    if args.model not in agent.known_models:
        await agent._register_model(args.model)

    print(f"\n🚀 Running mandatory benchmark for: {args.model}\n")

    await agent._run_benchmark(args.model)

    status = agent.known_models.get(args.model)
    if status and status.benchmark_score:
        print(f"\n✓ Benchmark complete: {status.benchmark_score:.2%}")
    else:
        print(f"\n✗ Benchmark failed")

    agent._save_state()


async def list_models(args):
    """List all known models and their status."""
    agent = PiAgentBoss(
        ollama_base_url=args.ollama_url,
        router_api_url=args.router_url,
        state_dir=args.state_dir,
    )

    agent._load_state()

    print("\n" + "="*70)
    print(" KNOWN MODELS")
    print("="*70 + "\n")

    if not agent.known_models:
        print("No models known yet. Run the agent to discover models.\n")
        return

    for model_name, status in sorted(agent.known_models.items()):
        print(f"📦 {model_name}")
        print(f"   In Pool: {status.in_pool}")
        print(f"   Loaded: {status.loaded}")
        print(f"   Benchmark Score: {f'{status.benchmark_score:.2%}' if status.benchmark_score else 'Not benchmarked'}")
        print(f"   Queries Handled: {status.queries_handled}")
        print(f"   Avg Latency: {status.avg_latency_ms:.0f}ms")
        print()

    print("="*70 + "\n")


async def run_discovery(args):
    """Run model discovery and report findings."""
    import httpx

    print("\n🔍 Discovering Ollama models...\n")

    agent = PiAgentBoss(
        ollama_base_url=args.ollama_url,
        router_api_url=args.router_url,
        state_dir=args.state_dir,
    )

    # Discover models
    await agent._discover_ollama_models()

    print(f"✓ Discovery complete: {len(agent.known_models)} models found\n")

    # List discovered models
    for model_name in sorted(agent.known_models.keys()):
        status = agent.known_models[model_name]
        print(f"  • {model_name:30} | {'✓ New' if not status.benchmark_score else '✓ Known'}")

    agent._save_state()
    print()


async def disk_report(args):
    """Show detailed disk usage report."""
    agent = PiAgentBoss(
        ollama_base_url=args.ollama_url,
        router_api_url=args.router_url,
        state_dir=args.state_dir,
    )

    agent._load_state()

    report = await agent.get_disk_report()

    print("\n" + "="*70)
    print(" DISK USAGE REPORT")
    print("="*70 + "\n")

    disk = report['disk_usage']
    print(f"💾 Ollama Models Directory:")
    print(f"   Path: {agent.ollama_models_path}")
    print(f"   Used: {disk['ollama_models_size_gb']:.2f}GB / {disk['max_size_gb']:.0f}GB")
    print(f"   Free: {disk['free_gb']:.2f}GB")
    print(f"   Usage: {disk['usage_percent']:.1f}%")
    print(f"   Models: {disk['model_count']}")
    print(f"   Cleanup Threshold: {report['cleanup_threshold']:.0f}%")

    usage_bar = "█" * int(disk['usage_percent'] / 5) + "░" * (20 - int(disk['usage_percent'] / 5))
    print(f"   [{usage_bar}]\n")

    print(f"📦 Model Sizes:")
    for model in report['models']:
        recommended = " ⭐" if model['recommended'] else ""
        loaded = " 📥" if model['loaded'] else ""
        print(f"   {model['name']:30} | {model['size_gb']:>8} | "
              f"Score: {model['benchmark_score']:8} | "
              f"Priority: {model['priority']:3}{recommended}{loaded}")

    print("\n" + "="*70)
    print("\nLegend:")
    print("  ⭐ = Recommended for routing")
    print("  📥 = Currently loaded")
    print("  Priority = Lower value = higher removal priority")
    print("\n" + "="*70 + "\n")


async def cleanup_models(args):
    """Force cleanup of low-priority models."""
    agent = PiAgentBoss(
        ollama_base_url=args.ollama_url,
        router_api_url=args.router_url,
        state_dir=args.state_dir,
        mode=AgentMode.BOSS,
    )

    agent._load_state()

    print("\n🧹 Starting model cleanup...\n")

    disk_usage = await agent._get_disk_usage()

    print(f"Current disk usage: {disk_usage.ollama_models_size_gb:.2f}GB / {disk_usage.max_size_gb:.0f}GB")
    print(f"Cleanup will target low-priority models\n")

    await agent._cleanup_models(disk_usage)

    # Show new usage
    new_disk = await agent._get_disk_usage()
    print(f"\n✓ Cleanup complete!")
    print(f"New disk usage: {new_disk.ollama_models_size_gb:.2f}GB / {new_disk.max_size_gb:.0f}GB")
    print(f"Freed: {disk_usage.ollama_models_size_gb - new_disk.ollama_models_size_gb:.2f}GB\n")


async def routing_report(args):
    """Show routing comparison report."""
    import json

    agent = PiAgentBoss(
        ollama_base_url=args.ollama_url,
        router_api_url=args.router_url,
        state_dir=args.state_dir,
    )

    agent._load_state()

    report_file = agent.state_dir / "routing_comparison_report.json"

    if not report_file.exists():
        print("\n❌ No routing comparison report found.")
        print("   Run the agent first to generate benchmarks:\n")
        print("     python scripts/pi_agent.py start\n")
        return

    with open(report_file, 'r') as f:
        report = json.load(f)

    print("\n" + "="*70)
    print(" ROUTING COMPARISON REPORT")
    print("="*70)
    print(f"\nGenerated: {report['timestamp']}\n")

    # Auto-routing results
    print("🔄 AUTO-ROUTING PERFORMANCE:")
    print("-" * 70)
    for category, result in report['auto_routing_results'].items():
        print(f"\n  {category.upper()}:")
        print(f"    Score: {result['score']:.2%}")
        print(f"    Avg Latency: {result['avg_latency']:.0f}ms")
        print(f"    Queries: {result['queries']}")
        print(f"    Model Selection: {result['model_selection']}")

    # Model benchmarks
    print("\n\n📊 MODEL BENCHMARKS:")
    print("-" * 70)
    for model, data in report['model_benchmarks'].items():
        print(f"\n  {model}:")
        print(f"    Score: {data['score']:.2%}")
        print(f"    Avg Latency: {data['avg_latency']:.0f}ms")
        print(f"    Queries: {data['queries']}")

    # Classification accuracy
    if report.get('classification_accuracy'):
        print("\n\n🎯 CLASSIFICATION ACCURACY:")
        print("-" * 70)
        cls_acc = report['classification_accuracy']
        print(f"\n  Overall: {cls_acc['overall']:.2%}")

        print("\n  By Category:")
        for category, data in cls_acc['by_category'].items():
            print(f"    {category:12} | {data['accuracy']:.2%} ({data['correct']}/{data['total']})")
            print(f"                  Models: {data['model_usage']}")

    print("\n" + "="*70 + "\n")


async def update_fallback(args):
    """Force update of fallback chains."""
    agent = PiAgentBoss(
        ollama_base_url=args.ollama_url,
        router_api_url=args.router_url,
        state_dir=args.state_dir,
        mode=AgentMode.BOSS,
    )

    agent._load_state()

    print("\n🔧 Updating fallback chains based on benchmark results...\n")

    await agent._update_fallback_chains()

    print("✓ Fallback chains updated\n")


def main():
    parser = argparse.ArgumentParser(
        description="Pi Agent Boss - Manager of MoE Router Stack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  passive      - Monitor only, no changes
  advisory     - Make recommendations, wait for approval
  active       - Automatically optimize routing
  boss         - Full control: manage models, routing, benchmarks (default)

Examples:
  # Start agent in boss mode (default)
  python scripts/pi_agent.py start

  # Start in passive mode (monitor only)
  python scripts/pi_agent.py start --mode passive

  # Show dashboard
  python scripts/pi_agent.py dashboard

  # Benchmark a specific model
  python scripts/pi_agent.py benchmark qwen2.5-coder

  # List all known models
  python scripts/pi_agent.py list

  # Run model discovery
  python scripts/pi_agent.py discover

  # Show disk usage report
  python scripts/pi_agent.py disk

  # Cleanup low-priority models
  python scripts/pi_agent.py cleanup

  # Set custom disk size limit (100GB)
  python scripts/pi_agent.py start --max-disk-size 100

  # Show routing comparison report
  python scripts/pi_agent.py routing-report

  # Update fallback chains based on benchmarks
  python scripts/pi_agent.py update-fallback

  # Start with external API models for benchmarking
  python scripts/pi_agent.py start --external-api-config config/external_apis.yaml
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start Pi Agent')
    start_parser.add_argument('--mode', choices=['passive', 'advisory', 'active', 'boss'],
                             default='boss', help='Agent operating mode')
    start_parser.add_argument('--ollama-url', default='http://localhost:11434',
                             help='Ollama API URL')
    start_parser.add_argument('--router-url', default='http://localhost:8000',
                             help='Router API URL')
    start_parser.add_argument('--state-dir', default='pi_agent_state',
                             help='State directory')
    start_parser.add_argument('--categories',
                             help='Comma-separated mandatory benchmark categories')
    start_parser.add_argument('--discovery-interval', type=int, default=300,
                             help='Model discovery interval (seconds)')
    start_parser.add_argument('--health-interval', type=int, default=60,
                             help='Health check interval (seconds)')
    start_parser.add_argument('--max-disk-size', type=float, default=50.0,
                             help='Maximum disk size for Ollama models in GB (default: 50)')
    start_parser.add_argument('--cleanup-threshold', type=float, default=0.90,
                             help='Disk cleanup threshold (0-1, default: 0.90 = 90%%)')
    start_parser.add_argument('--no-auto-optimize', dest='auto_optimize',
                             action='store_false', default=True,
                             help='Disable auto routing optimization')
    start_parser.add_argument('--no-auto-manage', dest='auto_manage',
                             action='store_false', default=True,
                             help='Disable auto pool management')
    start_parser.add_argument('--external-api-config',
                             help='Path to external API configuration file (e.g., config/external_apis.yaml)')
    start_parser.set_defaults(func=run_agent)

    # Dashboard command
    dash_parser = subparsers.add_parser('dashboard', help='Show agent dashboard')
    dash_parser.add_argument('--ollama-url', default='http://localhost:11434')
    dash_parser.add_argument('--router-url', default='http://localhost:8000')
    dash_parser.add_argument('--state-dir', default='pi_agent_state')
    dash_parser.set_defaults(func=show_dashboard)

    # Benchmark command
    bench_parser = subparsers.add_parser('benchmark', help='Benchmark a specific model')
    bench_parser.add_argument('model', help='Model name to benchmark')
    bench_parser.add_argument('--ollama-url', default='http://localhost:11434')
    bench_parser.add_argument('--router-url', default='http://localhost:8000')
    bench_parser.add_argument('--state-dir', default='pi_agent_state')
    bench_parser.set_defaults(func=benchmark_model)

    # List command
    list_parser = subparsers.add_parser('list', help='List known models')
    list_parser.add_argument('--ollama-url', default='http://localhost:11434')
    list_parser.add_argument('--router-url', default='http://localhost:8000')
    list_parser.add_argument('--state-dir', default='pi_agent_state')
    list_parser.set_defaults(func=list_models)

    # Discover command
    disc_parser = subparsers.add_parser('discover', help='Run model discovery')
    disc_parser.add_argument('--ollama-url', default='http://localhost:11434')
    disc_parser.add_argument('--router-url', default='http://localhost:8000')
    disc_parser.add_argument('--state-dir', default='pi_agent_state')
    disc_parser.set_defaults(func=run_discovery)

    # Disk report command
    disk_parser = subparsers.add_parser('disk', help='Show disk usage report')
    disk_parser.add_argument('--ollama-url', default='http://localhost:11434')
    disk_parser.add_argument('--router-url', default='http://localhost:8000')
    disk_parser.add_argument('--state-dir', default='pi_agent_state')
    disk_parser.set_defaults(func=disk_report)

    # Cleanup command
    clean_parser = subparsers.add_parser('cleanup', help='Cleanup low-priority models')
    clean_parser.add_argument('--ollama-url', default='http://localhost:11434')
    clean_parser.add_argument('--router-url', default='http://localhost:8000')
    clean_parser.add_argument('--state-dir', default='pi_agent_state')
    clean_parser.set_defaults(func=cleanup_models)

    # Routing report command
    routing_parser = subparsers.add_parser('routing-report', help='Show routing comparison report')
    routing_parser.add_argument('--ollama-url', default='http://localhost:11434')
    routing_parser.add_argument('--router-url', default='http://localhost:8000')
    routing_parser.add_argument('--state-dir', default='pi_agent_state')
    routing_parser.set_defaults(func=routing_report)

    # Update fallback command
    fallback_parser = subparsers.add_parser('update-fallback', help='Update fallback chains')
    fallback_parser.add_argument('--ollama-url', default='http://localhost:11434')
    fallback_parser.add_argument('--router-url', default='http://localhost:8000')
    fallback_parser.add_argument('--state-dir', default='pi_agent_state')
    fallback_parser.set_defaults(func=update_fallback)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Run command
    if args.command == 'start':
        asyncio.run(args.func(args))
    elif args.command == 'dashboard':
        asyncio.run(args.func(args))
    elif args.command == 'benchmark':
        asyncio.run(args.func(args))
    elif args.command == 'list':
        asyncio.run(args.func(args))
    elif args.command == 'discover':
        asyncio.run(args.func(args))
    elif args.command == 'disk':
        asyncio.run(args.func(args))
    elif args.command == 'cleanup':
        asyncio.run(args.func(args))
    elif args.command == 'routing-report':
        asyncio.run(args.func(args))
    elif args.command == 'update-fallback':
        asyncio.run(args.func(args))


if __name__ == "__main__":
    main()
