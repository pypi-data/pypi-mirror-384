"""Streaming guardrails processor for real-time policy enforcement."""

import logging
import time
from typing import Dict, Optional, Deque, Any
from collections import deque
import threading

from .types import StreamChunk, StreamValidationResult
from ..guardrails.engine import GuardrailsEngine
from ..guardrails.fast_rules import FastRulesEngine

logger = logging.getLogger("klira.streaming.guardrails")


class StreamGuardrailsProcessor:
    """Real-time guardrails processor for streaming content.

    Features:
    - Real-time validation of streaming chunks
    - Partial content analysis with context buffering
    - Intelligent policy enforcement for streaming data
    - Performance-optimized validation with caching
    - Backpressure handling for policy evaluation
    """

    def __init__(
        self,
        validation_interval: int = 1,
        realtime_validation: bool = True,
        buffer_size: int = 50,
        max_context_length: int = 2000,
    ):
        """Initialize streaming guardrails processor.

        Args:
            validation_interval: Validate every N chunks
            realtime_validation: Enable real-time validation
            buffer_size: Context buffer size for partial analysis
            max_context_length: Maximum context length for analysis
        """
        self.validation_interval = validation_interval
        self.realtime_validation = realtime_validation
        self.buffer_size = buffer_size
        self.max_context_length = max_context_length

        # Core components
        self._guardrails_engine: Optional[GuardrailsEngine] = None
        self._fast_rules: Optional[FastRulesEngine] = None

        # State management
        self._stream_contexts: Dict[str, Deque[StreamChunk]] = {}
        self._validation_cache: Dict[str, StreamValidationResult] = {}
        self._chunk_counters: Dict[str, int] = {}
        self._lock = threading.RLock()

        # Performance tracking
        self._validation_times: Deque[float] = deque(maxlen=100)
        self._cache_hits = 0
        self._cache_misses = 0

        self._initialize_components()
        logger.info(
            f"StreamGuardrailsProcessor initialized with interval={validation_interval}"
        )

    def _initialize_components(self) -> None:
        """Initialize guardrails components."""
        try:
            # Get guardrails engine instance
            self._guardrails_engine = GuardrailsEngine.get_instance()
            if not self._guardrails_engine:
                logger.warning(
                    "GuardrailsEngine not available - creating minimal instance"
                )
                # Could create a minimal fallback engine here if needed

            # Initialize fast rules for quick checks
            try:
                from ..config import get_policies_path

                policies_path = get_policies_path()
                self._fast_rules = FastRulesEngine(policies_path)
            except Exception as e:
                logger.warning(f"FastRulesEngine not available: {e}")

        except Exception as e:
            logger.error(f"Failed to initialize streaming guardrails: {e}")
            # Continue with degraded functionality

    async def validate_chunk(
        self, stream_id: str, chunk: StreamChunk, full_context: str = ""
    ) -> StreamValidationResult:
        """Validate a streaming chunk with context awareness.

        Args:
            stream_id: Stream identifier
            chunk: Chunk to validate
            full_context: Full context up to this point

        Returns:
            StreamValidationResult: Validation result with any necessary actions
        """
        start_time = time.time()

        # Initialize stream context if needed
        with self._lock:
            if stream_id not in self._stream_contexts:
                self._stream_contexts[stream_id] = deque(maxlen=self.buffer_size)
                self._chunk_counters[stream_id] = 0

            self._chunk_counters[stream_id] += 1
            chunk_count = self._chunk_counters[stream_id]

        try:
            # Add chunk to context buffer
            self._stream_contexts[stream_id].append(chunk)

            # Determine if validation is needed
            should_validate = self._should_validate_chunk(stream_id, chunk_count)

            if not should_validate:
                # Return cached result or allow by default
                cached_result = self._get_cached_result(stream_id, chunk.content)
                if cached_result:
                    self._cache_hits += 1
                    return cached_result

                # Default allow for non-validated chunks
                return StreamValidationResult(
                    is_valid=True,
                    confidence_score=0.5,  # Lower confidence for non-validated
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

            # Perform validation
            validation_result = await self._validate_with_context(
                stream_id, chunk, full_context
            )

            # Cache result for similar content
            self._cache_result(stream_id, chunk.content, validation_result)
            self._cache_misses += 1

            # Update performance metrics
            processing_time = (time.time() - start_time) * 1000
            validation_result.processing_time_ms = processing_time
            self._validation_times.append(processing_time)

            return validation_result

        except Exception as e:
            logger.error(f"Error validating chunk in stream {stream_id}: {e}")
            # Fail safe - allow content on validation errors
            return StreamValidationResult(
                is_valid=True,
                violation_reasons=[f"Validation error: {str(e)}"],
                confidence_score=0.0,
                processing_time_ms=(time.time() - start_time) * 1000,
            )

    def _should_validate_chunk(self, stream_id: str, chunk_count: int) -> bool:
        """Determine if a chunk should be validated."""
        if not self.realtime_validation:
            return False

        # Always validate first chunk
        if chunk_count == 1:
            return True

        # Validate based on interval
        return chunk_count % self.validation_interval == 0

    async def _validate_with_context(
        self, stream_id: str, chunk: StreamChunk, full_context: str
    ) -> StreamValidationResult:
        """Perform validation with full context awareness."""

        # Quick fast rules check first
        if self._fast_rules:
            fast_result = await self._validate_with_fast_rules(chunk, full_context)
            if not fast_result.is_valid:
                return fast_result

        # Full guardrails validation if available
        if self._guardrails_engine:
            return await self._validate_with_guardrails_engine(chunk, full_context)

        # Default validation (allow all)
        return StreamValidationResult(is_valid=True, confidence_score=1.0)

    async def _validate_with_fast_rules(
        self, chunk: StreamChunk, full_context: str
    ) -> StreamValidationResult:
        """Validate using fast rules engine."""
        try:
            # Check if fast rules engine is available
            if self._fast_rules is None:
                return StreamValidationResult(is_valid=True, confidence_score=0.5)

            # Check the chunk content
            chunk_result = self._fast_rules.evaluate(chunk.content)

            # Check accumulated context if chunk is clean
            if chunk_result.get("allowed", True) and full_context:
                # Use recent context for evaluation (limit length for performance)
                recent_context = full_context[-self.max_context_length :]
                context_result = self._fast_rules.evaluate(recent_context)

                if not context_result.get("allowed", True):
                    # Get violation reason from violations list
                    violation_reason = "Context violation"
                    violations = context_result.get("violations", [])
                    if violations:
                        violation_reason = f"Context violation: {violations[0].get('policy_id', 'unknown')}"

                    return StreamValidationResult(
                        is_valid=False,
                        blocked_content=[chunk.content],
                        violation_reasons=[violation_reason],
                        confidence_score=context_result.get("confidence", 1.0),
                    )

            if not chunk_result.get("allowed", True):
                # Get violation reason from violations list
                violation_reason = "Policy violation"
                violations = chunk_result.get("violations", [])
                if violations:
                    violation_reason = violations[0].get("policy_id", "unknown")

                return StreamValidationResult(
                    is_valid=False,
                    blocked_content=[chunk.content],
                    violation_reasons=[violation_reason],
                    confidence_score=chunk_result.get("confidence", 1.0),
                )

            return StreamValidationResult(
                is_valid=True, confidence_score=chunk_result.get("confidence", 1.0)
            )

        except Exception as e:
            logger.warning(f"Fast rules validation failed: {e}")
            return StreamValidationResult(is_valid=True, confidence_score=0.5)

    async def _validate_with_guardrails_engine(
        self, chunk: StreamChunk, full_context: str
    ) -> StreamValidationResult:
        """Validate using full guardrails engine."""
        try:
            # For streaming, we validate the chunk in context
            content_to_validate = chunk.content

            # Include recent context for better analysis
            if full_context:
                recent_context = full_context[-self.max_context_length :]
                content_to_validate = f"{recent_context}{chunk.content}"

            # Process with guardrails engine
            if self._guardrails_engine is None:
                return StreamValidationResult(is_valid=True, confidence_score=0.5)

            result = await self._guardrails_engine.process_message(
                content_to_validate,
                {"stream_mode": True, "chunk_content": chunk.content},
            )

            if not result.get("allowed", True):
                return StreamValidationResult(
                    is_valid=False,
                    blocked_content=[chunk.content],
                    violation_reasons=[str(result.get("reason", "Policy violation"))],
                    confidence_score=result.get("confidence", 1.0),
                )

            # Check for content modification suggestions
            modified_content = result.get("modified_content")
            if modified_content and modified_content != chunk.content:
                return StreamValidationResult(
                    is_valid=True,
                    modified_content=str(modified_content)
                    if modified_content
                    else None,
                    confidence_score=result.get("confidence", 1.0),
                )

            return StreamValidationResult(
                is_valid=True, confidence_score=result.get("confidence", 1.0)
            )

        except Exception as e:
            logger.error(f"Guardrails engine validation failed: {e}")
            # Fail safe - allow content
            return StreamValidationResult(is_valid=True, confidence_score=0.0)

    def _get_cached_result(
        self, stream_id: str, content: str
    ) -> Optional[StreamValidationResult]:
        """Get cached validation result for similar content."""
        cache_key = f"{stream_id}:{hash(content[:100])}"  # Use content hash for caching
        return self._validation_cache.get(cache_key)

    def _cache_result(
        self, stream_id: str, content: str, result: StreamValidationResult
    ) -> None:
        """Cache validation result for future use."""
        cache_key = f"{stream_id}:{hash(content[:100])}"

        # Limit cache size
        if len(self._validation_cache) > 1000:
            # Remove oldest entries (simple FIFO)
            oldest_keys = list(self._validation_cache.keys())[:100]
            for key in oldest_keys:
                self._validation_cache.pop(key, None)

        self._validation_cache[cache_key] = result

    async def validate_complete_stream(
        self, stream_id: str, final_content: str
    ) -> StreamValidationResult:
        """Validate the complete stream content for final approval.

        Args:
            stream_id: Stream identifier
            final_content: Complete stream content

        Returns:
            StreamValidationResult: Final validation result
        """
        if not self._guardrails_engine:
            return StreamValidationResult(is_valid=True, confidence_score=1.0)

        try:
            # Perform final validation on complete content
            result = await self._guardrails_engine.process_message(
                final_content, {"stream_mode": False, "final_validation": True}
            )

            if not result.get("allowed", True):
                return StreamValidationResult(
                    is_valid=False,
                    blocked_content=[final_content],
                    violation_reasons=[
                        str(result.get("reason", "Final validation failed"))
                    ],
                    confidence_score=result.get("confidence", 1.0),
                )

            return StreamValidationResult(
                is_valid=True, confidence_score=result.get("confidence", 1.0)
            )

        except Exception as e:
            logger.error(f"Final stream validation failed for {stream_id}: {e}")
            return StreamValidationResult(is_valid=True, confidence_score=0.0)

    def get_stream_stats(self) -> Dict[str, Any]:
        """Get streaming guardrails statistics."""
        with self._lock:
            total_cache_requests = self._cache_hits + self._cache_misses
            cache_hit_rate = (
                (self._cache_hits / total_cache_requests * 100)
                if total_cache_requests > 0
                else 0
            )

            avg_validation_time = (
                sum(self._validation_times) / len(self._validation_times)
                if self._validation_times
                else 0
            )

            return {
                "active_streams": len(self._stream_contexts),
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "cache_hit_rate": round(cache_hit_rate, 2),
                "avg_validation_time_ms": round(avg_validation_time, 2),
                "total_cached_results": len(self._validation_cache),
                "guardrails_engine_available": self._guardrails_engine is not None,
                "fast_rules_available": self._fast_rules is not None,
            }

    def cleanup_stream(self, stream_id: str) -> None:
        """Cleanup resources for a completed stream."""
        with self._lock:
            self._stream_contexts.pop(stream_id, None)
            self._chunk_counters.pop(stream_id, None)

            # Remove cached results for this stream
            keys_to_remove = [
                k
                for k in self._validation_cache.keys()
                if k.startswith(f"{stream_id}:")
            ]
            for key in keys_to_remove:
                self._validation_cache.pop(key, None)

    def cleanup_all(self) -> None:
        """Cleanup all streaming guardrails resources."""
        with self._lock:
            self._stream_contexts.clear()
            self._chunk_counters.clear()
            self._validation_cache.clear()
            self._validation_times.clear()
            self._cache_hits = 0
            self._cache_misses = 0


# Factory function for easy instantiation
def create_stream_guardrails_processor(
    validation_interval: int = 1, realtime_validation: bool = True
) -> StreamGuardrailsProcessor:
    """Create streaming guardrails processor with configuration.

    Args:
        validation_interval: Validate every N chunks
        realtime_validation: Enable real-time validation

    Returns:
        Configured StreamGuardrailsProcessor instance
    """
    return StreamGuardrailsProcessor(
        validation_interval=validation_interval, realtime_validation=realtime_validation
    )
