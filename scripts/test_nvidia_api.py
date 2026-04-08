#!/usr/bin/env python3
"""Test NVIDIA API connection with provided API key."""

import asyncio
import os
import sys
from pathlib import Path

# Set UTF-8 for Windows
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set API key
os.environ["NVIDIA_API_KEY"] = "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"

from models.external_api_client import ExternalAPIClient


async def test_nvidia_api():
    """Test NVIDIA API connection with a real query."""
    print("\n" + "="*70)
    print(" TESTING NVIDIA API CONNECTION")
    print("="*70 + "\n")

    # Initialize client
    print("1. Initializing ExternalAPIClient...")
    client = ExternalAPIClient("config/external_apis.yaml")

    models = client.get_models()
    if not models:
        print("   ✗ No models found - check API key")
        return

    print(f"   ✓ Found {len(models)} model(s)")

    # Get the NVIDIA model
    model_id = list(models.keys())[0]
    model_config = models[model_id]

    print(f"\n2. Testing model: {model_config.display_name}")
    print(f"   ID: {model_id}")
    print(f"   API: {model_config.api}")
    print(f"   Categories: {', '.join(model_config.categories)}")

    # Test query
    print(f"\n3. Sending test query...")
    test_query = "What is the capital of France? Answer in one word."
    print(f"   Query: {test_query}")

    try:
        messages = [{"role": "user", "content": test_query}]
        response = await client.query(
            model_id,
            messages,
            temperature=0.7,
            max_tokens=100
        )

        print(f"\n   ✓ Response received!")
        print(f"   Content: {response['content'][:200]}")
        print(f"   Latency: {response['latency_ms']:.0f}ms")
        print(f"   Usage: {response['usage']}")

    except Exception as e:
        print(f"\n   ✗ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Cleanup
    await client.close()

    print("\n" + "="*70)
    print(" ✓ NVIDIA API TEST SUCCESSFUL")
    print("="*70 + "\n")

    print("Next steps:")
    print("1. Start Pi Agent Boss:")
    print("   set NVIDIA_API_KEY=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")
    print("   python scripts/pi_agent.py start --external-api-config config/external_apis.yaml")
    print()


if __name__ == "__main__":
    asyncio.run(test_nvidia_api())
