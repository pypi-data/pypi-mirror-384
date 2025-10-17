"""Core types and interfaces for streaming LLM support."""

import time
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, AsyncIterator
from dataclasses import dataclass, field
import uuid


class StreamEventType(Enum):
    """Types of streaming events."""

    START = "stream_start"  # Stream initialization
    CHUNK = "stream_chunk"  # Content chunk received
    COMPLETE = "stream_complete"  # Stream completed successfully
    ERROR = "stream_error"  # Error occurred
    GUARDRAIL_BLOCK = "guardrail_block"  # Content blocked by guardrails
    GUARDRAIL_MODIFY = "guardrail_modify"  # Content modified by guardrails
    CACHE_HIT = "cache_hit"  # Partial content served from cache
    METRICS = "metrics"  # Performance metrics update


@dataclass
class StreamChunk:
    """Represents a chunk of streaming content."""

    content: str
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    token_count: Optional[int] = None
    is_final: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        """Return content length."""
        return len(self.content)

    def is_empty(self) -> bool:
        """Check if chunk is empty."""
        return not self.content.strip()


@dataclass
class StreamEvent:
    """Represents a streaming event."""

    event_type: StreamEventType
    data: Any
    stream_id: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def start(cls, stream_id: str, **metadata: Any) -> "StreamEvent":
        """Create stream start event."""
        return cls(
            event_type=StreamEventType.START,
            data={"status": "started"},
            stream_id=stream_id,
            metadata=metadata,
        )

    @classmethod
    def chunk(
        cls, stream_id: str, chunk: StreamChunk, **metadata: Any
    ) -> "StreamEvent":
        """Create stream chunk event."""
        return cls(
            event_type=StreamEventType.CHUNK,
            data=chunk,
            stream_id=stream_id,
            metadata=metadata,
        )

    @classmethod
    def complete(
        cls, stream_id: str, final_content: str, **metadata: Any
    ) -> "StreamEvent":
        """Create stream complete event."""
        return cls(
            event_type=StreamEventType.COMPLETE,
            data={"final_content": final_content, "status": "completed"},
            stream_id=stream_id,
            metadata=metadata,
        )

    @classmethod
    def error(cls, stream_id: str, error: Exception, **metadata: Any) -> "StreamEvent":
        """Create stream error event."""
        return cls(
            event_type=StreamEventType.ERROR,
            data={"error": str(error), "error_type": type(error).__name__},
            stream_id=stream_id,
            metadata=metadata,
        )


@dataclass
class StreamMetrics:
    """Performance metrics for streaming operations."""

    stream_id: str
    start_time: float
    end_time: Optional[float] = None
    total_chunks: int = 0
    total_tokens: int = 0
    total_bytes: int = 0
    guardrail_checks: int = 0
    guardrail_blocks: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    error_count: int = 0

    def __post_init__(self) -> None:
        """Initialize computed fields."""
        if not hasattr(self, "_chunk_timestamps"):
            self._chunk_timestamps: List[float] = []

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate stream duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second."""
        duration = self.duration_seconds
        if duration and duration > 0:
            return self.total_tokens / duration
        return 0.0

    @property
    def chunks_per_second(self) -> float:
        """Calculate chunks per second."""
        duration = self.duration_seconds
        if duration and duration > 0:
            return self.total_chunks / duration
        return 0.0

    @property
    def average_chunk_size(self) -> float:
        """Calculate average chunk size in tokens."""
        if self.total_chunks > 0:
            return self.total_tokens / self.total_chunks
        return 0.0

    @property
    def guardrail_block_rate(self) -> float:
        """Calculate guardrail block rate."""
        if self.guardrail_checks > 0:
            return (self.guardrail_blocks / self.guardrail_checks) * 100
        return 0.0

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests > 0:
            return (self.cache_hits / total_cache_requests) * 100
        return 0.0

    def add_chunk(self, chunk: StreamChunk) -> None:
        """Add chunk metrics."""
        self.total_chunks += 1
        self.total_bytes += len(chunk.content)
        if chunk.token_count:
            self.total_tokens += chunk.token_count
        self._chunk_timestamps.append(chunk.timestamp)

    def mark_complete(self) -> None:
        """Mark stream as completed."""
        self.end_time = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "stream_id": self.stream_id,
            "duration_seconds": self.duration_seconds,
            "total_chunks": self.total_chunks,
            "total_tokens": self.total_tokens,
            "total_bytes": self.total_bytes,
            "tokens_per_second": self.tokens_per_second,
            "chunks_per_second": self.chunks_per_second,
            "average_chunk_size": self.average_chunk_size,
            "guardrail_checks": self.guardrail_checks,
            "guardrail_blocks": self.guardrail_blocks,
            "guardrail_block_rate": self.guardrail_block_rate,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hit_rate,
            "error_count": self.error_count,
        }


@dataclass
class StreamValidationResult:
    """Result of streaming content validation."""

    is_valid: bool
    blocked_content: List[str] = field(default_factory=list)
    modified_content: Optional[str] = None
    violation_reasons: List[str] = field(default_factory=list)
    confidence_score: float = 1.0
    processing_time_ms: float = 0.0

    @property
    def has_violations(self) -> bool:
        """Check if there are policy violations."""
        return len(self.violation_reasons) > 0

    @property
    def action_required(self) -> bool:
        """Check if action is required (block or modify)."""
        return not self.is_valid or self.modified_content is not None


@runtime_checkable
class StreamProcessor(Protocol):
    """Protocol for stream processors."""

    async def process_stream(
        self, stream_id: str, input_stream: Any, **kwargs: Any
    ) -> Any:
        """Process a streaming input."""
        ...

    async def handle_chunk(
        self, stream_id: str, chunk: StreamChunk
    ) -> StreamValidationResult:
        """Handle individual chunk."""
        ...


@runtime_checkable
class StreamAdapter(Protocol):
    """Protocol for framework-specific streaming adapters."""

    def supports_streaming(self) -> bool:
        """Check if adapter supports streaming."""
        ...

    def create_stream(self, **kwargs: Any) -> AsyncIterator[Any]:
        """Create a new stream."""
        ...

    async def process_stream_chunk(self, chunk_data: Any) -> StreamChunk:
        """Process framework-specific chunk data."""
        ...


@dataclass
class StreamConfig:
    """Configuration for streaming operations."""

    # Performance settings
    max_chunk_size: int = 1024  # Max tokens per chunk
    buffer_size: int = 10  # Chunk buffer size
    timeout_seconds: float = 30.0  # Stream timeout

    # Guardrail settings
    enable_guardrails: bool = True
    realtime_validation: bool = True
    validation_interval: int = 1  # Validate every N chunks

    # Caching settings
    enable_caching: bool = True
    cache_partial_responses: bool = True
    cache_ttl_seconds: int = 300

    # Monitoring settings
    enable_metrics: bool = True
    metrics_interval: float = 1.0  # Metrics update interval

    # Framework settings
    framework_specific: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate configuration and return errors."""
        errors = []

        if self.max_chunk_size <= 0:
            errors.append("max_chunk_size must be positive")

        if self.buffer_size <= 0:
            errors.append("buffer_size must be positive")

        if self.timeout_seconds <= 0:
            errors.append("timeout_seconds must be positive")

        if self.validation_interval <= 0:
            errors.append("validation_interval must be positive")

        if self.cache_ttl_seconds <= 0:
            errors.append("cache_ttl_seconds must be positive")

        return errors
