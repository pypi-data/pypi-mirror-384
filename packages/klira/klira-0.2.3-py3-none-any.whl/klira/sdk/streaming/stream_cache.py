"""Streaming cache system for LLM response caching and optimization."""

import logging
import time
import hashlib
from typing import Dict, Optional, Any, Tuple, cast
import threading

# Import Phase 3 cache infrastructure
from ..cache.cache_hierarchy import CacheHierarchy
from ..utils.cache_manager import CacheManager

logger = logging.getLogger("klira.streaming.cache")


class StreamCache:
    """Intelligent caching system for streaming LLM responses.

    Features:
    - Partial response caching for faster streaming
    - Complete response caching for replay scenarios
    - Semantic similarity matching for cache hits
    - Integration with Phase 3 cache hierarchy
    - TTL-based expiration and cleanup
    - Performance metrics and monitoring
    """

    def __init__(
        self,
        ttl_seconds: int = 300,
        enable_partial_caching: bool = True,
        max_partial_cache_size: int = 1000,
        max_response_cache_size: int = 500,
        similarity_threshold: float = 0.85,
    ):
        """Initialize streaming cache system.

        Args:
            ttl_seconds: Time to live for cached responses
            enable_partial_caching: Enable caching of partial responses
            max_partial_cache_size: Maximum partial cache entries
            max_response_cache_size: Maximum complete response cache entries
            similarity_threshold: Threshold for semantic similarity matching
        """
        self.ttl_seconds = ttl_seconds
        self.enable_partial_caching = enable_partial_caching
        self.max_partial_cache_size = max_partial_cache_size
        self.max_response_cache_size = max_response_cache_size
        self.similarity_threshold = similarity_threshold

        # Cache stores
        self._partial_cache: Dict[
            str, Tuple[str, float]
        ] = {}  # stream_id -> (content, timestamp)
        self._response_cache: Dict[
            str, Tuple[str, float]
        ] = {}  # prompt_hash -> (response, timestamp)
        self._prompt_index: Dict[str, str] = {}  # prompt -> prompt_hash for lookups

        # Performance tracking
        self._stats = {
            "partial_hits": 0,
            "partial_misses": 0,
            "response_hits": 0,
            "response_misses": 0,
            "partial_stores": 0,
            "response_stores": 0,
            "evictions": 0,
            "expirations": 0,
        }

        # Thread safety
        self._lock = threading.RLock()

        # Phase 3 cache integration
        self._cache_hierarchy: Optional[CacheHierarchy] = None
        self._local_cache: Optional[CacheManager] = None

        self._initialize_cache_infrastructure()
        logger.info(
            f"StreamCache initialized with TTL={ttl_seconds}s, partial_caching={enable_partial_caching}"
        )

    def _initialize_cache_infrastructure(self) -> None:
        """Initialize cache infrastructure with Phase 3 integration."""
        try:
            # Try to use existing cache hierarchy from Phase 3
            self._cache_hierarchy = CacheHierarchy()
            logger.info("StreamCache connected to Phase 3 cache hierarchy")

        except Exception as e:
            logger.debug(f"Phase 3 cache hierarchy not available: {e}")
            # Fallback to local cache only
            try:
                self._local_cache = CacheManager(
                    max_size=self.max_response_cache_size, ttl_seconds=self.ttl_seconds
                )
                logger.info("StreamCache using local cache fallback")
            except Exception as e2:
                logger.warning(f"Failed to initialize local cache: {e2}")

    async def cache_partial(self, stream_id: str, content: str) -> bool:
        """Cache partial response for a streaming session.

        Args:
            stream_id: Stream identifier
            content: Partial content to cache

        Returns:
            bool: True if cached successfully
        """
        if not self.enable_partial_caching:
            return False

        try:
            current_time = time.time()

            with self._lock:
                # Check cache size and evict if needed
                if len(self._partial_cache) >= self.max_partial_cache_size:
                    self._evict_oldest_partial()

                # Store partial content
                self._partial_cache[stream_id] = (content, current_time)
                self._stats["partial_stores"] += 1

            # Also store in distributed cache if available
            if self._cache_hierarchy:
                try:
                    cache_key = f"stream:partial:{stream_id}"
                    await self._cache_hierarchy.aset(
                        cache_key, content, ttl=self.ttl_seconds
                    )
                except Exception as e:
                    logger.debug(f"Failed to cache partial content in hierarchy: {e}")

            logger.debug(
                f"Cached partial content for stream {stream_id} ({len(content)} chars)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to cache partial content for stream {stream_id}: {e}")
            return False

    async def get_partial(self, stream_id: str) -> Optional[str]:
        """Get cached partial response for a stream.

        Args:
            stream_id: Stream identifier

        Returns:
            Cached partial content or None
        """
        if not self.enable_partial_caching:
            return None

        try:
            # Check local cache first
            with self._lock:
                if stream_id in self._partial_cache:
                    content, timestamp = self._partial_cache[stream_id]

                    # Check TTL
                    if time.time() - timestamp <= self.ttl_seconds:
                        self._stats["partial_hits"] += 1
                        logger.debug(f"Partial cache hit for stream {stream_id}")
                        return content
                    else:
                        # Expired
                        del self._partial_cache[stream_id]
                        self._stats["expirations"] += 1

            # Check distributed cache if available
            if self._cache_hierarchy:
                try:
                    cache_key = f"stream:partial:{stream_id}"
                    cached_content = await self._cache_hierarchy.aget(cache_key)
                    if cached_content and isinstance(cached_content, str):
                        self._stats["partial_hits"] += 1
                        logger.debug(
                            f"Partial cache hit in hierarchy for stream {stream_id}"
                        )
                        return cast(str, cached_content)
                except Exception as e:
                    logger.debug(f"Failed to get partial content from hierarchy: {e}")

            # Cache miss
            with self._lock:
                self._stats["partial_misses"] += 1

            return None

        except Exception as e:
            logger.error(f"Failed to get partial content for stream {stream_id}: {e}")
            return None

    async def cache_final(self, prompt: str, response: str) -> bool:
        """Cache final complete response.

        Args:
            prompt: Original prompt
            response: Complete response

        Returns:
            bool: True if cached successfully
        """
        try:
            prompt_hash = self._hash_prompt(prompt)
            current_time = time.time()

            with self._lock:
                # Check cache size and evict if needed
                if len(self._response_cache) >= self.max_response_cache_size:
                    self._evict_oldest_response()

                # Store response
                self._response_cache[prompt_hash] = (response, current_time)
                self._prompt_index[prompt] = prompt_hash
                self._stats["response_stores"] += 1

            # Store in distributed cache if available
            if self._cache_hierarchy:
                try:
                    cache_key = f"stream:response:{prompt_hash}"
                    await self._cache_hierarchy.aset(
                        cache_key, response, ttl=self.ttl_seconds
                    )
                except Exception as e:
                    logger.debug(f"Failed to cache final response in hierarchy: {e}")
            elif self._local_cache:
                try:
                    cache_key = f"response:{prompt_hash}"
                    self._local_cache.set(cache_key, response, ttl=self.ttl_seconds)
                except Exception as e:
                    logger.debug(f"Failed to cache final response locally: {e}")

            logger.debug(
                f"Cached final response for prompt hash {prompt_hash[:8]}... ({len(response)} chars)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to cache final response: {e}")
            return False

    async def get_cached_response(self, prompt: str) -> Optional[str]:
        """Get cached response for a prompt.

        Args:
            prompt: Original prompt

        Returns:
            Cached response or None
        """
        try:
            prompt_hash = self._hash_prompt(prompt)

            # Check local cache first
            with self._lock:
                if prompt_hash in self._response_cache:
                    response, timestamp = self._response_cache[prompt_hash]

                    # Check TTL
                    if time.time() - timestamp <= self.ttl_seconds:
                        self._stats["response_hits"] += 1
                        logger.debug(
                            f"Response cache hit for prompt hash {prompt_hash[:8]}..."
                        )
                        return response
                    else:
                        # Expired
                        del self._response_cache[prompt_hash]
                        self._prompt_index.pop(prompt, None)
                        self._stats["expirations"] += 1

            # Check distributed cache if available
            if self._cache_hierarchy:
                try:
                    cache_key = f"stream:response:{prompt_hash}"
                    cached_response = await self._cache_hierarchy.aget(cache_key)
                    if cached_response and isinstance(cached_response, str):
                        self._stats["response_hits"] += 1
                        logger.debug(
                            f"Response cache hit in hierarchy for {prompt_hash[:8]}..."
                        )
                        return cast(str, cached_response)
                except Exception as e:
                    logger.debug(f"Failed to get response from hierarchy: {e}")
            elif self._local_cache:
                try:
                    cache_key = f"response:{prompt_hash}"
                    cached_response = self._local_cache.get(cache_key)
                    if cached_response and isinstance(cached_response, str):
                        self._stats["response_hits"] += 1
                        logger.debug(
                            f"Response cache hit locally for {prompt_hash[:8]}..."
                        )
                        return cast(str, cached_response)
                except Exception as e:
                    logger.debug(f"Failed to get response locally: {e}")

            # Try semantic similarity matching for similar prompts
            similar_response = await self._find_similar_response(prompt)
            if similar_response:
                self._stats["response_hits"] += 1
                logger.debug("Semantic cache hit for similar prompt")
                return similar_response

            # Cache miss
            with self._lock:
                self._stats["response_misses"] += 1

            return None

        except Exception as e:
            logger.error(f"Failed to get cached response: {e}")
            return None

    async def _find_similar_response(self, prompt: str) -> Optional[str]:
        """Find response for semantically similar prompt.

        Args:
            prompt: Prompt to find similar cached response for

        Returns:
            Similar cached response or None
        """
        try:
            # Simple similarity matching based on common words
            # In a production system, this would use embeddings or other semantic matching
            prompt_words = set(prompt.lower().split())

            best_match = None
            best_similarity = 0.0

            with self._lock:
                for cached_prompt, prompt_hash in self._prompt_index.items():
                    if prompt_hash not in self._response_cache:
                        continue

                    cached_words = set(cached_prompt.lower().split())

                    # Calculate Jaccard similarity
                    intersection = len(prompt_words & cached_words)
                    union = len(prompt_words | cached_words)

                    if union > 0:
                        similarity = intersection / union

                        if (
                            similarity > best_similarity
                            and similarity >= self.similarity_threshold
                        ):
                            best_similarity = similarity
                            response, timestamp = self._response_cache[prompt_hash]

                            # Check TTL
                            if time.time() - timestamp <= self.ttl_seconds:
                                best_match = response

            if best_match:
                logger.debug(
                    f"Found similar response with {best_similarity:.2f} similarity"
                )

            return best_match

        except Exception as e:
            logger.warning(f"Error in semantic similarity matching: {e}")
            return None

    def _hash_prompt(self, prompt: str) -> str:
        """Create hash for prompt."""
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    def _evict_oldest_partial(self) -> None:
        """Evict oldest partial cache entry."""
        if not self._partial_cache:
            return

        oldest_stream = min(
            self._partial_cache.keys(), key=lambda k: self._partial_cache[k][1]
        )
        del self._partial_cache[oldest_stream]
        self._stats["evictions"] += 1
        logger.debug(f"Evicted oldest partial cache entry: {oldest_stream}")

    def _evict_oldest_response(self) -> None:
        """Evict oldest response cache entry."""
        if not self._response_cache:
            return

        oldest_hash = min(
            self._response_cache.keys(), key=lambda k: self._response_cache[k][1]
        )
        del self._response_cache[oldest_hash]

        # Remove from prompt index
        prompt_to_remove = None
        for prompt, hash_val in self._prompt_index.items():
            if hash_val == oldest_hash:
                prompt_to_remove = prompt
                break

        if prompt_to_remove:
            del self._prompt_index[prompt_to_remove]

        self._stats["evictions"] += 1
        logger.debug(f"Evicted oldest response cache entry: {oldest_hash[:8]}...")

    async def cleanup_expired(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        current_time = time.time()
        removed_count = 0

        with self._lock:
            # Clean partial cache
            expired_streams = []
            for stream_id, (content, timestamp) in self._partial_cache.items():
                if current_time - timestamp > self.ttl_seconds:
                    expired_streams.append(stream_id)

            for stream_id in expired_streams:
                del self._partial_cache[stream_id]
                removed_count += 1
                self._stats["expirations"] += 1

            # Clean response cache
            expired_hashes = []
            for prompt_hash, (response, timestamp) in self._response_cache.items():
                if current_time - timestamp > self.ttl_seconds:
                    expired_hashes.append(prompt_hash)

            for prompt_hash in expired_hashes:
                del self._response_cache[prompt_hash]
                removed_count += 1
                self._stats["expirations"] += 1

                # Remove from prompt index
                prompt_to_remove = None
                for prompt, hash_val in self._prompt_index.items():
                    if hash_val == prompt_hash:
                        prompt_to_remove = prompt
                        break

                if prompt_to_remove:
                    del self._prompt_index[prompt_to_remove]

        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} expired cache entries")

        return removed_count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        with self._lock:
            total_partial_requests = (
                self._stats["partial_hits"] + self._stats["partial_misses"]
            )
            total_response_requests = (
                self._stats["response_hits"] + self._stats["response_misses"]
            )

            partial_hit_rate = (
                (self._stats["partial_hits"] / total_partial_requests * 100)
                if total_partial_requests > 0
                else 0
            )

            response_hit_rate = (
                (self._stats["response_hits"] / total_response_requests * 100)
                if total_response_requests > 0
                else 0
            )

            return {
                "backend": "stream_cache",
                "partial_cache": {
                    "size": len(self._partial_cache),
                    "max_size": self.max_partial_cache_size,
                    "hit_rate": round(partial_hit_rate, 2),
                    "hits": self._stats["partial_hits"],
                    "misses": self._stats["partial_misses"],
                    "stores": self._stats["partial_stores"],
                },
                "response_cache": {
                    "size": len(self._response_cache),
                    "max_size": self.max_response_cache_size,
                    "hit_rate": round(response_hit_rate, 2),
                    "hits": self._stats["response_hits"],
                    "misses": self._stats["response_misses"],
                    "stores": self._stats["response_stores"],
                },
                "overall": {
                    "evictions": self._stats["evictions"],
                    "expirations": self._stats["expirations"],
                    "ttl_seconds": self.ttl_seconds,
                    "similarity_threshold": self.similarity_threshold,
                },
                "cache_hierarchy_available": self._cache_hierarchy is not None,
                "local_cache_available": self._local_cache is not None,
            }

    def clear(self) -> None:
        """Clear all cache data."""
        with self._lock:
            self._partial_cache.clear()
            self._response_cache.clear()
            self._prompt_index.clear()

            # Reset stats
            for key in self._stats:
                self._stats[key] = 0

        logger.info("StreamCache cleared")


# Factory function for easy instantiation
def create_stream_cache(
    ttl_seconds: int = 300, enable_partial_caching: bool = True
) -> StreamCache:
    """Create stream cache with configuration.

    Args:
        ttl_seconds: Time to live for cached responses
        enable_partial_caching: Enable caching of partial responses

    Returns:
        Configured StreamCache instance
    """
    return StreamCache(
        ttl_seconds=ttl_seconds, enable_partial_caching=enable_partial_caching
    )
