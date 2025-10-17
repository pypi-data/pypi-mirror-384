"""Adapter for patching the OpenAI Chat Completion API."""

import functools
import logging
from typing import Any, Dict, Optional

from klira.sdk.adapters.llm_base_adapter import BaseLLMAdapter

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
except ImportError:
    otel_context = None  # type: ignore[assignment]

logger = logging.getLogger("klira.adapters.openai_completion")


class OpenAICompletionAdapter(BaseLLMAdapter):
    """Patches OpenAI Chat Completion API calls for guideline injection."""

    is_available = OPENAI_CLIENT_AVAILABLE

    def patch(self) -> None:
        """Patch the OpenAI chat.completions.create method."""
        logger.debug(
            "OpenAICompletionAdapter: Attempting to patch openai.chat.completions methods..."
        )

        # Get the original method directly from openai
        original_create = openai.chat.completions.create

        # Define wrapper function
        def patched_create(*args: Any, **kwargs: Any) -> Any:
            from klira.sdk.tracing.tracing import get_tracer
            from opentelemetry.trace import StatusCode

            tracer = get_tracer()

            # Extract model and parameters
            model = kwargs.get("model", "unknown")
            temperature = kwargs.get("temperature")
            max_tokens = kwargs.get("max_tokens")

            # Create LLM request span
            with tracer.start_span("klira.llm.request") as llm_span:
                try:
                    # Extract messages from args/kwargs
                    messages = kwargs.get("messages") or (
                        args[0].get("messages")
                        if args and isinstance(args[0], dict)
                        else []
                    )

                    # Store original messages before augmentation
                    import copy
                    original_messages = copy.deepcopy(messages) if messages else None

                    # Set request attributes
                    self._create_llm_request_span(
                        llm_span,
                        provider="openai",
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )

                    # Add augmentation tracking if guidelines present (pass original messages)
                    self._add_augmentation_attributes(llm_span, original_messages=original_messages)

                    if messages:
                        # Find the first system message
                        system_msg = next(
                            (m for m in messages if m.get("role") == "system"), None
                        )
                        if system_msg and isinstance(system_msg.get("content"), str):
                            from klira.sdk.guardrails.engine import GuardrailsEngine

                            guidelines = GuardrailsEngine.get_current_guidelines()

                            if guidelines:
                                # Build augmentation text
                                augmentation_text = "\n\nIMPORTANT POLICY DIRECTIVES:\n"
                                augmentation_text += "\n".join(
                                    [f"• {g}" for g in guidelines]
                                )

                                # Inject into system prompt
                                system_msg["content"] += augmentation_text

                                # Clear context to prevent double-injection
                                GuardrailsEngine.clear_current_guidelines()

                                # Debug logging
                                logger.info(
                                    f"Injected {len(guidelines)} policy guidelines into system prompt"
                                )
                except Exception as e:
                    logger.error(f"Policy injection error: {str(e)}")

                try:
                    # Call the original method
                    result = original_create(*args, **kwargs)

                    # Add response attributes
                    self._add_llm_response_attributes(llm_span, result, "openai")

                    llm_span.set_status(StatusCode.OK)

                except Exception as e:
                    llm_span.set_status(StatusCode.ERROR, str(e))
                    llm_span.record_exception(e)
                    raise

                # Apply outbound guardrails evaluation
                result = self._apply_outbound_guardrails(result)

                return result

        # Apply patch directly to openai
        openai.chat.completions.create = patched_create
        logger.info(
            "Successfully patched openai.chat.completions.create for augmentation."
        )

        # Also patch the async variant if available
        try:
            # Check if acreate exists before attempting to patch it
            if hasattr(openai.chat.completions, "acreate"):
                original_acreate = openai.chat.completions.acreate

                async def patched_acreate(*args: Any, **kwargs: Any) -> Any:
                    from klira.sdk.tracing.tracing import get_tracer
                    from opentelemetry.trace import StatusCode

                    tracer = get_tracer()

                    # Extract model and parameters
                    model = kwargs.get("model", "unknown")
                    temperature = kwargs.get("temperature")
                    max_tokens = kwargs.get("max_tokens")

                    # Create LLM request span
                    with tracer.start_span("klira.llm.request") as llm_span:
                        try:
                            # Extract messages from args/kwargs
                            messages = kwargs.get("messages") or (
                                args[0].get("messages")
                                if args and isinstance(args[0], dict)
                                else []
                            )

                            # Store original messages before augmentation
                            import copy
                            original_messages = copy.deepcopy(messages) if messages else None

                            # Set request attributes
                            self._create_llm_request_span(
                                llm_span,
                                provider="openai",
                                model=model,
                                messages=messages,
                                temperature=temperature,
                                max_tokens=max_tokens
                            )

                            # Add augmentation tracking if guidelines present (pass original messages)
                            self._add_augmentation_attributes(llm_span, original_messages=original_messages)

                            if messages:
                                system_msg = next(
                                    (m for m in messages if m.get("role") == "system"), None
                                )
                                if system_msg and isinstance(
                                    system_msg.get("content"), str
                                ):
                                    from klira.sdk.guardrails.engine import GuardrailsEngine

                                    guidelines = GuardrailsEngine.get_current_guidelines()
                                    if guidelines:
                                        augmentation_text = (
                                            "\n\nIMPORTANT POLICY DIRECTIVES:\n"
                                        )
                                        augmentation_text += "\n".join(
                                            [f"• {g}" for g in guidelines]
                                        )
                                        system_msg["content"] += augmentation_text
                                        GuardrailsEngine.clear_current_guidelines()
                                        logger.info(
                                            f"Injected {len(guidelines)} policy guidelines into async system prompt"
                                        )
                        except Exception as e:
                            logger.error(
                                f"Policy injection error in async completion: {str(e)}"
                            )

                        try:
                            result = await original_acreate(*args, **kwargs)

                            # Add response attributes
                            self._add_llm_response_attributes(llm_span, result, "openai")

                            llm_span.set_status(StatusCode.OK)

                        except Exception as e:
                            llm_span.set_status(StatusCode.ERROR, str(e))
                            llm_span.record_exception(e)
                            raise

                        # Apply outbound guardrails evaluation
                        result = await self._apply_outbound_guardrails_async(result)

                        return result

                openai.chat.completions.acreate = patched_acreate
                logger.info(
                    "Successfully patched async openai.chat.completions.acreate for augmentation."
                )
            else:
                logger.debug(
                    "OpenAI async completions (acreate) not found, skipping patch."
                )
        except Exception as e:
            logger.debug(f"Failed to patch async completions: {e}")

    def _patch_sync_create(self) -> None:
        """Patches the synchronous openai.chat.completions.create method."""
        try:
            target_obj = openai.chat.completions
            method_name = "create"
            if hasattr(target_obj, method_name) and not hasattr(
                getattr(target_obj, method_name), "_klira_augmented"
            ):
                original_create = getattr(target_obj, method_name)

                @functools.wraps(original_create)
                def patched_create(*args: Any, **kwargs: Any) -> Any:
                    modified_kwargs = self._inject_guidelines_into_kwargs(kwargs)
                    return original_create(*args, **modified_kwargs)

                setattr(patched_create, "_klira_augmented", True)
                setattr(target_obj, method_name, patched_create)
                logger.info(
                    f"Successfully patched openai.chat.completions.{method_name} for augmentation."
                )
            elif hasattr(getattr(target_obj, method_name, None), "_klira_augmented"):
                logger.debug(f"openai.chat.completions.{method_name} already patched.")
            else:
                logger.warning(
                    f"Could not find openai.chat.completions.{method_name} to patch."
                )
        except AttributeError as e:
            logger.error(f"AttributeError during sync OpenAI patching: {e}")
        except Exception as e:
            logger.error(f"Error patching sync OpenAI client: {e}", exc_info=True)

    def _patch_async_create(self) -> None:
        """Patches the asynchronous chat completions create method."""
        try:
            # Common locations for the async client/methods
            async_locations = [
                getattr(
                    getattr(openai.chat, "completions", None), "async_", None
                ),  # Older pattern?
                getattr(
                    openai.chat.completions, "AsyncCompletions", None
                ),  # Newer pattern?
                # Add other potential locations if library structure changes
            ]

            async_target_obj = None
            for loc in async_locations:
                if loc is not None:
                    async_target_obj = loc
                    break

            if not async_target_obj:
                logger.debug(
                    "OpenAI async completions module/class not found, skipping patch."
                )
                return

            # Determine the correct async create method name (e.g., create, acreate)
            async_method_name = None
            for name_to_check in ["create", "acreate"]:  # Check common names
                if hasattr(async_target_obj, name_to_check):
                    async_method_name = name_to_check
                    break

            if not async_method_name:
                logger.debug(
                    f"Could not find async create method on {async_target_obj}, skipping patch."
                )
                return

            target_method = getattr(async_target_obj, async_method_name)
            if not hasattr(target_method, "_klira_augmented"):
                original_async_create = target_method

                @functools.wraps(original_async_create)
                async def patched_async_create(*args: Any, **kwargs: Any) -> Any:
                    modified_kwargs = self._inject_guidelines_into_kwargs(kwargs)
                    return await original_async_create(*args, **modified_kwargs)

                setattr(patched_async_create, "_klira_augmented", True)
                setattr(async_target_obj, async_method_name, patched_async_create)
                logger.info(
                    f"Successfully patched async openai.chat.completions method '{async_method_name}'."
                )
            elif hasattr(target_method, "_klira_augmented"):
                logger.debug(
                    f"Async openai.chat.completions method '{async_method_name}' already patched."
                )

        except AttributeError as e:
            logger.error(f"AttributeError during async OpenAI patching: {e}")
        except Exception as e:
            logger.error(f"Error patching async OpenAI client: {e}", exc_info=True)

    def _inject_guidelines_into_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Injects guidelines into the payload, by appending to the system prompt or creating
        a new system message if none exists.
        """
        guidelines = None

        # First try getting guidelines through GuardrailsEngine (newer, preferred method)
        try:
            from klira.sdk.guardrails.engine import GuardrailsEngine

            engine = GuardrailsEngine.get_instance()
            if engine:
                guidelines = engine.get_current_guidelines()
                if guidelines:
                    logger.debug(
                        f"[OpenAICompletionAdapter] Retrieved {len(guidelines)} guidelines from GuardrailsEngine."
                    )
                    logger.debug(
                        f"Found {len(guidelines)} guidelines to inject at OpenAI Chat Completions call time"
                    )

            # If we couldn't get guidelines from GuardrailsEngine, try legacy OTel method
            if not guidelines and otel_context:
                current_ctx = otel_context.get_current()
                guidelines = otel_context.get_value(
                    "klira.augmentation.guidelines", context=current_ctx
                )  # type: ignore[assignment]
                if guidelines:
                    logger.debug(
                        f"[OpenAICompletionAdapter] Retrieved {len(guidelines)} guidelines from OTel context (fallback)."
                    )
        except Exception as e:
            logger.debug(f"Error retrieving guidelines from GuardrailsEngine: {e}")
            # Try legacy method if GuardrailsEngine failed
            if otel_context:
                try:
                    current_ctx = otel_context.get_current()
                    guidelines = otel_context.get_value(
                        "klira.augmentation.guidelines", context=current_ctx
                    )  # type: ignore[assignment]
                except Exception as e2:
                    logger.debug(
                        f"Could not retrieve guidelines from OTel context either: {e2}"
                    )

        if not guidelines:
            logger.debug("No guidelines found to inject in OpenAICompletionAdapter.")
            return kwargs

        modified_kwargs = kwargs.copy()  # Work on a copy
        guidelines_injected = False

        # Only proceed if the 'messages' key is present and it's a list
        if "messages" in modified_kwargs and isinstance(
            modified_kwargs["messages"], list
        ):
            messages = list(modified_kwargs["messages"])
            policy_section_header = "\n\nIMPORTANT POLICY GUIDELINES:"
            formatted_guidelines = (
                policy_section_header + "\n" + "\n".join([f"- {g}" for g in guidelines])
            )
            system_message_found = False

            for i, msg in enumerate(messages):
                if isinstance(msg, dict) and msg.get("role") == "system":
                    system_message_found = True
                    mod_msg = msg.copy()
                    original_content = mod_msg.get("content", "")
                    if not isinstance(original_content, str):
                        original_content = str(original_content)
                        # Avoid duplicate injection by splitting at policy section if it exists
                    if policy_section_header in original_content:
                        original_content = original_content.split(
                            policy_section_header
                        )[0].rstrip()
                    separator = "\n\n" if original_content else ""
                    mod_msg["content"] = (
                        original_content + separator + formatted_guidelines
                    )
                    messages[i] = mod_msg
                    logger.debug(
                        f"Injected {len(guidelines)} guidelines into existing system prompt."
                    )
                    logger.debug(
                        f"Injected {len(guidelines)} policy guidelines into system message at Chat Completions call"
                    )
                    guidelines_injected = True
                    break

            if not system_message_found:
                # No system message found, create and prepend one
                messages.insert(
                    0, {"role": "system", "content": formatted_guidelines.strip()}
                )
                logger.debug(
                    f"No system prompt found. Created and prepended one with {len(guidelines)} guidelines."
                )
                logger.debug(
                    f"Created new system message with {len(guidelines)} policy guidelines at Chat Completions call"
                )
                guidelines_injected = True

            if guidelines_injected:
                modified_kwargs["messages"] = (
                    messages  # Update kwargs with modified messages
                )
        else:
            logger.warning(
                "Could not inject guidelines: 'messages' key not found in kwargs or not a list."
            )

        # Clear context only if injection was attempted (successful or not in finding a usable target)
        if guidelines_injected:
            try:
                # Try to clear via GuardrailsEngine first (preferred)
                from klira.sdk.guardrails.engine import GuardrailsEngine

                engine = GuardrailsEngine.get_instance()
                if engine:
                    engine.clear_current_guidelines()
                    logger.debug(
                        "Cleared guidelines from GuardrailsEngine after Completion injection."
                    )
                # Fallback to OTel if needed
                elif otel_context:
                    current_ctx = otel_context.get_current()
                    new_ctx = otel_context.set_value(
                        "klira.augmentation.guidelines", None, current_ctx
                    )
                    otel_context.attach(new_ctx)
                    logger.debug(
                        "Cleared guidelines from OTel context after Completion injection."
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to clear guidelines from context (Completion): {e}"
                )

        return (
            modified_kwargs if guidelines_injected else kwargs
        )  # Return modified only if something was changed

    def _apply_outbound_guardrails(self, result: Any) -> Any:
        """Apply outbound guardrails to OpenAI completion results (synchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine
            
            # Extract content from OpenAI response
            response_text = self._extract_response_content(result)
            if not response_text.strip():
                return result
            
            # Create evaluation context
            context = {
                "llm_client": "openai",
                "function_name": "openai.chat.completions.create"
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
                        "Cannot run outbound guardrails evaluation for OpenAI completion in sync context within async loop. "
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
                    f"OpenAI completion outbound guardrails blocked response: {decision.reason}"
                )
                # Return a modified response with blocked content
                return self._create_blocked_response(result, decision.reason or "Content policy violation detected")
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying outbound guardrails for OpenAI completion: {e}", exc_info=True)
            # Fail open - return original result
            return result

    async def _apply_outbound_guardrails_async(self, result: Any) -> Any:
        """Apply outbound guardrails to OpenAI completion results (asynchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine
            
            # Extract content from OpenAI response
            response_text = self._extract_response_content(result)
            if not response_text.strip():
                return result
            
            # Create evaluation context
            context = {
                "llm_client": "openai",
                "function_name": "openai.chat.completions.acreate"
            }
            
            # Get guardrails engine and evaluate
            engine = GuardrailsEngine.get_instance()
            decision = await engine.evaluate(response_text, context, direction="outbound")
            
            if not decision.allowed:
                logger.warning(
                    f"OpenAI async completion outbound guardrails blocked response: {decision.reason}"
                )
                # Return a modified response with blocked content
                return self._create_blocked_response(result, decision.reason or "Content policy violation detected")
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying outbound guardrails for OpenAI async completion: {e}", exc_info=True)
            # Fail open - return original result
            return result

    def _extract_response_content(self, result: Any) -> str:
        """Extract text content from OpenAI response object."""
        try:
            # Handle different OpenAI response formats
            if hasattr(result, 'choices') and result.choices:
                choice = result.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    return str(choice.message.content) if choice.message.content else ""
                elif hasattr(choice, 'text'):
                    return str(choice.text) if choice.text else ""
            
            # Fallback: try to convert to string
            return str(result) if result else ""
            
        except Exception as e:
            logger.debug(f"Error extracting content from OpenAI response: {e}")
            return ""

    def _create_blocked_response(self, original_result: Any, reason: str) -> Any:
        """Create a blocked response that matches the original response format."""
        try:
            blocked_message = f"[BLOCKED BY GUARDRAILS] - {reason}" if reason else "[BLOCKED BY GUARDRAILS] - Content policy violation detected"
            
            # Try to modify the original response in place
            if hasattr(original_result, 'choices') and original_result.choices:
                choice = original_result.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    choice.message.content = blocked_message
                    return original_result
                elif hasattr(choice, 'text'):
                    choice.text = blocked_message
                    return original_result
            
            # Fallback: return the blocked message as string
            return blocked_message
            
        except Exception as e:
            logger.error(f"Error creating blocked response: {e}")
            # Ultimate fallback
            return "[BLOCKED BY GUARDRAILS] - Content policy violation detected"

    def _extract_prompt_text(self, messages: Any, provider: str) -> str:
        """Extract prompt text from OpenAI messages."""
        if isinstance(messages, list):
            # Combine all message contents
            parts = []
            for msg in messages:
                if isinstance(msg, dict) and "content" in msg:
                    parts.append(f"{msg.get('role', 'user')}: {msg['content']}")
            return "\n".join(parts)
        return str(messages)

    def _extract_response_text(self, response: Any, provider: str) -> str:
        """Extract response text from OpenAI response."""
        try:
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    return str(choice.message.content) if choice.message.content else ""
            return ""
        except Exception as e:
            logger.debug(f"Error extracting OpenAI response text: {e}")
            return ""

    def _extract_token_usage(self, response: Any, provider: str) -> Optional[Dict[str, int]]:
        """Extract token usage from OpenAI response."""
        try:
            if hasattr(response, 'usage'):
                return {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens
                }
            return None
        except Exception as e:
            logger.debug(f"Error extracting OpenAI token usage: {e}")
            return None

    def _extract_finish_reason(self, response: Any, provider: str) -> Optional[str]:
        """Extract finish reason from OpenAI response."""
        try:
            if hasattr(response, 'choices') and response.choices:
                return response.choices[0].finish_reason
            return None
        except Exception as e:
            logger.debug(f"Error extracting OpenAI finish reason: {e}")
            return None
