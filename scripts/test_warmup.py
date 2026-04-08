"""Test script to verify model warmup approach solves timeout issues."""

import asyncio
import httpx
import time

async def warmup_and_test(model: str):
    """Warm up model then test various queries."""
    print(f"\n{'='*60}")
    print(f"Testing {model}")
    print(f"{'='*60}\n")

    async with httpx.AsyncClient(timeout=300.0) as client:
        # Step 1: Warmup
        print("Step 1: Warming up model...")
        start = time.time()
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/query",
                json={
                    "query": "OK",
                    "model": model,
                    "use_cache": False,
                    "options": {"num_predict": 5}
                }
            )
            warmup_time = time.time() - start
            print(f"  Warmup: {warmup_time:.2f}s")
        except Exception as e:
            print(f"  Warmup failed: {e}")
            return

        # Step 2: Test queries
        queries = [
            ("Factual", "What is the capital of France?"),
            ("Code", "Write a hello world in python"),
            ("Document", "Write a brief project update email"),
            ("Agentic", "Plan a 2-day trip. Keep it brief.")
        ]

        print("\nStep 2: Testing queries...")
        for qtype, query in queries:
            try:
                start = time.time()
                response = await client.post(
                    "http://localhost:8000/api/v1/query",
                    json={
                        "query": query,
                        "model": model,
                        "use_cache": False
                    }
                )
                elapsed = time.time() - start

                if response.status_code == 200:
                    data = response.json()
                    tokens = data.get("tokens_generated", 0)
                    print(f"  {qtype}: {elapsed:.2f}s ({tokens} tokens, {tokens/elapsed:.1f} t/s)")
                else:
                    print(f"  {qtype}: FAILED ({response.status_code})")
            except Exception as e:
                print(f"  {qtype}: ERROR - {str(e)[:50]}")

async def main():
    models = ["phi3:mini", "qwen3:4b", "gemma4:e4b"]

    for model in models:
        try:
            await warmup_and_test(model)
            await asyncio.sleep(2)  # Brief pause between models
        except Exception as e:
            print(f"Error testing {model}: {e}")

if __name__ == "__main__":
    print("Model Warmup Test")
    print("="*60)
    asyncio.run(main())
