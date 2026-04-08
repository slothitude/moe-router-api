"""Memory management utilities."""

import logging
import gc
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def get_object_size(obj) -> int:
    """
    Get approximate size of object in bytes.

    Args:
        obj: Python object

    Returns:
        Size in bytes
    """
    import sys
    return sys.getsizeof(obj)


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes to human readable string.

    Args:
        bytes_value: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


async def force_garbage_collect() -> Dict[str, int]:
    """
    Force garbage collection and return stats.

    Returns:
        Dict with collection stats
    """
    import gc

    before = gc.get_count()

    # Run collection
    collected = gc.collect()

    after = gc.get_count()

    logger.info(f"Garbage collection: collected {collected} objects")

    return {
        "collected": collected,
        "before_objects": before,
        "after_objects": after
    }


class MemoryTracker:
    """Track memory usage for components."""

    def __init__(self):
        """Initialize memory tracker."""
        self.allocations: Dict[str, int] = {}
        self._enabled = True

    def track_allocation(self, component: str, size_mb: int):
        """
        Track a memory allocation.

        Args:
            component: Component name
            size_mb: Size in MB
        """
        if not self._enabled:
            return

        self.allocations[component] = self.allocations.get(component, 0) + size_mb
        logger.debug(f"Memory allocation: {component} +{size_mb}MB "
                    f"(total: {self.allocations[component]}MB)")

    def track_deallocation(self, component: str, size_mb: int):
        """
        Track a memory deallocation.

        Args:
            component: Component name
            size_mb: Size in MB
        """
        if not self._enabled:
            return

        self.allocations[component] = self.allocations.get(component, 0) - size_mb
        logger.debug(f"Memory deallocation: {component} -{size_mb}MB "
                    f"(total: {self.allocations[component]}MB)")

    def get_total_tracked(self) -> int:
        """
        Get total tracked memory.

        Returns:
            Total tracked memory in MB
        """
        return sum(self.allocations.values())

    def get_breakdown(self) -> Dict[str, int]:
        """
        Get memory breakdown by component.

        Returns:
            Dict of component to memory in MB
        """
        return self.allocations.copy()

    def reset(self):
        """Reset all tracking."""
        self.allocations.clear()
        logger.debug("Memory tracker reset")
