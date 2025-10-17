"""Decorators for Klira AI SDK.

Provides decorators for tracing workflows, tasks, agents, and tools in your LLM application,
now with automatic framework adaptation.
"""

from typing import Optional, Callable, Any, Union, TypeVar

# Remove direct traceloop imports, base handles fallback

# Import guardrails decorator from the correct module
from klira.sdk.decorators.guardrails import guardrails

# Import add_policies for backward compatibility
from klira.sdk.decorators.policies import add_policies

# Import MCP guardrails decorator
from klira.sdk.decorators.mcp_guardrails import mcp_guardrails, MCPGuardrailsError, ViolationMode

# Import the context-aware decorators from base
from klira.sdk.decorators.base import (
    workflow_with_context,
    task_with_context,
    agent_with_context,
    tool_with_context,
)

# Type variable definitions
F = TypeVar("F", bound=Callable[..., Any])
C = TypeVar("C", bound=type)

# Public decorators now simply call the context-aware versions from base.py
# They pass through arguments like name, version, and framework-specific ones.


def workflow(
    name: Optional[str] = None,
    version: Optional[int] = None,
    # Removed method_name - handled by adapters/detection
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None,
    **kwargs: Any,  # Pass extra args
) -> Callable[[Union[F, C]], Union[F, C]]:
    """
    Decorate a function or class as a workflow.

    Automatically adapts tracing based on the detected LLM framework
    (OpenAI Agents, LangChain, LlamaIndex, CrewAI) or falls back to standard tracing.

    A workflow is typically a high-level process.

    Args:
        name: Name of the workflow. Defaults to function/class name.
        version: Version of the workflow.
        organization_id: The organization ID for context (used in fallback).
        project_id: The project ID for context (used in fallback).
        **kwargs: Additional arguments passed to the underlying adapter or Traceloop.

    Returns:
        The decorated function or class.
    """
    return workflow_with_context(        name=name,
        version=version,
        organization_id=organization_id,
        project_id=project_id,
        **kwargs,
    )


def task(
    name: Optional[str] = None,
    version: Optional[int] = None,
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    **kwargs: Any,
) -> Callable[[Union[F, C]], Union[F, C]]:
    """
    Decorate a function or class as a task.

    Adapts tracing based on framework (e.g., CrewAI Task) or falls back.
    A task is typically a distinct operation within a workflow.

    Args:
        name: Name of the task. Defaults to function/class name.
        version: Version of the task.
        organization_id: The organization ID for context.
        project_id: The project ID for context.
        task_id: Specific ID for the task (used in fallback context).
        **kwargs: Additional arguments.

    Returns:
        The decorated function or class.
    """
    return task_with_context(        name=name,
        version=version,
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        **kwargs,
    )


def agent(
    name: Optional[str] = None,
    version: Optional[int] = None,
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    **kwargs: Any,
) -> Callable[[Union[F, C]], Union[F, C]]:
    """
    Decorate a function or class related to an agent.

    Adapts tracing based on framework (e.g., CrewAI Agent creation, LangChain AgentExecutor patching).
    An agent is often an autonomous component using tools.

    Args:
        name: Name of the agent. Defaults to function/class name.
        version: Version of the agent.
        organization_id: The organization ID for context.
        project_id: The project ID for context.
        agent_id: Specific ID for the agent (used in fallback context).
        **kwargs: Additional arguments.

    Returns:
        The decorated function or class.
    """
    return agent_with_context(        name=name,
        version=version,
        organization_id=organization_id,
        project_id=project_id,
        agent_id=agent_id,
        **kwargs,
    )


def tool(
    name: Optional[str] = None,
    version: Optional[int] = None,
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    tool_id: Optional[str] = None,
    **kwargs: Any,
) -> Callable[[Union[F, C]], Union[F, C]]:
    """
    Decorate a function or class as a tool.

    Adapts tracing based on framework (e.g., OpenAI function_tool, LangChain BaseTool, CrewAI tool func).
    A tool is typically a utility used by agents.

    Args:
        name: Name of the tool. Defaults to function/class name.
        version: Version of the tool.
        organization_id: The organization ID for context.
        project_id: The project ID for context.
        agent_id: ID of the agent using the tool (context).
        tool_id: Specific ID for the tool (context).
        **kwargs: Additional arguments.

    Returns:
        The decorated function or class.
    """
    return tool_with_context(        name=name,
        version=version,
        organization_id=organization_id,
        project_id=project_id,
        agent_id=agent_id,
        tool_id=tool_id,
        **kwargs,
    )


# Optional CrewAI specific alias
def crew(
    name: Optional[str] = None,
    version: Optional[int] = None,
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None,
    **kwargs: Any,
) -> Callable[[Union[F, C]], Union[F, C]]:
    """
    Decorate a function or class related to a CrewAI Crew.

    Maps to the `workflow` decorator internally but uses the CrewAI adapter
    if a CrewAI object/function is detected for creation tracing and patching.

    Args:
        name: Name of the crew. Defaults to function/class name.
        version: Version of the crew definition.
        organization_id: The organization ID for context.
        project_id: The project ID for context.
        **kwargs: Additional arguments.

    Returns:
        The decorated function or class.
    """
    # Uses workflow_with_context which calls _apply_klira_decorator("workflow", ...)
    # The CrewAI adapter implements adapt_workflow to handle crew-specific logic.
    # Alternatively, could call _apply_klira_decorator("crew", ...) if adapt_crew exists
    return workflow_with_context(        name=name,
        version=version,
        organization_id=organization_id,
        project_id=project_id,
        **kwargs,
    )


# Update __all__ to remove guardrail_wrapper
__all__ = [
    "workflow",
    "task",
    "agent",
    "tool",
    "crew",
    "add_policies",
    "guardrails",
    "mcp_guardrails",
    "MCPGuardrailsError",
    "ViolationMode",
]
