"""Base OpenTelemetry decorator implementations for the Klira AI SDK.

Provides wrappers around Traceloop decorators OR framework-specific adapters
to automatically add Klira AI-specific context attributes and apply framework-aware tracing.
"""

import functools
import logging
from typing import Optional, Callable, Any, Dict, Type, TypeVar, cast

from opentelemetry import context
from opentelemetry.semconv_ai import TraceloopSpanKindValues

# Import Traceloop decorators for fallback
try:
    from traceloop.sdk.decorators import (
        workflow as traceloop_workflow,
        task as traceloop_task,
        agent as traceloop_agent,
        tool as traceloop_tool,
    )

    TRACELOOP_DECORATORS_AVAILABLE = True
except ImportError:
    TRACELOOP_DECORATORS_AVAILABLE = False

    # Define dummy fallback decorators if Traceloop isn't fully available
    def _dummy_decorator(
        name: Optional[str] = None, **kwargs: Any
    ) -> Callable[..., Any]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(func)
            def wrapper(*args: Any, **_kwargs: Any) -> Any:
                return func(*args, **_kwargs)

            return wrapper

        return decorator

    traceloop_workflow = traceloop_task = traceloop_agent = traceloop_tool = (
        _dummy_decorator
    )

# Klira AI SDK specific imports
from klira.sdk.utils.framework_detection import (
    detect_framework_cached as detect_framework,
)
from klira.sdk.utils.framework_registry import FrameworkRegistry

# Type variable definitions (keep as before)
F = TypeVar("F", bound=Callable[..., Any])
C = TypeVar("C", bound=Type[Any])

logger = logging.getLogger("klira.decorators.base")

# Mapping from Traceloop span kind to Klira entity type (keep as before)
_SPAN_KIND_TO_KLIRA_ENTITY_TYPE: Dict[TraceloopSpanKindValues, str] = {
    TraceloopSpanKindValues.WORKFLOW: "workflow",
    TraceloopSpanKindValues.TASK: "task",
    TraceloopSpanKindValues.AGENT: "agent",
    TraceloopSpanKindValues.TOOL: "tool",
}


def _validate_user_id(
    decorator_type: str, func_or_class: Any, ctx_attrs: Dict[str, Any]
) -> None:
    """
    Validate that user_id is provided via decorator parameter or global context.

    Args:
        decorator_type: The type of decorator (workflow, task, agent, tool)
        func_or_class: The decorated function or class
        ctx_attrs: Context attributes from decorator

    Raises:
        ValueError: If user_id is not found in either location
    """
    from klira.sdk.tracing.tracing import get_current_context

    # Check decorator parameter first
    user_id_from_decorator = ctx_attrs.get("user_id")

    if not user_id_from_decorator:
        # Fall back to global context
        current_context = get_current_context()
        user_id_from_context = current_context.get("user_id")

        if not user_id_from_context:
            # Neither source has user_id - raise error
            func_name = getattr(func_or_class, "__name__", "unknown")

            raise ValueError(
                f"user_id is required for {decorator_type} '{func_name}'. "
                f"Provide it via decorator parameter or set_hierarchy_context().\n\n"
                f"Example 1 - Via decorator parameter:\n"
                f"  @{decorator_type}(name='my_{decorator_type}', user_id='user_123')\n"
                f"  def {func_name}():\n"
                f"      pass\n\n"
                f"Example 2 - Via global context:\n"
                f"  from klira.sdk.tracing import set_hierarchy_context\n"
                f"  set_hierarchy_context(user_id='user_123')\n"
                f"  @{decorator_type}(name='my_{decorator_type}')\n"
                f"  def {func_name}():\n"
                f"      pass\n\n"
                f"For more information, see: https://docs.getklira.com/user-tracking"
            )


def _add_klira_context(
    ctx_attributes: Optional[Dict[str, str]],
    span_kind: Optional[
        TraceloopSpanKindValues
    ] = None,  # Made optional, may not always apply
) -> None:
    """Helper to add custom klira.* attributes to the current OTel context."""
    current_ctx = context.get_current()
    new_values: Dict[str, Any] = {}

    # Add custom context attributes prefixed with 'klira.'
    if ctx_attributes:
        for key, value in ctx_attributes.items():
            new_values[f"klira.{key}"] = value

    # Add klira.entity_type based on span kind if provided
    if span_kind:
        entity_type = _SPAN_KIND_TO_KLIRA_ENTITY_TYPE.get(span_kind)
        if entity_type:
            new_values["klira.entity_type"] = entity_type

    if new_values:
        modified_ctx = current_ctx
        for key, value in new_values.items():
            modified_ctx = context.set_value(key, value, context=modified_ctx)
        context.attach(modified_ctx)


# --- New Core Decorator Logic ---


def _apply_klira_decorator(
    decorator_type: str,  # e.g., "workflow", "tool"
    func_or_class: Any,
    name: Optional[str] = None,
    # context_attributes removed here, handled by specific decorators below
    **kwargs: Any,  # Pass other kwargs (like version, and context_attributes/tlp_span_kind for fallback context) through
) -> Any:
    """Core helper function to apply Klira decorators with framework adaptation."""

    # Detect framework based on the function/class being decorated
    try:
        framework = detect_framework(func_or_class)
    except Exception as e:
        logger.error(
            f"Error detecting framework for {getattr(func_or_class, '__name__', func_or_class)}: {e}. Defaulting to 'standard'.",
            exc_info=True,
        )
        framework = "standard"

    adapter = FrameworkRegistry.get_adapter(framework)
    logger.debug(
        f"Applying Klira decorator '{decorator_type}' for detected framework '{framework}'. Adapter: {type(adapter).__name__ if adapter else 'None'}"
    )

    adapter_method_name = f"adapt_{decorator_type}"

    # Determine the fallback Traceloop decorator
    fallback_decorator = None
    if TRACELOOP_DECORATORS_AVAILABLE:
        fallback_decorator = globals().get(f"traceloop_{decorator_type}")

    adapted_func_or_class: Any = (
        func_or_class  # Default to original if everything fails
    )
    applied_adapter = False

    # Get original name for preservation
    original_name = getattr(func_or_class, "__name__", None)
    if not original_name and hasattr(func_or_class, "__class__"):
        original_name = func_or_class.__class__.__name__

    # Use provided name or original name as fallback
    func_name = name or original_name or "unknown_function"

    if adapter and hasattr(adapter, adapter_method_name):
        try:
            # Call the specific adapter method (e.g., adapter.adapt_tool)
            # Adapter is responsible for wrapping/tracing

            # Separate Klira-specific context args from args meant for the adapter/traceloop
            adapter_kwargs = {
                k: v
                for k, v in kwargs.items()
                if k not in ["context_attributes", "tlp_span_kind"]
            }
            adapted_func_or_class = getattr(adapter, adapter_method_name)(
                func_or_class, name=name, **adapter_kwargs
            )

            # Ensure name is preserved
            if original_name and hasattr(adapted_func_or_class, "__name__"):
                adapted_func_or_class.__name__ = original_name

            applied_adapter = True
            logger.debug(
                f"Applied adapter method '{adapter_method_name}' for framework '{framework}'"
            )
        except NotImplementedError:
            logger.warning(
                f"Klira Adapter '{type(adapter).__name__}' does not implement '{adapter_method_name}' for framework '{framework}'. Falling back if possible."
            )
        except Exception as e:
            logger.error(
                f"Klira Error applying adapter '{adapter_method_name}' for '{framework}': {e}. Falling back if possible.",
                exc_info=True,
            )

    # Fallback to standard Traceloop decorator ONLY if adapter wasn't applied successfully
    if not applied_adapter:
        if fallback_decorator:
            try:
                logger.debug(
                    f"Falling back to Traceloop decorator 'traceloop_{decorator_type}'"
                )
                # Separate Klira-specific context args from args meant for the traceloop decorator
                traceloop_kwargs = {
                    k: v
                    for k, v in kwargs.items()
                    if k not in ["context_attributes", "tlp_span_kind"]
                }

                # Apply the Traceloop decorator with *only* its expected arguments
                decorated_by_traceloop = fallback_decorator(
                    name=name, **traceloop_kwargs
                )(func_or_class)

                # Wrap the Traceloop decorator to add Klira context *before* it runs
                # This is only needed if we didn't use a Klira adapter
                @functools.wraps(
                    func_or_class
                )  # Keep original signature info if possible
                def context_wrapper(*args: Any, **wrapper_kwargs: Any) -> Any:
                    """Wrapper to ensure the context is set properly."""

                    # Validate user_id before any other logic
                    _validate_user_id(
                        decorator_type=decorator_type,
                        func_or_class=func_or_class,
                        ctx_attrs=kwargs.get("context_attributes", {}),
                    )

                    # Identify the correct span kind for context using the original kwargs
                    tlp_span_kind = kwargs.get("tlp_span_kind")
                    if not tlp_span_kind:
                        kind_map = {
                            "workflow": TraceloopSpanKindValues.WORKFLOW,
                            "task": TraceloopSpanKindValues.TASK,
                            "agent": TraceloopSpanKindValues.AGENT,
                            "tool": TraceloopSpanKindValues.TOOL,
                        }
                        tlp_span_kind = kind_map.get(decorator_type)

                    # Get Klira context attributes passed to the original decorator call from original kwargs
                    klira_ctx_attrs = kwargs.get("context_attributes", {})
                    _add_klira_context(klira_ctx_attrs, tlp_span_kind)

                    # Call the function that Traceloop decorated
                    return decorated_by_traceloop(*args, **wrapper_kwargs)

                # Ensure name property is preserved
                context_wrapper.__name__ = func_name
                if hasattr(func_or_class, "__annotations__"):
                    context_wrapper.__annotations__ = func_or_class.__annotations__

                adapted_func_or_class = cast(Any, context_wrapper)

            except Exception as e:
                logger.error(
                    f"Error applying Traceloop fallback decorator 'traceloop_{decorator_type}': {e}. Returning original function.",
                    exc_info=True,
                )
                adapted_func_or_class = (
                    func_or_class  # Revert to original on fallback error
                )
        else:
            # If no adapter and no fallback, return the original function with a warning
            logger.warning(
                f"Klira Warning: No adapter method '{adapter_method_name}' found for '{framework}' and no Traceloop fallback available for decorator type '{decorator_type}'. Returning original function/class without tracing."
            )
            adapted_func_or_class = func_or_class

    # Final check to ensure name is preserved
    if original_name and hasattr(adapted_func_or_class, "__name__"):
        try:
            adapted_func_or_class.__name__ = original_name
        except (AttributeError, TypeError):
            pass  # Couldn't set name, not critical

    return adapted_func_or_class


# --- Context-aware Decorator Definitions ---
# These functions now primarily gather context and call the core _apply_klira_decorator


def workflow_with_context(
    name: Optional[str] = None,
    version: Optional[int] = None,
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None,
    **other_kwargs: Any,  # Catch any other traceloop args
) -> Callable[[Any], Any]:
    """Decorator factory for a workflow entity.

    Applies framework-specific adaptation or falls back to Traceloop workflow decorator.
    Adds Klira context attributes (user_id, organization_id, project_id) if falling back.
    """
    ctx_attrs = {}
    if user_id:
        ctx_attrs["user_id"] = user_id
    if organization_id:
        ctx_attrs["organization_id"] = organization_id
    if project_id:
        ctx_attrs["project_id"] = project_id

    def decorator(func_or_class: Any) -> Any:
        # Pass context attributes and span kind for potential fallback use
        return _apply_klira_decorator(
            "workflow",
            func_or_class,
            name=name,
            version=version,
            context_attributes=ctx_attrs,
            tlp_span_kind=TraceloopSpanKindValues.WORKFLOW,
            **other_kwargs,
        )

    return decorator


def agent_with_context(
    name: Optional[str] = None,
    version: Optional[int] = None,
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    **other_kwargs: Any,
) -> Callable[[Any], Any]:
    """Decorator factory for an agent entity."""
    effective_agent_id = agent_id  # Use provided agent_id
    # We don't default agent_id to name here anymore, adapters might handle naming better

    ctx_attrs = {}
    if user_id:
        ctx_attrs["user_id"] = user_id
    if organization_id:
        ctx_attrs["organization_id"] = organization_id
    if project_id:
        ctx_attrs["project_id"] = project_id
    if effective_agent_id:
        ctx_attrs["agent_id"] = effective_agent_id

    def decorator(func_or_class: Any) -> Any:
        return _apply_klira_decorator(
            "agent",
            func_or_class,
            name=name,
            version=version,
            context_attributes=ctx_attrs,
            tlp_span_kind=TraceloopSpanKindValues.AGENT,
            **other_kwargs,
        )

    return decorator


def tool_with_context(
    name: Optional[str] = None,
    version: Optional[int] = None,
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    tool_id: Optional[str] = None,
    **other_kwargs: Any,
) -> Callable[[Any], Any]:
    """Decorator factory for a tool entity."""
    effective_tool_id = tool_id

    ctx_attrs = {}
    if user_id:
        ctx_attrs["user_id"] = user_id
    if organization_id:
        ctx_attrs["organization_id"] = organization_id
    if project_id:
        ctx_attrs["project_id"] = project_id
    if agent_id:
        ctx_attrs["agent_id"] = agent_id  # Context for fallback
    if effective_tool_id:
        ctx_attrs["tool_id"] = effective_tool_id

    def decorator(func_or_class: Any) -> Any:
        return _apply_klira_decorator(
            "tool",
            func_or_class,  # Can be function or class
            name=name,
            version=version,
            context_attributes=ctx_attrs,
            tlp_span_kind=TraceloopSpanKindValues.TOOL,
            **other_kwargs,
        )

    return decorator


def task_with_context(
    name: Optional[str] = None,
    version: Optional[int] = None,
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    **other_kwargs: Any,
) -> Callable[[Any], Any]:
    """Decorator factory for a task entity."""
    effective_task_id = task_id

    ctx_attrs = {}
    if user_id:
        ctx_attrs["user_id"] = user_id
    if organization_id:
        ctx_attrs["organization_id"] = organization_id
    if project_id:
        ctx_attrs["project_id"] = project_id
    if effective_task_id:
        ctx_attrs["task_id"] = effective_task_id

    def decorator(func_or_class: Any) -> Any:
        return _apply_klira_decorator(
            "task",
            func_or_class,
            name=name,
            version=version,
            context_attributes=ctx_attrs,
            tlp_span_kind=TraceloopSpanKindValues.TASK,
            **other_kwargs,
        )

    return decorator
