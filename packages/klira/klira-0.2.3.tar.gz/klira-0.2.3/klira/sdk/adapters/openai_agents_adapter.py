"""
Adapter for OpenAI Agents SDK integration with Klira AI.
"""
# mypy: disable-error-code=unreachable

import functools
import inspect
import logging
import asyncio
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, cast
import uuid

# --- Framework specific imports and dummy definitions ---
AGENTS_SDK_AVAILABLE: bool
_OriginalFunctionTool: Optional[Callable[..., Any]] = (
    None  # To store original if needed
)

try:
    from agents import Agent, Runner, function_tool as ImportedFunctionTool
    from agents.exceptions import InputGuardrailTripwireTriggered

    _OriginalFunctionTool = ImportedFunctionTool  # Store the real one
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    AGENTS_SDK_AVAILABLE = False

    class Agent(object):  # type: ignore[no-redef]
        instructions: Optional[str] = None
        name: Optional[str] = None

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class Runner(object):  # type: ignore[no-redef]
        @classmethod
        async def run(cls, *args: Any, **kwargs: Any) -> Any:
            return None

    class InputGuardrailTripwireTriggered(Exception):  # type: ignore[no-redef]
        result: Any = None

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args)

    # Define function_tool dummy here if agents import failed
    _F = TypeVar("_F", bound=Callable[..., Any])

    def function_tool(*args: Any, **kwargs: Any) -> Callable[[_F], _F]:
        def decorator(func: _F) -> _F:
            # Add attributes to func if the real function_tool does
            # setattr(func, '__is_function_tool__', True)
            return func

        return decorator

    _OriginalFunctionTool = (
        function_tool  # If import failed, _OriginalFunctionTool is now the dummy
    )

# Ensure function_tool is always defined for the rest of the module
if AGENTS_SDK_AVAILABLE and ImportedFunctionTool is not None:
    function_tool = ImportedFunctionTool
elif not AGENTS_SDK_AVAILABLE:
    # function_tool is already the dummy from the except block
    pass

# Try to import OpenAI client for patching
try:
    import openai

    OPENAI_CLIENT_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_CLIENT_AVAILABLE = False

# Try to import OTel context
try:
    from opentelemetry import context as otel_context

    OTEL_CONTEXT_AVAILABLE = True
except ImportError:
    otel_context = None  # type: ignore[assignment]
    OTEL_CONTEXT_AVAILABLE = False

from klira.sdk.adapters.framework_adapter import KliraFrameworkAdapter  # noqa: E402
from klira.sdk.tracing import (  # noqa: E402
    create_span,
    set_span_attribute,
    set_conversation_context,
    set_hierarchy_context,
)
from klira.sdk.guardrails.engine import GuardrailsEngine  # noqa: E402

logger = logging.getLogger("klira.adapters.openai_agents")

F = TypeVar("F", bound=Callable[..., Any])

# Store original methods
_original_runner_run = None


class OpenAIAgentsAdapter(KliraFrameworkAdapter):
    """Adapter for OpenAI Agents SDK."""

    FRAMEWORK_NAME = "agents_sdk"

    def __init__(self) -> None:
        super().__init__()
        if not AGENTS_SDK_AVAILABLE:
            logger.debug(
                "OpenAI Agents SDK is not installed. Limited functionality will be available."
            )

    def patch_framework(self) -> None:
        """Patches necessary parts of the OpenAI Agents SDK."""
        # Guidelines injection is now handled directly in the @guardrails decorator
        # No framework patching needed for OpenAI Agents
        logger.debug(
            "OpenAIAgentsAdapter: Guidelines injection handled by @guardrails decorator."
        )
        pass

    # --- Adapter methods (adapt_tool, adapt_workflow, etc.) --- #

    def _get_name(self, func: Callable[..., Any], name: Optional[str] = None) -> str:
        """Get a name for a function, with fallbacks."""
        if name:
            return name
        if hasattr(func, "__name__"):
            return func.__name__
        return "unknown"

    def _create_tracing_wrapper(
        self,
        func: F,
        span_name_prefix: str,
        name: str,
        extra_attributes: Optional[Dict[str, str]] = None,
    ) -> F:
        """Create a wrapper that traces a function execution."""
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                span_name = f"{span_name_prefix}.{name}"
                with create_span(span_name) as span:
                    # Set standard attributes
                    set_span_attribute(span, "framework", self.FRAMEWORK_NAME)
                    set_span_attribute(span, "name", name)

                    # Set extra attributes if provided
                    if extra_attributes:
                        for key, value in extra_attributes.items():
                            set_span_attribute(span, key, value)

                    try:
                        # Extract and log any input arguments
                        if args and len(args) > 0:
                            input_arg = args[0]
                            if isinstance(input_arg, str):
                                set_span_attribute(span, "input", input_arg[:500])

                        # Call the original function
                        result = await func(*args, **kwargs)

                        # Log the result
                        if result:
                            if hasattr(result, "final_output"):
                                set_span_attribute(
                                    span, "output", str(result.final_output)[:500]
                                )
                            else:
                                set_span_attribute(span, "output", str(result)[:500])

                        return result
                    except Exception as e:
                        set_span_attribute(span, "error", str(e))
                        span.record_exception(e)
                        raise

            return cast(F, async_wrapper)
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                span_name = f"{span_name_prefix}.{name}"
                with create_span(span_name) as span:
                    # Set standard attributes
                    set_span_attribute(span, "framework", self.FRAMEWORK_NAME)
                    set_span_attribute(span, "name", name)

                    # Set extra attributes if provided
                    if extra_attributes:
                        for key, value in extra_attributes.items():
                            set_span_attribute(span, key, value)

                    try:
                        # Extract and log any input arguments
                        if args and len(args) > 0:
                            input_arg = args[0]
                            if isinstance(input_arg, str):
                                set_span_attribute(span, "input", input_arg[:500])

                        # Call the original function
                        result = func(*args, **kwargs)

                        # Log the result
                        if result:
                            if hasattr(result, "final_output"):
                                set_span_attribute(
                                    span, "output", str(result.final_output)[:500]
                                )
                            else:
                                set_span_attribute(span, "output", str(result)[:500])

                        return result
                    except Exception as e:
                        set_span_attribute(span, "error", str(e))
                        span.record_exception(e)
                        raise

            return cast(F, sync_wrapper)

    def adapt_tool(
        self,
        func_or_class: Callable[..., Any] | type,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Callable[..., Any] | type:
        """
        Adapt a function to be used as a tool with OpenAI Agents.

        Args:
            func_or_class: The function or class to adapt
            name: Optional override for the tool name
            **kwargs: Additional context attributes

        Returns:
            A decorated function or class that can be used with OpenAI Agents
        """
        if not AGENTS_SDK_AVAILABLE:
            logger.debug(
                "OpenAI Agents SDK is not installed. Tool will be traced but not adapted."
            )
            return func_or_class

        # Get tool name
        tool_name = self._get_name(func_or_class, name)

        # Create attributes to pass to the tracing wrapper
        extra_attrs = {"tool_name": tool_name, "entity_type": "tool"}

        # Add any additional context from kwargs
        for key in ["organization_id", "project_id", "agent_id", "tool_id"]:
            if key in kwargs and kwargs[key]:
                extra_attrs[key] = kwargs[key]

        # Handle class vs function differently
        if inspect.isclass(func_or_class):
            # For classes, just return the class with some logging
            logger.debug(
                f"Tool adaptation for class '{tool_name}' - returning original class"
            )
            return func_or_class

        # For functions, apply tracing and framework-specific decorators
        # First apply Klira AI tracing
        traced_func = self._create_tracing_wrapper(
            func=func_or_class,
            span_name_prefix="agents_sdk.tool",
            name=tool_name,
            extra_attributes=extra_attrs,
        )

        # Then apply the framework-specific decorator if available
        try:
            # Apply @function_tool decorator from agents library
            adapted_func = function_tool()(traced_func)
            logger.debug(
                f"Applied agents.function_tool decorator to tool '{tool_name}'"
            )

            # Check if function_tool returns a non-callable object and make it callable
            if hasattr(adapted_func, "__call__"):
                return adapted_func
            else:
                # If function_tool returns something like FunctionTool that's not directly callable,
                # we need to preserve the original function's callability
                logger.warning(
                    f"function_tool decorator returned non-callable object for '{tool_name}'. "
                    f"Preserving original function callability."
                )
                # Add function_tool attributes to the original function for compatibility
                if hasattr(adapted_func, "function"):
                    # If the FunctionTool has a .function attribute, use that
                    preserved_func = adapted_func.function
                else:
                    # Otherwise use the traced function and copy useful attributes
                    preserved_func = traced_func
                    # Copy any useful attributes from the FunctionTool to the function
                    for attr_name in ["name", "description", "parameters"]:
                        if hasattr(adapted_func, attr_name):
                            setattr(
                                preserved_func,
                                attr_name,
                                getattr(adapted_func, attr_name),
                            )

                return preserved_func
        except Exception as e:
            logger.error(
                f"Failed to apply agents.function_tool decorator: {e}. Returning traced function only."
            )
            return traced_func

    def adapt_workflow(self, func: F, name: Optional[str] = None, **kwargs: Any) -> F:
        """Adapt a workflow function for tracing and context management."""
        workflow_name = self._get_name(func, name)
        is_async = asyncio.iscoroutinefunction(func)

        extra_attrs = {
            "workflow_name": workflow_name,
            "entity_type": "workflow",
            **kwargs,  # Include organization_id, project_id, etc.
        }

        # Wrap with basic tracing first
        traced_func = self._create_tracing_wrapper(
            func=func,
            span_name_prefix="agents_sdk.workflow",
            name=workflow_name,
            extra_attributes=extra_attrs,
        )

        # Wrap with context setting
        if is_async:

            @functools.wraps(traced_func)
            async def async_context_wrapper(*args: Any, **kw: Any) -> Any:
                # Extract IDs from kwargs or args if possible
                # Runner might have `conversation_id` in kwargs
                conversation_id = kw.get("conversation_id")
                user_id = kw.get("user_id")

                # More robust extraction from args if not in kwargs
                # Example: some_function(query, conversation_id, user_id)
                # This is highly dependent on function signature, best effort here.
                if len(args) > 0 and not conversation_id:
                    # Check if args[0] could be query, args[1] conv_id, args[2] user_id
                    if len(args) >= 2 and isinstance(args[1], str):
                        conversation_id = args[1]
                    if len(args) >= 3 and isinstance(args[2], str):
                        user_id = args[2]

                # Generate IDs if missing
                if not conversation_id:
                    conversation_id = f"conv_{uuid.uuid4()}"
                    logger.debug(
                        f"Generated new conversation ID for workflow {workflow_name}: {conversation_id}"
                    )

                # Set context
                if conversation_id or user_id:
                    set_conversation_context(conversation_id, user_id)

                # Set hierarchy if top-level IDs provided
                org_id = kw.get("organization_id")
                proj_id = kw.get("project_id")
                agent_id = kw.get("agent_id")
                if org_id or proj_id or agent_id:
                    set_hierarchy_context(
                        org_id, proj_id, agent_id, conversation_id, user_id
                    )

                return await traced_func(*args, **kw)

            return cast(F, async_context_wrapper)
        else:

            @functools.wraps(traced_func)
            def sync_context_wrapper(*args: Any, **kw: Any) -> Any:
                # Similar context setting logic for sync functions
                conversation_id = kw.get("conversation_id")
                user_id = kw.get("user_id")
                if len(args) > 0 and not conversation_id:
                    if len(args) >= 2 and isinstance(args[1], str):
                        conversation_id = args[1]
                    if len(args) >= 3 and isinstance(args[2], str):
                        user_id = args[2]
                if not conversation_id:
                    conversation_id = f"conv_{uuid.uuid4()}"
                if conversation_id or user_id:
                    set_conversation_context(conversation_id, user_id)
                org_id = kw.get("organization_id")
                proj_id = kw.get("project_id")
                agent_id = kw.get("agent_id")
                if org_id or proj_id or agent_id:
                    set_hierarchy_context(
                        org_id, proj_id, agent_id, conversation_id, user_id
                    )
                return traced_func(*args, **kw)

            return cast(F, sync_context_wrapper)

    def adapt_agent(  # type: ignore[override]
        self,
        agent_or_func: Union[Type[Agent], F],
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[Type[Agent], F]:
        """
        Adapt an agent definition or creation function.
        Currently focuses on adding tracing around agent creation if it's a function.
        If it's already an Agent class/instance, no adaptation is done here.
        """
        # Check if it's an Agent class
        if isinstance(agent_or_func, type) and issubclass(agent_or_func, Agent):
            # It's an Agent class, no adaptation needed here for now.
            # Specific agent execution tracing might be handled by patching Runner.run
            logger.debug(
                f"adapt_agent called with Agent class '{agent_or_func.__name__}'. No adaptation applied."
            )
            return agent_or_func

        # Check if it's an Agent instance
        if isinstance(agent_or_func, Agent):
            # It's an Agent instance
            logger.debug(
                f"adapt_agent called with Agent instance '{getattr(agent_or_func, 'name', 'unnamed')}'. No adaptation applied."
            )
            return agent_or_func

        # Check if it's a callable (function)
        if callable(agent_or_func):
            # Assume it's a function that *creates* an agent
            agent_creation_func = cast(F, agent_or_func)
            agent_name = self._get_name(agent_creation_func, name)
            logger.debug(
                f"adapt_agent called with agent creation function '{agent_name}'. Applying tracing wrapper."
            )
            extra_attrs = {
                "agent_name": agent_name,
                "entity_type": "agent_creation",
                **kwargs,
            }
            return self._create_tracing_wrapper(
                func=agent_creation_func,
                span_name_prefix="agents_sdk.agent.create",
                name=agent_name,
                extra_attributes=extra_attrs,
            )

        # Default case - unexpected type
        logger.warning(
            f"adapt_agent received an unexpected type: {type(agent_or_func)}. Returning original."
        )
        return agent_or_func

    def adapt_task(self, func: F, name: Optional[str] = None, **kwargs: Any) -> F:
        """
        Adapt a function representing a task or step within an agent/workflow.
        Applies standard Klira AI tracing.
        """
        task_name = self._get_name(func, name)
        extra_attrs = {"task_name": task_name, "entity_type": "task", **kwargs}
        return self._create_tracing_wrapper(
            func=func,
            span_name_prefix="agents_sdk.task",
            name=task_name,
            extra_attributes=extra_attrs,
        )

    # --- Guardrails Integration --- #

    def _get_message_from_args(
        self, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> Optional[str]:
        """Attempt to extract the primary string message/query from function arguments."""
        # Common patterns: (query, ...), (self, query, ...), (messages=[...], ...), agent.run(query)
        if "query" in kwargs and isinstance(kwargs["query"], str):
            return kwargs["query"]
        if "message" in kwargs and isinstance(kwargs["message"], str):
            return kwargs["message"]
        if "input" in kwargs and isinstance(kwargs["input"], str):
            return kwargs["input"]

        # Check positional args
        for arg in args:
            if isinstance(arg, str):
                return arg  # Assume first string is the message

        # Check messages list (e.g., chat completions)
        if "messages" in kwargs and isinstance(kwargs["messages"], list):
            last_user_message = next(
                (
                    msg["content"]
                    for msg in reversed(kwargs["messages"])
                    if isinstance(msg, dict)
                    and msg.get("role") == "user"
                    and isinstance(msg.get("content"), str)
                ),
                None,
            )
            if last_user_message:
                return last_user_message

        return None

    def apply_input_guardrails(
        self,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        func_name: str,
        injection_strategy: str = "auto",
    ) -> tuple[tuple[Any, ...], dict[str, Any], bool, str]:
        """
        Apply input guardrails using GuardrailsEngine.
        Returns modified args, modified kwargs, whether to block, and violation response.

        Args:
            args: The positional arguments for the function
            kwargs: The keyword arguments for the function
            func_name: The name of the function
            injection_strategy: Strategy for injecting guidelines - 'auto', 'instructions', 'completion'

        Returns:
            Tuple of (modified args, modified kwargs, should_block, violation_reason)
        """

        async def _async_apply_input_guardrails() -> tuple[
            tuple[Any, ...], dict[str, Any], bool, str
        ]:
            """Internal async implementation"""
            message = self._get_message_from_args(args, kwargs)
            if not message:
                logger.debug("No message found for input guardrails")
                return args, kwargs, False, ""

            try:
                engine = GuardrailsEngine.get_instance()
                if not engine:
                    logger.warning(
                        "GuardrailsEngine not initialized. Skipping input check."
                    )
                    return args, kwargs, False, ""

                # Extract context info for the engine
                conv_id = kwargs.get("conversation_id")
                user_id = kwargs.get("user_id")

                # Create context
                context = {
                    "conversation_id": conv_id,
                    "user_id": user_id,
                }

                # Use process_message which is the correct method in GuardrailsEngine
                result = await engine.process_message(message, context)

                # Extract guidelines for potential augmentation
                guidelines = None
                if aug_result := result.get("augmentation_result"):
                    if isinstance(aug_result, dict):
                        guidelines = aug_result.get("extracted_guidelines")

                # Handle guidelines based on injection strategy
                if guidelines:
                    logger.debug(
                        f"Found {len(guidelines)} guidelines for injection with strategy '{injection_strategy}'"
                    )

                    # For 'instructions' strategy, directly modify agent instructions if possible
                    if injection_strategy == "instructions":
                        # Look for agent or runner in args to modify instructions
                        for arg in args:
                            if hasattr(arg, "instructions"):
                                # Direct modification of agent instructions
                                current_instructions = arg.instructions
                                policy_section = "\n\nPOLICY GUIDELINES:\n" + "\n".join(
                                    f"- {g}" for g in guidelines
                                )
                                if "POLICY GUIDELINES:" not in current_instructions:
                                    arg.instructions = (
                                        current_instructions + policy_section
                                    )
                                    logger.info(
                                        f"Injected {len(guidelines)} guidelines directly into agent instructions"
                                    )
                                break

                    # For 'completion' strategy, store in OTel context for runtime injection
                    elif injection_strategy == "completion":
                        if otel_context:
                            try:
                                current_ctx = otel_context.get_current()
                                new_ctx = otel_context.set_value(
                                    "klira.augmentation.guidelines",
                                    guidelines,
                                    current_ctx,
                                )
                                otel_context.attach(new_ctx)
                                logger.debug(
                                    f"Stored {len(guidelines)} augmentation guidelines in OTel context for completion-time injection."
                                )

                                # If we have messages in kwargs, try to directly inject into system message
                                if "messages" in kwargs and isinstance(
                                    kwargs["messages"], list
                                ):
                                    for i, msg in enumerate(kwargs["messages"]):
                                        if msg.get("role") == "system":
                                            # Only inject if not already present
                                            if "POLICY GUIDELINES:" not in msg.get(
                                                "content", ""
                                            ):
                                                policy_section = (
                                                    "\n\nPOLICY GUIDELINES:\n"
                                                    + "\n".join(
                                                        f"- {g}" for g in guidelines
                                                    )
                                                )
                                                kwargs["messages"][i]["content"] = (
                                                    msg["content"] + policy_section
                                                )
                                                logger.info(
                                                    f"Directly injected {len(guidelines)} guidelines into system message"
                                                )
                                            break
                            except Exception as e:
                                logger.warning(
                                    f"Failed to store guidelines in OTel context: {e}"
                                )

                    # For auto strategy or unknown, we've already determined the right strategy in the decorator
                    else:
                        logger.debug(
                            f"Using already determined strategy: {injection_strategy}"
                        )
                        if otel_context:
                            try:
                                current_ctx = otel_context.get_current()
                                new_ctx = otel_context.set_value(
                                    "klira.augmentation.guidelines",
                                    guidelines,
                                    current_ctx,
                                )
                                otel_context.attach(new_ctx)
                                logger.debug(
                                    f"Stored {len(guidelines)} augmentation guidelines in OTel context."
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to store guidelines in OTel context: {e}"
                                )

                if not result.get("allowed", True):
                    reason = result.get("blocked_reason", "Content policy violation")
                    logger.info(
                        f"Input guardrail blocked execution due to violation. Reason: {reason}"
                    )

                    response = result.get("response", "Content policy violation")
                    # Ensure response is always a string
                    if not isinstance(response, str):
                        response = "Content policy violation"
                    return args, kwargs, True, response
                else:
                    logger.debug("Input guardrail check passed.")
                    # Potential modification of input is not implemented yet
                    return args, kwargs, False, ""

            except Exception as e:
                logger.error(f"Error applying input guardrails: {e}", exc_info=True)
                # Default to not blocking if guardrails fail
                return args, kwargs, False, ""

        # Run the async method synchronously
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we need to use asyncio.create_task
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, _async_apply_input_guardrails()
                    )
                    return future.result()
            else:
                return loop.run_until_complete(_async_apply_input_guardrails())
        except RuntimeError:
            # No event loop available, create a new one
            return asyncio.run(_async_apply_input_guardrails())

    def apply_output_guardrails(
        self, result: Any, func_name: str
    ) -> tuple[Any, bool, str]:
        """
        Apply output guardrails using GuardrailsEngine.
        Returns modified result, whether to block, and violation response.
        """

        async def _async_apply_output_guardrails(
            original_result: Any,
        ) -> tuple[Any, bool, str]:
            """Internal async implementation"""
            output_text = None
            if isinstance(original_result, str):
                output_text = original_result
            elif (
                AGENTS_SDK_AVAILABLE
                and hasattr(original_result, "final_output")
                and isinstance(original_result.final_output, str)
            ):
                # Specific handling for Agents SDK Runner result
                output_text = original_result.final_output
            else:
                try:
                    output_text = str(original_result)  # Best effort
                except Exception:
                    logger.debug(
                        f"Could not convert result type {type(original_result)} to string for output guardrails in {func_name}"
                    )
                    return original_result, False, ""  # Cannot check non-string output

            if not output_text:
                logger.debug(
                    f"No output text found for output guardrails in {func_name}"
                )
                return original_result, False, ""

            try:
                engine = GuardrailsEngine.get_instance()
                if not engine:
                    logger.warning(
                        "GuardrailsEngine not initialized. Skipping output check."
                    )
                    return original_result, False, ""

                # Extract context info
                # Context might need to be retrieved differently for output checks
                conv_id = None  # TODO: Figure out how to get context here if needed
                user_id = None

                # Prepare context for check_output
                output_context = {
                    "conversation_id": conv_id,
                    "user_id": user_id,
                }

                # Use the new evaluate method with outbound direction
                decision = await engine.evaluate(
                    input_text=output_text,
                    context=output_context,
                    direction="outbound"
                )

                # Access attributes from the Decision object
                should_block = not decision.allowed
                reason = decision.reason or ""
                violation_response = f"[BLOCKED BY GUARDRAILS] - {reason}" if reason else "[BLOCKED BY GUARDRAILS] - Content policy violation detected"

                if should_block:
                    logger.info(
                        f"Output guardrail blocked result from {func_name} due to violation. Reason: {reason}"
                    )
                    # Return the alternative response
                    modified_result = (
                        violation_response or "Output blocked by content safety policy."
                    )
                    # If original result was an Agent Result object, try to modify its final_output
                    if AGENTS_SDK_AVAILABLE and hasattr(
                        original_result, "final_output"
                    ):
                        try:
                            # Attempt to create a modified result object (may need specific class knowledge)
                            # This is a simplification - might need a proper way to reconstruct/modify the result object
                            original_result.final_output = modified_result
                            return original_result, True, modified_result
                        except Exception as e:
                            logger.warning(
                                f"Failed to modify Agent Result final_output: {e}. Returning string response."
                            )
                            return (
                                modified_result,
                                True,
                                modified_result,
                            )  # Return the alternative string
                    else:
                        return (
                            modified_result,
                            True,
                            modified_result,
                        )  # Return the alternative string

                else:
                    logger.debug(f"Output guardrail check passed for {func_name}.")
                    # TODO: Implement output modification if needed (e.g., scrubbing PII)
                    return original_result, False, ""

            except Exception as e:
                logger.error(
                    f"Error applying output guardrails for {func_name}: {e}",
                    exc_info=True,
                )
                # Default to not blocking if guardrails fail
                return original_result, False, ""

        # Run the async method synchronously
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we need to use asyncio.create_task
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, _async_apply_output_guardrails(result)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(_async_apply_output_guardrails(result))
        except RuntimeError:
            # No event loop available, create a new one
            return asyncio.run(_async_apply_output_guardrails(result))

    def apply_augmentation(
        self,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        guidelines: list[str],
        func_name: str,
    ) -> tuple[tuple[Any, ...], dict[str, Any]]:
        """
        Apply prompt augmentation based on guardrail guidelines.

        Args:
            args: Original positional arguments.
            kwargs: Original keyword arguments.
            guidelines: List of augmentation guidelines from guardrails.
            func_name: Name of the function being decorated.

        Returns:
            A tuple containing:
            - Modified positional arguments.
            - Modified keyword arguments.
        """
        logger.debug(
            f"Apply_augmentation called for {func_name}, but augmentation is typically handled by LLM client patches."
        )

        # For OpenAI Agents, augmentation is primarily handled by patching Runner.run
        # This method is kept for compatibility with the base interface

        # Example for OpenAI Chat Completions style:
        if "messages" in kwargs and isinstance(kwargs["messages"], list):
            messages = list(kwargs["messages"])
            # Find or create system message and inject guidelines
            system_msg_found = False
            for i, msg in enumerate(messages):
                if msg.get("role") == "system":
                    if "POLICY GUIDELINES:" not in msg.get("content", ""):
                        policy_section = "\n\nPOLICY GUIDELINES:\n" + "\n".join(
                            f"- {g}" for g in guidelines
                        )
                        messages[i]["content"] = msg["content"] + policy_section
                        logger.info(
                            f"Injected {len(guidelines)} guidelines into system message for {func_name}"
                        )
                    system_msg_found = True
                    break

            if not system_msg_found and guidelines:
                # Create new system message with guidelines
                policy_section = "POLICY GUIDELINES:\n" + "\n".join(
                    f"- {g}" for g in guidelines
                )
                system_msg = {"role": "system", "content": policy_section}
                messages.insert(0, system_msg)
                logger.info(
                    f"Created new system message with {len(guidelines)} guidelines for {func_name}"
                )

            kwargs["messages"] = messages

        # Example for OpenAI Agents instructions style:
        elif "instructions" in kwargs and isinstance(kwargs["instructions"], str):
            instructions = kwargs["instructions"]
            if "POLICY GUIDELINES:" not in instructions:
                policy_section = "\n\nPOLICY GUIDELINES:\n" + "\n".join(
                    f"- {g}" for g in guidelines
                )
                kwargs["instructions"] = instructions + policy_section
                logger.info(
                    f"Injected {len(guidelines)} guidelines into instructions for {func_name}"
                )

        return args, kwargs

    def _apply_outbound_guardrails(self, result: Any) -> Any:
        """Apply outbound guardrails to OpenAI Agents results (synchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine
            
            # Extract content from OpenAI Agents response
            response_text = self._extract_response_content(result)
            if not response_text.strip():
                return result
            
            # Create evaluation context
            context = {
                "llm_client": "openai_agents",
                "function_name": "agents.Runner.run"
            }
            
            # Get guardrails engine and evaluate
            engine = GuardrailsEngine.get_instance()
            
            # Run async evaluation in sync context using asyncio
            import asyncio
            try:
                # Try to get the current event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, we can't use run_until_complete
                    # Return the result without evaluation and log a warning
                    logger.warning(
                        "Cannot run outbound guardrails evaluation for OpenAI Agents in sync context within async loop. "
                        "Consider using async methods."
                    )
                    return result
                else:
                    # We can safely run the async evaluation
                    decision = loop.run_until_complete(
                        engine.evaluate(response_text, context, direction="outbound")
                    )
            except RuntimeError:
                # No event loop, create one
                decision = asyncio.run(
                    engine.evaluate(response_text, context, direction="outbound")
                )
            
            if not decision.allowed:
                logger.warning(
                    f"OpenAI Agents outbound guardrails blocked response: {decision.reason}"
                )
                # Return a modified response with blocked content
                return self._create_blocked_response(result, decision.reason or "Content policy violation detected")
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying outbound guardrails for OpenAI Agents: {e}", exc_info=True)
            # Fail open - return original result
            return result

    async def _apply_outbound_guardrails_async(self, result: Any) -> Any:
        """Apply outbound guardrails to OpenAI Agents results (asynchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine
            
            # Extract content from OpenAI Agents response
            response_text = self._extract_response_content(result)
            if not response_text.strip():
                return result
            
            # Create evaluation context
            context = {
                "llm_client": "openai_agents",
                "function_name": "agents.Runner.run"
            }
            
            # Get guardrails engine and evaluate
            engine = GuardrailsEngine.get_instance()
            decision = await engine.evaluate(response_text, context, direction="outbound")
            
            if not decision.allowed:
                logger.warning(
                    f"OpenAI Agents async outbound guardrails blocked response: {decision.reason}"
                )
                # Return a modified response with blocked content
                return self._create_blocked_response(result, decision.reason or "Content policy violation detected")
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying outbound guardrails for OpenAI Agents async: {e}", exc_info=True)
            # Fail open - return original result
            return result

    def _extract_response_content(self, result: Any) -> str:
        """Extract text content from OpenAI Agents response object."""
        try:
            # Handle OpenAI Agents response formats
            if isinstance(result, str):
                return result
            elif AGENTS_SDK_AVAILABLE and hasattr(result, "final_output"):
                # Specific handling for Agents SDK Runner result
                return str(result.final_output) if result.final_output else ""
            elif hasattr(result, 'content'):
                return str(result.content)
            elif hasattr(result, 'text'):
                return str(result.text)
            elif isinstance(result, dict):
                # Look for common text fields
                for key in ["final_output", "output", "content", "text", "response", "result"]:
                    if key in result and result[key]:
                        return str(result[key])
            
            # Fallback: try to convert to string
            return str(result) if result else ""
            
        except Exception as e:
            logger.debug(f"Error extracting content from OpenAI Agents response: {e}")
            return ""

    def _create_blocked_response(self, original_result: Any, reason: str) -> Any:
        """Create a blocked response that matches the original response format."""
        try:
            blocked_message = f"[BLOCKED BY GUARDRAILS] - {reason}" if reason else "[BLOCKED BY GUARDRAILS] - Content policy violation detected"
            
            # Handle OpenAI Agents Result objects
            if AGENTS_SDK_AVAILABLE and hasattr(original_result, "final_output"):
                # Modify the final_output attribute if it exists
                original_result.final_output = blocked_message
                return original_result
            elif hasattr(original_result, 'content'):
                original_result.content = blocked_message
                return original_result
            elif hasattr(original_result, 'text'):
                original_result.text = blocked_message
                return original_result
            
            # Handle string results
            if isinstance(original_result, str):
                return blocked_message
            
            # Handle dictionary responses
            if isinstance(original_result, dict):
                # Create a copy to avoid modifying the original
                blocked_result = original_result.copy()
                # Look for common text fields to replace
                for key in ["final_output", "output", "content", "text", "response", "result"]:
                    if key in blocked_result:
                        blocked_result[key] = blocked_message
                        return blocked_result
                # If no specific field found, add a blocked message field
                blocked_result["final_output"] = blocked_message
                return blocked_result
            
            # Fallback: return the blocked message as string
            return blocked_message
            
        except Exception as e:
            logger.error(f"Error creating blocked response: {e}")
            # Ultimate fallback
            return "[BLOCKED BY GUARDRAILS] - Content policy violation detected"
