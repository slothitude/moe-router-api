#!/usr/bin/env python3
"""Direct test of NVIDIA API to find correct endpoint."""

import asyncio
import httpx
import json
import os
import sys

# Set UTF-8 for Windows
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Set API key
os.environ["NVIDIA_API_KEY"] = "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"

async def test_nvidia_endpoints():
    """Test different NVIDIA API endpoints."""

    api_key = os.getenv("NVIDIA_API_KEY")
    print(f"API Key: {api_key[:20]}...")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta/llama-3.1-405b-instruct",
        "messages": [{"role": "user", "content": "What is the capital of France? Answer in one word."}],
        "max_tokens": 50,
        "temperature": 0.7
    }

    # Test different endpoints
    endpoints = [
        "https://integrate.api.nvidia.com/v1/chat/completions",
        "https://integrate.api.nvidia.com/v1/chat/nvapi-meta/llama-3.1-405b-instruct/generate",
    ]

    for endpoint in endpoints:
        print(f"\n{'='*70}")
        print(f"Testing endpoint: {endpoint}")
        print('='*70)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(endpoint, headers=headers, json=payload)

                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✓ SUCCESS!")
                    print(f"Response: {json.dumps(data, indent=2)[:500]}")
                    return endpoint
                else:
                    print(f"✗ FAILED")
                    print(f"Response: {response.text[:500]}")

        except Exception as e:
            print(f"✗ ERROR: {e}")

    return None


if __name__ == "__main__":
    result = asyncio.run(test_nvidia_endpoints())

    if result:
        print(f"\n✓ Working endpoint found: {result}")
    else:
        print("\n✗ No working endpoint found")
