"""Cache hierarchy system for Klira AI SDK.

Provides intelligent multi-layer caching with automatic fallback,
performance optimization, and seamless scaling from local to distributed.
"""

import asyncio
import logging
import time
import threading
from typing import Any, Dict, Optional, Protocol, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

# Import local cache from Phase 2
from ..utils.cache_manager import CacheManager

# Import Redis adapter (optional) - Fixed module assignment pattern
if TYPE_CHECKING:
    from .redis_adapter import RedisAdapter, RedisConfig

    RedisAdapterType = RedisAdapter
    RedisConfigType = RedisConfig
    REDIS_AVAILABLE = True  # For type checking, assume available
else:
    try:
        from .redis_adapter import RedisAdapter, RedisConfig, REDIS_AVAILABLE

        RedisAdapterType = RedisAdapter
        RedisConfigType = RedisConfig
    except ImportError:
        REDIS_AVAILABLE = False
        RedisAdapterType = None  # type: ignore
        RedisConfigType = None  # type: ignore

logger = logging.getLogger("klira.cache.hierarchy")


class CacheLevel(Enum):
    """Cache hierarchy levels."""

    L1_MEMORY = "l1_memory"  # In-memory local cache (fastest)
    L2_DISTRIBUTED = "l2_distributed"  # Redis distributed cache
    L3_PERSISTENT = "l3_persistent"  # Future: Disk/DB cache


class CacheStrategy(Enum):
    """Cache access strategies."""

    READ_THROUGH = "read_through"  # Check L1 -> L2 -> L3
    WRITE_THROUGH = "write_through"  # Write to all levels
    WRITE_BEHIND = "write_behind"  # Async write to lower levels
    CACHE_ASIDE = "cache_aside"  # Manual cache management


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    l3_hits: int = 0
    l3_misses: int = 0
    total_requests: int = 0
    avg_latency_ms: float = 0.0

    @property
    def l1_hit_rate(self) -> float:
        total_l1 = self.l1_hits + self.l1_misses
        return (self.l1_hits / total_l1 * 100) if total_l1 > 0 else 0.0

    @property
    def l2_hit_rate(self) -> float:
        total_l2 = self.l2_hits + self.l2_misses
        return (self.l2_hits / total_l2 * 100) if total_l2 > 0 else 0.0

    @property
    def overall_hit_rate(self) -> float:
        total_hits = self.l1_hits + self.l2_hits + self.l3_hits
        return (
            (total_hits / self.total_requests * 100) if self.total_requests > 0 else 0.0
        )


class CacheAdapter(Protocol):
    """Protocol for cache adapters."""

    def get(self, key: str, value_type: Optional[type] = None) -> Optional[Any]: ...
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool: ...
    def delete(self, key: str) -> bool: ...
    async def aget(
        self, key: str, value_type: Optional[type] = None
    ) -> Optional[Any]: ...
    async def aset(self, key: str, value: Any, ttl: Optional[int] = None) -> bool: ...
    async def adelete(self, key: str) -> bool: ...
    def get_stats(self) -> Dict[str, Any]: ...


@dataclass
class CacheHierarchyConfig:
    """Configuration for cache hierarchy."""

    # L1 Cache (Local Memory)
    l1_enabled: bool = True
    l1_max_size: int = 10000
    l1_ttl_seconds: int = 300  # 5 minutes

    # L2 Cache (Distributed Redis)
    l2_enabled: bool = True
    l2_redis_url: Optional[str] = None
    l2_ttl_seconds: int = 3600  # 1 hour
    l2_fallback_on_error: bool = True

    # L3 Cache (Future: Persistent)
    l3_enabled: bool = False

    # Strategy
    strategy: CacheStrategy = CacheStrategy.READ_THROUGH

    # Performance
    async_write_behind: bool = True
    promotion_threshold: int = 3  # Promote to L1 after N L2 hits

    # Monitoring
    metrics_enabled: bool = True
    health_check_interval: int = 60  # seconds


class CacheHierarchy:
    """Multi-layer cache hierarchy with intelligent routing and fallback.

    Features:
    - L1: High-speed local memory cache (Phase 2 optimizations)
    - L2: Distributed Redis cache for multi-instance sync
    - L3: Future persistent storage
    - Automatic promotion/demotion between levels
    - Graceful fallback when layers are unavailable
    - Comprehensive metrics and monitoring
    """

    def __init__(self, config: Optional[CacheHierarchyConfig] = None):
        """Initialize cache hierarchy.

        Args:
            config: Cache hierarchy configuration
        """
        self.config = config or CacheHierarchyConfig()
        self._lock = threading.RLock()
        self._metrics = CacheMetrics()
        self._promotion_counters: Dict[str, int] = {}

        # Initialize cache layers
        self._l1_cache: Optional[CacheManager] = None
        self._l2_cache: Optional[RedisAdapterType] = None
        self._l3_cache: Optional[Any] = None  # Future implementation

        self._initialize_layers()

        # Background tasks
        self._health_check_task: Optional[asyncio.Task[Any]] = None
        self._start_background_tasks()

        logger.info(
            f"Cache hierarchy initialized with strategy: {self.config.strategy.value}"
        )

    def _initialize_layers(self) -> None:
        """Initialize available cache layers."""
        # L1: Local memory cache (always available)
        if self.config.l1_enabled:
            try:
                self._l1_cache = CacheManager(
                    max_size=self.config.l1_max_size,
                    ttl_seconds=self.config.l1_ttl_seconds,
                )
                logger.info("L1 cache (local memory) initialized")
            except Exception as e:
                logger.error(f"Failed to initialize L1 cache: {e}")

        # L2: Distributed Redis cache (optional)
        if self.config.l2_enabled and REDIS_AVAILABLE and self.config.l2_redis_url:
            try:
                redis_config = RedisConfigType(
                    url=self.config.l2_redis_url, default_ttl=self.config.l2_ttl_seconds
                )
                self._l2_cache = RedisAdapterType(redis_config)
                logger.info("L2 cache (Redis distributed) initialized")
            except Exception as e:
                logger.warning(
                    f"L2 cache initialization failed, continuing with L1 only: {e}"
                )
                if not self.config.l2_fallback_on_error:
                    raise

        # L3: Persistent cache (future)
        if self.config.l3_enabled:
            logger.info("L3 cache (persistent) not yet implemented")

    def _start_background_tasks(self) -> None:
        """Start background monitoring tasks."""
        if self.config.metrics_enabled:
            # Health checks will be implemented when needed
            pass

    def get(self, key: str, value_type: Optional[type] = None) -> Optional[Any]:
        """Get value from cache hierarchy synchronously.

        Args:
            key: Cache key
            value_type: Optional type hint for deserialization

        Returns:
            Cached value or None if not found
        """
        start_time = time.time()
        result = None

        try:
            # L1: Check local memory cache first
            if self._l1_cache:
                result = self._l1_cache.get(key)
                if result is not None:
                    self._metrics.l1_hits += 1
                    logger.debug(f"Cache L1 HIT: {key}")
                else:
                    self._metrics.l1_misses += 1

            # L2: Check distributed cache if L1 miss
            if result is None and self._l2_cache:
                try:
                    result = self._l2_cache.get(key, value_type)
                    if result is not None:
                        self._metrics.l2_hits += 1
                        logger.debug(f"Cache L2 HIT: {key}")

                        # Promote to L1 if hit threshold reached
                        self._consider_promotion(key, result)
                    else:
                        self._metrics.l2_misses += 1
                except Exception as e:
                    logger.warning(f"L2 cache error for key {key}: {e}")
                    self._metrics.l2_misses += 1

            # L3: Future implementation
            if result is None and self._l3_cache:
                # TODO: Implement L3 persistent cache
                pass

            return result

        finally:
            # Update metrics
            self._metrics.total_requests += 1
            latency = (time.time() - start_time) * 1000
            self._update_avg_latency(latency)

            if result is None:
                logger.debug(f"Cache MISS: {key}")

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache hierarchy synchronously.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successful in at least one layer
        """
        success = False

        # L1: Always write to local cache if available
        if self._l1_cache:
            try:
                l1_ttl = ttl or self.config.l1_ttl_seconds
                if self._l1_cache.set(key, value, l1_ttl):
                    success = True
                    logger.debug(f"Cache L1 SET: {key}")
            except Exception as e:
                logger.warning(f"L1 cache set error for key {key}: {e}")

        # L2: Write to distributed cache based on strategy
        if self._l2_cache:
            try:
                l2_ttl = ttl or self.config.l2_ttl_seconds
                if self.config.strategy in [
                    CacheStrategy.WRITE_THROUGH,
                    CacheStrategy.CACHE_ASIDE,
                ]:
                    if self._l2_cache.set(key, value, l2_ttl):
                        success = True
                        logger.debug(f"Cache L2 SET: {key}")
                elif (
                    self.config.strategy == CacheStrategy.WRITE_BEHIND
                    and self.config.async_write_behind
                ):
                    # Async write to L2 (fire and forget)
                    asyncio.create_task(self._async_l2_set(key, value, l2_ttl))
                    success = True
            except Exception as e:
                logger.warning(f"L2 cache set error for key {key}: {e}")

        return success

    async def aget(self, key: str, value_type: Optional[type] = None) -> Optional[Any]:
        """Get value from cache hierarchy asynchronously."""
        start_time = time.time()
        result = None

        try:
            # L1: Check local memory cache first
            if self._l1_cache:
                result = self._l1_cache.get(key)  # L1 is always sync
                if result is not None:
                    self._metrics.l1_hits += 1
                    logger.debug(f"Cache L1 AHIT: {key}")
                else:
                    self._metrics.l1_misses += 1

            # L2: Check distributed cache if L1 miss
            if result is None and self._l2_cache:
                try:
                    result = await self._l2_cache.aget(key, value_type)
                    if result is not None:
                        self._metrics.l2_hits += 1
                        logger.debug(f"Cache L2 AHIT: {key}")

                        # Promote to L1 if hit threshold reached
                        self._consider_promotion(key, result)
                    else:
                        self._metrics.l2_misses += 1
                except Exception as e:
                    logger.warning(f"L2 cache async error for key {key}: {e}")
                    self._metrics.l2_misses += 1

            return result

        finally:
            # Update metrics
            self._metrics.total_requests += 1
            latency = (time.time() - start_time) * 1000
            self._update_avg_latency(latency)

            if result is None:
                logger.debug(f"Cache AMISS: {key}")

    async def aset(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache hierarchy asynchronously."""
        success = False

        # L1: Always write to local cache if available
        if self._l1_cache:
            try:
                l1_ttl = ttl or self.config.l1_ttl_seconds
                if self._l1_cache.set(key, value, l1_ttl):  # L1 is always sync
                    success = True
                    logger.debug(f"Cache L1 ASET: {key}")
            except Exception as e:
                logger.warning(f"L1 cache async set error for key {key}: {e}")

        # L2: Write to distributed cache
        if self._l2_cache:
            try:
                l2_ttl = ttl or self.config.l2_ttl_seconds
                if await self._l2_cache.aset(key, value, l2_ttl):
                    success = True
                    logger.debug(f"Cache L2 ASET: {key}")
            except Exception as e:
                logger.warning(f"L2 cache async set error for key {key}: {e}")

        return success

    def delete(self, key: str) -> bool:
        """Delete key from all cache layers."""
        success = False

        # Delete from all layers
        if self._l1_cache:
            try:
                if self._l1_cache.delete(key):
                    success = True
                    logger.debug(f"Cache L1 DELETE: {key}")
            except Exception as e:
                logger.warning(f"L1 cache delete error for key {key}: {e}")

        if self._l2_cache:
            try:
                if self._l2_cache.delete(key):
                    success = True
                    logger.debug(f"Cache L2 DELETE: {key}")
            except Exception as e:
                logger.warning(f"L2 cache delete error for key {key}: {e}")

        # Remove from promotion counters
        with self._lock:
            self._promotion_counters.pop(key, None)

        return success

    async def adelete(self, key: str) -> bool:
        """Delete key from all cache layers asynchronously."""
        success = False

        # Delete from all layers
        if self._l1_cache:
            try:
                if self._l1_cache.delete(key):  # L1 is always sync
                    success = True
                    logger.debug(f"Cache L1 ADELETE: {key}")
            except Exception as e:
                logger.warning(f"L1 cache async delete error for key {key}: {e}")

        if self._l2_cache:
            try:
                if await self._l2_cache.adelete(key):
                    success = True
                    logger.debug(f"Cache L2 ADELETE: {key}")
            except Exception as e:
                logger.warning(f"L2 cache async delete error for key {key}: {e}")

        # Remove from promotion counters
        with self._lock:
            self._promotion_counters.pop(key, None)

        return success

    def _consider_promotion(self, key: str, value: Any) -> None:
        """Consider promoting a key from L2 to L1 based on access patterns."""
        if not self._l1_cache:
            return

        with self._lock:
            self._promotion_counters[key] = self._promotion_counters.get(key, 0) + 1

            if self._promotion_counters[key] >= self.config.promotion_threshold:
                # Promote to L1
                try:
                    self._l1_cache.set(key, value, self.config.l1_ttl_seconds)
                    logger.debug(f"Cache PROMOTION L2->L1: {key}")
                    # Reset counter
                    self._promotion_counters[key] = 0
                except Exception as e:
                    logger.warning(f"Cache promotion failed for key {key}: {e}")

    async def _async_l2_set(self, key: str, value: Any, ttl: int) -> None:
        """Asynchronously write to L2 cache (write-behind strategy)."""
        try:
            if self._l2_cache:
                await self._l2_cache.aset(key, value, ttl)
                logger.debug(f"Cache L2 ASYNC_SET: {key}")
        except Exception as e:
            logger.warning(f"Async L2 cache set failed for key {key}: {e}")

    def _update_avg_latency(self, latency_ms: float) -> None:
        """Update average latency with exponential moving average."""
        alpha = 0.1  # Smoothing factor
        if self._metrics.avg_latency_ms == 0:
            self._metrics.avg_latency_ms = latency_ms
        else:
            self._metrics.avg_latency_ms = (
                alpha * latency_ms + (1 - alpha) * self._metrics.avg_latency_ms
            )

    def get_metrics(self) -> CacheMetrics:
        """Get comprehensive cache metrics."""
        return self._metrics

    def get_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics."""
        stats: Dict[str, Any] = {
            "hierarchy": {
                "strategy": self.config.strategy.value,
                "layers_active": [],
                "metrics": {
                    "total_requests": self._metrics.total_requests,
                    "overall_hit_rate": self._metrics.overall_hit_rate,
                    "avg_latency_ms": round(self._metrics.avg_latency_ms, 2),
                },
            }
        }

        # L1 stats
        if self._l1_cache:
            stats["hierarchy"]["layers_active"].append("L1_MEMORY")
            stats["l1_memory"] = {
                "hits": self._metrics.l1_hits,
                "misses": self._metrics.l1_misses,
                "hit_rate": round(self._metrics.l1_hit_rate, 2),
                "backend": "local_memory",
            }

        # L2 stats
        if self._l2_cache:
            stats["hierarchy"]["layers_active"].append("L2_DISTRIBUTED")
            stats["l2_distributed"] = {
                "hits": self._metrics.l2_hits,
                "misses": self._metrics.l2_misses,
                "hit_rate": round(self._metrics.l2_hit_rate, 2),
                "backend": "redis",
            }

            # Include Redis-specific stats
            try:
                redis_stats = self._l2_cache.get_stats()
                stats["l2_distributed"].update(redis_stats)
            except Exception as e:
                logger.warning(f"Failed to get L2 stats: {e}")

        return stats

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all cache layers."""
        health: Dict[str, Any] = {
            "healthy": True,
            "layers": {},
            "timestamp": time.time(),
        }

        # L1 health
        if self._l1_cache:
            try:
                # Simple test
                test_key = f"health_check_{int(time.time())}"
                self._l1_cache.set(test_key, "ok", 10)
                result = self._l1_cache.get(test_key)
                self._l1_cache.delete(test_key)

                health["layers"]["l1_memory"] = {
                    "healthy": result == "ok",
                    "latency_ms": 0.1,  # L1 is always fast
                }
            except Exception as e:
                health["layers"]["l1_memory"] = {"healthy": False, "error": str(e)}
                health["healthy"] = False

        # L2 health
        if self._l2_cache:
            try:
                l2_health = self._l2_cache.health_check()
                health["layers"]["l2_distributed"] = l2_health
                if not l2_health.get("healthy", False):
                    health["healthy"] = False
            except Exception as e:
                health["layers"]["l2_distributed"] = {"healthy": False, "error": str(e)}
                health["healthy"] = False

        return health

    def close(self) -> None:
        """Close all cache connections and cleanup resources."""
        try:
            if self._l2_cache:
                self._l2_cache.close()

            if self._health_check_task:
                self._health_check_task.cancel()

            logger.info("Cache hierarchy closed")
        except Exception as e:
            logger.error(f"Error closing cache hierarchy: {e}")


# Factory function for easy instantiation
def create_cache_hierarchy(
    redis_url: Optional[str] = None,
    strategy: CacheStrategy = CacheStrategy.READ_THROUGH,
    **kwargs: Any,
) -> CacheHierarchy:
    """Create cache hierarchy with configuration.

    Args:
        redis_url: Redis connection URL (optional)
        strategy: Cache access strategy
        **kwargs: Additional configuration options

    Returns:
        Configured CacheHierarchy instance
    """
    config = CacheHierarchyConfig(l2_redis_url=redis_url, strategy=strategy, **kwargs)
    return CacheHierarchy(config)
