"""LRU response cache for query results."""

import hashlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import OrderedDict
import asyncio

logger = logging.getLogger(__name__)


class CacheEntry:
    """Single cache entry."""

    def __init__(self, key: str, value: Any, ttl_seconds: int):
        """
        Initialize cache entry.

        Args:
            key: Cache key
            value: Cached value
            ttl_seconds: Time to live in seconds
        """
        self.key = key
        self.value = value
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
        self.hit_count = 0

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return datetime.now() > self.expires_at

    def touch(self):
        """Update hit count."""
        self.hit_count += 1


class ResponseCache:
    """
    LRU cache for query responses.

    Features:
    - LRU eviction when full
    - TTL-based expiration
    - Automatic cleanup of expired entries
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600,
        cleanup_interval: int = 300
    ):
        """
        Initialize response cache.

        Args:
            max_size: Maximum number of entries
            ttl_seconds: Default TTL in seconds
            cleanup_interval: Cleanup interval in seconds
        """
        self.max_size = max_size
        self.default_ttl = ttl_seconds
        self.cleanup_interval = cleanup_interval

        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0
        }

        # Start cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start cache cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Cache cleanup task started")

    async def stop(self):
        """Stop cache cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Cache cleanup task stopped")

    async def _cleanup_loop(self):
        """Periodic cleanup of expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")

    def _generate_key(
        self,
        query: str,
        model: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate cache key from query parameters.

        Args:
            query: Query string
            model: Model name
            options: Generation options

        Returns:
            Cache key (hash)
        """
        # Normalize query
        normalized_query = query.strip().lower()

        # Create key data
        key_data = {
            "query": normalized_query,
            "model": model,
            "options": options or {}
        }

        # Generate hash
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    async def get(
        self,
        query: str,
        model: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available.

        Args:
            query: Query string
            model: Model name
            options: Generation options

        Returns:
            Cached response or None
        """
        async with self._lock:
            key = self._generate_key(query, model, options)

            if key not in self.cache:
                self._stats["misses"] += 1
                return None

            entry = self.cache[key]

            # Check expiration
            if entry.is_expired():
                del self.cache[key]
                self._stats["expirations"] += 1
                self._stats["misses"] += 1
                logger.debug(f"Cache entry expired: {key[:16]}...")
                return None

            # Move to end of LRU queue
            self.cache.move_to_end(key)
            entry.touch()

            self._stats["hits"] += 1
            logger.debug(f"Cache hit: {key[:16]}... (hits: {entry.hit_count})")
            return entry.value

    async def set(
        self,
        query: str,
        model: str,
        response: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ):
        """
        Cache a response.

        Args:
            query: Query string
            model: Model name
            response: Response to cache
            options: Generation options
            ttl: Custom TTL in seconds
        """
        async with self._lock:
            key = self._generate_key(query, model, options)
            ttl = ttl or self.default_ttl

            # Evict if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                await self._evict_one()

            # Add entry
            entry = CacheEntry(key, response, ttl)
            self.cache[key] = entry

            # Move to end of LRU queue
            self.cache.move_to_end(key)

            logger.debug(f"Cached response: {key[:16]}... (size: {len(self.cache)})")

    async def _evict_one(self):
        """Evict one LRU entry."""
        if not self.cache:
            return

        # Get first (oldest) entry
        key, entry = next(iter(self.cache.items()))
        del self.cache[key]
        self._stats["evictions"] += 1

        logger.debug(
            f"Evicted cache entry: {key[:16]}... "
            f"(age: {(datetime.now() - entry.created_at).total_seconds():.0f}s, "
            f"hits: {entry.hit_count})"
        )

    async def _cleanup_expired(self):
        """Remove all expired entries."""
        async with self._lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                del self.cache[key]
                self._stats["expirations"] += 1

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    async def invalidate(
        self,
        query: str,
        model: str,
        options: Optional[Dict[str, Any]] = None
    ):
        """
        Invalidate a specific cache entry.

        Args:
            query: Query string
            model: Model name
            options: Generation options
        """
        async with self._lock:
            key = self._generate_key(query, model, options)

            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Invalidated cache entry: {key[:16]}...")

    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            count = len(self.cache)
            self.cache.clear()
            logger.info(f"Cleared {count} cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / max(total_requests, 1)) * 100

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": f"{hit_rate:.1f}%",
            "evictions": self._stats["evictions"],
            "expirations": self._stats["expirations"],
            "total_requests": total_requests
        }

    async def get_status(self) -> Dict[str, Any]:
        """
        Get detailed cache status.

        Returns:
            Dict with cache status
        """
        async with self._lock:
            # Calculate entry age statistics
            now = datetime.now()
            ages = [
                (now - entry.created_at).total_seconds()
                for entry in self.cache.values()
            ]

            return {
                **self.get_stats(),
                "avg_age_seconds": sum(ages) / max(len(ages), 1),
                "oldest_entry_seconds": max(ages) if ages else 0,
                "newest_entry_seconds": min(ages) if ages else 0,
                "total_hit_count": sum(
                    entry.hit_count for entry in self.cache.values()
                )
            }
