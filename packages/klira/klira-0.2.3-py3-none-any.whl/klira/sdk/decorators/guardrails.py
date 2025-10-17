import functools
import asyncio
import logging
from typing import Any, Callable, List, Optional, Union, Dict, Type

from klira.sdk.utils.framework_registry import FrameworkRegistry

logger = logging.getLogger("klira.decorators.guardrails")

# Import adapters (will be dynamically imported to avoid circular imports)
_ADAPTERS: Dict[str, Type[Any]] = {}

# Simple storage for guidelines that can be accessed across contexts
_current_guidelines: Optional[List[str]] = None


def _set_current_guidelines(guidelines: List[str]) -> None:
    """Set the current guidelines for decorator access."""
    global _current_guidelines
    _current_guidelines = guidelines


def _get_current_guidelines() -> Optional[List[str]]:
    """Get the current guidelines."""
    global _current_guidelines
    return _current_guidelines


def _clear_current_guidelines() -> None:
    """Clear the current guidelines."""
    global _current_guidelines
    _current_guidelines = None


def guardrails(
    _func: Optional[Callable[..., Any]] = None,
    *,
    check_input: bool = True,
    check_output: bool = True,
    augment_prompt: bool = True,
    on_input_violation: str = "exception",
    on_output_violation: str = "alternative",
    violation_response: str = "Request blocked due to policy violation.",
    output_violation_response: str = "Response blocked or modified due to policy violation.",
    injection_strategy: str = "auto",  # New parameter to control injection strategy
    **adapter_kwargs: Any,
) -> Union[Callable[..., Any], Callable[[Callable[..., Any]], Callable[..., Any]]]:
    """Decorator to apply Klira AI guardrails using framework adapters.

    This decorator detects the framework (or uses the one provided by other Klira AI decorators)
    and delegates guardrail application (input check, output check, augmentation)
    to the appropriate framework adapter.

    Args:
        check_input: If True, apply input guardrails.
        check_output: If True, apply output guardrails.
        augment_prompt: If True, attempt prompt augmentation based on input check results.
        on_input_violation: Action on input violation: 'exception' (raise KliraPolicyViolation),
                           'alternative' (return violation_response string).
        on_output_violation: Action on output violation: 'exception' (raise KliraPolicyViolation),
                             'alternative' (return output_violation_response or transformed/redacted response),
                             'redact' (synonym for 'alternative', relies on adapter's transformation).
        violation_response: String to return for 'alternative' input violation.
        output_violation_response: Default string for 'alternative' output violation if no specific transformation available.
        injection_strategy: Strategy for injecting guidelines - 'auto' (detect), 'instructions' (inject into agent instructions),
                            'completion' (store in OTel for completion methods to inject)
        **adapter_kwargs: Additional keyword arguments passed to the adapter's guardrail methods.
    """

    def decorator_guardrails(func: Callable[..., Any]) -> Callable[..., Any]:
        func_name = func.__name__
        is_async = asyncio.iscoroutinefunction(func)

        # Get the adapter instance early. This relies on the adapter
        # already being registered and potentially selected by another decorator.
        # If no adapter is found (e.g., @guardrails used alone without framework detection context),
        # it might default to a base/standard adapter or fail gracefully.
        adapter_instance = FrameworkRegistry.get_adapter_instance_for_function(func)

        if not adapter_instance:
            logger.warning(
                f"No adapter found for {func_name} in @guardrails. Checks may not work."
            )
            # Try to get a fallback adapter
            from klira.sdk.adapters.openai_agents_adapter import OpenAIAgentsAdapter

            try:
                # Create a fallback adapter for testing scenarios
                fallback_adapter = OpenAIAgentsAdapter()
                FrameworkRegistry.register_adapter("fallback", fallback_adapter)
                adapter_instance = fallback_adapter
                logger.debug(f"Using fallback adapter for {func_name}")
            except Exception as e:
                logger.debug(f"Failed to create fallback adapter: {e}")
                # Return original function if no adapter is found and fallback fails
                return func

        # Detect the function type for use in determining injection strategy
        def is_chat_completion_function(f: Callable[..., Any]) -> bool:
            """Check if this function appears to be an OpenAI chat.completions.create call."""
            return (
                "chat.completions.create" in func_name
                or "create" in func_name
                and hasattr(f, "__self__")
                and hasattr(f.__self__, "__class__")
                and "completion" in f.__self__.__class__.__name__.lower()
            )

        def is_agent_function(f: Callable[..., Any]) -> bool:
            """Check if this function appears to be an agent runner function."""
            return (
                "run" in func_name
                and hasattr(f, "__self__")
                and hasattr(f.__self__, "__class__")
                and "runner" in f.__self__.__class__.__name__.lower()
            )

        # Determine the effective injection strategy based on function type if set to auto
        effective_injection_strategy = injection_strategy
        if injection_strategy == "auto":
            if is_chat_completion_function(func):
                effective_injection_strategy = "completion"
                logger.debug(
                    f"Auto-detected 'completion' injection strategy for {func_name}"
                )
            elif is_agent_function(func):
                effective_injection_strategy = "instructions"
                logger.debug(
                    f"Auto-detected 'instructions' injection strategy for {func_name}"
                )
            else:
                # Default to completion-based strategy if we can't detect
                effective_injection_strategy = "completion"
                logger.debug(
                    f"Defaulting to 'completion' injection strategy for {func_name}"
                )

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal adapter_instance  # Ensure we use the adapter found outside
            nonlocal effective_injection_strategy

            if not adapter_instance:
                logger.error(
                    f"Guardrails adapter lost for {func_name} in async_wrapper. Skipping checks."
                )
                return await func(*args, **kwargs)  # Execute original function

            current_args, current_kwargs = args, kwargs
            guidelines: Optional[List[str]] = None  # Store guidelines from input check

            # --- 1. Input Check (if enabled) ---
            if check_input:
                try:
                    # Call adapter's input check method with explicit keywords
                    modified_args, modified_kwargs, blocked, reason = (
                        adapter_instance.apply_input_guardrails(
                            args=current_args,
                            kwargs=current_kwargs,
                            func_name=func_name,
                            injection_strategy=effective_injection_strategy,  # Pass the injection strategy to the adapter
                        )
                    )

                    # If blocked, handle based on configuration
                    if blocked:
                        if on_input_violation == "exception":
                            # Import exception class locally to avoid circular dependency issues
                            from klira.sdk.decorators.policies import KliraPolicyViolation

                            raise KliraPolicyViolation(
                                f"Input violation in {func_name}: {reason}"
                            )
                        elif on_input_violation == "alternative":
                            # If the reason itself is the alternative response (e.g., direct reply)
                            if reason and reason != "Input policy violation":
                                return reason
                            else:
                                return violation_response
                        else:  # Default or unknown: Log and potentially allow/block based on adapter's default?
                            logger.warning(
                                f"Unhandled input violation action '{on_input_violation}' for {func_name}. Blocking."
                            )
                            return violation_response  # Default to blocking safely

                    # Update args/kwargs if modified by the adapter (e.g., redaction)
                    current_args, current_kwargs = modified_args, modified_kwargs

                    # Retrieve guidelines from simple storage or OTel context
                    if augment_prompt:
                        global _current_guidelines

                        guidelines = None

                        # First try simple storage
                        if _current_guidelines:
                            guidelines = _current_guidelines
                        else:
                            # Fallback to OTel context
                            try:
                                from opentelemetry import context as otel_context

                                current_otel_ctx = otel_context.get_current()
                                guidelines = otel_context.get_value(
                                    "klira.augmentation.guidelines",
                                    context=current_otel_ctx,
                                )  # type: ignore[assignment]
                            except ImportError:
                                pass  # OpenTelemetry not available
                            except Exception as e:
                                logger.debug(
                                    f"Error retrieving guidelines from OTel context: {e}"
                                )

                        if guidelines and isinstance(guidelines, list):
                            logger.debug(
                                f"Retrieved {len(guidelines)} guidelines for {func_name}."
                            )

                            # Try to inject guidelines into global agent or function arguments
                            try:
                                agent_injected = _inject_guidelines_into_agent_args(
                                    current_args, current_kwargs, guidelines
                                )
                                if not agent_injected:
                                    # Try to find agent in function's global scope
                                    agent_injected = (
                                        _inject_guidelines_into_global_agent(
                                            func, guidelines
                                        )
                                    )

                                if agent_injected:
                                    logger.info(
                                        f"Successfully injected {len(guidelines)} guidelines into agent instructions for {func_name}."
                                    )
                                    # Clear guidelines after successful injection
                                    _current_guidelines = None
                                else:
                                    logger.debug(
                                        f"No agent found for {func_name}. Guidelines not injected."
                                    )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to inject guidelines into agent for {func_name}: {e}"
                                )

                except Exception as e:
                    logger.error(
                        f"Error during input guardrail check for {func_name}: {e}",
                        exc_info=True,
                    )
                    # Fail open on error during check

            # --- 3. Execute Original Function ---
            # Use the potentially modified current_args and current_kwargs from apply_input_guardrails
            try:
                result = await func(*current_args, **current_kwargs)
            except Exception as e:
                logger.error(
                    f"Error executing wrapped function {func_name} after guardrails: {e}",
                    exc_info=True,
                )
                raise  # Re-raise the original exception

            # --- 4. Output Check (if enabled) ---
            if check_output:
                try:
                    # Call adapter's output check method with explicit keywords
                    modified_result, blocked, alternative_response = (
                        adapter_instance.apply_output_guardrails(
                            result=result,
                            func_name=func_name,
                            # **adapter_kwargs # Base method doesn't take extra kwargs
                        )
                    )

                    # If blocked/modified, handle based on configuration
                    if blocked:
                        if on_output_violation == "exception":
                            from klira.sdk.decorators.policies import KliraPolicyViolation

                            raise KliraPolicyViolation(
                                f"Output violation in {func_name}: {alternative_response}"
                            )
                        # 'alternative' and 'redact' both use the alternative_response from the adapter
                        elif on_output_violation in ["alternative", "redact"]:
                            return (
                                alternative_response or output_violation_response
                            )  # Return adapter's response or default
                        else:
                            logger.warning(
                                f"Unhandled output violation action '{on_output_violation}' for {func_name}. Returning adapter response or default."
                            )
                            return alternative_response or output_violation_response
                    else:
                        # If not blocked, return the potentially modified result from the adapter
                        return modified_result

                except Exception as e:
                    logger.error(
                        f"Error during output guardrail check for {func_name}: {e}",
                        exc_info=True,
                    )
                    # Fail open on error during check, return original result
                    return result
            else:
                # If output check disabled, return original result
                return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Synchronous wrapper for guardrails processing."""
            nonlocal adapter_instance
            nonlocal effective_injection_strategy

            if not adapter_instance:
                logger.error(
                    f"Guardrails adapter lost for {func_name} in sync_wrapper. Skipping checks."
                )
                return func(*args, **kwargs)

            current_args, current_kwargs = args, kwargs
            guidelines: Optional[List[str]] = None

            # --- 1. Input Check (if enabled) ---
            if check_input:
                try:
                    modified_args, modified_kwargs, blocked, reason = (
                        adapter_instance.apply_input_guardrails(
                            args=current_args,
                            kwargs=current_kwargs,
                            func_name=func_name,
                            injection_strategy=effective_injection_strategy,
                        )
                    )

                    if blocked:
                        if on_input_violation == "exception":
                            from klira.sdk.decorators.policies import KliraPolicyViolation

                            raise KliraPolicyViolation(
                                f"Input violation in {func_name}: {reason}"
                            )
                        elif on_input_violation == "alternative":
                            if reason and reason != "Input policy violation":
                                return reason
                            else:
                                return violation_response
                        else:
                            logger.warning(
                                f"Unhandled input violation action '{on_input_violation}' for {func_name}. Blocking."
                            )
                            return violation_response

                    current_args, current_kwargs = modified_args, modified_kwargs

                    # Retrieve guidelines from simple storage or OTel context
                    if augment_prompt:
                        global _current_guidelines
                        guidelines = None

                        if _current_guidelines:
                            guidelines = _current_guidelines
                        else:
                            try:
                                from opentelemetry import context as otel_context

                                current_otel_ctx = otel_context.get_current()
                                guidelines_value = otel_context.get_value(
                                    "klira.augmentation.guidelines",
                                    context=current_otel_ctx,
                                )
                                guidelines = (
                                    guidelines_value
                                    if isinstance(guidelines_value, list)
                                    else None
                                )
                            except ImportError:
                                pass
                            except Exception as e:
                                logger.debug(
                                    f"Error retrieving guidelines from OTel context: {e}"
                                )

                        if guidelines and isinstance(guidelines, list):
                            logger.debug(
                                f"Retrieved {len(guidelines)} guidelines for {func_name}."
                            )

                            try:
                                agent_injected = _inject_guidelines_into_agent_args(
                                    current_args, current_kwargs, guidelines
                                )
                                if not agent_injected:
                                    agent_injected = (
                                        _inject_guidelines_into_global_agent(
                                            func, guidelines
                                        )
                                    )

                                if agent_injected:
                                    logger.info(
                                        f"Successfully injected {len(guidelines)} guidelines into agent instructions for {func_name}."
                                    )
                                    _current_guidelines = None
                                else:
                                    logger.debug(
                                        f"No agent found for {func_name}. Guidelines not injected."
                                    )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to inject guidelines into agent for {func_name}: {e}"
                                )

                except Exception as e:
                    logger.error(
                        f"Error during input guardrail check for {func_name}: {e}",
                        exc_info=True,
                    )

            # --- 2. Execute Original Function ---
            try:
                result = func(*current_args, **current_kwargs)
            except Exception as e:
                logger.error(
                    f"Error executing wrapped function {func_name} after guardrails: {e}",
                    exc_info=True,
                )
                raise

            # --- 3. Output Check (if enabled) ---
            if check_output:
                try:
                    modified_result, blocked, alternative_response = (
                        adapter_instance.apply_output_guardrails(
                            result=result,
                            func_name=func_name,
                        )
                    )

                    if blocked:
                        if on_output_violation == "exception":
                            from klira.sdk.decorators.policies import KliraPolicyViolation

                            raise KliraPolicyViolation(
                                f"Output violation in {func_name}: {alternative_response}"
                            )
                        elif on_output_violation in ["alternative", "redact"]:
                            return alternative_response or output_violation_response
                        else:
                            logger.warning(
                                f"Unhandled output violation action '{on_output_violation}' for {func_name}. Returning adapter response or default."
                            )
                            return alternative_response or output_violation_response
                    else:
                        return modified_result

                except Exception as e:
                    logger.error(
                        f"Error during output guardrail check for {func_name}: {e}",
                        exc_info=True,
                    )
                    return result
            else:
                return result

        # Return the correct wrapper based on the original function type
        if is_async:
            return async_wrapper
        else:
            return sync_wrapper

    # Handle decorator called with or without arguments
    if _func is None:
        return decorator_guardrails  # Called with arguments: @guardrails(...)
    else:
        # Support both sync and async functions
        return decorator_guardrails(_func)  # Called without arguments: @guardrails


# Alias for backward compatibility with previous Klira AI SDK versions
add_policies = guardrails


def _inject_guidelines_into_global_agent(
    func: Callable[..., Any], guidelines: List[str]
) -> bool:
    """
    Helper function to inject guidelines into agent found in function's global scope.

    Args:
        func: The function whose globals to search
        guidelines: List of guideline strings to inject

    Returns:
        True if an agent was found and guidelines were injected, False otherwise
    """
    try:
        # Try to import agents module to check for Agent instances
        try:
            from agents import Agent
        except ImportError:
            # OpenAI Agents SDK not available
            return False

        # Get the function's global namespace
        func_globals = getattr(func, "__globals__", {})

        # Look for Agent instances in the global namespace
        for name, value in func_globals.items():
            if isinstance(value, Agent) and hasattr(value, "instructions"):
                original_instructions = getattr(value, "instructions", "")
                if not isinstance(original_instructions, str):
                    original_instructions = str(original_instructions)

                # Format guidelines
                policy_section_header = "\n\nIMPORTANT POLICY GUIDELINES:"
                formatted_guidelines = (
                    policy_section_header
                    + "\n"
                    + "\n".join([f"- {g}" for g in guidelines])
                )

                # Avoid duplicate injection
                if policy_section_header in original_instructions:
                    original_instructions = original_instructions.split(
                        policy_section_header
                    )[0].rstrip()

                # Inject guidelines
                separator = "\n\n" if original_instructions else ""
                new_instructions = (
                    original_instructions + separator + formatted_guidelines
                )

                # Update agent instructions
                setattr(value, "instructions", new_instructions)
                logger.debug(
                    f"Injected {len(guidelines)} guidelines into global Agent '{name}'"
                )
                return True

        return False

    except Exception as e:
        logger.error(
            f"Error in _inject_guidelines_into_global_agent: {e}", exc_info=True
        )
        return False


def _inject_guidelines_into_agent_args(
    args: tuple[Any, ...], kwargs: dict[str, Any], guidelines: List[str]
) -> bool:
    """
    Helper function to inject guidelines into agent instructions found in function arguments.

    Args:
        args: Function positional arguments
        kwargs: Function keyword arguments
        guidelines: List of guideline strings to inject

    Returns:
        True if an agent was found and guidelines were injected, False otherwise
    """
    try:
        # Try to import agents module to check for Agent instances
        try:
            from agents import Agent
        except ImportError:
            # OpenAI Agents SDK not available
            return False

        # Look for Agent instances in the arguments
        agent_found = False

        # Check positional arguments
        for arg in args:
            if isinstance(arg, Agent) and hasattr(arg, "instructions"):
                agent_found = True
                original_instructions = getattr(arg, "instructions", "")
                if not isinstance(original_instructions, str):
                    original_instructions = str(original_instructions)

                # Format guidelines
                policy_section_header = "\n\nIMPORTANT POLICY GUIDELINES:"
                formatted_guidelines = (
                    policy_section_header
                    + "\n"
                    + "\n".join([f"- {g}" for g in guidelines])
                )

                # Avoid duplicate injection
                if policy_section_header in original_instructions:
                    original_instructions = original_instructions.split(
                        policy_section_header
                    )[0].rstrip()

                # Inject guidelines
                separator = "\n\n" if original_instructions else ""
                new_instructions = (
                    original_instructions + separator + formatted_guidelines
                )

                # Update agent instructions
                setattr(arg, "instructions", new_instructions)
                logger.debug(
                    f"Injected {len(guidelines)} guidelines into Agent.instructions"
                )

        # Check keyword arguments
        for key, value in kwargs.items():
            if isinstance(value, Agent) and hasattr(value, "instructions"):
                agent_found = True
                original_instructions = getattr(value, "instructions", "")
                if not isinstance(original_instructions, str):
                    original_instructions = str(original_instructions)

                # Format guidelines
                policy_section_header = "\n\nIMPORTANT POLICY GUIDELINES:"
                formatted_guidelines = (
                    policy_section_header
                    + "\n"
                    + "\n".join([f"- {g}" for g in guidelines])
                )

                # Avoid duplicate injection
                if policy_section_header in original_instructions:
                    original_instructions = original_instructions.split(
                        policy_section_header
                    )[0].rstrip()

                # Inject guidelines
                separator = "\n\n" if original_instructions else ""
                new_instructions = (
                    original_instructions + separator + formatted_guidelines
                )

                # Update agent instructions
                setattr(value, "instructions", new_instructions)
                logger.debug(
                    f"Injected {len(guidelines)} guidelines into Agent.instructions (kwarg: {key})"
                )

        return agent_found

    except Exception as e:
        logger.error(f"Error in _inject_guidelines_into_agent_args: {e}", exc_info=True)
        return False
