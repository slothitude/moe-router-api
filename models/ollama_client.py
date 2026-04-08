"""Ollama API client wrapper for model inference and embeddings."""

import httpx
from typing import Optional, Dict, Any, List, AsyncGenerator
import logging
import json

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, base_url: str = "http://localhost:11434", timeout: float = 120.0):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama API base URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout
            )
        return self._client

    async def generate(
        self,
        model: str,
        prompt: str,
        options: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        format: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a response from the model.

        Args:
            model: Model name
            prompt: Input prompt
            options: Generation options (temperature, top_p, etc.)
            system: System prompt
            format: Response format (e.g., "json")
            stream: Whether to stream response

        Returns:
            Response dict with 'response', 'model', 'created_at', etc.
        """
        client = self._get_client()

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }

        if options:
            payload["options"] = options
        if system:
            payload["system"] = system
        if format:
            payload["format"] = format

        try:
            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()

            if stream:
                # Handle streaming response (return first chunk for now)
                return {"response": response.text, "model": model}

            data = response.json()
            logger.debug(f"Generated response from {model}: {len(data.get('response', ''))} chars")
            return data

        except httpx.HTTPError as e:
            logger.error(f"HTTP error generating from {model}: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {model}: {e}")
            raise

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        options: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response from the model.

        Args:
            model: Model name
            prompt: Input prompt
            options: Generation options
            system: System prompt

        Yields:
            Response chunks as they arrive
        """
        client = self._get_client()

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True
        }

        if options:
            payload["options"] = options
        if system:
            payload["system"] = system

        try:
            async with client.stream("POST", "/api/generate", json=payload) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            if "response" in chunk:
                                yield chunk["response"]
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse streaming chunk: {line}")
                            continue

        except httpx.HTTPError as e:
            logger.error(f"HTTP error in stream from {model}: {e}")
            raise

    async def embeddings(
        self,
        model: str,
        text: str
    ) -> List[float]:
        """
        Get embeddings for text.

        Args:
            model: Model name (should be nomic-embed-text)
            text: Input text

        Returns:
            Embedding vector as list of floats
        """
        client = self._get_client()

        payload = {
            "model": model,
            "prompt": text
        }

        try:
            response = await client.post("/api/embeddings", json=payload)
            response.raise_for_status()

            data = response.json()
            embedding = data.get("embedding", [])

            logger.debug(f"Generated embedding for {model}: dim={len(embedding)}")
            return embedding

        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting embeddings from {model}: {e}")
            raise

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models.

        Returns:
            List of model dicts with 'name', 'size', etc.
        """
        client = self._get_client()

        try:
            response = await client.get("/api/tags")
            response.raise_for_status()

            data = response.json()
            models = data.get("models", [])

            logger.debug(f"Found {len(models)} models")
            return models

        except httpx.HTTPError as e:
            logger.error(f"HTTP error listing models: {e}")
            raise

    async def show_model(self, model: str) -> Dict[str, Any]:
        """
        Get detailed information about a model.

        Args:
            model: Model name

        Returns:
            Model information dict
        """
        client = self._get_client()

        payload = {"name": model}

        try:
            response = await client.post("/api/show", json=payload)
            response.raise_for_status()

            data = response.json()
            return data

        except httpx.HTTPError as e:
            logger.error(f"HTTP error showing model {model}: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Check if Ollama is healthy and responding.

        Returns:
            True if healthy, False otherwise
        """
        client = self._get_client()

        try:
            # Try to list models as a health check
            response = await client.get("/api/tags", timeout=5.0)
            response.raise_for_status()
            logger.debug("Ollama health check passed")
            return True

        except httpx.HTTPError as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    async def pull_model(self, model: str, stream: bool = False) -> Dict[str, Any]:
        """
        Pull a model from Ollama library.

        Args:
            model: Model name to pull
            stream: Whether to stream progress

        Returns:
            Pull status dict
        """
        client = self._get_client()

        payload = {"name": model, "stream": stream}

        try:
            response = await client.post("/api/pull", json=payload)
            response.raise_for_status()

            if not stream:
                return response.json()

            # For streaming, return immediately
            return {"status": "pulling"}

        except httpx.HTTPError as e:
            logger.error(f"HTTP error pulling model {model}: {e}")
            raise
