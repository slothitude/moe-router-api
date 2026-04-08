#!/usr/bin/env python3
"""Discover and list all models (local + external)."""

import asyncio
import os
import sys
from pathlib import Path

# Set UTF-8 for Windows
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Set API key
os.environ["NVIDIA_API_KEY"] = "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"

sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark.pi_agent_boss import PiAgentBoss


async def main():
    """Discover and list all models."""
    print("\n" + "="*70)
    print(" DISCOVERING ALL MODELS (LOCAL + EXTERNAL)")
    print("="*70 + "\n")

    # Initialize agent with external API config
    agent = PiAgentBoss(
        ollama_base_url="http://localhost:11434",
        router_api_url="http://localhost:8000",
        state_dir="pi_agent_state",
        external_api_config="config/external_apis.yaml"
    )

    # Load state
    agent._load_state()

    # Discover local models
    print("Discovering local Ollama models...")
    await agent._discover_ollama_models()

    # Discover external models
    print("\nDiscovering external API models...")
    await agent._discover_external_models()

    # List all models
    print("\n" + "="*70)
    print(" ALL AVAILABLE MODELS")
    print("="*70 + "\n")

    local_count = 0
    external_count = 0

    for model_name, status in sorted(agent.known_models.items()):
        if model_name.startswith("external/"):
            external_count += 1
            print(f"☁️  {status.name}")
            print(f"    Location: {status.location}")
            print(f"    Status: {'Loaded' if status.loaded else 'Not Loaded'}")
            print(f"    Benchmark: {f'{status.benchmark_score:.1%}' if status.benchmark_score else 'Not benchmarked'}")
        else:
            local_count += 1
            print(f"🖥️  {status.name}")
            print(f"    Location: {status.location or 'local'}")
            print(f"    In Pool: {status.in_pool}")
            print(f"    Loaded: {status.loaded}")
            print(f"    Benchmark: {f'{status.benchmark_score:.1%}' if status.benchmark_score else 'Not benchmarked'}")
        print()

    print("="*70)
    print(f"TOTAL: {local_count} local models + {external_count} external models = {len(agent.known_models)} models")
    print("="*70 + "\n")

    # Save state
    agent._save_state()


if __name__ == "__main__":
    asyncio.run(main())
