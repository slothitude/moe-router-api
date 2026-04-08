"""Health monitoring and system checks."""

import asyncio
import logging
import psutil
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitor system health and resource usage."""

    def __init__(self, check_interval: int = 30):
        """
        Initialize health monitor.

        Args:
            check_interval: Health check interval in seconds
        """
        self.check_interval = check_interval
        self._last_check = None
        self._health_status = {
            "ollama": False,
            "memory": True,
            "disk": True
        }

    async def check_ollama(self, ollama_client) -> bool:
        """
        Check Ollama health.

        Args:
            ollama_client: Ollama client instance

        Returns:
            True if healthy
        """
        try:
            is_healthy = await ollama_client.health_check()
            self._health_status["ollama"] = is_healthy
            return is_healthy
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            self._health_status["ollama"] = False
            return False

    def check_memory(self, threshold_percent: float = 90.0) -> bool:
        """
        Check system memory usage.

        Args:
            threshold_percent: Alert threshold in percent

        Returns:
            True if memory OK
        """
        try:
            memory = psutil.virtual_memory()
            is_healthy = memory.percent < threshold_percent

            if not is_healthy:
                logger.warning(
                    f"High memory usage: {memory.percent:.1f}% "
                    f"({memory.available / 1024**3:.1f}GB available)"
                )

            self._health_status["memory"] = is_healthy
            return is_healthy
        except Exception as e:
            logger.error(f"Memory check failed: {e}")
            return True  # Assume OK on error

    def check_disk(self, threshold_percent: float = 90.0) -> bool:
        """
        Check disk usage.

        Args:
            threshold_percent: Alert threshold in percent

        Returns:
            True if disk OK
        """
        try:
            disk = psutil.disk_usage('/')
            is_healthy = disk.percent < threshold_percent

            if not is_healthy:
                logger.warning(
                    f"High disk usage: {disk.percent:.1f}% "
                    f"({disk.free / 1024**3:.1f}GB available)"
                )

            self._health_status["disk"] = is_healthy
            return is_healthy
        except Exception as e:
            logger.error(f"Disk check failed: {e}")
            return True  # Assume OK on error

    def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information.

        Returns:
            Dict with system info
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / 1024**3,
                "memory_total_gb": memory.total / 1024**3,
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / 1024**3,
                "disk_total_gb": disk.total / 1024**3,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {"error": str(e)}

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get overall health status.

        Returns:
            Dict with health status
        """
        return {
            **self._health_status,
            "overall": all(self._health_status.values()),
            "last_check": self._last_check.isoformat() if self._last_check else None
        }

    async def run_checks(self, ollama_client) -> Dict[str, bool]:
        """
        Run all health checks.

        Args:
            ollama_client: Ollama client instance

        Returns:
            Dict of check name to result
        """
        self._last_check = datetime.now()

        results = {
            "ollama": await self.check_ollama(ollama_client),
            "memory": self.check_memory(),
            "disk": self.check_disk()
        }

        return results


async def health_check_task(
    monitor: HealthMonitor,
    ollama_client,
    metrics_collector
):
    """
    Background task for periodic health checks.

    Args:
        monitor: Health monitor instance
        ollama_client: Ollama client
        metrics_collector: Metrics collector instance
    """
    while True:
        try:
            await asyncio.sleep(monitor.check_interval)

            # Run health checks
            await monitor.run_checks(ollama_client)

            # Update system info metrics
            system_info = monitor.get_system_info()
            logger.debug(f"System info: CPU={system_info.get('cpu_percent')}%, "
                        f"Memory={system_info.get('memory_percent')}%")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Health check task error: {e}")
