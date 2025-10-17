"""Provides the @add_policies decorator for applying Klira AI guardrails."""

import functools
import uuid
import inspect
import asyncio
import logging
from typing import Optional, Dict, Any, Callable, TypeVar, cast, List

from opentelemetry import context as otel_context  # Avoid name clash

# Import the engine itself
from klira.sdk.guardrails.engine import GuardrailsEngine
# The specific result types are not directly needed here,
# as we rely on the return types of the engine's methods.
# Removed: , GuardrailResult

# Type variable for decorated function
F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger("klira.decorators.policies")


class KliraPolicyViolation(Exception):
    """Exception raised when a message or output violates configured policies.

    Attributes:
        message: The error message describing the violation.
        violated_policies: A list of policy IDs that were violated.
    """

    violated_policies: list[str]

    def __init__(self, message: str, violated_policies: Optional[list[str]] = None):
        """Initializes the KliraPolicyViolation exception.

        Args:
            message: The error message.
            violated_policies: Optional list of violated policy IDs.
        """
        self.message = message
        self.violated_policies = violated_policies or []
        super().__init__(self.message)


# Heuristic parameter names to search for
_MESSAGE_PARAM_NAMES = {"message", "query", "input", "text"}
_SYSTEM_PROMPT_PARAM_NAMES = {"system_prompt", "prompt", "instructions"}
_CONTEXT_PARAM_NAMES = {"context", "metadata"}


def _extract_params(
    sig: inspect.Signature, args: tuple[Any, ...], kwargs: Dict[str, Any]
) -> tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """Extracts message, system_prompt, and context from args/kwargs based on signature."""
    bound_args = sig.bind_partial(*args, **kwargs)
    bound_args.apply_defaults()

    message: Optional[str] = None
    system_prompt: Optional[str] = None
    guardrails_context: Dict[str, Any] = {}

    for name, value in bound_args.arguments.items():
        if name in _MESSAGE_PARAM_NAMES:
            if isinstance(value, str):
                message = value
        elif name in _SYSTEM_PROMPT_PARAM_NAMES:
            if isinstance(value, str):
                system_prompt = value
        elif name in _CONTEXT_PARAM_NAMES:
            if isinstance(value, dict):
                guardrails_context.update(value)

    return message, system_prompt, guardrails_context


def add_policies(
    config: Optional[Dict[str, Any]] = None,
    *,  # Make subsequent arguments keyword-only
    augment_prompt: bool = True,
    check_output: bool = False,
    on_input_violation: str = "default",  # 'default', 'exception', 'alternative'
    on_output_violation: str = "alternative",  # 'exception', 'alternative', 'redact' (maps to transformed_response)
    violation_response: str = "I cannot process that request due to policy restrictions.",
    output_violation_response: str = "I cannot provide that information due to policy restrictions.",
) -> Callable[[F], F]:
    """(DEPRECATED) Decorator to apply Klira AI policy guardrails to function inputs and outputs.

    WARNING: This decorator is deprecated and will be removed in a future version.
    Please use the new `@klira.guardrails` decorator instead, which utilizes framework
    adapters for more robust and flexible integration.

    Original Description:
    This decorator inspects the decorated function's arguments to find the
    user message/input, system prompt, and additional context based on common
    parameter names (e.g., 'message', 'query', 'system_prompt', 'context').

    It processes the input message using `GuardrailsEngine.process_message`.
    If allowed and `augment_prompt` is True, it uses `augment_system_prompt`.
    If allowed and `check_output` is True, it checks the function's string output
    using `check_output`.

    Handles both synchronous and asynchronous functions.

    Args:
        config: Base configuration dictionary for GuardrailsEngine.
        augment_prompt: If True, attempt to augment the system prompt.
        check_output: If True, check the function's string output against policies.
        on_input_violation: Action on input violation: 'default' (return result dict),
                           'exception' (raise KliraPolicyViolation), 'alternative' (return string).
        on_output_violation: Action on output violation: 'alternative' (return string),
                             'exception' (raise KliraPolicyViolation), 'redact' (use transformed_response).
        violation_response: String to return if `on_input_violation` is 'alternative'.
        output_violation_response: String to return if `on_output_violation` is 'alternative' and no redaction available.

    Returns:
        A decorator that wraps the function with guardrail checks.

    Raises:
        KliraPolicyViolation: If `on_input_violation` or `on_output_violation` is 'exception' and a policy is violated.
    """
    logger.warning(
        "The @add_policies decorator is deprecated. Please switch to @klira.guardrails."
    )

    guardrail_config = config or {}

    # Get or initialize the guardrails engine
    # Note: Ensure GuardrailsEngine handles singleton/initialization correctly
    guardrails_instance = GuardrailsEngine.get_instance(guardrail_config)

    def decorator(func: F) -> F:
        sig = inspect.signature(func)
        is_async = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            message, system_prompt, guardrails_context = _extract_params(
                sig, args, kwargs
            )

            # If no message detected, skip guardrails and execute function
            if not message:
                logger.debug(
                    "No message parameter found for guardrails, skipping checks for function '%s'.",
                    func.__name__,
                )
                if is_async:
                    return await func(*args, **kwargs)
                else:
                    # Execute sync func in executor if called via async wrapper
                    # This should ideally be handled by the caller managing loops
                    loop = asyncio.get_running_loop()
                    return await loop.run_in_executor(None, func, *args, **kwargs)

            # Prepare context
            conversation_id = kwargs.get(
                "conversation_id", kwargs.get("user_id", str(uuid.uuid4()))
            )
            base_context = {
                "conversation_id": conversation_id,
                "function_name": func.__name__,
                **guardrails_context,  # Add context extracted from params
            }

            # Add OTel trace context if available
            otel_ctx = otel_context.get_current()
            trace_id = otel_context.get_value("trace_id", context=otel_ctx)
            if trace_id:
                base_context["trace_id"] = trace_id

            # 1. Process Input Message
            input_result = await guardrails_instance.process_message(
                message=message, context=base_context
            )

            # Handle input violation
            if not input_result["allowed"]:
                violated = input_result.get("violated_policies", [])
                reason = input_result.get("blocked_reason", "Policy violation")
                logger.warning(
                    "Input policy violation in '%s' (ConvID: %s): %s. Policies: %s",
                    func.__name__,
                    conversation_id,
                    reason,
                    violated,
                )
                if on_input_violation == "exception":
                    raise KliraPolicyViolation(str(reason), violated)
                elif on_input_violation == "alternative":
                    return (
                        f"{violation_response}: {reason}"
                        if reason
                        else violation_response
                    )
                else:  # 'default' or unrecognized
                    return input_result  # Return the raw result dict

            # If policy provided a direct response, return it
            if "response" in input_result and input_result["response"]:
                return input_result["response"]

            # 2. Augment Prompt Arguments (if applicable)
            current_args = list(args)
            current_kwargs = kwargs.copy()

            # Extract guidelines from the processing result if augmentation occurred
            guidelines: Optional[List[str]] = None
            if aug_res := input_result.get("augmentation_result"):
                # Ensure augmentation_result is a dict before accessing keys
                if isinstance(aug_res, dict):
                    guidelines = aug_res.get("extracted_guidelines")

            if augment_prompt and guidelines:
                logger.debug(
                    "Attempting to augment prompt with %d guidelines.", len(guidelines)
                )
                try:
                    # --- Find and modify the 'messages' argument ---
                    messages_arg_name = None
                    # Bind arguments to signature to find 'messages' reliably
                    bound_args = sig.bind_partial(*args, **kwargs)
                    bound_args.apply_defaults()

                    if "messages" in bound_args.arguments:
                        messages_arg_name = "messages"
                        original_messages = bound_args.arguments[messages_arg_name]
                        if isinstance(original_messages, list):
                            modified_messages = _inject_guidelines_into_messages(
                                original_messages, guidelines
                            )
                            if modified_messages:
                                # Update kwargs if 'messages' was passed by name
                                if messages_arg_name in kwargs:
                                    current_kwargs[messages_arg_name] = (
                                        modified_messages
                                    )
                                    logger.info(
                                        "Successfully augmented system prompt in 'messages' (kwargs)."
                                    )
                                # Update args if 'messages' was passed positionally
                                else:
                                    # Find positional index
                                    for i, param_name in enumerate(sig.parameters):
                                        if param_name == messages_arg_name:
                                            if i < len(current_args):
                                                current_args[i] = modified_messages
                                                logger.info(
                                                    "Successfully augmented system prompt in 'messages' (args)."
                                                )
                                                break
                            else:
                                logger.debug("Guideline injection returned no changes.")
                        else:
                            logger.warning(
                                "'messages' argument found but is not a list."
                            )
                    else:
                        logger.warning(
                            "Could not find 'messages' argument in decorated function '%s' to augment prompt.",
                            func.__name__,
                        )

                except Exception as e:
                    logger.error(
                        "Error augmenting prompt arguments in '%s': %s",
                        func.__name__,
                        e,
                        exc_info=True,
                    )
                    # Continue without augmentation on error

            # 3. Call the original function with potentially modified arguments
            if is_async:
                function_result = await func(*current_args, **current_kwargs)
            else:
                # Run sync function in executor
                loop = asyncio.get_running_loop()
                function_result = await loop.run_in_executor(
                    None, func, *current_args, **current_kwargs
                )

            # 4. Check Output (if applicable)
            if check_output and isinstance(function_result, str):
                output_result = await guardrails_instance.check_output(
                    output=function_result, context=base_context
                )

                if not output_result["allowed"]:
                    violated = output_result.get("violated_policies", [])
                    reason = output_result.get(
                        "blocked_reason", "Output policy violation"
                    )
                    logger.warning(
                        "Output policy violation in '%s' (ConvID: %s): %s. Policies: %s",
                        func.__name__,
                        conversation_id,
                        reason,
                        violated,
                    )
                    # Handle output violation
                    if (
                        on_output_violation == "redact"
                        and "transformed_response" in output_result
                    ):
                        return output_result["transformed_response"]
                    elif on_output_violation == "exception":
                        raise KliraPolicyViolation(str(reason), violated)
                    else:  # 'alternative' or default
                        return (
                            f"{output_violation_response}: {reason}"
                            if reason
                            else output_violation_response
                        )

            return function_result

        # --- Sync Wrapper Removed ---
        # Sync functions are no longer supported by the deprecated @add_policies decorator
        # due to issues with running async guardrail logic synchronously.
        # Please migrate to @klira.guardrails and use 'async def'.

        # Return the correct wrapper based on the original function type
        if is_async:
            return cast(F, async_wrapper)  # Cast async wrapper back to F
        else:
            # Raise error for sync functions
            raise TypeError(
                "The deprecated @add_policies decorator no longer supports synchronous functions (`def`). Please migrate to @klira.guardrails and use `async def`."
            )

    return decorator


# --- Helper Function for Prompt Injection (Copied from previous plan) ---


def _inject_guidelines_into_messages(
    messages: List[Dict[str, str]], guidelines: List[str]
) -> Optional[List[Dict[str, str]]]:
    """Injects guidelines into the system prompt of a message list."""
    if not messages or not guidelines:
        return None  # Nothing to inject or no messages to inject into

    modified = False
    new_messages = []
    system_prompt_found = False

    # Standard guideline formatting
    guideline_block = "\n".join([f"- {g}" for g in guidelines])
    augmentation_text = (
        f"\n\n--- IMPORTANT POLICY GUIDELINES ---\n"
        f"{guideline_block}\n"
        f"--- END POLICY GUIDELINES ---\n"
    )

    for message in messages:
        new_message = (
            message.copy()
        )  # Make a copy to avoid modifying original list/dicts
        if new_message.get("role") == "system":
            original_content = new_message.get("content", "")
            # Append guidelines to existing system prompt
            new_message["content"] = original_content + augmentation_text
            modified = True
            system_prompt_found = True
        new_messages.append(new_message)

    # If no system prompt was found, prepend one
    if not system_prompt_found:
        logger.warning(
            "No system prompt found in messages. Prepending guidelines as a new system message."
        )
        new_messages.insert(0, {"role": "system", "content": augmentation_text.strip()})
        modified = True

    return (
        new_messages if modified else messages
    )  # Return modified list or original if no change needed


# --- New guardrails decorator for individual LLM calls ---


def guardrails(
    augment_prompt: bool = True,
    check_output: bool = False,
    on_input_violation: str = "alternative",  # 'exception', 'alternative'
    on_output_violation: str = "alternative",  # 'exception', 'alternative', 'redact'
    violation_response: str = "I cannot process that request due to policy restrictions.",
    output_violation_response: str = "I cannot provide that information due to policy restrictions.",
) -> Callable[[F], F]:
    """Decorator to apply Klira AI guardrails to individual LLM calls.

    This decorator should be applied to functions that make LLM API calls.
    It intercepts the 'messages' parameter in the function arguments and applies
    the 3-step guardrail process (fast-rules, policy augmentation, LLM fallback).

    Args:
        augment_prompt: If True, attempt to augment the system prompt.
        check_output: If True, check the function's string output against policies.
        on_input_violation: Action on input violation: 'exception' (raise KliraPolicyViolation),
                           'alternative' (return string).
        on_output_violation: Action on output violation: 'alternative' (return string),
                             'exception' (raise KliraPolicyViolation), 'redact' (use transformed_response).
        violation_response: String to return if `on_input_violation` is 'alternative'.
        output_violation_response: String to return if `on_output_violation` is 'alternative' and no redaction available.

    Returns:
        A decorator that wraps the function with guardrail checks.
    """
    # Get or initialize the guardrails engine
    guardrails_instance = GuardrailsEngine.get_instance()

    def decorator(func: F) -> F:
        is_async = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Check if 'messages' is in kwargs
            if "messages" not in kwargs:
                logger.warning(
                    f"No 'messages' parameter found in function '{func.__name__}'. Skipping guardrails."
                )
                if is_async:
                    return await func(*args, **kwargs)
                else:
                    loop = asyncio.get_running_loop()
                    return await loop.run_in_executor(None, func, *args, **kwargs)

            messages = kwargs["messages"]
            if not isinstance(messages, list) or not messages:
                logger.warning(
                    f"'messages' parameter in '{func.__name__}' is not a valid message list. Skipping guardrails."
                )
                if is_async:
                    return await func(*args, **kwargs)
                else:
                    loop = asyncio.get_running_loop()
                    return await loop.run_in_executor(None, func, *args, **kwargs)

            # Extract user message for policy checking
            user_message = None
            for msg in messages:
                if msg.get("role") == "user":
                    user_message = msg.get("content")
                    break

            if not user_message:
                logger.warning(
                    f"No user message found in 'messages' parameter in '{func.__name__}'. Skipping guardrails."
                )
                if is_async:
                    return await func(*args, **kwargs)
                else:
                    loop = asyncio.get_running_loop()
                    return await loop.run_in_executor(None, func, *args, **kwargs)

            # Setup context
            conversation_id = kwargs.get("conversation_id", str(uuid.uuid4()))
            context = {
                "conversation_id": conversation_id,
                "function_name": func.__name__,
            }

            # 1. Process input through fast rules and policy matching
            input_result = await guardrails_instance.process_message(
                message=user_message, context=context
            )

            # Handle input violation
            if not input_result["allowed"]:
                violated = input_result.get("violated_policies", [])
                reason = input_result.get("blocked_reason", "Policy violation")
                logger.warning(
                    "Input policy violation in '%s' (ConvID: %s): %s. Policies: %s",
                    func.__name__,
                    conversation_id,
                    reason,
                    violated,
                )
                if on_input_violation == "exception":
                    raise KliraPolicyViolation(str(reason), violated)
                else:  # 'alternative'
                    return (
                        f"{violation_response}: {reason}"
                        if reason
                        else violation_response
                    )

            # 2. Apply prompt augmentation if enabled
            if augment_prompt:
                guidelines = None
                if aug_res := input_result.get("augmentation_result"):
                    if isinstance(aug_res, dict):
                        guidelines = aug_res.get("extracted_guidelines")

                if guidelines:
                    logger.debug(f"Applying {len(guidelines)} guidelines to messages.")
                    modified_messages = _inject_guidelines_into_messages(
                        messages, guidelines
                    )
                    if modified_messages:
                        kwargs["messages"] = modified_messages
                        logger.info(
                            "Successfully augmented prompt with policy guidelines."
                        )

            # 3. Call the original function
            if is_async:
                result = await func(*args, **kwargs)
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, func, *args, **kwargs)

            # 4. Check output if needed
            if check_output and hasattr(result, "choices") and result.choices:
                # Extract the text from the response
                output_text = result.choices[0].message.content

                output_result = await guardrails_instance.check_output(
                    ai_response=output_text, context=context
                )

                if not output_result["allowed"]:
                    violated = output_result.get("violated_policies", [])
                    reason = output_result.get(
                        "blocked_reason", "Output policy violation"
                    )
                    logger.warning(
                        "Output policy violation in '%s' (ConvID: %s): %s. Policies: %s",
                        func.__name__,
                        conversation_id,
                        reason,
                        violated,
                    )

                    if (
                        on_output_violation == "redact"
                        and "transformed_response" in output_result
                    ):
                        # Replace the message content with the transformed version
                        result.choices[0].message.content = output_result[
                            "transformed_response"
                        ]
                    elif on_output_violation == "exception":
                        raise KliraPolicyViolation(str(reason), violated)
                    else:  # 'alternative'
                        # Replace with alternative message
                        alternative = (
                            f"{output_violation_response}: {reason}"
                            if reason
                            else output_violation_response
                        )
                        result.choices[0].message.content = alternative

            # Fallback for sync function call
            else:
                logger.warning(
                    f"Cannot apply output check to sync function '{func.__name__}' result. Skipping check."
                )
            return result

        # --- Sync Wrapper Removed ---

        # Return the correct wrapper based on the original function type
        if is_async:
            return cast(F, async_wrapper)
        else:
            # Raise error for sync functions
            raise TypeError(
                "The new @guardrails LLM call decorator only supports asynchronous functions (`async def`)."
            )

    return decorator


__all__ = ["add_policies", "KliraPolicyViolation", "guardrails"]
