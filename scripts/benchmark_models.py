#!/usr/bin/env python3
"""
Model benchmarking utility.

Benchmarks all available models to update routing metrics.
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.ollama_client import OllamaClient


# Test queries for different scenarios
TEST_QUERIES = {
    "code": 'Debug this Python function: def add(a, b): return a - b',
    "simple": "What is the capital of France?",
    "creative": "Write a short story about a robot learning to paint",
    "analysis": "Analyze the themes of love and loss in classic literature"
}


async def benchmark_model(ollama: OllamaClient, model_name: str) -> Dict:
    """
    Benchmark a single model.

    Args:
        ollama: Ollama client
        model_name: Model to benchmark

    Returns:
        Dict with benchmark results
    """
    print(f"\nBenchmarking {model_name}...")

    results = {
        "model": model_name,
        "tests": {}
    }

    for test_name, query in TEST_QUERIES.items():
        try:
            print(f"  Running {test_name} test...")

            start_time = time.time()

            response = await ollama.generate(
                model=model_name,
                prompt=query,
                options={"num_predict": 100}
            )

            elapsed = time.time() - start_time

            # Extract metrics from response
            prompt_eval_count = response.get("prompt_eval_count", 0)
            eval_count = response.get("eval_count", 0)
            prompt_eval_duration = response.get("prompt_eval_duration", 0) / 1e9  # ns to s
            eval_duration = response.get("eval_duration", 0) / 1e9

            # Calculate speeds
            prompt_speed = prompt_eval_count / max(prompt_eval_duration, 0.001)
            gen_speed = eval_count / max(eval_duration, 0.001)

            results["tests"][test_name] = {
                "total_time": elapsed,
                "prompt_eval_count": prompt_eval_count,
                "eval_count": eval_count,
                "prompt_speed_tps": prompt_speed,
                "gen_speed_tps": gen_speed
            }

            print(f"    Time: {elapsed:.2f}s, Prompt: {prompt_speed:.0f} t/s, Gen: {gen_speed:.0f} t/s")

        except Exception as e:
            print(f"    Error: {e}")
            results["tests"][test_name] = {"error": str(e)}

    return results


async def main():
    """Main benchmark function."""
    print("=" * 60)
    print("MoE Router - Model Benchmarking Utility")
    print("=" * 60)

    # Initialize Ollama client
    ollama = OllamaClient(base_url="http://localhost:11434")

    # Check health
    if not await ollama.health_check():
        print("Error: Ollama is not available. Please start Ollama first.")
        return

    print("\nOllama is healthy")

    # Get available models
    available = await ollama.list_models()
    model_names = [m["name"] for m in available]

    print(f"\nFound {len(model_names)} models:")
    for name in model_names:
        print(f"  - {name}")

    # Benchmark each model
    all_results = []

    for model_name in model_names:
        results = await benchmark_model(ollama, model_name)
        all_results.append(results)

    # Print summary
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)

    for results in all_results:
        model = results["model"]
        print(f"\n{model}:")
        for test_name, test_results in results["tests"].items():
            if "error" not in test_results:
                print(f"  {test_name}:")
                print(f"    Total: {test_results['total_time']:.2f}s")
                print(f"    Prompt: {test_results['prompt_speed_tps']:.0f} t/s")
                print(f"    Gen: {test_results['gen_speed_tps']:.0f} t/s")
            else:
                print(f"  {test_name}: ERROR - {test_results['error']}")

    # Calculate averages
    print("\n" + "=" * 60)
    print("AVERAGE PERFORMANCE")
    print("=" * 60)

    for results in all_results:
        model = results["model"]

        # Calculate averages across successful tests
        successful_tests = [
            t for t in results["tests"].values()
            if "error" not in t
        ]

        if successful_tests:
            avg_total = sum(t["total_time"] for t in successful_tests) / len(successful_tests)
            avg_prompt = sum(t["prompt_speed_tps"] for t in successful_tests) / len(successful_tests)
            avg_gen = sum(t["gen_speed_tps"] for t in successful_tests) / len(successful_tests)

            print(f"\n{model}:")
            print(f"  Avg Total Time: {avg_total:.2f}s")
            print(f"  Avg Prompt Speed: {avg_prompt:.0f} t/s")
            print(f"  Avg Gen Speed: {avg_gen:.0f} t/s")

    print("\n" + "=" * 60)
    print("Benchmarking complete!")
    print("=" * 60)

    # Close Ollama client
    await ollama.__aexit__(None, None, None)


if __name__ == "__main__":
    asyncio.run(main())
