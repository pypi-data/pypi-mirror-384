"""Adapter for patching the Anthropic Messages API."""

import copy
import functools
import logging
from typing import Any, Dict, Optional

from klira.sdk.adapters.llm_base_adapter import BaseLLMAdapter

# Try to import Anthropic client for patching
try:
    import anthropic

    ANTHROPIC_CLIENT_AVAILABLE = True
    anthropic_module: Optional[Any] = anthropic
except ImportError:
    anthropic = None  # type: ignore[assignment]
    anthropic_module = None
    ANTHROPIC_CLIENT_AVAILABLE = False

# Try to import OTel context
try:
    from opentelemetry import context as otel_context
except ImportError:
    otel_context = None  # type: ignore[assignment]

logger = logging.getLogger("klira.adapters.anthropic")


class AnthropicAdapter(BaseLLMAdapter):
    """Patches Anthropic Messages API calls for guideline injection."""

    is_available = ANTHROPIC_CLIENT_AVAILABLE

    def patch(self) -> None:
        """Patch the Anthropic messages.create method."""
        logger.debug(
            "AnthropicAdapter: Attempting to patch anthropic.messages.create methods..."
        )

        if not ANTHROPIC_CLIENT_AVAILABLE or anthropic_module is None:
            logger.debug("Anthropic client not available. Skipping patch.")
            return

        try:
            # Get the original method directly from anthropic
            if hasattr(anthropic_module, "resources") and hasattr(
                anthropic_module.resources, "messages"
            ):
                if hasattr(anthropic_module.resources.messages, "create"):
                    original_create = anthropic_module.resources.messages.create
                else:
                    logger.warning(
                        "Could not find messages.create method in anthropic.resources.messages"
                    )
                    return
            elif hasattr(anthropic_module, "messages") and hasattr(
                anthropic_module.messages, "create"
            ):
                original_create = anthropic_module.messages.create
            else:
                logger.warning(
                    "Could not find messages.create method in anthropic module"
                )
                return

            # Define wrapper function
            def patched_create(*args: Any, **kwargs: Any) -> Any:
                from klira.sdk.tracing.tracing import get_tracer
                from opentelemetry.trace import StatusCode

                tracer = get_tracer()

                # Extract model and parameters
                model = kwargs.get("model", "unknown")
                max_tokens = kwargs.get("max_tokens")
                temperature = kwargs.get("temperature")

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
                        original_messages = copy.deepcopy(messages) if messages else None

                        # Set request attributes
                        self._create_llm_request_span(
                            llm_span,
                            provider="anthropic",
                            model=model,
                            messages=messages,
                            max_tokens=max_tokens,
                            temperature=temperature
                        )

                        # Add augmentation tracking if guidelines present (pass original messages)
                        self._add_augmentation_attributes(llm_span, original_messages=original_messages)

                        if messages:
                            # Find the last user message to augment
                            user_msg = None
                            for i in range(len(messages) - 1, -1, -1):
                                if messages[i].get("role") == "user":
                                    user_msg = messages[i]
                                    break

                            if user_msg and isinstance(user_msg.get("content"), str):
                                from klira.sdk.guardrails.engine import GuardrailsEngine

                                guidelines = GuardrailsEngine.get_current_guidelines()

                                if guidelines:
                                    # Build augmentation text
                                    augmentation_text = "\n\nIMPORTANT POLICY DIRECTIVES:\n"
                                    augmentation_text += "\n".join(
                                        [f"• {g}" for g in guidelines]
                                    )

                                    # Inject into user message content
                                    user_msg["content"] += augmentation_text

                                    # Clear context to prevent double-injection
                                    GuardrailsEngine.clear_current_guidelines()

                                    # Debug logging
                                    logger.info(
                                        f"Injected {len(guidelines)} policy guidelines into user message"
                                    )

                            # Handle system prompt augmentation if no user message found
                            elif not user_msg:
                                from klira.sdk.guardrails.engine import GuardrailsEngine

                                guidelines = GuardrailsEngine.get_current_guidelines()

                                if guidelines:
                                    # Check if there's a system parameter to augment
                                    system_prompt = kwargs.get("system", "")
                                    if isinstance(system_prompt, str):
                                        augmentation_text = (
                                            "\n\nIMPORTANT POLICY DIRECTIVES:\n"
                                        )
                                        augmentation_text += "\n".join(
                                            [f"• {g}" for g in guidelines]
                                        )
                                        kwargs["system"] = system_prompt + augmentation_text
                                    elif isinstance(system_prompt, list):
                                        # Handle system prompt as list of content blocks
                                        augmentation_text = (
                                            "\n\nIMPORTANT POLICY DIRECTIVES:\n"
                                        )
                                        augmentation_text += "\n".join(
                                            [f"• {g}" for g in guidelines]
                                        )
                                        system_prompt.append(
                                            {"type": "text", "text": augmentation_text}
                                        )
                                        kwargs["system"] = system_prompt

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
                        self._add_llm_response_attributes(llm_span, result, "anthropic")

                        llm_span.set_status(StatusCode.OK)

                    except Exception as e:
                        llm_span.set_status(StatusCode.ERROR, str(e))
                        llm_span.record_exception(e)
                        raise

                    # Apply outbound guardrails evaluation
                    result = self._apply_outbound_guardrails(result)

                    return result

            # Apply patch directly to anthropic - handle different module structures
            if hasattr(anthropic_module, "resources") and hasattr(
                anthropic_module.resources, "messages"
            ):
                anthropic_module.resources.messages.create = patched_create
            elif hasattr(anthropic_module, "messages"):
                anthropic_module.messages.create = patched_create

            logger.info(
                "Successfully patched anthropic.messages.create for augmentation."
            )

            # Also patch the async variant if available
            try:
                # Check if acreate exists before attempting to patch it
                async_target = None
                if hasattr(anthropic_module, "resources") and hasattr(
                    anthropic_module.resources, "messages"
                ):
                    if hasattr(anthropic_module.resources.messages, "acreate"):
                        async_target = anthropic_module.resources.messages
                        original_acreate = anthropic_module.resources.messages.acreate
                elif hasattr(anthropic_module, "messages") and hasattr(
                    anthropic_module.messages, "acreate"
                ):
                    async_target = anthropic_module.messages
                    original_acreate = anthropic_module.messages.acreate

                if async_target is not None:

                    async def patched_acreate(*args: Any, **kwargs: Any) -> Any:
                        from klira.sdk.tracing.tracing import get_tracer
                        from opentelemetry.trace import StatusCode

                        tracer = get_tracer()

                        # Extract model and parameters
                        model = kwargs.get("model", "unknown")
                        max_tokens = kwargs.get("max_tokens")
                        temperature = kwargs.get("temperature")

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
                                original_messages = copy.deepcopy(messages) if messages else None

                                # Set request attributes
                                self._create_llm_request_span(
                                    llm_span,
                                    provider="anthropic",
                                    model=model,
                                    messages=messages,
                                    max_tokens=max_tokens,
                                    temperature=temperature
                                )

                                # Add augmentation tracking if guidelines present (pass original messages)
                                self._add_augmentation_attributes(llm_span, original_messages=original_messages)

                                if messages:
                                    # Find the last user message to augment
                                    user_msg = None
                                    for i in range(len(messages) - 1, -1, -1):
                                        if messages[i].get("role") == "user":
                                            user_msg = messages[i]
                                            break

                                    if user_msg and isinstance(user_msg.get("content"), str):
                                        from klira.sdk.guardrails.engine import GuardrailsEngine

                                        guidelines = GuardrailsEngine.get_current_guidelines()

                                        if guidelines:
                                            # Build augmentation text
                                            augmentation_text = "\n\nIMPORTANT POLICY DIRECTIVES:\n"
                                            augmentation_text += "\n".join(
                                                [f"• {g}" for g in guidelines]
                                            )

                                            # Inject into user message content
                                            user_msg["content"] += augmentation_text

                                            # Clear context to prevent double-injection
                                            GuardrailsEngine.clear_current_guidelines()

                                            # Debug logging
                                            logger.info(
                                                f"Injected {len(guidelines)} policy guidelines into async user message"
                                            )

                                    # Handle system prompt augmentation if no user message found
                                    elif not user_msg:
                                        from klira.sdk.guardrails.engine import GuardrailsEngine

                                        guidelines = GuardrailsEngine.get_current_guidelines()

                                        if guidelines:
                                            # Check if there's a system parameter to augment
                                            system_prompt = kwargs.get("system", "")
                                            if isinstance(system_prompt, str):
                                                augmentation_text = (
                                                    "\n\nIMPORTANT POLICY DIRECTIVES:\n"
                                                )
                                                augmentation_text += "\n".join(
                                                    [f"• {g}" for g in guidelines]
                                                )
                                                kwargs["system"] = system_prompt + augmentation_text
                                            elif isinstance(system_prompt, list):
                                                # Handle system prompt as list of content blocks
                                                augmentation_text = (
                                                    "\n\nIMPORTANT POLICY DIRECTIVES:\n"
                                                )
                                                augmentation_text += "\n".join(
                                                    [f"• {g}" for g in guidelines]
                                                )
                                                system_prompt.append(
                                                    {"type": "text", "text": augmentation_text}
                                                )
                                                kwargs["system"] = system_prompt

                                            # Clear context to prevent double-injection
                                            GuardrailsEngine.clear_current_guidelines()

                                            # Debug logging
                                            logger.info(
                                                f"Injected {len(guidelines)} policy guidelines into async system prompt"
                                            )

                            except Exception as e:
                                logger.error(f"Policy injection error in async messages: {str(e)}")

                            try:
                                # Call the original method
                                result = await original_acreate(*args, **kwargs)

                                # Add response attributes
                                self._add_llm_response_attributes(llm_span, result, "anthropic")

                                llm_span.set_status(StatusCode.OK)

                            except Exception as e:
                                llm_span.set_status(StatusCode.ERROR, str(e))
                                llm_span.record_exception(e)
                                raise

                            # Apply outbound guardrails evaluation
                            result = await self._apply_outbound_guardrails_async(result)

                            return result

                    async_target.acreate = patched_acreate
                    logger.info(
                        "Successfully patched async anthropic.messages.acreate for augmentation."
                    )
                else:
                    logger.debug(
                        "Anthropic async messages (acreate) not found, skipping patch."
                    )
            except Exception as e:
                logger.debug(f"Failed to patch async messages: {e}")

        except Exception as e:
            logger.error(f"Error patching Anthropic client: {e}", exc_info=True)

    def _patch_sync_create(self) -> None:
        """Patches the synchronous anthropic.messages.create method."""
        if not ANTHROPIC_CLIENT_AVAILABLE or anthropic_module is None:
            return

        try:
            target_obj = None
            if hasattr(anthropic_module, "resources") and hasattr(
                anthropic_module.resources, "messages"
            ):
                target_obj = anthropic_module.resources.messages
            elif hasattr(anthropic_module, "messages"):
                target_obj = anthropic_module.messages

            if target_obj is None:
                logger.warning("Could not find messages object to patch")
                return

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
                    f"Successfully patched anthropic.messages.{method_name} for augmentation."
                )
            elif hasattr(getattr(target_obj, method_name, None), "_klira_augmented"):
                logger.debug(f"anthropic.messages.{method_name} already patched.")
            else:
                logger.warning(
                    f"Could not find anthropic.messages.{method_name} to patch."
                )
        except AttributeError as e:
            logger.error(f"AttributeError during sync Anthropic patching: {e}")
        except Exception as e:
            logger.error(f"Error patching sync Anthropic client: {e}", exc_info=True)

    def _patch_async_create(self) -> None:
        """Patches the asynchronous messages create method."""
        if not ANTHROPIC_CLIENT_AVAILABLE or anthropic_module is None:
            return

        try:
            # Common locations for the async client/methods
            async_locations = []

            # Try resources.messages structure first
            if hasattr(anthropic_module, "resources") and hasattr(
                anthropic_module.resources, "messages"
            ):
                async_locations.append(anthropic_module.resources.messages)

            # Try direct messages structure
            if hasattr(anthropic_module, "messages"):
                async_locations.extend(
                    [
                        getattr(
                            getattr(anthropic_module.messages, "async_", None),
                            "create",
                            None,
                        ),  # Older pattern?
                        getattr(
                            anthropic_module.messages, "AsyncMessages", None
                        ),  # Newer pattern?
                        anthropic_module.messages,  # Direct access
                    ]
                )

            async_target_obj = None
            for loc in async_locations:
                if loc is not None and hasattr(loc, "acreate"):
                    async_target_obj = loc
                    break

            if not async_target_obj:
                logger.debug(
                    "Anthropic async messages module/class not found, skipping patch."
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
                    f"Successfully patched async anthropic.messages method '{async_method_name}'."
                )
            elif hasattr(target_method, "_klira_augmented"):
                logger.debug(
                    f"Async anthropic.messages method '{async_method_name}' already patched."
                )

        except AttributeError as e:
            logger.error(f"AttributeError during async Anthropic patching: {e}")
        except Exception as e:
            logger.error(f"Error patching async Anthropic client: {e}", exc_info=True)

    def _inject_guidelines_into_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Injects guidelines into the payload, by appending to the user message or system prompt.
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
                        f"[AnthropicAdapter] Retrieved {len(guidelines)} guidelines from GuardrailsEngine."
                    )
                    logger.debug(
                        f"Found {len(guidelines)} guidelines to inject at Anthropic Messages call time"
                    )

            # If we couldn't get guidelines from GuardrailsEngine, try legacy OTel method
            if not guidelines and otel_context is not None:
                try:
                    current_context = otel_context.get_current()
                    otel_guidelines = current_context.get("klira_guidelines")
                    if otel_guidelines and isinstance(otel_guidelines, list):
                        guidelines = otel_guidelines
                        logger.debug(
                            f"[AnthropicAdapter] Retrieved {len(guidelines)} guidelines from OTel context."
                        )
                except Exception as e:
                    logger.debug(
                        f"[AnthropicAdapter] Could not retrieve guidelines from OTel context: {e}"
                    )

            if not guidelines:
                logger.debug("[AnthropicAdapter] No guidelines found to inject.")
                return kwargs

            # Create a copy of kwargs to avoid modifying the original
            modified_kwargs = kwargs.copy()

            # Inject guidelines into messages
            messages = modified_kwargs.get("messages", [])
            if messages:
                # Find the last user message to augment
                user_msg_index = None
                for i in range(len(messages) - 1, -1, -1):
                    if messages[i].get("role") == "user":
                        user_msg_index = i
                        break

                if user_msg_index is not None:
                    # Create a copy of messages to avoid modifying the original
                    messages_copy = messages.copy()
                    user_msg = messages_copy[user_msg_index].copy()

                    # Augment user message content
                    content = user_msg.get("content", "")
                    if isinstance(content, str):
                        augmentation_text = "\n\nIMPORTANT POLICY DIRECTIVES:\n"
                        augmentation_text += "\n".join([f"• {g}" for g in guidelines])
                        user_msg["content"] = content + augmentation_text
                        messages_copy[user_msg_index] = user_msg
                        modified_kwargs["messages"] = messages_copy

                        logger.info(
                            f"Injected {len(guidelines)} policy guidelines into user message"
                        )
                    elif isinstance(content, list):
                        # Handle content as list of content blocks
                        content_copy = content.copy()
                        augmentation_text = "\n\nIMPORTANT POLICY DIRECTIVES:\n"
                        augmentation_text += "\n".join([f"• {g}" for g in guidelines])
                        content_copy.append({"type": "text", "text": augmentation_text})
                        user_msg["content"] = content_copy
                        messages_copy[user_msg_index] = user_msg
                        modified_kwargs["messages"] = messages_copy

                        logger.info(
                            f"Injected {len(guidelines)} policy guidelines into user message content blocks"
                        )
                else:
                    # No user message found, try to augment system prompt
                    system_prompt = modified_kwargs.get("system", "")
                    if isinstance(system_prompt, str):
                        augmentation_text = "\n\nIMPORTANT POLICY DIRECTIVES:\n"
                        augmentation_text += "\n".join([f"• {g}" for g in guidelines])
                        modified_kwargs["system"] = system_prompt + augmentation_text
                        logger.info(
                            f"Injected {len(guidelines)} policy guidelines into system prompt"
                        )
                    elif isinstance(system_prompt, list):
                        # Handle system prompt as list of content blocks
                        system_copy = system_prompt.copy()
                        augmentation_text = "\n\nIMPORTANT POLICY DIRECTIVES:\n"
                        augmentation_text += "\n".join([f"• {g}" for g in guidelines])
                        system_copy.append({"type": "text", "text": augmentation_text})
                        modified_kwargs["system"] = system_copy
                        logger.info(
                            f"Injected {len(guidelines)} policy guidelines into system prompt blocks"
                        )
            else:
                # No messages, try to augment system prompt
                system_prompt = modified_kwargs.get("system", "")
                if isinstance(system_prompt, str):
                    augmentation_text = "\n\nIMPORTANT POLICY DIRECTIVES:\n"
                    augmentation_text += "\n".join([f"• {g}" for g in guidelines])
                    modified_kwargs["system"] = system_prompt + augmentation_text
                    logger.info(
                        f"Injected {len(guidelines)} policy guidelines into system prompt"
                    )

            # Clear guidelines from context to prevent double-injection
            if engine:
                engine.clear_current_guidelines()

            return modified_kwargs

        except Exception as e:
            logger.error(
                f"Error injecting guidelines into Anthropic request: {e}", exc_info=True
            )
            return kwargs

    def _apply_outbound_guardrails(self, result: Any) -> Any:
        """Apply outbound guardrails to Anthropic message results (synchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine
            
            # Extract content from Anthropic response
            response_text = self._extract_response_content(result)
            if not response_text.strip():
                return result
            
            # Create evaluation context
            context = {
                "llm_client": "anthropic",
                "function_name": "anthropic.messages.create"
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
                        "Cannot run outbound guardrails evaluation for Anthropic message in sync context within async loop. "
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
                    f"Anthropic message outbound guardrails blocked response: {decision.reason}"
                )
                # Return a modified response with blocked content
                return self._create_blocked_response(result, decision.reason or "Content policy violation detected")
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying outbound guardrails for Anthropic message: {e}", exc_info=True)
            # Fail open - return original result
            return result

    async def _apply_outbound_guardrails_async(self, result: Any) -> Any:
        """Apply outbound guardrails to Anthropic message results (asynchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine
            
            # Extract content from Anthropic response
            response_text = self._extract_response_content(result)
            if not response_text.strip():
                return result
            
            # Create evaluation context
            context = {
                "llm_client": "anthropic",
                "function_name": "anthropic.messages.acreate"
            }
            
            # Get guardrails engine and evaluate
            engine = GuardrailsEngine.get_instance()
            decision = await engine.evaluate(response_text, context, direction="outbound")
            
            if not decision.allowed:
                logger.warning(
                    f"Anthropic async message outbound guardrails blocked response: {decision.reason}"
                )
                # Return a modified response with blocked content
                return self._create_blocked_response(result, decision.reason or "Content policy violation detected")
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying outbound guardrails for Anthropic async message: {e}", exc_info=True)
            # Fail open - return original result
            return result

    def _extract_response_content(self, result: Any) -> str:
        """Extract text content from Anthropic response object."""
        try:
            # Handle Anthropic response format
            if hasattr(result, 'content') and result.content:
                # Anthropic responses have a content list
                content_parts = []
                for content_block in result.content:
                    if hasattr(content_block, 'text'):
                        content_parts.append(str(content_block.text))
                    elif isinstance(content_block, dict) and 'text' in content_block:
                        content_parts.append(str(content_block['text']))
                return ' '.join(content_parts) if content_parts else ""
            
            # Fallback: try to convert to string
            return str(result) if result else ""
            
        except Exception as e:
            logger.debug(f"Error extracting content from Anthropic response: {e}")
            return ""

    def _create_blocked_response(self, original_result: Any, reason: str) -> Any:
        """Create a blocked response that matches the original response format."""
        try:
            blocked_message = f"[BLOCKED BY GUARDRAILS] - {reason}" if reason else "[BLOCKED BY GUARDRAILS] - Content policy violation detected"

            # Try to modify the original response in place
            if hasattr(original_result, 'content') and original_result.content:
                # Anthropic responses have a content list
                for content_block in original_result.content:
                    if hasattr(content_block, 'text'):
                        content_block.text = blocked_message
                        return original_result
                    elif isinstance(content_block, dict) and 'text' in content_block:
                        content_block['text'] = blocked_message
                        return original_result

            # Fallback: return the blocked message as string
            return blocked_message

        except Exception as e:
            logger.error(f"Error creating blocked response: {e}")
            # Ultimate fallback
            return "[BLOCKED BY GUARDRAILS] - Content policy violation detected"

    # Provider-specific extraction methods for LLM span attributes

    def _extract_prompt_text(self, messages: Any, provider: str) -> str:
        """Extract prompt text from Anthropic messages format."""
        if isinstance(messages, list):
            parts = []
            for msg in messages:
                if isinstance(msg, dict):
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')

                    # Handle content as string
                    if isinstance(content, str):
                        parts.append(f"{role}: {content}")
                    # Handle content as list of content blocks
                    elif isinstance(content, list):
                        content_texts = []
                        for block in content:
                            if isinstance(block, dict) and 'text' in block:
                                content_texts.append(block['text'])
                            elif hasattr(block, 'text'):
                                content_texts.append(str(block.text))
                        if content_texts:
                            parts.append(f"{role}: {' '.join(content_texts)}")
            return "\n".join(parts)
        return str(messages)

    def _extract_response_text(self, response: Any, provider: str) -> str:
        """Extract response text from Anthropic response format."""
        try:
            # Handle Anthropic response format with content blocks
            if hasattr(response, 'content') and response.content:
                content_parts = []
                for content_block in response.content:
                    if hasattr(content_block, 'text'):
                        content_parts.append(str(content_block.text))
                    elif isinstance(content_block, dict) and 'text' in content_block:
                        content_parts.append(str(content_block['text']))
                return ' '.join(content_parts) if content_parts else ""

            # Fallback
            return str(response) if response else ""
        except Exception as e:
            logger.debug(f"Error extracting Anthropic response text: {e}")
            return ""

    def _extract_token_usage(self, response: Any, provider: str) -> Optional[Dict[str, int]]:
        """Extract token usage from Anthropic response."""
        try:
            if hasattr(response, 'usage'):
                usage = response.usage
                return {
                    "input_tokens": getattr(usage, 'input_tokens', 0),
                    "output_tokens": getattr(usage, 'output_tokens', 0)
                }
            return None
        except Exception as e:
            logger.debug(f"Error extracting Anthropic token usage: {e}")
            return None

    def _extract_finish_reason(self, response: Any, provider: str) -> Optional[str]:
        """Extract finish reason from Anthropic response."""
        try:
            if hasattr(response, 'stop_reason'):
                return str(response.stop_reason)
            return None
        except Exception as e:
            logger.debug(f"Error extracting Anthropic finish reason: {e}")
            return None
