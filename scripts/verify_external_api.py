#!/usr/bin/env python3
"""Verification script for external API integration.

This script tests the external API integration components to ensure
everything is working correctly.
"""

import asyncio
import sys
import os
from pathlib import Path

# Set UTF-8 for Windows
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.external_api_client import ExternalAPIClient
from models.model_specs import ModelRegistry


async def test_external_api_client():
    """Test external API client initialization and model discovery."""
    print("\n" + "="*70)
    print(" TESTING EXTERNAL API CLIENT")
    print("="*70 + "\n")

    # Test 1: Initialize client
    print("1. Initializing ExternalAPIClient...")
    try:
        client = ExternalAPIClient("config/external_apis.yaml")
        print(f"   ✓ Client initialized successfully")
    except Exception as e:
        print(f"   ✗ Failed to initialize: {e}")
        return False

    # Test 2: Check models
    print("\n2. Checking available models...")
    models = client.get_models()
    if models:
        print(f"   ✓ Found {len(models)} external model(s):")
        for model_id, config in models.items():
            print(f"     - {config.display_name}")
            print(f"       ID: {model_id}")
            print(f"       Categories: {', '.join(config.categories)}")
            print(f"       Priority: {config.priority}")
    else:
        print("   ⚠ No external models found")
        print("   This is expected if NVIDIA_API_KEY is not set")

    # Test 3: Check model registry
    print("\n3. Checking model registry...")
    for model_id, config in models.items():
        # Register the model
        ModelRegistry.register_external_model(model_id, {
            "display_name": config.display_name,
            "categories": config.categories,
            "specialization": config.specialization,
            "priority": config.priority,
            "api": config.api
        })

        # Verify it's in the registry
        if model_id in ModelRegistry.MODELS:
            spec = ModelRegistry.MODELS[model_id]
            print(f"   ✓ Model registered: {spec.name}")
            print(f"     Strength: {spec.strength}")
            print(f"     Query types: {[qt.value for qt in spec.query_types]}")
        else:
            print(f"   ✗ Model not in registry: {model_id}")

    # Test 4: Check API key
    print("\n4. Checking API key configuration...")
    import os
    api_key = os.getenv("NVIDIA_API_KEY")
    if api_key:
        print(f"   ✓ NVIDIA_API_KEY is set (length: {len(api_key)})")
        if api_key.startswith("nvapi-"):
            print(f"   ✓ API key format looks correct")
        else:
            print(f"   ⚠ API key format may be incorrect (should start with 'nvapi-')")
    else:
        print("   ⚠ NVIDIA_API_KEY not set")
        print("   Set it with: export NVIDIA_API_KEY='your-key'")

    # Cleanup
    await client.close()

    print("\n" + "="*70)
    print(" EXTERNAL API CLIENT TEST COMPLETE")
    print("="*70 + "\n")

    return True


def test_config_file():
    """Test configuration file exists and is valid."""
    print("\n" + "="*70)
    print(" TESTING CONFIGURATION FILE")
    print("="*70 + "\n")

    config_path = Path("config/external_apis.yaml")

    if not config_path.exists():
        print(f"   ✗ Config file not found: {config_path}")
        return False

    print(f"   ✓ Config file exists: {config_path}")

    # Try to load it
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        if 'external_apis' in config:
            print(f"   ✓ Config has 'external_apis' section")

            for api_name, api_config in config['external_apis'].items():
                print(f"\n   API: {api_name}")
                print(f"     Enabled: {api_config.get('enabled', False)}")
                print(f"     Base URL: {api_config.get('base_url', 'N/A')}")
                print(f"     Models: {len(api_config.get('models', []))}")

                if api_config.get('enabled'):
                    for model in api_config.get('models', []):
                        print(f"       - {model.get('display_name', model['name'])}")
        else:
            print(f"   ⚠ Config missing 'external_apis' section")

    except Exception as e:
        print(f"   ✗ Failed to load config: {e}")
        return False

    print("\n" + "="*70)
    print(" CONFIGURATION FILE TEST COMPLETE")
    print("="*70 + "\n")

    return True


def main():
    """Run all verification tests."""
    print("\n" + "="*70)
    print(" EXTERNAL API INTEGRATION VERIFICATION")
    print("="*70)

    # Test config file
    config_ok = test_config_file()

    # Test API client
    client_ok = asyncio.run(test_external_api_client())

    # Summary
    print("\n" + "="*70)
    print(" VERIFICATION SUMMARY")
    print("="*70)
    print(f"\nConfig File: {'✓ PASS' if config_ok else '✗ FAIL'}")
    print(f"API Client:  {'✓ PASS' if client_ok else '✗ FAIL'}")

    if config_ok and client_ok:
        print("\n✓ All tests passed!")
        print("\nNext steps:")
        print("1. Set NVIDIA_API_KEY environment variable")
        print("2. Run: python scripts/pi_agent.py start --external-api-config config/external_apis.yaml")
        print("3. Monitor logs for external model discovery")
    else:
        print("\n✗ Some tests failed. Please check the errors above.")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
