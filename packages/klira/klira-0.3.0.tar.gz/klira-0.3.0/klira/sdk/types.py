"""Core type definitions and protocols for Klira AI SDK.

This module provides comprehensive type annotations, protocols, and type aliases
for improved type safety across the SDK.
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    Protocol,
    TypeVar,
    Callable,
    Coroutine,
    runtime_checkable,
    Literal,
    TypedDict,
    TYPE_CHECKING,
)
from dataclasses import dataclass
from enum import Enum

# Core type variables
F = TypeVar("F", bound=Callable[..., Any])
C = TypeVar("C", bound=type)
T = TypeVar("T")

# Framework types
FrameworkName = Literal[
    "openai_agents", "langchain", "crewai", "llama_index", "standard"
]

# Decorator types
DecoratorType = Literal["workflow", "task", "agent", "tool", "crew"]

# String literal types for better type safety
GuardrailStrategy = Literal["auto", "instructions", "completion"]
GuardrailAction = Literal["allow", "block", "alternative"]
PolicyEnforcement = Literal["strict", "permissive", "advisory"]


# Configuration types
@dataclass
class ContextAttributes:
    """Context attributes for tracing and organization."""

    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    agent_id: Optional[str] = None
    tool_id: Optional[str] = None
    task_id: Optional[str] = None
    workflow_id: Optional[str] = None


# Result types for guardrails
class GuardrailResultDict(TypedDict, total=False):
    """TypedDict for guardrail results."""

    allowed: bool
    reason: Optional[str]
    confidence: float
    modified_content: Optional[str]
    guidelines: Optional[List[str]]
    violation_response: Optional[str]


# LLM Service Protocol
@runtime_checkable
class LLMServiceProtocol(Protocol):
    """Protocol for LLM service implementations."""

    async def evaluate(
        self, input_text: str, context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResultDict:
        """Evaluate input text for policy compliance."""
        ...


# Framework Adapter Protocol
@runtime_checkable
class FrameworkAdapterProtocol(Protocol):
    """Protocol for framework adapters."""

    FRAMEWORK_NAME: str

    def adapt_workflow(
        self, func: Callable[..., Any], name: Optional[str] = None, **kwargs: Any
    ) -> Callable[..., Any]:
        """Adapt a workflow function."""
        ...

    def adapt_task(
        self, func: Callable[..., Any], name: Optional[str] = None, **kwargs: Any
    ) -> Callable[..., Any]:
        """Adapt a task function."""
        ...

    def adapt_agent(
        self, func: Callable[..., Any], name: Optional[str] = None, **kwargs: Any
    ) -> Callable[..., Any]:
        """Adapt an agent function."""
        ...

    def adapt_tool(
        self,
        func_or_class: Union[Callable[..., Any], type],
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[Callable[..., Any], type]:
        """Adapt a tool function or class."""
        ...


# Guardrails Protocols
@runtime_checkable
class GuardrailsProcessorProtocol(Protocol):
    """Protocol for guardrails processors."""

    async def process_message(
        self, message: str, context: Dict[str, Any]
    ) -> GuardrailResultDict:
        """Process a message through guardrails."""
        ...


@runtime_checkable
class PolicyAugmentationProtocol(Protocol):
    """Protocol for policy augmentation."""

    async def augment_prompt(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Augment prompt with policy guidelines."""
        ...


# Cache Protocols
@runtime_checkable
class CacheAdapterProtocol(Protocol):
    """Protocol for cache adapters."""

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        ...

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        ...

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        ...

    async def clear(self) -> bool:
        """Clear all cache entries."""
        ...


# Telemetry and Tracing
@runtime_checkable
class TracerProtocol(Protocol):
    """Protocol for tracing implementations."""

    def start_span(
        self, name: str, **kwargs: Any
    ) -> Any:  # Span type varies by implementation
        """Start a new span."""
        ...


# Error handling types
class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class KliraErrorInfo:
    """Information about a Klira AI SDK error."""

    message: str
    severity: ErrorSeverity
    context: Dict[str, Any]
    original_exception: Optional[Exception] = None


# Configuration protocol
@runtime_checkable
class ConfigProtocol(Protocol):
    """Protocol for configuration objects."""

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        ...

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        ...


# Async callback types
AsyncCallback = Callable[..., Coroutine[Any, Any, Any]]
SyncCallback = Callable[..., Any]
CallbackType = Union[AsyncCallback, SyncCallback]

# Result union types for better type safety
GuardrailResult = Union[
    GuardrailResultDict, Dict[str, Any]  # Fallback for compatibility
]

# Decorator factory types
DecoratorFactory = Callable[..., Callable[[F], F]]
ClassDecoratorFactory = Callable[..., Callable[[C], C]]
UniversalDecoratorFactory = Callable[..., Callable[[Union[F, C]], Union[F, C]]]

# Streaming types (forward references for streaming module)
if TYPE_CHECKING:
    from klira.sdk.streaming.types import (
        StreamChunk as StreamChunkType,
        StreamEvent as StreamEventType,
        StreamMetrics as StreamMetricsType,
    )
else:
    StreamChunkType = Any
    StreamEventType = Any
    StreamMetricsType = Any

# Registry types
AdapterRegistry = Dict[str, FrameworkAdapterProtocol]
LLMRegistry = Dict[str, LLMServiceProtocol]

# Export all types for easy importing
__all__ = [
    # Type variables
    "F",
    "C",
    "T",
    # Literal types
    "FrameworkName",
    "DecoratorType",
    "GuardrailStrategy",
    "GuardrailAction",
    "PolicyEnforcement",
    # Data classes
    "ContextAttributes",
    "KliraErrorInfo",
    # TypedDicts
    "GuardrailResultDict",
    # Protocols
    "LLMServiceProtocol",
    "FrameworkAdapterProtocol",
    "GuardrailsProcessorProtocol",
    "PolicyAugmentationProtocol",
    "CacheAdapterProtocol",
    "TracerProtocol",
    "ConfigProtocol",
    # Enums
    "ErrorSeverity",
    # Callback types
    "AsyncCallback",
    "SyncCallback",
    "CallbackType",
    # Result types
    "GuardrailResult",
    # Decorator types
    "DecoratorFactory",
    "ClassDecoratorFactory",
    "UniversalDecoratorFactory",
    # Registry types
    "AdapterRegistry",
    "LLMRegistry",
    # Streaming forward references
    "StreamChunkType",
    "StreamEventType",
    "StreamMetricsType",
]
