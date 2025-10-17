"""
Adapter implementation for OpenAI Agents SDK.
"""

import logging
import asyncio
from typing import Any, Dict, Optional, Union, Callable

# Moved E402 imports here
from klira.sdk.adapters.guardrail_adapter import KliraGuardrailAdapter
from klira.sdk.guardrails.types import PolicySet
from klira.sdk.tracing import create_span, set_span_attribute

# Import OpenAI Agents types for type checking, with fallbacks
AGENTS_SDK_AVAILABLE = False
try:
    # Try importing from agents SDK first
    from agents import Agent, Runner
    from agents.exceptions import InputGuardrailTripwireTriggered
    from agents import InputGuardrail, GuardrailFunctionOutput

    # Try to import Workflow and Task if they exist
    try:
        from agents import Workflow, Task 
    except (ImportError, AttributeError):
        # These might not be available in all versions, create minimal placeholders
        class Workflow:  # type: ignore[no-redef]
            pass

        class Task:  # type: ignore[no-redef]
            pass

    AGENTS_SDK_AVAILABLE = True
except ImportError:
    # Create placeholder classes if not available
    class Agent:  # type: ignore[no-redef]
        pass

    class Runner:  # type: ignore[no-redef]
        pass

    class Workflow:  # type: ignore[no-redef]
        pass

    class Task:  # type: ignore[no-redef]
        pass

    class InputGuardrailTripwireTriggered(Exception):  # type: ignore[no-redef]
        pass

    # Define placeholder classes for InputGuardrail and GuardrailFunctionOutput
    class InputGuardrail:  # type: ignore[no-redef]
        def __init__(
            self, guardrail_function: Optional[Callable[..., Any]] = None
        ) -> None:
            self.guardrail_function = guardrail_function
            self.name = "klira_guardrail"

        def get_name(self) -> str:
            return self.name

        async def run(
            self, agent: Any, input_text: str, context: Optional[Any] = None
        ) -> Optional[Any]:
            """Run the guardrail function with the input text."""
            if self.guardrail_function:
                return await self.guardrail_function(context, agent, input_text)
            return None

    class GuardrailFunctionOutput:  # type: ignore[no-redef]
        def __init__(
            self,
            output_info: Optional[Dict[str, Any]] = None,
            tripwire_triggered: bool = False,
        ) -> None:
            self.output_info = output_info or {}
            self.tripwire_triggered = tripwire_triggered
            # Add this property for compatibility with OpenAI Agents SDK
            self.output = self  # Self-reference for compatibility


try:
    from opentelemetry import context as otel_context
except ImportError:
    otel_context = None  # type: ignore[assignment]


logger = logging.getLogger("klira.adapters.agents")


class AgentsSDKAdapter(KliraGuardrailAdapter):
    """Adapter for OpenAI Agents SDK"""

    def __init__(
        self,
        policies_or_agent: Optional[
            Union[PolicySet, Any]
        ] = None,  # Changed Agent to Any to avoid type conflicts
        organization_id: Optional[str] = None,
        project_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ):
        # Check if we received an Agent object instead of policies
        if policies_or_agent is not None and hasattr(policies_or_agent, "instructions"):
            # It's an Agent object
            self.agent = policies_or_agent
            policies = None
            logger.debug(
                f"Initialized with Agent: {getattr(self.agent, 'name', 'unnamed')}"
            )
        else:
            # It's a PolicySet or None
            self.agent = None
            policies = policies_or_agent
            if policies and hasattr(policies, "get_policies"):
                logger.info(
                    f"Using custom PolicySet with {len(policies.get_policies())} policies"
                )

        super().__init__(policies)
        logger.info("AgentsSDKAdapter initialized")
        self.organization_id = organization_id
        self.project_id = project_id
        self.agent_id = agent_id

    def adapt_to_agents_sdk(self) -> Callable[..., Any]:
        """Returns a function compatible with OpenAI Agents SDK GuardrailFunction"""
        logger.info("Creating Agents SDK guardrail function")
        return self._create_agents_guardrail_function()

    def _create_agents_guardrail_function(self) -> Callable[..., Any]:
        """Creates a guardrail function for Agents SDK"""

        async def klira_guardrail_function(ctx: Any, agent: Any, input_data: str) -> Any:
            """
            Guardrail function compatible with OpenAI Agents SDK

            Args:
                ctx: The context from Agents SDK
                agent: The Agent object from Agents SDK
                input_data: The user input to evaluate

            Returns:
                GuardrailFunctionOutput with tripwire_triggered based on Klira AI decision
            """
            agent_name = getattr(agent, "name", "unknown")
            logger.info(f"Klira AI guardrail function called for agent '{agent_name}'")
            logger.info(f"Input: '{input_data}'")

            # Create a span for tracing
            span = create_span("klira.guardrails.agents_sdk")
            # Add context attributes for tracing
            set_span_attribute(span, "agent.name", agent_name)
            set_span_attribute(span, "input.length", len(input_data))

            # Add organization, project, and agent IDs if available
            if self.organization_id:
                set_span_attribute(span, "organization_id", self.organization_id)
            if self.project_id:
                set_span_attribute(span, "project_id", self.project_id)
            if self.agent_id:
                set_span_attribute(span, "agent_id", self.agent_id)

            try:
                # Convert Agents SDK context to Klira AI context
                klira_context = self._convert_agents_context_to_klira(ctx, agent)
                logger.debug(f"Converted context: {klira_context}")

                # Run evaluation through Klira AI guardrail engine
                logger.debug("Evaluating input with Klira AI guardrail engine")
                decision = await self.evaluate(input_data, context=klira_context)

                # Log the decision
                logger.info(
                    f"Decision: allowed={decision.allowed}, reason={decision.reason}, policy_id={decision.policy_id}"
                )
                set_span_attribute(span, "decision.allowed", decision.allowed)
                set_span_attribute(span, "decision.reason", decision.reason or "")

                # Check if the agent's instructions should be augmented
                if hasattr(agent, "instructions") and isinstance(
                    agent.instructions, str
                ):
                    logger.debug("Checking if agent instructions should be augmented")
                    original_instructions = agent.instructions

                    # Try to augment instructions if allowed
                    if decision.allowed:
                        try:
                            # See if augmentation is available through the engine
                            if hasattr(self.engine, "augment_system_prompt"):
                                logger.debug("Attempting to augment system prompt")
                                # Call the augmentation method - Corrected to await
                                augmented_instructions = (
                                    await self.engine.augment_system_prompt(
                                        original_instructions,
                                        context={
                                            "message_for_guideline_matching": input_data
                                        },
                                    )
                                )

                                # Previous logic handled potential coroutine return, which is now redundant
                                # because we awaited above. But keep check for safety/clarity.
                                if asyncio.iscoroutine(augmented_instructions):
                                    logger.warning(
                                        "augment_system_prompt returned a coroutine even after await. Awaiting again."
                                    )
                                    augmented_instructions = (
                                        await augmented_instructions
                                    )  # Await again if needed

                                if augmented_instructions != original_instructions:
                                    logger.info("Agent instructions were augmented")
                                    logger.debug(f"Original: {original_instructions}")
                                    logger.debug(f"Augmented: {augmented_instructions}")
                                    agent.instructions = augmented_instructions
                                else:
                                    logger.info(
                                        "No augmentation was applied to instructions"
                                    )
                        except Exception as e:
                            logger.error(
                                f"Error during prompt augmentation: {str(e)}",
                                exc_info=True,
                            )

                # Convert to Agents SDK format
                return GuardrailFunctionOutput(
                    output_info={
                        "allowed": decision.allowed,
                        "reason": decision.reason,
                        "policy_id": decision.policy_id,
                    },
                    tripwire_triggered=not decision.allowed,
                )
            except Exception as e:
                logger.error(f"Error in guardrail function: {str(e)}", exc_info=True)
                raise
            finally:
                # Clean up any resources if needed
                pass

        return klira_guardrail_function

    def _convert_agents_context_to_klira(self, ctx: Any, agent: Any) -> Dict[str, Any]:
        """Convert OpenAI Agents SDK context to Klira AI guardrail context"""
        klira_context = {}

        # Extract agent information
        if hasattr(agent, "name"):
            klira_context["agent_name"] = agent.name
        if hasattr(agent, "id"):
            klira_context["agent_id"] = agent.id

        # Extract context information
        if ctx:
            # Common context fields
            if hasattr(ctx, "user_id"):
                klira_context["user_id"] = ctx.user_id
            if hasattr(ctx, "conversation_id"):
                klira_context["conversation_id"] = ctx.conversation_id
            if hasattr(ctx, "session_id"):
                klira_context["session_id"] = ctx.session_id

            # If context is a dict-like object
            if hasattr(ctx, "get"):
                klira_context.update(ctx.get("klira_context", {}))
            elif hasattr(ctx, "__dict__"):
                # Extract all attributes as context
                for key, value in ctx.__dict__.items():
                    if not key.startswith("_"):  # Skip private attributes
                        klira_context[f"ctx_{key}"] = value

        # Add our own IDs if available
        if self.organization_id:
            klira_context["organization_id"] = self.organization_id
        if self.project_id:
            klira_context["project_id"] = self.project_id
        if self.agent_id:
            klira_context["agent_id"] = self.agent_id

        return klira_context


def add_klira_guardrails(
    agent: Any,  # Changed from Agent to Any to avoid type conflicts
    policies: Optional[PolicySet] = None,
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> str:  # Changed return type to str to match the actual return
    """
    Add Klira AI guardrails to an OpenAI Agents SDK Agent.

    Args:
        agent: The Agent object to add guardrails to
        policies: Optional custom PolicySet to use
        organization_id: Organization ID for tracking
        project_id: Project ID for tracking
        agent_id: Agent ID for tracking

    Returns:
        The agent name as a string
    """
    if not AGENTS_SDK_AVAILABLE:
        logger.debug("OpenAI Agents SDK not available. Cannot add guardrails.")
        return "agent_unavailable"

    if not hasattr(agent, "guardrails"):
        logger.warning(
            "Agent does not have a 'guardrails' attribute. Cannot add Klira AI guardrails."
        )
        return getattr(agent, "name", "agent_no_guardrails")

    # Create Klira AI adapter
    adapter = AgentsSDKAdapter(
        policies_or_agent=policies,
        organization_id=organization_id,
        project_id=project_id,
        agent_id=agent_id,
    )

    # Get the compatible guardrail function
    klira_guardrail_func = adapter.adapt_to_agents_sdk()

    # Create an InputGuardrail object
    klira_guardrail = InputGuardrail(guardrail_function=klira_guardrail_func)

    # Add to agent's guardrails
    if hasattr(agent.guardrails, "append"):
        agent.guardrails.append(klira_guardrail)
    elif hasattr(agent.guardrails, "add"):
        agent.guardrails.add(klira_guardrail)
    else:
        # Try setting guardrails as a list
        current_guardrails = getattr(agent, "guardrails", [])
        if isinstance(current_guardrails, list):
            current_guardrails.append(klira_guardrail)
        else:
            # Create new list
            current_guardrails = [current_guardrails, klira_guardrail]

        # Update the agent - this is safe as we're modifying agent properties, not reassigning methods
        setattr(agent, "guardrails", current_guardrails)

    # Return the agent name or a default string
    return (
        getattr(agent, "name", "unnamed_agent") if hasattr(agent, "name") else "agent"
    )
