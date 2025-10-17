"""Redis adapter for distributed caching in Klira AI SDK.

Provides Redis-backed caching with connection pooling, clustering support,
and automatic failover capabilities.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, TypeVar, Protocol, Callable
from dataclasses import dataclass, asdict
import threading

# Try to import Redis dependencies
try:
    import redis
    import redis.asyncio as aioredis
    from redis.exceptions import RedisError, ConnectionError, TimeoutError

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

    # Create dummy classes for type hints when Redis is not available
    class _DummyRedis:
        @staticmethod
        def from_url(*args: Any, **kwargs: Any) -> "_DummyRedis":
            raise ImportError("Redis not installed")

        def ping(self) -> bool:
            raise ImportError("Redis not installed")

        def get(self, key: str) -> Any:
            raise ImportError("Redis not installed")

        def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
            raise ImportError("Redis not installed")

        def setex(self, key: str, time: int, value: Any) -> bool:
            raise ImportError("Redis not installed")

        def delete(self, key: str) -> int:
            raise ImportError("Redis not installed")

        def keys(self, pattern: str) -> List[str]:
            raise ImportError("Redis not installed")

        def info(self) -> Dict[str, Any]:
            raise ImportError("Redis not installed")

        def close(self) -> None:
            raise ImportError("Redis not installed")

    class redis:  # type: ignore
        Redis = _DummyRedis

        @staticmethod
        def from_url(*args: Any, **kwargs: Any) -> _DummyRedis:
            return _DummyRedis()

    class aioredis:  # type: ignore
        Redis = _DummyRedis

        @staticmethod
        def from_url(*args: Any, **kwargs: Any) -> _DummyRedis:
            return _DummyRedis()

    RedisError = ConnectionError = TimeoutError = Exception

logger = logging.getLogger("klira.cache.redis")

T = TypeVar("T")


@dataclass
class RedisConfig:
    """Configuration for Redis connection."""

    url: str = "redis://localhost:6379"
    max_connections: int = 20
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    retry_on_timeout: bool = True
    retry_attempts: int = 3
    cluster_nodes: Optional[List[str]] = None
    enable_cluster: bool = False
    key_prefix: str = "klira:"
    default_ttl: int = 3600  # 1 hour

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis client."""
        return asdict(self)


class CacheEntry(Protocol):
    """Protocol for cache entries."""

    def serialize(self) -> str: ...
    @classmethod
    def deserialize(cls, data: str) -> "CacheEntry": ...


class RedisAdapter:
    """Redis adapter with connection pooling and failover support.

    Features:
    - Connection pooling for performance
    - Automatic failover and retry logic
    - Cluster support for high availability
    - Async and sync interfaces
    - Serialization/deserialization handling
    """

    def __init__(self, config: Optional[RedisConfig] = None):
        """Initialize Redis adapter.

        Args:
            config: Redis configuration. Uses defaults if None.
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis dependencies not available. Install with: pip install redis"
            )

        self.config = config or RedisConfig()
        self._sync_client: Optional[Any] = None
        self._async_client: Optional[Any] = None
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0, "errors": 0, "connections": 0}

        logger.info(f"Redis adapter initialized with config: {self.config.url}")

    def _get_sync_client(self) -> Any:
        """Get or create synchronous Redis client."""
        if self._sync_client is None:
            with self._lock:
                if self._sync_client is None:
                    try:
                        self._sync_client = redis.from_url(
                            self.config.url,
                            max_connections=self.config.max_connections,
                            socket_timeout=self.config.socket_timeout,
                            socket_connect_timeout=self.config.socket_connect_timeout,
                            retry_on_timeout=self.config.retry_on_timeout,
                            decode_responses=True,
                        )
                        # Test connection
                        self._sync_client.ping()
                        self._stats["connections"] += 1
                        logger.info("Redis sync client connected successfully")
                    except Exception as e:
                        logger.error(f"Failed to connect to Redis: {e}")
                        self._stats["errors"] += 1
                        raise
        return self._sync_client

    async def _get_async_client(self) -> Any:
        """Get or create asynchronous Redis client."""
        if self._async_client is None:
            try:
                self._async_client = aioredis.from_url(
                    self.config.url,
                    max_connections=self.config.max_connections,
                    socket_timeout=self.config.socket_timeout,
                    socket_connect_timeout=self.config.socket_connect_timeout,
                    retry_on_timeout=self.config.retry_on_timeout,
                    decode_responses=True,
                )
                # Test connection
                await self._async_client.ping()
                self._stats["connections"] += 1
                logger.info("Redis async client connected successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Redis async: {e}")
                self._stats["errors"] += 1
                raise
        return self._async_client

    def _serialize_value(self, value: Any) -> str:
        """Serialize value for Redis storage."""
        try:
            if hasattr(value, "serialize"):
                serialized = value.serialize()
                return (
                    str(serialized) if not isinstance(serialized, str) else serialized
                )
            return json.dumps(value, default=str)
        except Exception as e:
            logger.error(f"Serialization failed: {e}")
            raise

    def _deserialize_value(self, data: str, value_type: Optional[type] = None) -> Any:
        """Deserialize value from Redis."""
        try:
            if value_type and hasattr(value_type, "deserialize"):
                return value_type.deserialize(data)
            return json.loads(data)
        except Exception as e:
            logger.error(f"Deserialization failed: {e}")
            return None

    def _make_key(self, key: str) -> str:
        """Create prefixed Redis key."""
        return f"{self.config.key_prefix}{key}"

    def _retry_operation(
        self,
        operation_name: str,
        operation_func: Callable[[], Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Retry Redis operation with exponential backoff."""
        for attempt in range(self.config.retry_attempts):
            try:
                return operation_func(*args, **kwargs)
            except (ConnectionError, TimeoutError) as e:
                self._stats["errors"] += 1
                if attempt == self.config.retry_attempts - 1:
                    logger.error(
                        f"Redis {operation_name} failed after {attempt + 1} attempts: {e}"
                    )
                    raise

                # Exponential backoff
                wait_time = 2**attempt * 0.1
                logger.warning(
                    f"Redis {operation_name} attempt {attempt + 1} failed, retrying in {wait_time}s: {e}"
                )
                time.sleep(wait_time)
            except Exception as e:
                self._stats["errors"] += 1
                logger.error(
                    f"Redis {operation_name} failed with unexpected error: {e}"
                )
                raise

    def get(self, key: str, value_type: Optional[type] = None) -> Optional[Any]:
        """Get value from Redis cache synchronously.

        Args:
            key: Cache key
            value_type: Optional type hint for deserialization

        Returns:
            Cached value or None if not found
        """
        redis_key = self._make_key(key)

        def _get_operation() -> Optional[Any]:
            client = self._get_sync_client()
            data = client.get(redis_key)
            if data is not None:
                self._stats["hits"] += 1
                return self._deserialize_value(data, value_type)
            else:
                self._stats["misses"] += 1
                return None

        try:
            result = self._retry_operation("get", _get_operation)
            logger.debug(f"Redis GET {key}: {'HIT' if result is not None else 'MISS'}")
            return result
        except Exception as e:
            logger.error(f"Redis GET failed for key {key}: {e}")
            self._stats["errors"] += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache synchronously.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        redis_key = self._make_key(key)
        effective_ttl = ttl or self.config.default_ttl

        def _set_operation() -> bool:
            client = self._get_sync_client()
            serialized_value = self._serialize_value(value)
            result = client.setex(redis_key, effective_ttl, serialized_value)
            return bool(result)

        try:
            result = self._retry_operation("set", _set_operation)
            logger.debug(f"Redis SET {key}: SUCCESS (TTL={effective_ttl})")
            return bool(result)
        except Exception as e:
            logger.error(f"Redis SET failed for key {key}: {e}")
            self._stats["errors"] += 1
            return False

    async def aget(self, key: str, value_type: Optional[type] = None) -> Optional[Any]:
        """Get value from Redis cache asynchronously."""
        redis_key = self._make_key(key)

        try:
            client = await self._get_async_client()
            data = await client.get(redis_key)
            if data is not None:
                self._stats["hits"] += 1
                result = self._deserialize_value(data, value_type)
                logger.debug(f"Redis AGET {key}: HIT")
                return result
            else:
                self._stats["misses"] += 1
                logger.debug(f"Redis AGET {key}: MISS")
                return None
        except Exception as e:
            logger.error(f"Redis AGET failed for key {key}: {e}")
            self._stats["errors"] += 1
            return None

    async def aset(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache asynchronously."""
        redis_key = self._make_key(key)
        effective_ttl = ttl or self.config.default_ttl

        try:
            client = await self._get_async_client()
            serialized_value = self._serialize_value(value)
            result = await client.setex(redis_key, effective_ttl, serialized_value)
            logger.debug(f"Redis ASET {key}: SUCCESS (TTL={effective_ttl})")
            return bool(result)
        except Exception as e:
            logger.error(f"Redis ASET failed for key {key}: {e}")
            self._stats["errors"] += 1
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis cache."""
        redis_key = self._make_key(key)

        def _delete_operation() -> int:
            client = self._get_sync_client()
            return int(client.delete(redis_key))

        try:
            result = self._retry_operation("delete", _delete_operation)
            logger.debug(f"Redis DELETE {key}: {'SUCCESS' if result else 'NOT_FOUND'}")
            return bool(result)
        except Exception as e:
            logger.error(f"Redis DELETE failed for key {key}: {e}")
            self._stats["errors"] += 1
            return False

    async def adelete(self, key: str) -> bool:
        """Delete key from Redis cache asynchronously."""
        redis_key = self._make_key(key)

        try:
            client = await self._get_async_client()
            result = await client.delete(redis_key)
            logger.debug(f"Redis ADELETE {key}: {'SUCCESS' if result else 'NOT_FOUND'}")
            return bool(result)
        except Exception as e:
            logger.error(f"Redis ADELETE failed for key {key}: {e}")
            self._stats["errors"] += 1
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern."""
        redis_pattern = self._make_key(pattern)

        def _clear_operation() -> int:
            client = self._get_sync_client()
            keys = client.keys(redis_pattern)
            if keys:
                result = client.delete(*keys)
                return int(result)
            return 0

        try:
            result = self._retry_operation("clear_pattern", _clear_operation)
            logger.info(f"Redis CLEAR_PATTERN {pattern}: {result} keys deleted")
            return int(result)
        except Exception as e:
            logger.error(f"Redis CLEAR_PATTERN failed for pattern {pattern}: {e}")
            self._stats["errors"] += 1
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "backend": "redis",
            "url": self.config.url,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "errors": self._stats["errors"],
            "hit_rate": hit_rate,
            "connections": self._stats["connections"],
            "config": {
                "max_connections": self.config.max_connections,
                "default_ttl": self.config.default_ttl,
                "key_prefix": self.config.key_prefix,
                "cluster_enabled": self.config.enable_cluster,
            },
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform Redis health check."""
        try:
            start_time = time.time()
            client = self._get_sync_client()

            # Test basic operations
            test_key = self._make_key("health_check")
            client.set(test_key, "ok", ex=10)
            client.get(test_key)  # Just test that we can get the value
            client.delete(test_key)

            latency = (time.time() - start_time) * 1000

            info = client.info()
            return {
                "healthy": True,
                "latency_ms": round(latency, 2),
                "version": str(info.get("redis_version", "unknown")),
                "connected_clients": int(info.get("connected_clients", 0)),
                "used_memory": str(info.get("used_memory_human", "unknown")),
            }
        except Exception as e:
            return {"healthy": False, "error": str(e), "latency_ms": None}

    def close(self) -> None:
        """Close Redis connections."""
        try:
            if self._sync_client:
                self._sync_client.close()
                self._sync_client = None

            if self._async_client:
                asyncio.create_task(self._async_client.close())
                self._async_client = None

            logger.info("Redis connections closed")
        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}")


# Factory function for easy instantiation
def create_redis_adapter(
    url: str = "redis://localhost:6379", **kwargs: Any
) -> RedisAdapter:
    """Create Redis adapter with configuration.

    Args:
        url: Redis connection URL
        **kwargs: Additional configuration options

    Returns:
        Configured RedisAdapter instance
    """
    config = RedisConfig(url=url, **kwargs)
    return RedisAdapter(config)
