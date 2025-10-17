"""Tracing module for Klira AI SDK."""

from traceloop.sdk.tracing import (
    get_tracer,
    set_workflow_name,
)

# Import local functions
from .tracing import (
    set_conversation_context,
    set_hierarchy_context,
    set_organization,
    set_project,
    get_current_context,
    set_association_properties,
    set_external_prompt_tracing_context,
    create_span,
    set_span_attribute,
    get_current_span,
)

__all__ = [
    "get_tracer",
    "set_workflow_name",
    "set_conversation_context",
    "set_hierarchy_context",
    "set_organization",
    "set_project",
    "get_current_context",
    "set_association_properties",
    "set_external_prompt_tracing_context",
    "create_span",
    "set_span_attribute",
    "get_current_span",
]
