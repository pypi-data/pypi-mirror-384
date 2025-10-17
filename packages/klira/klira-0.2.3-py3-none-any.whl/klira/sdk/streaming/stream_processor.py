"""Core stream processor for real-time LLM streaming with guardrails."""

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, AsyncIterator, Callable
from collections import deque
import threading

from .types import (
    StreamChunk,
    StreamEvent,
    StreamEventType,
    StreamMetrics,
    StreamConfig,
)
from .stream_guardrails import StreamGuardrailsProcessor
from .stream_cache import StreamCache
from ..cache.cache_hierarchy import CacheHierarchy

logger = logging.getLogger("klira.streaming.processor")


class StreamProcessor:
    """Core processor for streaming LLM operations with integrated guardrails and caching.

    Features:
    - Real-time chunk processing with guardrails
    - Partial response caching for performance
    - Backpressure handling and flow control
    - Comprehensive metrics and monitoring
    - Framework-agnostic streaming interface
    """

    def __init__(self, config: Optional[StreamConfig] = None):
        """Initialize stream processor.

        Args:
            config: Stream processing configuration
        """
        self.config = config or StreamConfig()

        # Validate configuration
        config_errors = self.config.validate()
        if config_errors:
            raise ValueError(f"Invalid stream config: {', '.join(config_errors)}")

        # Core components
        self._guardrails_processor: Optional[StreamGuardrailsProcessor] = None
        self._stream_cache: Optional[StreamCache] = None
        self._cache_hierarchy: Optional[CacheHierarchy] = None

        # State management
        self._active_streams: Dict[str, StreamMetrics] = {}
        self._stream_buffers: Dict[str, deque[StreamChunk]] = {}
        self._event_handlers: List[Callable[[StreamEvent], None]] = []
        self._lock = threading.RLock()

        # Background tasks
        self._metrics_task: Optional[asyncio.Task[None]] = None
        self._cleanup_task: Optional[asyncio.Task[None]] = None

        self._initialize_components()
        logger.info(f"StreamProcessor initialized with config: {self.config}")

    def _initialize_components(self) -> None:
        """Initialize streaming components."""
        try:
            # Initialize guardrails processor if enabled
            if self.config.enable_guardrails:
                self._guardrails_processor = StreamGuardrailsProcessor(
                    validation_interval=self.config.validation_interval,
                    realtime_validation=self.config.realtime_validation,
                )

            # Initialize stream cache if enabled
            if self.config.enable_caching:
                self._stream_cache = StreamCache(
                    ttl_seconds=self.config.cache_ttl_seconds,
                    enable_partial_caching=self.config.cache_partial_responses,
                )

                # Try to get cache hierarchy from existing infrastructure
                try:
                    from ..cache.cache_hierarchy import CacheHierarchy

                    self._cache_hierarchy = CacheHierarchy()
                except Exception as e:
                    logger.debug(f"Cache hierarchy not available: {e}")

            # Start background tasks
            if self.config.enable_metrics:
                self._start_background_tasks()

        except Exception as e:
            logger.error(f"Failed to initialize stream processor components: {e}")
            raise

    async def process_stream(
        self,
        stream_id: Optional[str] = None,
        input_stream: Optional[AsyncIterator[Any]] = None,
        initial_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamEvent]:
        """Process a streaming LLM response with integrated guardrails and caching.

        Args:
            stream_id: Unique stream identifier
            input_stream: Async iterator of stream chunks
            initial_prompt: Initial prompt for caching
            **kwargs: Additional processing options

        Yields:
            StreamEvent: Stream events including chunks, metrics, and errors
        """
        if not stream_id:
            stream_id = str(uuid.uuid4())

        if input_stream is None:
            raise ValueError("input_stream is required for stream processing")

        # Initialize stream metrics
        metrics = StreamMetrics(stream_id=stream_id, start_time=time.time())

        with self._lock:
            self._active_streams[stream_id] = metrics
            self._stream_buffers[stream_id] = deque(maxlen=self.config.buffer_size)

        try:
            # Emit start event
            yield StreamEvent.start(stream_id, initial_prompt=initial_prompt)

            # Check cache for partial responses
            cached_content = None
            if self.config.enable_caching and initial_prompt:
                cached_content = await self._check_cache(stream_id, initial_prompt)
                if cached_content:
                    metrics.cache_hits += 1
                    yield StreamEvent(
                        event_type=StreamEventType.CACHE_HIT,
                        data={"content": cached_content},
                        stream_id=stream_id,
                    )

            # Process stream chunks
            full_content = cached_content or ""
            async for chunk_data in input_stream:
                try:
                    # Convert to StreamChunk
                    chunk = await self._process_chunk_data(chunk_data)
                    if chunk.is_empty():
                        continue

                    # Apply guardrails if enabled
                    validation_result = None
                    if self._guardrails_processor:
                        validation_result = (
                            await self._guardrails_processor.validate_chunk(
                                stream_id, chunk, full_content
                            )
                        )
                        metrics.guardrail_checks += 1

                        if not validation_result.is_valid:
                            metrics.guardrail_blocks += 1
                            yield StreamEvent(
                                event_type=StreamEventType.GUARDRAIL_BLOCK,
                                data={
                                    "blocked_content": validation_result.blocked_content,
                                    "reasons": validation_result.violation_reasons,
                                },
                                stream_id=stream_id,
                            )
                            continue

                        if validation_result.modified_content:
                            chunk.content = validation_result.modified_content
                            yield StreamEvent(
                                event_type=StreamEventType.GUARDRAIL_MODIFY,
                                data={
                                    "original": chunk_data,
                                    "modified": chunk.content,
                                },
                                stream_id=stream_id,
                            )

                    # Update metrics and buffer
                    metrics.add_chunk(chunk)
                    self._stream_buffers[stream_id].append(chunk)
                    full_content += chunk.content

                    # Cache partial responses
                    if self._stream_cache and self.config.cache_partial_responses:
                        await self._stream_cache.cache_partial(stream_id, full_content)

                    # Emit chunk event
                    yield StreamEvent.chunk(
                        stream_id, chunk, validation=validation_result
                    )

                    # Check for backpressure
                    if len(self._stream_buffers[stream_id]) >= self.config.buffer_size:
                        await asyncio.sleep(0.01)  # Small delay for backpressure

                except Exception as e:
                    logger.error(f"Error processing chunk in stream {stream_id}: {e}")
                    metrics.error_count += 1
                    yield StreamEvent.error(stream_id, e)

            # Mark completion
            metrics.mark_complete()

            # Cache final response
            if self._stream_cache and initial_prompt and full_content:
                await self._stream_cache.cache_final(initial_prompt, full_content)

            # Emit completion event
            yield StreamEvent.complete(stream_id, full_content)

            # Emit final metrics
            if self.config.enable_metrics:
                yield StreamEvent(
                    event_type=StreamEventType.METRICS,
                    data=metrics.to_dict(),
                    stream_id=stream_id,
                )

        except Exception as e:
            logger.error(f"Error in stream processing {stream_id}: {e}")
            metrics.error_count += 1
            yield StreamEvent.error(stream_id, e)

        finally:
            # Cleanup
            with self._lock:
                self._active_streams.pop(stream_id, None)
                self._stream_buffers.pop(stream_id, None)

    async def _process_chunk_data(self, chunk_data: Any) -> StreamChunk:
        """Convert raw chunk data to StreamChunk."""
        if isinstance(chunk_data, StreamChunk):
            return chunk_data

        if isinstance(chunk_data, str):
            return StreamChunk(content=chunk_data)

        if isinstance(chunk_data, dict):
            content = chunk_data.get("content", "")
            if isinstance(content, str):
                return StreamChunk(
                    content=content,
                    token_count=chunk_data.get("token_count"),
                    metadata=chunk_data.get("metadata", {}),
                )

        # Try to extract content from common streaming formats
        if hasattr(chunk_data, "choices") and chunk_data.choices:
            # OpenAI streaming format
            choice = chunk_data.choices[0]
            if hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                content = choice.delta.content or ""
                return StreamChunk(content=content)

        # Default fallback
        return StreamChunk(content=str(chunk_data))

    async def _check_cache(self, stream_id: str, prompt: str) -> Optional[str]:
        """Check cache for existing responses."""
        if not self._stream_cache:
            return None

        try:
            # Check stream cache first
            cached = await self._stream_cache.get_cached_response(prompt)
            if cached:
                logger.debug(f"Cache hit for stream {stream_id}")
                return cached

            # Check cache hierarchy if available
            if self._cache_hierarchy:
                cache_key = f"stream:response:{hash(prompt)}"
                cached = await self._cache_hierarchy.aget(cache_key)
                if cached:
                    logger.debug(f"Cache hierarchy hit for stream {stream_id}")
                    return str(cached) if cached is not None else None

        except Exception as e:
            logger.warning(f"Cache check failed for stream {stream_id}: {e}")

        return None

    def add_event_handler(self, handler: Callable[[StreamEvent], None]) -> None:
        """Add event handler for stream events."""
        self._event_handlers.append(handler)

    def remove_event_handler(self, handler: Callable[[StreamEvent], None]) -> None:
        """Remove event handler."""
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)

    def get_active_streams(self) -> Dict[str, StreamMetrics]:
        """Get metrics for all active streams."""
        with self._lock:
            return dict(self._active_streams)

    def get_stream_metrics(self, stream_id: str) -> Optional[StreamMetrics]:
        """Get metrics for specific stream."""
        with self._lock:
            return self._active_streams.get(stream_id)

    def _start_background_tasks(self) -> None:
        """Start background monitoring tasks."""
        try:
            self._metrics_task = asyncio.create_task(self._metrics_monitor())
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        except Exception as e:
            logger.warning(f"Failed to start background tasks: {e}")

    async def _metrics_monitor(self) -> None:
        """Background task for metrics monitoring."""
        while True:
            try:
                await asyncio.sleep(self.config.metrics_interval)

                with self._lock:
                    for stream_id, metrics in self._active_streams.items():
                        # Emit periodic metrics for long-running streams
                        if metrics.duration_seconds and metrics.duration_seconds > 5:
                            event = StreamEvent(
                                event_type=StreamEventType.METRICS,
                                data=metrics.to_dict(),
                                stream_id=stream_id,
                            )
                            # Notify handlers
                            for handler in self._event_handlers:
                                try:
                                    handler(event)
                                except Exception as e:
                                    logger.warning(f"Event handler error: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics monitor error: {e}")

    async def _periodic_cleanup(self) -> None:
        """Background task for periodic cleanup."""
        while True:
            try:
                await asyncio.sleep(60)  # Cleanup every minute

                current_time = time.time()
                expired_streams = []

                with self._lock:
                    for stream_id, metrics in self._active_streams.items():
                        # Mark streams as expired if they've been inactive too long
                        if (
                            current_time - metrics.start_time
                        ) > self.config.timeout_seconds:
                            expired_streams.append(stream_id)

                # Cleanup expired streams
                for stream_id in expired_streams:
                    logger.warning(f"Cleaning up expired stream: {stream_id}")
                    with self._lock:
                        self._active_streams.pop(stream_id, None)
                        self._stream_buffers.pop(stream_id, None)

                # Cleanup cache if available
                if self._stream_cache:
                    await self._stream_cache.cleanup_expired()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")

    async def shutdown(self) -> None:
        """Shutdown stream processor and cleanup resources."""
        logger.info("Shutting down stream processor...")

        # Cancel background tasks
        if self._metrics_task:
            self._metrics_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # Wait for tasks to complete
        try:
            if self._metrics_task:
                await self._metrics_task
            if self._cleanup_task:
                await self._cleanup_task
        except asyncio.CancelledError:
            pass

        # Cleanup components
        if self._stream_cache:
            await self._stream_cache.cleanup_expired()

        # Clear state
        with self._lock:
            self._active_streams.clear()
            self._stream_buffers.clear()
            self._event_handlers.clear()

        logger.info("Stream processor shutdown complete")


# Factory function for easy instantiation
def create_stream_processor(config: Optional[StreamConfig] = None) -> StreamProcessor:
    """Create stream processor with configuration.

    Args:
        config: Stream processing configuration

    Returns:
        Configured StreamProcessor instance
    """
    return StreamProcessor(config=config)
