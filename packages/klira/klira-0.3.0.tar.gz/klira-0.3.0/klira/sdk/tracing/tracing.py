"""Core tracing functionality for Klira AI SDK."""

from typing import Dict, Any, Optional
from opentelemetry import context
from opentelemetry import trace
from opentelemetry.context import attach
from opentelemetry.trace import Span

# Import from traceloop.sdk.tracing module
from traceloop.sdk.tracing import (
    set_workflow_name as traceloop_set_workflow_name,
    get_tracer as traceloop_get_tracer,
)

# Import set_association_properties from the main Traceloop class
from traceloop.sdk import Traceloop


def set_organization(org_id: str) -> None:
    """
    Set the organization ID for the current trace.

    Args:
        org_id: The organization ID
    """
    ctx = context.set_value("klira.organization_id", org_id)
    attach(ctx)

    # Use Traceloop directly for association properties
    properties = {"organization_id": org_id}
    Traceloop.set_association_properties(properties)


def set_project(project_id: str) -> None:
    """
    Set the project ID for the current trace.

    Args:
        project_id: The project ID
    """
    ctx = context.set_value("klira.project_id", project_id)
    attach(ctx)

    # Use Traceloop directly for association properties
    properties = {"project_id": project_id}
    Traceloop.set_association_properties(properties)


def set_conversation_context(
    conversation_id: str, user_id: Optional[str] = None
) -> None:
    """
    Set the conversation context for the current trace.

    Args:
        conversation_id: The unique identifier for the conversation
        user_id: The user identifier
    """
    properties = {"conversation_id": conversation_id}
    if user_id:
        properties["user_id"] = user_id

    # Set in context
    ctx = context.set_value("klira.conversation_id", conversation_id)
    attach(ctx)
    if user_id:
        ctx = context.set_value("klira.user_id", user_id)
        attach(ctx)

    # Use Traceloop directly for association properties
    Traceloop.set_association_properties(properties)


def set_hierarchy_context(
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
    tool_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> None:
    """
    Set the complete hierarchy context for the current trace.

    This is a convenience function to set all hierarchy levels at once.

    **IMPORTANT**: user_id is REQUIRED for all decorated functions (@workflow, @task,
    @agent, @tool). You must provide it either via this function OR via decorator
    parameters. If not provided, decorated functions will raise ValueError.

    Args:
        organization_id: The organization ID (optional, inferred from API key)
        project_id: The project ID (optional, inferred from API key)
        agent_id: The agent ID (optional)
        task_id: The task ID (optional)
        tool_id: The tool ID (optional)
        conversation_id: The conversation ID (optional)
        user_id: The user ID (REQUIRED for decorated functions)

    Example:
        # Set user_id globally for all decorators
        set_hierarchy_context(user_id="user_123")

        @workflow(name="my_workflow")
        def process_data():
            pass  # Uses user_id from context

    Note:
        Decorator parameters take precedence over global context values.
    """
    properties = {}

    if organization_id:
        properties["organization_id"] = organization_id
        ctx = context.set_value("klira.organization_id", organization_id)
        attach(ctx)

    if project_id:
        properties["project_id"] = project_id
        ctx = context.set_value("klira.project_id", project_id)
        attach(ctx)

    if agent_id:
        properties["agent_id"] = agent_id
        ctx = context.set_value("klira.agent_id", agent_id)
        attach(ctx)

    if task_id:
        properties["task_id"] = task_id
        ctx = context.set_value("klira.task_id", task_id)
        attach(ctx)

    if tool_id:
        properties["tool_id"] = tool_id
        ctx = context.set_value("klira.tool_id", tool_id)
        attach(ctx)

    if conversation_id:
        properties["conversation_id"] = conversation_id
        ctx = context.set_value("klira.conversation_id", conversation_id)
        attach(ctx)

    if user_id:
        properties["user_id"] = user_id
        ctx = context.set_value("klira.user_id", user_id)
        attach(ctx)

    # Use Traceloop directly for association properties
    if properties:
        Traceloop.set_association_properties(properties)


def get_current_context() -> Dict[str, Any]:
    """
    Get the current context values as a dictionary.

    Returns:
        Dict containing all current context values
    """
    context_dict = {}

    # Extract all Klira AI-specific context values
    for key in [
        "klira.organization_id",
        "klira.project_id",
        "klira.agent_id",
        "klira.task_id",
        "klira.tool_id",
        "klira.conversation_id",
        "klira.user_id",
    ]:
        value = context.get_value(key)
        if value is not None:
            # Strip the "klira." prefix for cleaner output
            clean_key = key.replace("klira.", "")
            context_dict[clean_key] = value

    return context_dict


def clear_hierarchy_context() -> None:
    """
    Clear all hierarchy context values.

    This is primarily useful for testing to ensure a clean state between tests.

    Example:
        clear_hierarchy_context()
        # All hierarchy context is now cleared
    """
    # Clear each context value
    for key in [
        "klira.organization_id",
        "klira.project_id",
        "klira.agent_id",
        "klira.task_id",
        "klira.tool_id",
        "klira.conversation_id",
        "klira.user_id",
    ]:
        ctx = context.set_value(key, None)
        attach(ctx)

    # Clear Traceloop properties
    Traceloop.set_association_properties({})


# Define external prompt tracing context if needed
def set_external_prompt_tracing_context(
    prompt_id: str, model: str, parameters: Optional[Dict[str, Any]] = None
) -> None:
    """
    Set additional context for external prompt traces.

    Args:
        prompt_id: The ID or name of the prompt.
        model: The model being used.
        parameters: Optional parameters used for the model.
    """
    # Set any values that might be useful for Klira AI
    properties = {"prompt_id": prompt_id, "model": model}
    if parameters:
        for key, value in parameters.items():
            if isinstance(value, (str, int, float, bool)):
                properties[f"param_{key}"] = str(value)

    # Use Traceloop directly
    Traceloop.set_association_properties(properties)


# Re-export functions from Traceloop for compatibility
set_workflow_name = traceloop_set_workflow_name
# Set association properties function using Traceloop class
set_association_properties = Traceloop.set_association_properties
get_tracer = traceloop_get_tracer


def create_span(name: str) -> Span:
    """
    Create a new span with the given name.

    Args:
        name: The name of the span

    Returns:
        The created span
    """
    # Use OpenTelemetry's tracer directly instead of Traceloop's wrapper
    tracer = trace.get_tracer("klira")
    return tracer.start_span(name)


def set_span_attribute(span: Span, key: str, value: Any) -> None:
    """
    Set an attribute on a span.

    Args:
        span: The span to set the attribute on
        key: The attribute key
        value: The attribute value
    """
    # Use the safe utility function to handle None values and type conversion
    from klira.sdk.utils.span_utils import safe_set_span_attribute

    safe_set_span_attribute(span, key, value)


def get_current_span() -> Optional[Span]:
    """
    Get the current active span.

    Returns:
        The current span, or None if no span is active
    """
    return trace.get_current_span()
