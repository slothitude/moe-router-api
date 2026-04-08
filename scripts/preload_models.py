#!/usr/bin/env python3
"""
Model preloading utility.

Preloads models into the model pool to reduce cold start time.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.ollama_client import OllamaClient
from core.model_pool import ModelPool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main preload function."""
    logger.info("Starting model preload...")

    # Initialize Ollama client
    ollama = OllamaClient(base_url="http://localhost:11434")

    # Check health
    if not await ollama.health_check():
        logger.error("Ollama is not available. Please start Ollama first.")
        return

    logger.info("Ollama is healthy")

    # Get available models
    available = await ollama.list_models()
    available_names = [m["name"] for m in available]
    logger.info(f"Available models: {available_names}")

    # Models to preload (from config)
    preload_models = [
        "qwen3:4b",
        "qwen2.5-coder",
        "llama3.1",
        "ministral-3"
    ]

    # Initialize model pool
    pool = ModelPool(
        gpu_capacity_mb=3500,
        ram_capacity_mb=20000,
        preload_models=preload_models
    )

    # Initialize pool (this loads the models)
    await pool.initialize(ollama)

    # Warm up models
    logger.info("Warming up models...")
    await pool.warmup_models()

    # Show status
    status = pool.get_status()
    logger.info(f"Model pool status: {status}")

    logger.info("Preload complete!")

    # Close Ollama client
    await ollama.__aexit__(None, None, None)


if __name__ == "__main__":
    asyncio.run(main())
