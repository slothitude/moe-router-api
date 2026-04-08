#!/usr/bin/env python3
"""
Test script for MoE Router API.

Tests the API endpoints to verify functionality.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx


BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


async def test_root():
    """Test root endpoint."""
    print_section("Testing Root Endpoint")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")


async def test_health():
    """Test health check endpoint."""
    print_section("Testing Health Check")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")


async def test_list_models():
    """Test list models endpoint."""
    print_section("Testing List Models")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/models")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total models: {data['total']}")
        for model in data['models']:
            print(f"  - {model['name']}: {model['strength']}")


async def test_pool_status():
    """Test pool status endpoint."""
    print_section("Testing Model Pool Status")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/models/pool")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")


async def test_query():
    """Test query endpoint."""
    print_section("Testing Query Endpoint")

    async with httpx.AsyncClient(timeout=120.0) as client:
        query = "What is the capital of France?"

        print(f"Query: {query}")

        start_time = time.time()
        response = await client.post(
            f"{BASE_URL}/api/v1/query",
            json={"query": query}
        )
        elapsed = time.time() - start_time

        print(f"Status: {response.status_code}")
        print(f"Time: {elapsed:.2f}s")

        if response.status_code == 200:
            data = response.json()
            print(f"Model used: {data['model_used']}")
            print(f"Query type: {data['routing_decision']['query_type']}")
            print(f"Tokens: {data['tokens_generated']}")
            print(f"From cache: {data['from_cache']}")
            print(f"Response: {data['response'][:100]}...")


async def test_code_query():
    """Test code query routing."""
    print_section("Testing Code Query Routing")

    async with httpx.AsyncClient(timeout=120.0) as client:
        query = "Debug this Python function: def add(a, b): return a - b"

        print(f"Query: {query}")

        start_time = time.time()
        response = await client.post(
            f"{BASE_URL}/api/v1/query",
            json={"query": query}
        )
        elapsed = time.time() - start_time

        print(f"Status: {response.status_code}")
        print(f"Time: {elapsed:.2f}s")

        if response.status_code == 200:
            data = response.json()
            print(f"Model used: {data['model_used']}")
            print(f"Query type: {data['routing_decision']['query_type']}")
            print(f"Routing reasoning: {data['routing_decision']['reasoning']}")


async def test_cache():
    """Test caching functionality."""
    print_section("Testing Cache")

    async with httpx.AsyncClient(timeout=120.0) as client:
        query = "What is quantum computing?"

        # First request
        print("First request (cache miss expected):")
        start_time = time.time()
        response1 = await client.post(
            f"{BASE_URL}/api/v1/query",
            json={"query": query}
        )
        time1 = time.time() - start_time

        if response1.status_code == 200:
            data1 = response1.json()
            print(f"  Time: {time1:.2f}s")
            print(f"  From cache: {data1['from_cache']}")

        # Second request (should hit cache)
        print("\nSecond request (cache hit expected):")
        start_time = time.time()
        response2 = await client.post(
            f"{BASE_URL}/api/v1/query",
            json={"query": query}
        )
        time2 = time.time() - start_time

        if response2.status_code == 200:
            data2 = response2.json()
            print(f"  Time: {time2:.2f}s")
            print(f"  From cache: {data2['from_cache']}")
            print(f"  Speedup: {time1/time2:.1f}x")


async def test_metrics():
    """Test metrics endpoint."""
    print_section("Testing Metrics")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/metrics")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")


async def test_cache_stats():
    """Test cache stats endpoint."""
    print_section("Testing Cache Stats")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/cache/stats")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("MoE Router API - Test Suite")
    print("=" * 60)
    print(f"\nTarget: {BASE_URL}")
    print("Make sure the API is running before starting tests.")

    await asyncio.sleep(2)

    try:
        # Run tests
        await test_root()
        await test_health()
        await test_list_models()
        await test_pool_status()
        await test_query()
        await test_code_query()
        await test_cache()
        await test_metrics()
        await test_cache_stats()

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except httpx.ConnectError:
        print("\nError: Could not connect to API.")
        print("Please start the API first:")
        print("  Windows: scripts\\start.bat")
        print("  Linux/Mac: ./scripts/start.sh")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
