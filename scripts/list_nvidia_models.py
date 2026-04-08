#!/usr/bin/env python3
"""List all available NVIDIA NIM models."""

import asyncio
import httpx
import json
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


async def list_nvidia_models():
    """Get list of all available NVIDIA NIM models."""

    api_key = os.getenv("NVIDIA_API_KEY")
    print(f"Using API Key: {api_key[:20]}...\n")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Try to get models from the catalog
    endpoints = [
        "https://integrate.api.nvidia.com/v1/models",
        "https://integrate.api.nvidia.com/v2/models",
    ]

    for endpoint in endpoints:
        print(f"Trying endpoint: {endpoint}")
        print("="*70)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(endpoint, headers=headers)
                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"\n✓ SUCCESS! Found models:\n")

                    # Pretty print the response
                    print(json.dumps(data, indent=2)[:2000])

                    # Extract model list if available
                    if "data" in data:
                        models = data["data"]
                        print(f"\n\n{'='*70}")
                        print(f"AVAILABLE MODELS ({len(models)} total)")
                        print('='*70 + "\n")

                        for model in models:
                            model_id = model.get("id", "unknown")
                            model_name = model.get("object", "model")
                            print(f"📦 {model_id}")
                            print(f"   Type: {model_name}")
                            if "owned_by" in model:
                                print(f"   Owner: {model['owned_by']}")
                            print()

                    return endpoint
                else:
                    print(f"✗ FAILED: {response.text[:500]}")

        except Exception as e:
            print(f"✗ ERROR: {e}")

        print()

    # If catalog endpoints don't work, try known models
    print("\n" + "="*70)
    print(" TESTING KNOWN NVIDIA MODELS")
    print("="*70 + "\n")

    known_models = [
        "meta/llama-3.1-405b-instruct",
        "meta/llama-3.1-70b-instruct",
        "meta/llama-3.1-8b-instruct",
        "meta/llama-3.2-3b-instruct",
        "meta/llama-3.2-1b-instruct",
        "mistralai/mistral-7b-instruct-v0.3",
        "mistralai/mixtral-8x7b-instruct-v0.1",
        "google/gemma-7b",
        "google/gemma-2-27b-it",
        "microsoft/phi-3-mini-128k-instruct",
        "nvidia/llama-3.1-nemotron-70b-instruct",
    ]

    available_models = []

    for model_name in known_models:
        try:
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    print(f"✓ {model_name}")
                    available_models.append(model_name)
                elif response.status_code == 404:
                    print(f"✗ {model_name} (not found)")
                elif response.status_code == 400:
                    print(f"? {model_name} (may be available)")
                    available_models.append(model_name)
                else:
                    print(f"✗ {model_name} (error: {response.status_code})")

        except Exception as e:
            print(f"✗ {model_name} (timeout)")

    print(f"\n\n{'='*70}")
    print(f"AVAILABLE MODELS ({len(available_models)} found)")
    print('='*70 + "\n")

    for model in available_models:
        print(f"  - {model}")

    return available_models


if __name__ == "__main__":
    asyncio.run(list_nvidia_models())
