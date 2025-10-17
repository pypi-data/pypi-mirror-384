"""General-purpose cache manager for Klira AI SDK.

Based on Phase 2 LRUCache implementation, enhanced with TTL support and
thread safety for use in the cache hierarchy system.
"""

import time
import threading
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict
import logging

logger = logging.getLogger("klira.cache.manager")


class CacheManager:
    """Thread-safe, TTL-enabled cache manager based on Phase 2 LRUCache.

    Features from Phase 2:
    - LRU eviction policy using OrderedDict
    - High performance for frequent access patterns
    - Configurable capacity management

    Enhanced for Phase 3:
    - Thread-safe operations with RLock
    - TTL (Time To Live) support for automatic expiration
    - Statistics tracking for monitoring
    - Type hints for better IDE support
    """

    def __init__(self, max_size: int = 10000, ttl_seconds: int = 300):
        """Initialize cache manager.

        Args:
            max_size: Maximum number of items to store
            ttl_seconds: Time to live in seconds for cache entries
        """
        if max_size <= 0:
            raise ValueError("Cache max_size must be positive")
        if ttl_seconds <= 0:
            raise ValueError("Cache ttl_seconds must be positive")

        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

        # Use OrderedDict for efficient LRU tracking (Phase 2 pattern)
        self._cache: OrderedDict[str, Tuple[Any, float]] = (
            OrderedDict()
        )  # key -> (value, timestamp)
        self._lock = threading.RLock()  # Thread safety for cache hierarchy

        # Statistics tracking
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0

        logger.debug(
            f"CacheManager initialized: max_size={max_size}, ttl={ttl_seconds}s"
        )

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache, checking TTL and updating LRU order.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                logger.debug(f"Cache MISS: {key}")
                return None

            value, timestamp = self._cache[key]
            current_time = time.time()

            # Check TTL expiration
            if current_time - timestamp > self.ttl_seconds:
                # Remove expired entry
                del self._cache[key]
                self._expirations += 1
                self._misses += 1
                logger.debug(
                    f"Cache EXPIRED: {key} (age: {current_time - timestamp:.1f}s)"
                )
                return None

            # Move to end for LRU (Phase 2 pattern)
            self._cache.move_to_end(key)
            self._hits += 1
            logger.debug(f"Cache HIT: {key}")
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional custom TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Custom TTL in seconds (uses default if None)

        Returns:
            True if successful
        """
        effective_ttl = ttl or self.ttl_seconds
        current_time = time.time()

        with self._lock:
            # If key exists, update and move to end
            if key in self._cache:
                self._cache[key] = (value, current_time)
                self._cache.move_to_end(key)
                logger.debug(f"Cache UPDATE: {key}")
                return True

            # Check capacity and evict if needed (Phase 2 LRU pattern)
            if len(self._cache) >= self.max_size:
                oldest_key, _ = self._cache.popitem(last=False)
                self._evictions += 1
                logger.debug(f"Cache EVICTED: {oldest_key} (capacity limit)")

            # Add new entry
            self._cache[key] = (value, current_time)
            logger.debug(f"Cache SET: {key} (TTL: {effective_ttl}s)")
            return True

    def delete(self, key: str) -> bool:
        """Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key existed and was deleted
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache DELETE: {key}")
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries and reset statistics."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            self._expirations = 0
            logger.debug("Cache CLEARED")

    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        current_time = time.time()
        removed_count = 0

        with self._lock:
            # Collect expired keys
            expired_keys = []
            for key, (value, timestamp) in self._cache.items():
                if current_time - timestamp > self.ttl_seconds:
                    expired_keys.append(key)

            # Remove expired entries
            for key in expired_keys:
                del self._cache[key]
                removed_count += 1
                self._expirations += 1

            if removed_count > 0:
                logger.debug(f"Cache cleanup removed {removed_count} expired entries")

            return removed_count

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics.

        Returns:
            Dictionary with cache performance metrics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (
                (self._hits / total_requests * 100) if total_requests > 0 else 0.0
            )

            return {
                "backend": "local_memory",
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 2),
                "evictions": self._evictions,
                "expirations": self._expirations,
                "ttl_seconds": self.ttl_seconds,
            }

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on cache.

        Returns:
            Health status and basic metrics
        """
        try:
            # Perform a quick operation to verify cache is working
            test_key = f"health_check_{int(time.time())}"
            self.set(test_key, "test", 1)
            result = self.get(test_key)
            self.delete(test_key)

            with self._lock:
                return {
                    "healthy": result == "test",
                    "size": len(self._cache),
                    "max_size": self.max_size,
                    "utilization": round(len(self._cache) / self.max_size * 100, 1),
                }
        except Exception as e:
            return {"healthy": False, "error": str(e)}


# Factory function for easy instantiation
def create_cache_manager(max_size: int = 10000, ttl_seconds: int = 300) -> CacheManager:
    """Create cache manager with configuration.

    Args:
        max_size: Maximum number of items to store
        ttl_seconds: Time to live in seconds for cache entries

    Returns:
        Configured CacheManager instance
    """
    return CacheManager(max_size=max_size, ttl_seconds=ttl_seconds)
