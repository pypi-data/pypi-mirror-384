"""Adapter for patching the OpenAI Responses API (used by Agents SDK)."""

import copy
import functools
import logging
from typing import Any, Dict

from klira.sdk.adapters.llm_base_adapter import BaseLLMAdapter

# Try to import OpenAI client for patching
try:
    import openai

    # Check specifically for the 'responses' attribute
    if hasattr(openai, "responses") and hasattr(openai.responses, "create"):
        OPENAI_RESPONSES_API_AVAILABLE = True
    else:
        OPENAI_RESPONSES_API_AVAILABLE = False
except ImportError:
    openai = None
    OPENAI_RESPONSES_API_AVAILABLE = False

# Try to import OTel context
try:
    from opentelemetry import context as otel_context
except ImportError:
    otel_context = None  # type: ignore[assignment]

logger = logging.getLogger("klira.adapters.openai_responses")


class OpenAIResponsesAdapter(BaseLLMAdapter):
    """Patches the OpenAI Responses API (openai.responses.create) for guideline injection."""

    is_available = OPENAI_RESPONSES_API_AVAILABLE

    def patch(self) -> None:
        """Patch the OpenAI responses.create method for guideline injection."""
        logger.debug(
            "OpenAIResponsesAdapter: Attempting to patch openai.responses.create..."
        )

        # Store the original methods directly from openai
        original_create = openai.responses.create

        def patched_create(*args: Any, **kwargs: Any) -> Any:
            try:
                # Store original instructions/messages before augmentation
                copy.deepcopy(kwargs.get("instructions")) if kwargs.get(
                    "instructions"
                ) else None
                copy.deepcopy(kwargs.get("messages")) if kwargs.get(
                    "messages"
                ) else None

                # Check for instructions in kwargs
                instructions = kwargs.get("instructions")
                if instructions and isinstance(instructions, str):
                    from klira.sdk.guardrails.engine import GuardrailsEngine

                    guidelines = GuardrailsEngine.get_current_guidelines()

                    if guidelines:
                        # Build augmentation text
                        augmentation_text = "\n\nIMPORTANT POLICY DIRECTIVES:\n"
                        augmentation_text += "\n".join([f"• {g}" for g in guidelines])

                        # Inject into instructions
                        kwargs["instructions"] = instructions + augmentation_text

                        # Clear context to prevent double-injection
                        GuardrailsEngine.clear_current_guidelines()

                        # Debug logging
                        logger.info(
                            f"Injected {len(guidelines)} policy guidelines into responses.create instructions"
                        )
            except Exception as e:
                logger.error(f"Policy injection error in responses.create: {str(e)}")

            result = original_create(*args, **kwargs)

            # Apply outbound guardrails evaluation
            result = self._apply_outbound_guardrails(result)

            return result

        # Apply the patched method directly to openai
        openai.responses.create = patched_create
        logger.info("Successfully patched openai.responses.create for augmentation.")

        # Also patch the async variant if available
        try:
            if hasattr(openai.responses, "acreate"):
                original_acreate = openai.responses.acreate

                async def patched_acreate(*args: Any, **kwargs: Any) -> Any:
                    # Similar augmentation logic as above
                    try:
                        # Store original instructions/messages before augmentation
                        copy.deepcopy(kwargs.get("instructions")) if kwargs.get(
                            "instructions"
                        ) else None
                        copy.deepcopy(kwargs.get("messages")) if kwargs.get(
                            "messages"
                        ) else None

                        instructions = kwargs.get("instructions")
                        if instructions and isinstance(instructions, str):
                            from klira.sdk.guardrails.engine import GuardrailsEngine

                            guidelines = GuardrailsEngine.get_current_guidelines()
                            if guidelines:
                                augmentation_text = "\n\nIMPORTANT POLICY DIRECTIVES:\n"
                                augmentation_text += "\n".join(
                                    [f"• {g}" for g in guidelines]
                                )
                                kwargs["instructions"] = (
                                    instructions + augmentation_text
                                )
                                GuardrailsEngine.clear_current_guidelines()
                                logger.info(
                                    f"Injected {len(guidelines)} policy guidelines into async responses.create instructions"
                                )
                    except Exception as e:
                        logger.error(
                            f"Policy injection error in async responses.create: {str(e)}"
                        )

                    result = await original_acreate(*args, **kwargs)

                    # Apply outbound guardrails evaluation
                    result = await self._apply_outbound_guardrails_async(result)

                    return result

                openai.responses.acreate = patched_acreate
                logger.info("Successfully patched async openai.responses.create.")
            else:
                logger.debug("Async openai.responses.acreate not found.")
        except Exception as e:
            logger.warning(f"Failed to patch async responses.create: {e}")

    def _patch_sync_responses_create(self) -> None:
        """Patches the synchronous openai.responses.create method."""
        try:
            target_obj = openai.responses
            method_name = "create"
            if hasattr(target_obj, method_name) and not hasattr(
                getattr(target_obj, method_name), "_klira_augmented"
            ):
                original_create = getattr(target_obj, method_name)

                @functools.wraps(original_create)
                def patched_create(*args: Any, **kwargs: Any) -> Any:
                    # Inject guidelines into kwargs, focusing on 'instructions'
                    modified_kwargs = self._inject_guidelines_into_kwargs(kwargs)
                    return original_create(*args, **modified_kwargs)

                setattr(patched_create, "_klira_augmented", True)
                setattr(target_obj, method_name, patched_create)
                logger.info(
                    f"Successfully patched openai.responses.{method_name} for augmentation."
                )
            elif hasattr(getattr(target_obj, method_name, None), "_klira_augmented"):
                logger.debug(f"openai.responses.{method_name} already patched.")
            else:
                logger.warning(
                    f"Could not find openai.responses.{method_name} to patch."
                )
        except AttributeError as e:
            logger.error(f"AttributeError during sync OpenAI Responses patching: {e}")
        except Exception as e:
            logger.error(
                f"Error patching sync OpenAI Responses client: {e}", exc_info=True
            )

    def _patch_async_responses_create(self) -> None:
        """Patches the asynchronous openai.responses.create method (if it exists)."""
        # Note: As of recent openai library versions, there might not be a separate async client
        # for the legacy '/responses' endpoint. Check carefully.
        try:
            async_target_obj = getattr(
                openai, "AsyncResponses", None
            )  # Or maybe openai.responses.async_client?
            if not async_target_obj:
                # Try finding it under the main async client if structure changed
                if hasattr(openai, "AsyncOpenAI"):
                    temp_client = openai.AsyncOpenAI(
                        api_key="temp", base_url="http://localhost"
                    )  # Need instance
                    if hasattr(temp_client, "responses"):
                        async_target_obj = (
                            temp_client.responses
                        )  # Get it from an instance

            if not async_target_obj:
                logger.debug(
                    "Could not locate OpenAI AsyncResponses object/client for patching."
                )
                return

            method_name = "create"
            if hasattr(async_target_obj, method_name) and not hasattr(
                getattr(async_target_obj, method_name), "_klira_augmented"
            ):
                original_async_create = getattr(async_target_obj, method_name)

                @functools.wraps(original_async_create)
                async def patched_async_create(*args: Any, **kwargs: Any) -> Any:
                    modified_kwargs = self._inject_guidelines_into_kwargs(kwargs)
                    # Ensure the call is awaited if the original was async
                    return await original_async_create(*args, **modified_kwargs)

                setattr(patched_async_create, "_klira_augmented", True)
                setattr(async_target_obj, method_name, patched_async_create)
                logger.info(
                    f"Successfully patched async openai.responses.{method_name}."
                )
            elif hasattr(
                getattr(async_target_obj, method_name, None), "_klira_augmented"
            ):
                logger.debug(f"Async openai.responses.{method_name} already patched.")
            else:
                logger.warning(
                    f"Could not find async method openai.responses.{method_name} to patch."
                )
        except AttributeError as e:
            logger.error(f"AttributeError during async OpenAI Responses patching: {e}")
        except Exception as e:
            logger.error(
                f"Error patching async OpenAI Responses client: {e}", exc_info=True
            )

    def _inject_guidelines_into_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Injects guidelines into the 'instructions' field or system prompt of the payload kwargs."""
        guidelines = None

        # First try getting guidelines through GuardrailsEngine (newer, preferred method)
        try:
            from klira.sdk.guardrails.engine import GuardrailsEngine

            engine = GuardrailsEngine.get_instance()
            if engine:
                guidelines = engine.get_current_guidelines()
                if guidelines:
                    logger.debug(
                        f"[OpenAIResponsesAdapter] Retrieved {len(guidelines)} guidelines from GuardrailsEngine."
                    )
                    logger.debug(
                        f"Found {len(guidelines)} guidelines to inject at OpenAI Responses call time"
                    )

            # If we couldn't get guidelines from GuardrailsEngine, try legacy OTel method
            if not guidelines and otel_context:
                current_ctx = otel_context.get_current()
                guidelines = otel_context.get_value(
                    "klira.augmentation.guidelines", context=current_ctx
                )  # type: ignore[assignment]
                if guidelines:
                    logger.debug(
                        f"[OpenAIResponsesAdapter] Retrieved {len(guidelines)} guidelines from OTel context (fallback)."
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
            logger.debug("No guidelines found to inject in OpenAIResponsesAdapter.")
            return kwargs

        modified_kwargs = kwargs.copy()  # Work on a copy
        guidelines_injected = False
        policy_section_header = "\n\nIMPORTANT POLICY GUIDELINES:"
        formatted_guidelines = (
            policy_section_header + "\n" + "\n".join([f"- {g}" for g in guidelines])
        )

        # Prioritize injecting into 'instructions' field used by /responses
        if "instructions" in modified_kwargs and isinstance(
            modified_kwargs["instructions"], str
        ):
            logger.debug("Found 'instructions' key for guideline injection.")
            original_instructions = modified_kwargs["instructions"]
            # Avoid duplicate injection
            if policy_section_header in original_instructions:
                original_instructions = original_instructions.split(
                    policy_section_header
                )[0].rstrip()
            separator = "\n\n" if original_instructions else ""
            modified_kwargs["instructions"] = (
                original_instructions + separator + formatted_guidelines
            )
            logger.debug(
                f"Injected {len(guidelines)} guidelines into instructions field."
            )
            logger.debug(
                f"Injected {len(guidelines)} policy guidelines into OpenAI Responses 'instructions' field"
            )
            guidelines_injected = True
        else:
            # Fallback: Check if 'messages' structure is used
            if "messages" in modified_kwargs and isinstance(
                modified_kwargs["messages"], list
            ):
                logger.debug(
                    "'instructions' not found, attempting system prompt injection in 'messages' as fallback."
                )
                messages = list(modified_kwargs["messages"])
                system_message_found = False

                for i, msg in enumerate(messages):
                    if isinstance(msg, dict) and msg.get("role") == "system":
                        system_message_found = True
                        mod_msg = msg.copy()
                        original_content = mod_msg.get("content", "")
                        if not isinstance(original_content, str):
                            original_content = str(original_content)
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
                            f"Injected {len(guidelines)} guidelines into system prompt (fallback)."
                        )
                        logger.debug(
                            f"Injected {len(guidelines)} policy guidelines into system message (fallback)"
                        )
                        guidelines_injected = True
                        break

                if not system_message_found:
                    # Create and prepend system message if not found
                    messages.insert(
                        0, {"role": "system", "content": formatted_guidelines.strip()}
                    )
                    logger.debug(
                        f"No system prompt found in messages. Created and prepended one with {len(guidelines)} guidelines (fallback)."
                    )
                    logger.debug(
                        f"Created new system message with {len(guidelines)} policy guidelines at Responses call"
                    )
                    guidelines_injected = True

                if guidelines_injected:
                    modified_kwargs["messages"] = (
                        messages  # Update kwargs if messages were modified
                    )
            else:
                logger.warning(
                    "Could not inject guidelines into Responses API call: Neither 'instructions' nor 'messages' suitable for injection found."
                )

        # Clear context only if injection was attempted (successful or not in finding target)
        if guidelines_injected:
            try:
                # Try to clear via GuardrailsEngine first (preferred)
                from klira.sdk.guardrails.engine import GuardrailsEngine

                engine = GuardrailsEngine.get_instance()
                if engine:
                    engine.clear_current_guidelines()
                    logger.debug(
                        "Cleared guidelines from GuardrailsEngine after Responses injection."
                    )
                # Fallback to OTel if needed
                elif otel_context:
                    current_ctx = otel_context.get_current()
                    new_ctx = otel_context.set_value(
                        "klira.augmentation.guidelines", None, current_ctx
                    )
                    otel_context.attach(new_ctx)
                    logger.debug(
                        "Cleared guidelines from OTel context after Responses injection."
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to clear guidelines from context (Responses): {e}"
                )

        return (
            modified_kwargs if guidelines_injected else kwargs
        )  # Return modified only if something was changed

    def _apply_outbound_guardrails(self, result: Any) -> Any:
        """Apply outbound guardrails to OpenAI Responses results (synchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine

            # Extract content from OpenAI Responses response
            response_text = self._extract_response_content(result)
            if not response_text.strip():
                return result

            # Create evaluation context
            context = {
                "llm_client": "openai_responses",
                "function_name": "openai.responses.create",
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
                        "Cannot run outbound guardrails evaluation for OpenAI Responses in sync context within async loop. "
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
                    f"OpenAI Responses outbound guardrails blocked response: {decision.reason}"
                )
                # Return a modified response with blocked content
                return self._create_blocked_response(
                    result, decision.reason or "Content policy violation detected"
                )

            return result

        except Exception as e:
            logger.error(
                f"Error applying outbound guardrails for OpenAI Responses: {e}",
                exc_info=True,
            )
            # Fail open - return original result
            return result

    async def _apply_outbound_guardrails_async(self, result: Any) -> Any:
        """Apply outbound guardrails to OpenAI Responses results (asynchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine

            # Extract content from OpenAI Responses response
            response_text = self._extract_response_content(result)
            if not response_text.strip():
                return result

            # Create evaluation context
            context = {
                "llm_client": "openai_responses",
                "function_name": "openai.responses.acreate",
            }

            # Get guardrails engine and evaluate
            engine = GuardrailsEngine.get_instance()
            decision = await engine.evaluate(
                response_text, context, direction="outbound"
            )

            if not decision.allowed:
                logger.warning(
                    f"OpenAI Responses async outbound guardrails blocked response: {decision.reason}"
                )
                # Return a modified response with blocked content
                return self._create_blocked_response(
                    result, decision.reason or "Content policy violation detected"
                )

            return result

        except Exception as e:
            logger.error(
                f"Error applying outbound guardrails for OpenAI Responses async: {e}",
                exc_info=True,
            )
            # Fail open - return original result
            return result

    def _extract_response_content(self, result: Any) -> str:
        """Extract text content from OpenAI Responses response object."""
        try:
            # Handle OpenAI Responses response format
            if hasattr(result, "content") and result.content:
                return str(result.content)
            elif hasattr(result, "text") and result.text:
                return str(result.text)
            elif hasattr(result, "choices") and result.choices:
                # Similar to chat completions format
                choice = result.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    return str(choice.message.content) if choice.message.content else ""
                elif hasattr(choice, "text"):
                    return str(choice.text) if choice.text else ""
            elif isinstance(result, dict):
                # Handle dictionary response
                if "content" in result:
                    return str(result["content"])
                elif "text" in result:
                    return str(result["text"])
                elif "response" in result:
                    return str(result["response"])

            # Fallback: try to convert to string
            return str(result) if result else ""

        except Exception as e:
            logger.debug(
                f"Error extracting content from OpenAI Responses response: {e}"
            )
            return ""

    def _create_blocked_response(self, original_result: Any, reason: str) -> Any:
        """Create a blocked response that matches the original response format."""
        try:
            blocked_message = (
                f"[BLOCKED BY GUARDRAILS] - {reason}"
                if reason
                else "[BLOCKED BY GUARDRAILS] - Content policy violation detected"
            )

            # Try to modify the original response in place
            if hasattr(original_result, "content"):
                original_result.content = blocked_message
                return original_result
            elif hasattr(original_result, "text"):
                original_result.text = blocked_message
                return original_result
            elif hasattr(original_result, "choices") and original_result.choices:
                # Similar to chat completions format
                choice = original_result.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    choice.message.content = blocked_message
                    return original_result
                elif hasattr(choice, "text"):
                    choice.text = blocked_message
                    return original_result
            elif isinstance(original_result, dict):
                # Handle dictionary response
                if "content" in original_result:
                    original_result["content"] = blocked_message
                    return original_result
                elif "text" in original_result:
                    original_result["text"] = blocked_message
                    return original_result
                elif "response" in original_result:
                    original_result["response"] = blocked_message
                    return original_result

            # Fallback: return the blocked message as string
            return blocked_message

        except Exception as e:
            logger.error(f"Error creating blocked response: {e}")
            # Ultimate fallback
            return "[BLOCKED BY GUARDRAILS] - Content policy violation detected"
