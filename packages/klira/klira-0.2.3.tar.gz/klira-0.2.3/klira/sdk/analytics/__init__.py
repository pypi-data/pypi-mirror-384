"""Klira AI SDK Analytics Framework.

This module provides comprehensive analytics capabilities including:
- Event collection and tracking
- Metrics aggregation and computation
- Pluggable analytics processors
- Privacy-preserving data collection
- Real-time and batch analytics
- Integration with Klira AI Control Center for blocked messages and policy violations
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Set, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
import threading
import uuid
import logging
from collections import deque

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Standard event types for Klira AI SDK analytics."""

    # SDK Lifecycle Events
    SDK_INITIALIZED = "sdk.initialized"
    SDK_SHUTDOWN = "sdk.shutdown"

    # Decorator Events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"

    TOOL_CALLED = "tool.called"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"

    # Framework Events
    FRAMEWORK_DETECTED = "framework.detected"
    ADAPTER_LOADED = "adapter.loaded"
    ADAPTER_FAILED = "adapter.failed"

    # Guardrails Events
    GUARDRAILS_INPUT_CHECKED = "guardrails.input.checked"
    GUARDRAILS_OUTPUT_CHECKED = "guardrails.output.checked"
    GUARDRAILS_BLOCKED = "guardrails.blocked"
    GUARDRAILS_ALLOWED = "guardrails.allowed"

    POLICY_MATCHED = "policy.matched"
    POLICY_VIOLATED = "policy.violated"

    # LLM Events
    LLM_REQUEST_STARTED = "llm.request.started"
    LLM_REQUEST_COMPLETED = "llm.request.completed"
    LLM_REQUEST_FAILED = "llm.request.failed"

    # Performance Events
    PERFORMANCE_METRIC = "performance.metric"
    LATENCY_MEASURED = "latency.measured"

    # Error Events
    ERROR_OCCURRED = "error.occurred"
    EXCEPTION_RAISED = "exception.raised"

    # Plugin Events
    PLUGIN_DISCOVERED = "plugin.discovered"
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_FAILED = "plugin.failed"

    # Custom Events
    CUSTOM = "custom"


class MetricType(Enum):
    """Types of metrics that can be collected."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    DISTRIBUTION = "distribution"


@dataclass
class AnalyticsEvent:
    """Represents an analytics event."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: Union[EventType, str] = EventType.CUSTOM
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None
    agent_id: Optional[str] = None

    # Performance data
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None

    # Metadata
    sdk_version: Optional[str] = None
    framework: Optional[str] = None
    adapter: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        result = asdict(self)

        # Convert enum to string
        if isinstance(self.event_type, EventType):
            result["event_type"] = self.event_type.value

        # Convert datetime to ISO string
        result["timestamp"] = self.timestamp.isoformat()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalyticsEvent":
        """Create event from dictionary."""
        # Convert timestamp back
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        # Convert event_type back
        if "event_type" in data and isinstance(data["event_type"], str):
            try:
                data["event_type"] = EventType(data["event_type"])
            except ValueError:
                # Keep as string for custom events
                pass

        return cls(**data)


@dataclass
class Metric:
    """Represents a metric measurement."""

    name: str
    value: Union[float, int]
    metric_type: MetricType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        result = asdict(self)
        result["metric_type"] = self.metric_type.value
        result["timestamp"] = self.timestamp.isoformat()
        return result


class AnalyticsProcessor(ABC):
    """Base class for analytics processors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Processor name."""
        pass

    @abstractmethod
    def process_event(self, event: AnalyticsEvent) -> None:
        """Process a single analytics event."""
        pass

    @abstractmethod
    def process_metric(self, metric: Metric) -> None:
        """Process a single metric."""
        pass

    def process_batch(
        self, events: List[AnalyticsEvent], metrics: List[Metric]
    ) -> None:
        """Process a batch of events and metrics (default implementation)."""
        for event in events:
            self.process_event(event)
        for metric in metrics:
            self.process_metric(metric)

    @abstractmethod
    def flush(self) -> None:
        """Flush any pending data."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close and cleanup resources."""
        pass


class AnalyticsCollector:
    """Main analytics collection engine."""

    def __init__(
        self,
        max_events_in_memory: int = 10000,
        max_metrics_in_memory: int = 5000,
        batch_size: int = 100,
        flush_interval_seconds: int = 30,
        enable_real_time: bool = True,
    ):
        """Initialize analytics collector.

        Args:
            max_events_in_memory: Maximum events to keep in memory
            max_metrics_in_memory: Maximum metrics to keep in memory
            batch_size: Size of batches for processing
            flush_interval_seconds: How often to flush data
            enable_real_time: Whether to enable real-time processing
        """
        self.max_events_in_memory = max_events_in_memory
        self.max_metrics_in_memory = max_metrics_in_memory
        self.batch_size = batch_size
        self.flush_interval_seconds = flush_interval_seconds
        self.enable_real_time = enable_real_time

        # Data storage
        self.events: deque[AnalyticsEvent] = deque(maxlen=max_events_in_memory)
        self.metrics: deque[Metric] = deque(maxlen=max_metrics_in_memory)

        # Processors
        self.processors: List[AnalyticsProcessor] = []
        self.real_time_processors: Set[str] = set()

        # Context management
        self._current_context: Dict[str, Any] = {}
        self._context_stack: List[Dict[str, Any]] = []

        # Thread safety
        self._lock = threading.RLock()

        # Background processing
        self._flush_thread: Optional[threading.Thread] = None
        self._stop_flush_thread = threading.Event()
        self._start_background_flush()

        # Session management
        self.session_id = str(uuid.uuid4())
        self.session_start_time = datetime.now(timezone.utc)

        # Event filters
        self._event_filters: List[Callable[[AnalyticsEvent], bool]] = []
        self._metric_filters: List[Callable[[Metric], bool]] = []

    def add_processor(
        self, processor: AnalyticsProcessor, real_time: bool = False
    ) -> None:
        """Add an analytics processor.

        Args:
            processor: Processor to add
            real_time: Whether to process events in real-time
        """
        with self._lock:
            self.processors.append(processor)
            if real_time:
                self.real_time_processors.add(processor.name)

        logger.info(
            f"Added analytics processor: {processor.name} (real_time={real_time})"
        )

    def remove_processor(self, processor_name: str) -> None:
        """Remove an analytics processor."""
        with self._lock:
            self.processors = [p for p in self.processors if p.name != processor_name]
            self.real_time_processors.discard(processor_name)

        logger.info(f"Removed analytics processor: {processor_name}")

    def add_event_filter(self, filter_func: Callable[[AnalyticsEvent], bool]) -> None:
        """Add an event filter function."""
        self._event_filters.append(filter_func)

    def add_metric_filter(self, filter_func: Callable[[Metric], bool]) -> None:
        """Add a metric filter function."""
        self._metric_filters.append(filter_func)

    def set_context(self, **context: Any) -> None:
        """Set analytics context."""
        with self._lock:
            self._current_context.update(context)

    def push_context(self, **context: Any) -> None:
        """Push current context and set new context."""
        with self._lock:
            self._context_stack.append(self._current_context.copy())
            self._current_context.update(context)

    def pop_context(self) -> None:
        """Pop context from stack."""
        with self._lock:
            if self._context_stack:
                self._current_context = self._context_stack.pop()

    def track_event(
        self,
        event_type: Union[EventType, str],
        data: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> str:
        """Track an analytics event.

        Args:
            event_type: Type of event
            data: Event data
            **context: Additional context

        Returns:
            Event ID
        """
        # Create event with current context
        event_context = self._current_context.copy()
        event_context.update(context)

        event = AnalyticsEvent(
            event_type=event_type,
            data=data or {},
            context=event_context,
            session_id=self.session_id,
        )

        # Apply filters
        for filter_func in self._event_filters:
            try:
                if not filter_func(event):
                    logger.debug(f"Event filtered out: {event.event_type}")
                    return event.event_id
            except Exception as e:
                logger.warning(f"Error in event filter: {e}")

        # Store event
        with self._lock:
            self.events.append(event)

        # Real-time processing
        if self.enable_real_time:
            self._process_event_real_time(event)

        logger.debug(f"Tracked event: {event.event_type} ({event.event_id})")
        return event.event_id

    def track_metric(
        self,
        name: str,
        value: Union[float, int],
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None,
        unit: Optional[str] = None,
    ) -> None:
        """Track a metric.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            tags: Metric tags
            unit: Unit of measurement
        """
        metric = Metric(
            name=name, value=value, metric_type=metric_type, tags=tags or {}, unit=unit
        )

        # Apply filters
        for filter_func in self._metric_filters:
            try:
                if not filter_func(metric):
                    logger.debug(f"Metric filtered out: {metric.name}")
                    return
            except Exception as e:
                logger.warning(f"Error in metric filter: {e}")

        # Store metric
        with self._lock:
            self.metrics.append(metric)

        # Real-time processing
        if self.enable_real_time:
            self._process_metric_real_time(metric)

        logger.debug(
            f"Tracked metric: {metric.name} = {metric.value} ({metric.metric_type.value})"
        )

    def _process_event_real_time(self, event: AnalyticsEvent) -> None:
        """Process event in real-time."""
        for processor in self.processors:
            if processor.name in self.real_time_processors:
                try:
                    processor.process_event(event)
                except Exception as e:
                    logger.error(
                        f"Error in real-time event processing for {processor.name}: {e}"
                    )

    def _process_metric_real_time(self, metric: Metric) -> None:
        """Process metric in real-time."""
        for processor in self.processors:
            if processor.name in self.real_time_processors:
                try:
                    processor.process_metric(metric)
                except Exception as e:
                    logger.error(
                        f"Error in real-time metric processing for {processor.name}: {e}"
                    )

    def _start_background_flush(self) -> None:
        """Start background flush thread."""
        if self._flush_thread is None or not self._flush_thread.is_alive():
            self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
            self._flush_thread.start()

    def _flush_loop(self) -> None:
        """Background flush loop."""
        while not self._stop_flush_thread.wait(self.flush_interval_seconds):
            try:
                self.flush()
            except Exception as e:
                logger.error(f"Error in analytics flush: {e}")

    def flush(self) -> None:
        """Flush all pending events and metrics."""
        with self._lock:
            if not self.events and not self.metrics:
                return

            # Get batches to process
            events_to_process = list(self.events)
            metrics_to_process = list(self.metrics)

            # Clear the collections
            self.events.clear()
            self.metrics.clear()

        # Process in batches
        for processor in self.processors:
            if (
                processor.name not in self.real_time_processors
            ):  # Skip real-time processors
                try:
                    # Process in batches
                    for i in range(0, len(events_to_process), self.batch_size):
                        event_batch = events_to_process[i : i + self.batch_size]
                        metric_batch = (
                            metrics_to_process[i : i + self.batch_size]
                            if i < len(metrics_to_process)
                            else []
                        )
                        processor.process_batch(event_batch, metric_batch)

                    processor.flush()
                except Exception as e:
                    logger.error(f"Error flushing processor {processor.name}: {e}")

        logger.debug(
            f"Flushed {len(events_to_process)} events and {len(metrics_to_process)} metrics"
        )

    def get_recent_events(
        self, limit: int = 100, event_type: Optional[Union[EventType, str]] = None
    ) -> List[AnalyticsEvent]:
        """Get recent events from memory.

        Args:
            limit: Maximum number of events to return
            event_type: Optional filter by event type

        Returns:
            List of recent events matching criteria
        """
        with self._lock:
            events_list = list(self.events)

        # Filter by event type if specified
        if event_type is not None:
            if isinstance(event_type, EventType):
                event_type_str = event_type.value
            else:
                event_type_str = event_type

            events_list = [
                e
                for e in events_list
                if (
                    isinstance(e.event_type, EventType)
                    and e.event_type.value == event_type_str
                )
                or (isinstance(e.event_type, str) and e.event_type == event_type_str)
            ]

        # Return most recent events (deque is already ordered by insertion time)
        return events_list[-limit:] if len(events_list) > limit else events_list

    def get_recent_metrics(
        self, limit: int = 100, name_pattern: Optional[str] = None
    ) -> List[Metric]:
        """Get recent metrics from memory.

        Args:
            limit: Maximum number of metrics to return
            name_pattern: Optional pattern to match metric names

        Returns:
            List of recent metrics matching criteria
        """
        with self._lock:
            metrics_list = list(self.metrics)

        # Filter by name pattern if specified
        if name_pattern is not None:
            import re

            pattern = re.compile(name_pattern)
            metrics_list = [m for m in metrics_list if pattern.search(m.name)]

        # Return most recent metrics
        return metrics_list[-limit:] if len(metrics_list) > limit else metrics_list

    def get_stats(self) -> Dict[str, Any]:
        """Get analytics collector statistics."""
        with self._lock:
            return {
                "session_id": self.session_id,
                "session_duration_seconds": (
                    datetime.now(timezone.utc) - self.session_start_time
                ).total_seconds(),
                "events_in_memory": len(self.events),
                "metrics_in_memory": len(self.metrics),
                "processors_count": len(self.processors),
                "real_time_processors": list(self.real_time_processors),
                "max_events_in_memory": self.max_events_in_memory,
                "max_metrics_in_memory": self.max_metrics_in_memory,
                "batch_size": self.batch_size,
                "flush_interval_seconds": self.flush_interval_seconds,
            }

    def close(self) -> None:
        """Close analytics collector."""
        # Stop background thread
        self._stop_flush_thread.set()
        if self._flush_thread and self._flush_thread.is_alive():
            self._flush_thread.join(timeout=5)

        # Final flush
        try:
            self.flush()
        except Exception as e:
            logger.error(f"Error in final flush: {e}")

        # Close all processors
        for processor in self.processors:
            try:
                processor.close()
            except Exception as e:
                logger.error(f"Error closing processor {processor.name}: {e}")

        logger.info("Analytics collector closed")


# Global analytics collector
_global_collector: Optional[AnalyticsCollector] = None
_global_collector_lock = threading.Lock()


def get_global_collector() -> AnalyticsCollector:
    """Get the global analytics collector."""
    global _global_collector

    if _global_collector is None:
        with _global_collector_lock:
            if _global_collector is None:
                _global_collector = AnalyticsCollector()

    return _global_collector


def track_event(
    event_type: Union[EventType, str],
    data: Optional[Dict[str, Any]] = None,
    **context: Any,
) -> str:
    """Convenience function to track an event."""
    return get_global_collector().track_event(event_type, data, **context)


def track_metric(
    name: str,
    value: Union[float, int],
    metric_type: MetricType = MetricType.GAUGE,
    tags: Optional[Dict[str, str]] = None,
    unit: Optional[str] = None,
) -> None:
    """Convenience function to track a metric."""
    return get_global_collector().track_metric(name, value, metric_type, tags, unit)


def set_analytics_context(**context: Any) -> None:
    """Convenience function to set analytics context."""
    return get_global_collector().set_context(**context)


# Export main types
__all__ = [
    "EventType",
    "MetricType",
    "AnalyticsEvent",
    "Metric",
    "AnalyticsProcessor",
    "AnalyticsCollector",
    "get_global_collector",
    "track_event",
    "track_metric",
    "set_analytics_context",
]
