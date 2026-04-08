"""External API client for connecting Pi Agent to cloud AI models.

This module provides a client for querying external AI model APIs (NVIDIA NIM,
OpenAI, etc.) to benchmark and test the internal MOE router system.
"""

import httpx
import os
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ExternalModelConfig:
    """Configuration for an external model."""
    name: str
    display_name: str
    api: str
    base_url: str
    categories: List[str]
    specialization: str
    priority: int


class ExternalAPIClient:
    """Client for interacting with external AI model APIs.

    This client allows Pi Agent to query external models (NVIDIA NIM, OpenAI, etc.)
    for benchmarking and comparison with local Ollama models.
    """

    def __init__(self, config_path: str = "config/external_apis.yaml"):
        """Initialize the external API client.

        Args:
            config_path: Path to external API configuration YAML file
        """
        self.apis: Dict[str, Any] = {}
        self.models: Dict[str, ExternalModelConfig] = {}
        self.clients: Dict[str, httpx.AsyncClient] = {}
        self._load_config(config_path)

    def _load_config(self, config_path: str):
        """Load external API configurations from YAML file.

        Args:
            config_path: Path to configuration file
        """
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"No external API config found at {config_path}")
            return

        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

            for api_name, api_config in config.get('external_apis', {}).items():
                if not api_config.get('enabled', False):
                    logger.debug(f"Skipping disabled API: {api_name}")
                    continue

                api_key = os.getenv(api_config['api_key_env'])
                if not api_key:
                    logger.warning(f"No API key for {api_name} ({api_config['api_key_env']})")
                    continue

                # Create HTTP client for this API
                self.clients[api_name] = httpx.AsyncClient(
                    base_url=api_config['base_url'],
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=120.0
                )

                # Register models from this API
                for model in api_config.get('models', []):
                    model_id = f"external/{api_name}/{model['name']}"

                    self.models[model_id] = ExternalModelConfig(
                        name=model['name'],
                        display_name=model.get('display_name', model['name']),
                        api=api_name,
                        base_url=api_config['base_url'],
                        categories=model.get('categories', ['general']),
                        specialization=model.get('specialization', 'general'),
                        priority=model.get('priority', 50)
                    )

                logger.info(f"✓ Loaded external API: {api_name} ({len(api_config.get('models', []))} models)")

        except Exception as e:
            logger.error(f"Error loading external API config: {e}")

    def get_models(self) -> Dict[str, ExternalModelConfig]:
        """Get all available external models.

        Returns:
            Dict mapping model IDs to their configurations
        """
        return self.models

    def get_model(self, model_id: str) -> Optional[ExternalModelConfig]:
        """Get a specific model configuration.

        Args:
            model_id: External model ID (e.g., "external/nvidia_nim/model-name")

        Returns:
            ExternalModelConfig or None if not found
        """
        return self.models.get(model_id)

    def is_external_model(self, model_id: str) -> bool:
        """Check if a model ID is for an external API.

        Args:
            model_id: Model ID to check

        Returns:
            True if this is an external model
        """
        return model_id.startswith("external/")

    async def query(self, model_id: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Query an external model.

        Args:
            model_id: External model ID (e.g., "external/nvidia_nim/model-name")
            messages: Chat messages in OpenAI format
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Response with content, usage, timing

        Raises:
            ValueError: If model not found or API client not available
            httpx.HTTPError: If API request fails
        """
        model_config = self.get_model(model_id)
        if not model_config:
            raise ValueError(f"Unknown external model: {model_id}")

        client = self.clients.get(model_config.api)
        if not client:
            raise ValueError(f"No HTTP client for API: {model_config.api}")

        # Prepare request payload (OpenAI-compatible format)
        payload = {
            "model": model_config.name,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
            "top_p": kwargs.get("top_p", 1.0),
            "stream": False
        }

        # Make the request
        start_time = time.time()

        try:
            response = await client.post("/chat/completions", json=payload)
            response.raise_for_status()

            elapsed_ms = (time.time() - start_time) * 1000
            data = response.json()

            # Extract response
            return {
                "content": data["choices"][0]["message"]["content"],
                "model_used": model_id,
                "model_display_name": model_config.display_name,
                "usage": data.get("usage", {}),
                "latency_ms": elapsed_ms,
                "api": model_config.api
            }

        except httpx.HTTPError as e:
            logger.error(f"External API error for {model_id}: {e}")
            raise

    async def close(self):
        """Close all HTTP clients."""
        for client in self.clients.values():
            await client.aclose()
        logger.info("Closed all external API clients")

    def __del__(self):
        """Cleanup when client is destroyed."""
        # Note: Can't do async cleanup here, but we log it
        if self.clients:
            logger.debug("ExternalAPIClient destroyed (clients should be closed explicitly)")
