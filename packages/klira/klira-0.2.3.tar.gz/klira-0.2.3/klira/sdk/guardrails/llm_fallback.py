"""Provides caching and orchestration for LLM-based policy evaluations."""

import time
import hashlib
import logging
import re
from typing import Dict, Any, Optional, OrderedDict, List, Tuple, Union
from difflib import SequenceMatcher

# Import the protocol and result type defined in llm_service
from .llm_service import LLMServiceProtocol, LLMEvaluationResult, DefaultLLMService

logger = logging.getLogger("klira.guardrails.llm_evaluator")


class LRUCache:
    """Simple Least Recently Used (LRU) cache implementation.

    Uses an OrderedDict to maintain insertion/access order.
    """

    capacity: int
    cache: OrderedDict[str, LLMEvaluationResult]

    def __init__(self, capacity: int = 1000):
        """Initializes the LRU Cache.

        Args:
            capacity: The maximum number of items to store in the cache.
        """
        if capacity <= 0:
            raise ValueError("Cache capacity must be positive")
        self.capacity = capacity
        # Use OrderedDict for efficient LRU tracking
        self.cache = OrderedDict()

    def get(self, key: str) -> Optional[LLMEvaluationResult]:
        """Retrieves an item from the cache, updating its recency.

        Args:
            key: The key of the item to retrieve.

        Returns:
            The cached evaluation result, or None if the key is not found.
        """
        if key in self.cache:
            # Move the accessed item to the end to mark it as recently used
            self.cache.move_to_end(key)
            logger.debug(f"Cache hit for key: {key}")
            return self.cache[key]
        logger.debug(f"Cache miss for key: {key}")
        return None

    def set(self, key: str, value: LLMEvaluationResult) -> None:
        """Adds or updates an item in the cache, enforcing capacity.

        Args:
            key: The key of the item to add/update.
            value: The evaluation result to store.
        """
        if key in self.cache:
            # Move existing key to the end before updating
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.capacity:
            # Remove the least recently used item (first item in OrderedDict)
            oldest_key, _ = self.cache.popitem(last=False)
            logger.debug(f"Cache capacity reached. Evicted oldest key: {oldest_key}")

        self.cache[key] = value
        logger.debug(f"Cached result for key: {key}")

    def get_all_items(self) -> List[Tuple[str, LLMEvaluationResult]]:
        """Get all cache items for semantic search."""
        return list(self.cache.items())


class SemanticCache:
    """Enhanced cache with semantic similarity detection for improved hit rates."""

    def __init__(
        self, similarity_threshold: float = 0.85, max_semantic_search: int = 100
    ):
        """Initialize semantic cache.

        Args:
            similarity_threshold: Minimum similarity score (0.0-1.0) to consider a cache hit
            max_semantic_search: Maximum number of cache entries to search for similarity
        """
        self.similarity_threshold = similarity_threshold
        self.max_semantic_search = max_semantic_search
        self._text_cache: OrderedDict[str, str] = (
            OrderedDict()
        )  # cache_key -> normalized_text

    def _normalize_text(self, text: str) -> str:
        """Normalize text for better similarity matching."""
        # Convert to lowercase
        normalized = text.lower().strip()
        # Remove extra whitespace
        normalized = re.sub(r"\s+", " ", normalized)
        # Remove common punctuation that doesn't affect meaning
        normalized = re.sub(r"[.!?;,]+", "", normalized)
        return normalized

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)

        # Use SequenceMatcher for fuzzy string matching
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity

    def find_similar(
        self, text: str, cache: LRUCache
    ) -> Optional[Tuple[str, LLMEvaluationResult, float]]:
        """Find similar cached content.

        Returns:
            Tuple of (cache_key, result, similarity_score) if found, None otherwise
        """
        if len(cache.cache) == 0:
            return None

        # Get recent cache items to search (limit for performance)
        cache_items = list(cache.cache.items())[-self.max_semantic_search :]

        best_match = None
        best_similarity = 0.0

        for cache_key, result in cache_items:
            # Get the original text for this cache key if we have it
            if cache_key in self._text_cache:
                cached_text = self._text_cache[cache_key]
                similarity = self._calculate_similarity(text, cached_text)

                if (
                    similarity > best_similarity
                    and similarity >= self.similarity_threshold
                ):
                    best_similarity = similarity
                    best_match = (cache_key, result, similarity)

        if best_match:
            logger.debug(
                f"Semantic cache hit: similarity={best_similarity:.3f} for key: {best_match[0]}"
            )

        return best_match

    def store_text(self, cache_key: str, text: str) -> None:
        """Store the original text for semantic matching."""
        self._text_cache[cache_key] = text

        # Implement simple cleanup to prevent unlimited growth
        if len(self._text_cache) > self.max_semantic_search * 2:
            # Remove oldest entries
            items_to_remove = len(self._text_cache) - self.max_semantic_search
            for _ in range(items_to_remove):
                self._text_cache.popitem(last=False)


class LLMFallback:
    """Orchestrates LLM-based policy evaluations with enhanced semantic caching.

    Uses a configured LLM service (conforming to LLMServiceProtocol) to perform
    evaluations and caches the results using an LRU cache with semantic similarity detection.
    """

    llm_service: LLMServiceProtocol
    cache: LRUCache
    semantic_cache: Optional[SemanticCache]

    def __init__(
        self,
        llm_service: Optional[LLMServiceProtocol] = None,
        cache_size: int = 1000,
        semantic_similarity_threshold: float = 0.85,
        enable_semantic_cache: bool = True,
    ):
        """Initializes the LLM Fallback Evaluator.

        Args:
            llm_service: The LLM service to use for evaluations.
                         Defaults to DefaultLLMService (passthrough) if None.
            cache_size: The capacity of the LRU cache for storing evaluation results.
            semantic_similarity_threshold: Minimum similarity for semantic cache hits (0.0-1.0).
            enable_semantic_cache: Whether to enable semantic similarity caching.
        """
        if llm_service is None:
            logger.warning(
                "No LLM service provided to LLMFallback, using DefaultLLMService (passthrough). LLM checks will not be performed."
            )
            self.llm_service = DefaultLLMService()
        else:
            self.llm_service = llm_service
        self.cache = LRUCache(cache_size)

        self.enable_semantic_cache = enable_semantic_cache
        if enable_semantic_cache:
            self.semantic_cache = SemanticCache(
                similarity_threshold=semantic_similarity_threshold,
                max_semantic_search=min(
                    100, cache_size // 10
                ),  # Search up to 10% of cache
            )
            logger.info(
                f"LLMFallback initialized with semantic caching (threshold={semantic_similarity_threshold})"
            )
        else:
            self.semantic_cache = None
            logger.info("LLMFallback initialized without semantic caching")

        logger.info(f"LLMFallback initialized with cache size: {cache_size}")

    def _generate_cache_key(
        self, message: str, context: Optional[Dict[str, Any]]
    ) -> str:
        """Generates a cache key based on the message and relevant context.

        Args:
            message: The message content being evaluated.
            context: The evaluation context.

        Returns:
            A unique MD5 hash representing the evaluation request.
        """
        # Consider including more context if policies depend on it, e.g., active policies
        context_elements = context or {}
        context_id = context_elements.get("conversation_id", "no_conv_id")
        active_policies = sorted(
            context_elements.get("active_policies", [])
        )  # Sort for consistency

        # Combine message and key context elements for hashing
        key_str = (
            f"msg:{message}::conv:{context_id}::policies:{','.join(active_policies)}"
        )
        return hashlib.md5(key_str.encode("utf-8")).hexdigest()

    async def evaluate(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        fast_result: Optional[Dict[str, Any]] = None,
    ) -> LLMEvaluationResult:
        """Performs LLM evaluation, utilizing both exact and semantic caching.

        Args:
            message: The message content to evaluate.
            context: The evaluation context dictionary.
            fast_result: Optional results from preceding fast rule checks.

        Returns:
            The structured evaluation result from the LLM service.
        """
        if isinstance(self.llm_service, DefaultLLMService):
            # No need to cache default results
            return await self.llm_service.evaluate(message, context, fast_result)

        cache_key = self._generate_cache_key(message, context)

        # Check exact cache first
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.debug(f"Exact cache hit for key: {cache_key}")
            return cached_result

        # Check semantic cache if enabled
        if self.enable_semantic_cache and self.semantic_cache:
            semantic_match = self.semantic_cache.find_similar(message, self.cache)
            if semantic_match:
                cache_key_match, result, similarity = semantic_match
                logger.info(
                    f"Semantic cache hit (similarity={similarity:.3f}) for message: {message[:50]}..."
                )

                # Move the matched item to end (mark as recently used)
                self.cache.cache.move_to_end(cache_key_match)

                # Store this exact query in cache for future exact matches
                self.cache.set(cache_key, result)
                if self.semantic_cache:
                    self.semantic_cache.store_text(cache_key, message)

                return result

        # If not cached, call the LLM service's evaluate method
        logger.info(f"Performing LLM evaluation for cache key: {cache_key}")
        start_time = time.monotonic()
        try:
            llm_result = await self.llm_service.evaluate(
                message=message, context=context, fast_result=fast_result
            )
            elapsed = (time.monotonic() - start_time) * 1000
            logger.info(
                f"LLM evaluation completed in {elapsed:.2f} ms for key: {cache_key}"
            )

            # Cache the successful result
            self.cache.set(cache_key, llm_result)

            # Store text for semantic matching if enabled
            if self.enable_semantic_cache and self.semantic_cache:
                self.semantic_cache.store_text(cache_key, message)

            return llm_result

        except Exception as e:
            elapsed = (time.monotonic() - start_time) * 1000
            logger.error(
                f"LLM service evaluation failed after {elapsed:.2f} ms for key {cache_key}: {e}",
                exc_info=True,
            )
            # Return a default non-compliant result on error
            return LLMEvaluationResult(
                allowed=False,
                confidence=0.0,
                violated_policies=[],
                action="block",
                reasoning=f"LLM evaluation failed: {str(e)}",
                response=None,  # No raw response available on error
            )

    def get_cache_stats(self) -> Dict[str, Union[int, float, bool]]:
        """Get cache statistics including semantic cache performance."""
        stats: Dict[str, Union[int, float, bool]] = {
            "exact_cache_size": len(self.cache.cache),
            "exact_cache_capacity": self.cache.capacity,
            "semantic_cache_enabled": self.enable_semantic_cache,
        }

        if self.enable_semantic_cache and self.semantic_cache:
            stats.update(
                {
                    "semantic_cache_size": len(self.semantic_cache._text_cache),
                    "semantic_threshold": self.semantic_cache.similarity_threshold,
                    "max_semantic_search": self.semantic_cache.max_semantic_search,
                }
            )

        return stats
