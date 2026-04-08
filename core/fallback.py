"""Circuit breaker pattern and fallback management."""

import time
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class CircuitState:
    """State of a circuit breaker."""
    model_name: str
    is_open: bool = False
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    total_requests: int = 0
    total_failures: int = 0


class CircuitBreaker:
    """
    Circuit breaker for a single model.

    Opens after threshold failures and closes after cooldown.
    """

    def __init__(
        self,
        model_name: str,
        failure_threshold: int = 3,
        cooldown_seconds: int = 60
    ):
        """
        Initialize circuit breaker.

        Args:
            model_name: Name of model this breaker controls
            failure_threshold: Failures before opening circuit
            cooldown_seconds: Seconds to wait before closing circuit
        """
        self.model_name = model_name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.state = CircuitState(model_name=model_name)
        self._lock = asyncio.Lock()

    async def record_success(self):
        """Record a successful request."""
        async with self._lock:
            self.state.last_success_time = datetime.now()
            self.state.total_requests += 1

            # Reset failure count on success
            if self.state.failure_count > 0:
                self.state.failure_count = 0

            # Close circuit if it was open
            if self.state.is_open:
                logger.info(f"Circuit closed for {self.model_name}")
                self.state.is_open = False

    async def record_failure(self):
        """Record a failed request."""
        async with self._lock:
            self.state.last_failure_time = datetime.now()
            self.state.failure_count += 1
            self.state.total_requests += 1
            self.state.total_failures += 1

            # Open circuit if threshold reached
            if (self.state.failure_count >= self.failure_threshold
                and not self.state.is_open):
                logger.warning(
                    f"Circuit opened for {self.model_name} "
                    f"({self.state.failure_count} failures)"
                )
                self.state.is_open = True

    async def is_open(self) -> bool:
        """
        Check if circuit is open.

        Returns:
            True if circuit is open
        """
        async with self._lock:
            # Check if cooldown has passed
            if self.state.is_open and self.state.last_failure_time:
                elapsed = (datetime.now() - self.state.last_failure_time).total_seconds()
                if elapsed >= self.cooldown_seconds:
                    # Attempt to close circuit (half-open state)
                    logger.info(
                        f"Circuit cooldown elapsed for {self.model_name}, "
                        f"attempting to close"
                    )
                    self.state.is_open = False
                    self.state.failure_count = 0
                    return False

            return self.state.is_open

    async def can_attempt(self) -> bool:
        """
        Check if request can be attempted.

        Returns:
            True if circuit is closed
        """
        return not await self.is_open()

    def get_state(self) -> Dict:
        """
        Get circuit state as dict.

        Returns:
            Dict with circuit state
        """
        return {
            "model_name": self.state.model_name,
            "is_open": self.state.is_open,
            "failure_count": self.state.failure_count,
            "last_failure_time": self.state.last_failure_time.isoformat()
                if self.state.last_failure_time else None,
            "last_success_time": self.state.last_success_time.isoformat()
                if self.state.last_success_time else None,
            "total_requests": self.state.total_requests,
            "total_failures": self.state.total_failures,
            "failure_rate": (self.state.total_failures / max(self.state.total_requests, 1))
                * 100
        }


class FallbackManager:
    """
    Manages circuit breakers for all models.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        cooldown_seconds: int = 60
    ):
        """
        Initialize fallback manager.

        Args:
            failure_threshold: Failures before opening circuit
            cooldown_seconds: Seconds to wait before closing circuit
        """
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.circuits: Dict[str, CircuitBreaker] = {}

    def _get_or_create_circuit(self, model_name: str) -> CircuitBreaker:
        """
        Get or create circuit breaker for model.

        Args:
            model_name: Name of model

        Returns:
            CircuitBreaker instance
        """
        if model_name not in self.circuits:
            self.circuits[model_name] = CircuitBreaker(
                model_name=model_name,
                failure_threshold=self.failure_threshold,
                cooldown_seconds=self.cooldown_seconds
            )
        return self.circuits[model_name]

    async def record_success(self, model_name: str):
        """
        Record successful request for model.

        Args:
            model_name: Name of model
        """
        circuit = self._get_or_create_circuit(model_name)
        await circuit.record_success()

    async def record_failure(self, model_name: str):
        """
        Record failed request for model.

        Args:
            model_name: Name of model
        """
        circuit = self._get_or_create_circuit(model_name)
        await circuit.record_failure()

    async def is_circuit_open(self, model_name: str) -> bool:
        """
        Check if circuit is open for model.

        Args:
            model_name: Name of model

        Returns:
            True if circuit is open
        """
        circuit = self._get_or_create_circuit(model_name)
        return await circuit.is_open()

    async def can_attempt(self, model_name: str) -> bool:
        """
        Check if request can be attempted for model.

        Args:
            model_name: Name of model

        Returns:
            True if circuit is closed
        """
        circuit = self._get_or_create_circuit(model_name)
        return await circuit.can_attempt()

    def get_failure_rate(self, model_name: str) -> float:
        """
        Get failure rate for model.

        Args:
            model_name: Name of model

        Returns:
            Failure rate as percentage (0-100)
        """
        circuit = self._get_or_create_circuit(model_name)
        state = circuit.get_state()
        return state["failure_rate"]

    def get_state(self, model_name: str) -> Optional[Dict]:
        """
        Get circuit state for model.

        Args:
            model_name: Name of model

        Returns:
            Circuit state dict or None
        """
        if model_name not in self.circuits:
            return None
        return self.circuits[model_name].get_state()

    def get_all_states(self) -> Dict[str, Dict]:
        """
        Get all circuit states.

        Returns:
            Dict of model name to circuit state
        """
        return {
            model_name: circuit.get_state()
            for model_name, circuit in self.circuits.items()
        }

    async def reset_circuit(self, model_name: str):
        """
        Manually reset circuit for model.

        Args:
            model_name: Name of model
        """
        if model_name in self.circuits:
            circuit = self.circuits[model_name]
            async with circuit._lock:
                circuit.state.is_open = False
                circuit.state.failure_count = 0
            logger.info(f"Manually reset circuit for {model_name}")

    async def reset_all_circuits(self):
        """Reset all circuits."""
        for model_name in list(self.circuits.keys()):
            await self.reset_circuit(model_name)
        logger.info("Reset all circuits")
