"""Automatic Performance Instrumentation for Klira AI SDK.

This module provides transparent performance tracking for all Klira AI components:
- Guardrails pipeline timing
- Framework adapter performance
- LLM fallback latency
- Overall Klira AI overhead

All metrics are sent via the existing OpenTelemetry pipeline automatically.
No user configuration required.
"""

import time
import functools
import logging
from typing import Any, Callable, Optional, Dict, cast, List, TypeVar
from contextlib import contextmanager

# OpenTelemetry imports
try:
    from opentelemetry import trace, metrics
    from opentelemetry.trace import Span
    from opentelemetry.trace.status import Status, StatusCode

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    # Create dummy placeholders for when OpenTelemetry is not available
    from typing import Any

    trace = None  # type: ignore
    metrics = None  # type: ignore
    Span = Any  # type: ignore
    Status = Any  # type: ignore
    StatusCode = Any  # type: ignore

F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)

# Global performance instrumentation state
_instrumentation_enabled = True
_tracer = None
_meter = None


def init_performance_instrumentation(app_name: str = "klira") -> None:
    """Initialize performance instrumentation with OpenTelemetry."""
    global _tracer, _meter

    if not OTEL_AVAILABLE:
        logger.debug(
            "OpenTelemetry not available, performance instrumentation disabled"
        )
        return

    try:
        _tracer = trace.get_tracer(f"{app_name}.performance")
        _meter = metrics.get_meter(f"{app_name}.performance")
        logger.debug("Performance instrumentation initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize performance instrumentation: {e}")


def set_instrumentation_enabled(enabled: bool) -> None:
    """Enable or disable performance instrumentation."""
    global _instrumentation_enabled
    _instrumentation_enabled = enabled
    logger.debug(f"Performance instrumentation {'enabled' if enabled else 'disabled'}")


@contextmanager
def timed_operation(
    operation_name: str,
    component: str = "klira",
    tags: Optional[Dict[str, str]] = None,
) -> Any:
    """Context manager for timing operations automatically.

    Args:
        operation_name: Name of the operation (e.g., "fast_rules", "policy_augmentation")
        component: Component name (e.g., "guardrails", "adapter", "llm_fallback")
        tags: Additional tags for the metric
    """
    if not _instrumentation_enabled or not OTEL_AVAILABLE or not _tracer:
        yield
        return

    start_time = time.time()
    span_name = f"klira.{component}.{operation_name}"

    with _tracer.start_as_current_span(span_name) as span:
        try:
            # Add tags as span attributes
            if tags:
                for key, value in tags.items():
                    span.set_attribute(f"klira.{key}", value)

            span.set_attribute("klira.component", component)
            span.set_attribute("klira.operation", operation_name)

            yield span

            # Mark as successful
            span.set_status(Status(StatusCode.OK))

        except Exception as e:
            # Mark as error
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise
        finally:
            # Record timing metric
            duration_ms = (time.time() - start_time) * 1000
            span.set_attribute("klira.duration_ms", duration_ms)

            # Send metric to OTel pipeline (automatically forwarded to collectors)
            metric_name = f"klira.{component}.{operation_name}.duration_ms"
            try:
                if _meter:
                    histogram = _meter.create_histogram(
                        metric_name,
                        description=f"Duration of {component} {operation_name} operation",
                        unit="ms",
                    )
                    metric_tags = {"component": component, "operation": operation_name}
                    if tags:
                        metric_tags.update(tags)
                    histogram.record(duration_ms, metric_tags)
            except Exception as e:
                logger.debug(f"Failed to record metric {metric_name}: {e}")


@contextmanager
def conditional_span(
    condition: bool,
    operation_name: str,
    component: str = "klira",
    tags: Optional[Dict[str, str]] = None,
) -> Any:
    """Context manager that only creates a span when condition is True.

    Useful for reducing span overhead while maintaining debugging capability.
    When condition is False, the context manager yields None without creating a span.

    Args:
        condition: Only create span if True
        operation_name: Name of the operation (e.g., "fuzzy_match_detailed")
        component: Component name (e.g., "guardrails.fuzzy_matcher")
        tags: Additional tags for the metric

    Example:
        >>> from klira.sdk.performance import conditional_span
        >>> with conditional_span(
        ...     condition=debug_mode_enabled,
        ...     operation_name="detailed_operation",
        ...     component="my_component"
        ... ) as span:
        ...     # Code here only creates span if condition is True
        ...     pass
    """
    if condition and _instrumentation_enabled and OTEL_AVAILABLE and _tracer:
        with timed_operation(operation_name, component, tags) as span:
            yield span
    else:
        yield None


def performance_instrumented(
    component: str,
    operation: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
) -> Callable[[F], F]:
    """Decorator to automatically instrument function performance.

    Args:
        component: Component name (e.g., "guardrails", "adapter")
        operation: Operation name (defaults to function name)
        tags: Additional tags for metrics
    """

    def decorator(func: F) -> F:
        if not _instrumentation_enabled or not OTEL_AVAILABLE:
            return func

        operation_name = operation or func.__name__

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with timed_operation(operation_name, component, tags):
                return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with timed_operation(operation_name, component, tags):
                return await func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if hasattr(func, "__code__") and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


# Pre-configured decorators for specific Klira AI components
def guardrails_instrumented(operation: Optional[str] = None) -> Callable[[F], F]:
    """Instrument guardrails operations."""
    return performance_instrumented("guardrails", operation)


def adapter_instrumented(
    framework: str, operation: Optional[str] = None
) -> Callable[[F], F]:
    """Instrument framework adapter operations."""
    tags = {"framework": framework}
    return performance_instrumented("adapter", operation, tags)


def llm_fallback_instrumented(operation: Optional[str] = None) -> Callable[[F], F]:
    """Instrument LLM fallback operations."""
    return performance_instrumented("llm_fallback", operation)


def framework_detection_instrumented(
    operation: Optional[str] = None,
) -> Callable[[F], F]:
    """Instrument framework detection operations."""
    return performance_instrumented("framework_detection", operation)


# Utility functions for manual timing
class PerformanceTimer:
    """Manual timer for complex operations."""

    def __init__(
        self, component: str, operation: str, tags: Optional[Dict[str, str]] = None
    ):
        self.component = component
        self.operation = operation
        self.tags = tags or {}
        self.start_time: Optional[float] = None
        self.timings: List[Dict[str, Any]] = []

    def start_phase(self, phase_name: str) -> None:
        """Start timing a phase within the operation."""
        if not _instrumentation_enabled:
            return

        phase_start = time.time()
        self.timings.append({"phase": phase_name, "start": phase_start, "end": None})

    def end_phase(self, phase_name: str) -> Optional[float]:
        """End timing a phase and return duration in ms."""
        if not _instrumentation_enabled:
            return None

        end_time = time.time()
        for timing in reversed(self.timings):
            if timing["phase"] == phase_name and timing["end"] is None:
                timing["end"] = end_time
                duration_ms = (end_time - timing["start"]) * 1000

                # Record phase metric
                self._record_phase_metric(phase_name, duration_ms)
                return cast(float, duration_ms)
        return None

    def _record_phase_metric(self, phase_name: str, duration_ms: float) -> None:
        """Record phase timing metric."""
        if not OTEL_AVAILABLE or not _meter:
            return

        try:
            metric_name = (
                f"klira.{self.component}.{self.operation}.{phase_name}.duration_ms"
            )
            histogram = _meter.create_histogram(
                metric_name,
                description=f"Duration of {self.component} {self.operation} {phase_name}",
                unit="ms",
            )

            metric_tags = {
                "component": self.component,
                "operation": self.operation,
                "phase": phase_name,
            }
            metric_tags.update(self.tags)

            histogram.record(duration_ms, metric_tags)
        except Exception as e:
            logger.debug(f"Failed to record phase metric: {e}")

    def get_total_duration(self) -> Optional[float]:
        """Get total duration across all phases in ms."""
        if not self.timings:
            return None

        completed_timings = [t for t in self.timings if t["end"] is not None]
        if not completed_timings:
            return None

        start = min(t["start"] for t in completed_timings)
        end = max(t["end"] for t in completed_timings)
        return cast(float, (end - start) * 1000)

    def get_phase_breakdown(self) -> Dict[str, float]:
        """Get breakdown of time spent in each phase."""
        breakdown = {}
        for timing in self.timings:
            if timing["end"] is not None:
                duration_ms = (timing["end"] - timing["start"]) * 1000
                breakdown[timing["phase"]] = duration_ms
        return breakdown


# Export public API
__all__ = [
    "init_performance_instrumentation",
    "set_instrumentation_enabled",
    "timed_operation",
    "conditional_span",
    "performance_instrumented",
    "guardrails_instrumented",
    "adapter_instrumented",
    "llm_fallback_instrumented",
    "framework_detection_instrumented",
    "PerformanceTimer",
]
