"""Streaming LLM support for Klira AI SDK.

This module provides real-time streaming capabilities for LLM interactions
with integrated guardrails, tracing, and performance optimization.

Features:
- Real-time streaming response processing
- Integrated guardrails for streaming content
- Backpressure handling and flow control
- Partial response caching and validation
- WebSocket and Server-Sent Events support
- Framework-agnostic streaming interfaces
"""

from .stream_processor import StreamProcessor
from .stream_guardrails import StreamGuardrailsProcessor
from .stream_cache import StreamCache
from .stream_adapters import StreamAdapterRegistry
from .types import (
    StreamEvent,
    StreamEventType,
    StreamChunk,
    StreamMetrics,
    StreamValidationResult,
    StreamConfig,
)

__all__ = [
    # Core streaming
    "StreamProcessor",
    "StreamConfig",
    # Guardrails
    "StreamGuardrailsProcessor",
    # Caching
    "StreamCache",
    # Adapters
    "StreamAdapterRegistry",
    # Types
    "StreamEvent",
    "StreamEventType",
    "StreamChunk",
    "StreamMetrics",
    "StreamValidationResult",
]
