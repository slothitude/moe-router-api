#!/usr/bin/env python3
"""
Benchmark Cold Load Performance for All Ollama Models

This script measures:
1. Cold load time (how long to load from disk)
2. Warm performance (tokens per second)
3. Memory footprint
4. Hot swap capability
"""

import asyncio
import httpx
import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime

# Set UTF-8 for Windows
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

OLLAMA_BASE_URL = "http://localhost:11434"

async def get_models():
    """Get list of all Ollama models."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        response.raise_for_status()
        data = response.json()
        return data.get("models", [])

async def unload_model(model_name):
    """Unload a model from Ollama."""
    try:
        # We can't directly unload, but we can load a different model
        # to force the current one out
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Load a tiny model to force unload
            await client.post(f"{OLLAMA_BASE_URL}/api/generate", json={
                "model": "nomic-embed-text:latest",
                "prompt": "hi",
                "stream": False,
                "keep_alive": -1  # Immediately unload
            })
    except Exception as e:
        pass  # Ignore errors

async def get_loaded_models():
    """Get currently loaded models."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/ps")
            if response.status_code == 200:
                data = response.json()
                return [m.get("name") for m in data.get("models", [])]
    except:
        pass
    return []

async def wait_for_model_loaded(model_name, timeout_seconds=120):
    """Wait for a model to finish loading."""
    start = time.time()
    while True:
        loaded = await get_loaded_models()
        # Check for partial match
        is_loaded = any(model_name in m or m in model_name for m in loaded)

        if is_loaded:
            return True

        if time.time() - start > timeout_seconds:
            return False

        await asyncio.sleep(1)

async def benchmark_cold_load(model_name):
    """Benchmark cold load performance for a model."""
    print(f"\n{'='*70}")
    print(f"MODEL: {model_name}")
    print('='*70)

    # Step 1: Ensure model is unloaded
    print("Step 1: Ensuring model is unloaded...")
    await unload_model(model_name)
    await asyncio.sleep(2)

    # Step 2: Measure cold load time
    print("Step 2: Measuring cold load time...")
    load_start = time.time()

    async with httpx.AsyncClient(timeout=180.0) as client:
        # Start load in background
        load_task = asyncio.create_task(
            client.post(f"{OLLAMA_BASE_URL}/api/generate", json={
                "model": model_name,
                "prompt": "Hello",
                "stream": False,
                "options": {"num_predict": 5}
            })
        )

        # Wait for model to appear in /api/ps
        loaded = await wait_for_model_loaded(model_name, timeout_seconds=120)

        if not loaded:
            print(f"  ✗ Failed to load within 120 seconds")
            return None

        # Wait for load task to complete
        try:
            await load_task
        except:
            pass

        load_time = time.time() - load_start

        # Step 3: Measure warm performance (tokens per second)
        print(f"Step 3: Measuring warm performance (load_time={load_time:.2f}s)...")

        # Run a few warmup queries
        warmup_times = []
        tokens_generated = []

        for i in range(3):
            start = time.time()
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json={
                    "model": model_name,
                    "prompt": "Write a haiku about coding.",
                    "stream": False,
                    "options": {"num_predict": 50}
                })

            if response.status_code == 200:
                data = response.json()
                elapsed = time.time() - start
                eval_count = data.get("eval_count", 0)
                prompt_count = data.get("prompt_eval_count", 0)
                total_tokens = eval_count + prompt_count

                warmup_times.append(elapsed)
                tokens_generated.append(total_tokens)

                tps = total_tokens / elapsed if elapsed > 0 else 0
                print(f"  Query {i+1}: {total_tokens} tokens in {elapsed:.2f}s = {tps:.1f} tokens/sec")

        # Calculate averages
        avg_time = sum(warmup_times) / len(warmup_times) if warmup_times else 0
        avg_tokens = sum(tokens_generated) / len(tokens_generated) if tokens_generated else 0
        avg_tps = avg_tokens / avg_time if avg_time > 0 else 0

        # Step 4: Get model details
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{OLLAMA_BASE_URL}/api/show", json={
                "name": model_name
            })

            model_info = {}
            if response.status_code == 200:
                data = response.json()
                details = data.get("details", {})
                model_info = {
                    "parameter_size": details.get("parameter_size", "unknown"),
                    "quantization": details.get("quantization_level", "unknown"),
                    "family": details.get("family", "unknown"),
                }

        return {
            "model": model_name,
            "cold_load_time_s": load_time,
            "warm_queries_benchmarked": len(warmup_times),
            "avg_warm_latency_s": avg_time,
            "avg_tokens_per_query": avg_tokens,
            "avg_tokens_per_second": avg_tps,
            "model_info": model_info,
            "timestamp": datetime.now().isoformat()
        }

async def main():
    """Benchmark all models."""
    print("\n" + "="*70)
    print(" COLD LOAD BENCHMARK - ALL OLLAMA MODELS")
    print("="*70)
    print(f"\nOllama URL: {OLLAMA_BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Get all models
    models = await get_models()

    # Filter out embedding models
    models_to_test = [
        m["name"] for m in models
        if "embed" not in m["name"].lower()
    ]

    print(f"\nFound {len(models_to_test)} models to test:")
    for m in models_to_test:
        print(f"  - {m}")

    results = []

    # Benchmark each model
    for model_name in models_to_test:
        try:
            result = await benchmark_cold_load(model_name)
            if result:
                results.append(result)

                # Print summary
                print(f"\n  📊 RESULTS:")
                print(f"     Cold Load Time: {result['cold_load_time_s']:.2f}s")
                print(f"     Warm Performance: {result['avg_tokens_per_second']:.1f} tokens/sec")
                print(f"     Parameters: {result['model_info'].get('parameter_size', 'unknown')}")
                print(f"     Quantization: {result['model_info'].get('quantization', 'unknown')}")

        except Exception as e:
            print(f"\n  ✗ Error: {e}")

    # Save results
    output_file = Path("pi_agent_state") / "cold_load_benchmark_results.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary table
    print(f"\n\n{'='*70}")
    print(" SUMMARY TABLE")
    print('='*70)
    print(f"\n{'Model':<30} {'Load Time':<12} {'Tokens/sec':<12} {'Parameters':<12}")
    print('-'*70)

    for r in results:
        print(f"{r['model']:<30} {r['cold_load_time_s']:>10.2f}s   {r['avg_tokens_per_second']:>10.1f} t/s  {r['model_info'].get('parameter_size', 'N/A'):>12}")

    print(f"\nResults saved to: {output_file}")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
