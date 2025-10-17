"""
Base class for all guardrail adapters in Klira AI SDK.
"""

import logging
from typing import Any, Dict, Optional

# Use lazy imports to avoid circular dependencies
from klira.sdk.guardrails.types import Decision, PolicySet
from klira.sdk.tracing import get_current_span, set_span_attribute

logger = logging.getLogger("klira.adapters.guardrail")


class KliraGuardrailAdapter:
    """Base adapter for Klira AI guardrails to work with different frameworks"""

    def __init__(self, policies: Optional[PolicySet] = None):
        """Initialize the adapter with optional custom policies"""
        self.policies = policies
        self._engine: Optional[Any] = None  # Type the attribute to fix assignment error

    @property
    def engine(self) -> Any:
        """Lazy load the GuardrailsEngine to avoid circular imports"""
        if self._engine is None:
            # Import GuardrailsEngine here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine

            self._engine = (
                GuardrailsEngine.get_instance()
            )  # This assignment is now properly typed
            # Don't initialize components yet - they'll be initialized when needed
        return self._engine

    async def evaluate(
        self, input_text: str, context: Optional[Dict[str, Any]] = None
    ) -> Decision:
        """
        Run guardrail evaluation using the Klira AI engine.

        Args:
            input_text: The text to evaluate against policies
            context: Optional context information for the evaluation

        Returns:
            A Decision object with the evaluation result
        """
        # Add policy information to the context if we have custom policies
        ctx = context.copy() if context else {}
        if self.policies:
            ctx["custom_policies"] = self.policies

        # Create a span for tracing the evaluation
        span = get_current_span()
        if span:
            set_span_attribute(span, "guardrail.input_length", len(input_text))
            set_span_attribute(span, "guardrail.has_context", context is not None)
            if context and "organization_id" in context:
                set_span_attribute(span, "organization_id", context["organization_id"])
            if context and "project_id" in context:
                set_span_attribute(span, "project_id", context["project_id"])

        # Run the evaluation
        result = await self.engine.evaluate(input_text, context=ctx)

        # Log the decision in the span
        if span:
            set_span_attribute(span, "guardrail.allowed", result.allowed)
            set_span_attribute(span, "guardrail.policy_id", result.policy_id or "")
            set_span_attribute(span, "guardrail.reason", result.reason or "")

        # Ensure we return a Decision object
        return result

    def adapt_to_agents_sdk(self) -> Any:
        """Returns an adapter compatible with OpenAI Agents SDK"""
        # Will be implemented in agents_adapter.py
        raise NotImplementedError("adapt_to_agents_sdk not implemented")

    def adapt_to_langchain(self) -> Any:
        """Returns an adapter compatible with LangChain"""
        # Will be implemented in langchain_adapter.py
        raise NotImplementedError("adapt_to_langchain not implemented")

    def adapt_to_crewai(self) -> Any:
        """Returns an adapter compatible with CrewAI"""
        # Will be implemented in crewai_adapter.py
        raise NotImplementedError("adapt_to_crewai not implemented")

    def adapt_to_llamaindex(self) -> Any:
        """Returns an adapter compatible with LlamaIndex"""
        # Will be implemented in llamaindex_adapter.py
        raise NotImplementedError("adapt_to_llamaindex not implemented")
