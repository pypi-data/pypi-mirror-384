"""
Ollama LLM Adapter for Klira AI SDK

This adapter provides integration with Ollama API for LLM guardrails and observability.
It patches the Ollama client to inject guidelines and apply policy enforcement.
"""

import copy
import logging
from typing import Any, Dict, List, Optional, Callable

from klira.sdk.adapters.llm_base_adapter import BaseLLMAdapter
from klira.sdk.utils.error_handler import handle_errors

logger = logging.getLogger(__name__)

# Check if ollama is available
try:
    import ollama
    from ollama import Client, AsyncClient

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.debug("ollama not available, Ollama adapter will be disabled")


class OllamaAdapter(BaseLLMAdapter):
    """Adapter for Ollama API integration with Klira AI SDK guardrails."""

    is_available = OLLAMA_AVAILABLE

    # Type annotations for original methods
    original_chat: Optional[Callable[..., Any]]
    original_chat_async: Optional[Callable[..., Any]]
    original_generate: Optional[Callable[..., Any]]
    original_generate_async: Optional[Callable[..., Any]]
    _patched: bool

    def __init__(self) -> None:
        super().__init__()
        self.original_chat = None
        self.original_chat_async = None
        self.original_generate = None
        self.original_generate_async = None
        self._patched = False

    def patch(self) -> None:
        """Patch Ollama client methods to inject guidelines."""
        if not OLLAMA_AVAILABLE:
            logger.debug("Ollama not available, skipping patching")
            return

        if self._patched:
            logger.debug("Ollama client already patched")
            return

        try:
            # Patch the global ollama functions
            if hasattr(ollama, "chat"):
                self.original_chat = ollama.chat
                ollama.chat = self._patched_chat

            if hasattr(ollama, "generate"):
                self.original_generate = ollama.generate
                ollama.generate = self._patched_generate

            # Patch Client methods
            if hasattr(Client, "chat"):
                Client._original_chat = Client.chat
                Client.chat = self._patched_client_chat

            if hasattr(Client, "generate"):
                Client._original_generate = Client.generate
                Client.generate = self._patched_client_generate

            # Patch AsyncClient methods
            if hasattr(AsyncClient, "chat"):
                AsyncClient._original_chat = AsyncClient.chat
                AsyncClient.chat = self._patched_async_client_chat

            if hasattr(AsyncClient, "generate"):
                AsyncClient._original_generate = AsyncClient.generate
                AsyncClient.generate = self._patched_async_client_generate

            self._patched = True
            logger.info("Successfully patched Ollama client methods")

        except Exception as e:
            logger.error(f"Failed to patch Ollama client: {e}")

    def _patched_chat(
        self, model: str, messages: List[Dict[str, Any]], **kwargs: Any
    ) -> Any:
        """Patched version of ollama.chat that injects guidelines."""
        from klira.sdk.tracing.tracing import get_tracer
        from opentelemetry.trace import StatusCode

        tracer = get_tracer()

        # Create LLM request span
        with tracer.start_span("klira.llm.request") as llm_span:
            try:
                # Store original messages before augmentation
                original_messages = copy.deepcopy(messages) if messages else None

                # Set request attributes
                self._create_llm_request_span(
                    llm_span,
                    provider="ollama",
                    model=model,
                    messages=messages,
                    **kwargs,
                )

                # Add augmentation tracking if guidelines present (pass original messages)
                self._add_augmentation_attributes(
                    llm_span, original_messages=original_messages
                )

                # Get guidelines from guardrails engine
                guidelines = self._get_guidelines_for_messages(messages)

                if guidelines:
                    # Inject guidelines into the messages
                    modified_messages = self._inject_guidelines_into_messages(
                        messages, guidelines
                    )
                    logger.debug(
                        f"Injected guidelines into Ollama chat: {len(guidelines)} guidelines"
                    )
                    messages_to_use = modified_messages
                else:
                    messages_to_use = messages

            except Exception as e:
                logger.error(f"Policy injection error: {str(e)}")
                messages_to_use = messages

            try:
                # Call the original method
                if self.original_chat is not None:
                    result = self.original_chat(model, messages_to_use, **kwargs)

                    # Add response attributes
                    self._add_llm_response_attributes(llm_span, result, "ollama")

                    llm_span.set_status(StatusCode.OK)
                else:
                    result = None
                    llm_span.set_status(
                        StatusCode.ERROR, "Original method not available"
                    )

            except Exception as e:
                llm_span.set_status(StatusCode.ERROR, str(e))
                llm_span.record_exception(e)
                raise

            # Apply outbound guardrails evaluation
            if result is not None:
                result = self._apply_outbound_guardrails(result)

            return result

    def _patched_generate(self, model: str, prompt: str, **kwargs: Any) -> Any:
        """Patched version of ollama.generate that injects guidelines."""
        from klira.sdk.tracing.tracing import get_tracer
        from opentelemetry.trace import StatusCode

        tracer = get_tracer()

        # Create LLM request span
        with tracer.start_span("klira.llm.request") as llm_span:
            try:
                # Store original prompt before augmentation
                original_prompt = copy.deepcopy(prompt) if prompt else None

                # Set request attributes (use prompt as messages)
                self._create_llm_request_span(
                    llm_span, provider="ollama", model=model, messages=prompt, **kwargs
                )

                # Add augmentation tracking if guidelines present (pass original prompt)
                self._add_augmentation_attributes(
                    llm_span, original_messages=original_prompt
                )

                # Get guidelines from guardrails engine
                guidelines = self._get_guidelines_for_prompt(prompt)

                if guidelines:
                    # Inject guidelines into the prompt
                    modified_prompt = self._inject_guidelines_into_prompt(
                        prompt, guidelines
                    )
                    logger.debug(
                        f"Injected guidelines into Ollama generate: {len(guidelines)} guidelines"
                    )
                    prompt_to_use = modified_prompt
                else:
                    prompt_to_use = prompt

            except Exception as e:
                logger.error(f"Policy injection error: {str(e)}")
                prompt_to_use = prompt

            try:
                # Call the original method
                if self.original_generate is not None:
                    result = self.original_generate(model, prompt_to_use, **kwargs)

                    # Add response attributes
                    self._add_llm_response_attributes(llm_span, result, "ollama")

                    llm_span.set_status(StatusCode.OK)
                else:
                    result = None
                    llm_span.set_status(
                        StatusCode.ERROR, "Original method not available"
                    )

            except Exception as e:
                llm_span.set_status(StatusCode.ERROR, str(e))
                llm_span.record_exception(e)
                raise

            # Apply outbound guardrails evaluation
            if result is not None:
                result = self._apply_outbound_guardrails(result)

            return result

    def _patched_client_chat(
        self,
        client_instance: Any,
        model: str,
        messages: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> Any:
        """Patched version of Client.chat that injects guidelines."""
        try:
            # Get guidelines from guardrails engine
            guidelines = self._get_guidelines_for_messages(messages)

            if guidelines:
                # Inject guidelines into the messages
                modified_messages = self._inject_guidelines_into_messages(
                    messages, guidelines
                )
                logger.debug(
                    f"Injected guidelines into Ollama Client.chat: {len(guidelines)} guidelines"
                )
                result = client_instance._original_chat(
                    model, modified_messages, **kwargs
                )
                # Apply outbound guardrails evaluation
                result = self._apply_outbound_guardrails(result)
                return result
            else:
                result = client_instance._original_chat(model, messages, **kwargs)
                # Apply outbound guardrails evaluation
                result = self._apply_outbound_guardrails(result)
                return result

        except Exception as e:
            logger.error(f"Error in patched Ollama Client.chat: {e}")
            # Fallback to original method
            return client_instance._original_chat(model, messages, **kwargs)

    def _patched_client_generate(
        self, client_instance: Any, model: str, prompt: str, **kwargs: Any
    ) -> Any:
        """Patched version of Client.generate that injects guidelines."""
        try:
            # Get guidelines from guardrails engine
            guidelines = self._get_guidelines_for_prompt(prompt)

            if guidelines:
                # Inject guidelines into the prompt
                modified_prompt = self._inject_guidelines_into_prompt(
                    prompt, guidelines
                )
                logger.debug(
                    f"Injected guidelines into Ollama Client.generate: {len(guidelines)} guidelines"
                )
                result = client_instance._original_generate(
                    model, modified_prompt, **kwargs
                )
                # Apply outbound guardrails evaluation
                result = self._apply_outbound_guardrails(result)
                return result
            else:
                result = client_instance._original_generate(model, prompt, **kwargs)
                # Apply outbound guardrails evaluation
                result = self._apply_outbound_guardrails(result)
                return result

        except Exception as e:
            logger.error(f"Error in patched Ollama Client.generate: {e}")
            # Fallback to original method
            return client_instance._original_generate(model, prompt, **kwargs)

    async def _patched_async_client_chat(
        self,
        client_instance: Any,
        model: str,
        messages: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> Any:
        """Patched version of AsyncClient.chat that injects guidelines."""
        try:
            # Get guidelines from guardrails engine
            guidelines = self._get_guidelines_for_messages(messages)

            if guidelines:
                # Inject guidelines into the messages
                modified_messages = self._inject_guidelines_into_messages(
                    messages, guidelines
                )
                logger.debug(
                    f"Injected guidelines into Ollama AsyncClient.chat: {len(guidelines)} guidelines"
                )
                result = await client_instance._original_chat(
                    model, modified_messages, **kwargs
                )
                # Apply outbound guardrails evaluation
                result = await self._apply_outbound_guardrails_async(result)
                return result
            else:
                result = await client_instance._original_chat(model, messages, **kwargs)
                # Apply outbound guardrails evaluation
                result = await self._apply_outbound_guardrails_async(result)
                return result

        except Exception as e:
            logger.error(f"Error in patched Ollama AsyncClient.chat: {e}")
            # Fallback to original method
            return await client_instance._original_chat(model, messages, **kwargs)

    async def _patched_async_client_generate(
        self, client_instance: Any, model: str, prompt: str, **kwargs: Any
    ) -> Any:
        """Patched version of AsyncClient.generate that injects guidelines."""
        try:
            # Get guidelines from guardrails engine
            guidelines = self._get_guidelines_for_prompt(prompt)

            if guidelines:
                # Inject guidelines into the prompt
                modified_prompt = self._inject_guidelines_into_prompt(
                    prompt, guidelines
                )
                logger.debug(
                    f"Injected guidelines into Ollama AsyncClient.generate: {len(guidelines)} guidelines"
                )
                result = await client_instance._original_generate(
                    model, modified_prompt, **kwargs
                )
                # Apply outbound guardrails evaluation
                result = await self._apply_outbound_guardrails_async(result)
                return result
            else:
                result = await client_instance._original_generate(
                    model, prompt, **kwargs
                )
                # Apply outbound guardrails evaluation
                result = await self._apply_outbound_guardrails_async(result)
                return result

        except Exception as e:
            logger.error(f"Error in patched Ollama AsyncClient.generate: {e}")
            # Fallback to original method
            return await client_instance._original_generate(model, prompt, **kwargs)

    def _get_guidelines_for_messages(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract user message and get guidelines from guardrails engine."""
        try:
            from klira.sdk.guardrails.engine import GuardrailsEngine

            # Extract user message from messages
            user_message = self._extract_user_message_from_messages(messages)
            if not user_message:
                return []

            # Get guardrails engine instance
            guardrails_engine = GuardrailsEngine.get_instance()
            if not guardrails_engine or not guardrails_engine.policy_augmentation:
                return []

            # Get guidelines from policy augmentation
            matched_policies = guardrails_engine.policy_augmentation._match_policies(
                user_message
            )
            guidelines = guardrails_engine.policy_augmentation._extract_guidelines(
                matched_policies
            )

            return guidelines

        except Exception as e:
            logger.error(f"Error getting guidelines for Ollama messages: {e}")
            return []

    def _get_guidelines_for_prompt(self, prompt: str) -> List[str]:
        """Get guidelines from guardrails engine for a prompt."""
        try:
            from klira.sdk.guardrails.engine import GuardrailsEngine

            if not prompt:
                return []

            # Get guardrails engine instance
            guardrails_engine = GuardrailsEngine.get_instance()
            if not guardrails_engine or not guardrails_engine.policy_augmentation:
                return []

            # Get guidelines from policy augmentation
            matched_policies = guardrails_engine.policy_augmentation._match_policies(
                prompt
            )
            guidelines = guardrails_engine.policy_augmentation._extract_guidelines(
                matched_policies
            )

            return guidelines

        except Exception as e:
            logger.error(f"Error getting guidelines for Ollama prompt: {e}")
            return []

    def _extract_user_message_from_messages(
        self, messages: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Extract user message text from Ollama messages."""
        try:
            # Find the last user message
            for message in reversed(messages):
                if isinstance(message, dict) and message.get("role") == "user":
                    content = message.get("content", "")
                    if isinstance(content, str):
                        return content
                    elif isinstance(content, list):
                        # Handle list of content parts
                        text_parts = []
                        for part in content:
                            if isinstance(part, str):
                                text_parts.append(part)
                            elif isinstance(part, dict) and "text" in part:
                                text_parts.append(part["text"])
                        return " ".join(text_parts) if text_parts else None

            return None

        except Exception as e:
            logger.error(f"Error extracting user message from Ollama messages: {e}")
            return None

    def _inject_guidelines_into_messages(
        self, messages: List[Dict[str, Any]], guidelines: List[str]
    ) -> List[Dict[str, Any]]:
        """Inject guidelines into Ollama messages."""
        try:
            if not guidelines:
                return messages

            # Create guidelines text
            guidelines_text = "\n".join([f"- {guideline}" for guideline in guidelines])
            guideline_prompt = (
                f"\n\nPlease follow these guidelines:\n{guidelines_text}\n"
            )

            # Create a copy of messages to avoid modifying the original
            modified_messages = []
            for message in messages:
                modified_messages.append(message.copy())

            # Find the last user message and append guidelines
            for i in range(len(modified_messages) - 1, -1, -1):
                message = modified_messages[i]
                if isinstance(message, dict) and message.get("role") == "user":
                    content = message.get("content", "")
                    if isinstance(content, str):
                        message["content"] = content + guideline_prompt
                        break
                    elif isinstance(content, list):
                        # Handle list of content parts
                        modified_content = content.copy()
                        # Append to the last text part or add new text part
                        for j in range(len(modified_content) - 1, -1, -1):
                            part = modified_content[j]
                            if isinstance(part, str):
                                modified_content[j] = part + guideline_prompt
                                break
                            elif isinstance(part, dict) and "text" in part:
                                part["text"] += guideline_prompt
                                break
                        else:
                            # No text part found, add new text part
                            modified_content.append(
                                {"type": "text", "text": guideline_prompt}
                            )
                        message["content"] = modified_content
                        break

            return modified_messages

        except Exception as e:
            logger.error(f"Error injecting guidelines into Ollama messages: {e}")
            return messages

    def _inject_guidelines_into_prompt(self, prompt: str, guidelines: List[str]) -> str:
        """Inject guidelines into Ollama prompt."""
        try:
            if not guidelines:
                return prompt

            # Create guidelines text
            guidelines_text = "\n".join([f"- {guideline}" for guideline in guidelines])
            guideline_prompt = (
                f"\n\nPlease follow these guidelines:\n{guidelines_text}\n"
            )

            return prompt + guideline_prompt

        except Exception as e:
            logger.error(f"Error injecting guidelines into Ollama prompt: {e}")
            return prompt

    @handle_errors(fail_closed=False, default_return_on_error=False)
    def unpatch_llm_client(self) -> bool:
        """Restore original Ollama client methods."""
        if not OLLAMA_AVAILABLE or not self._patched:
            return False

        try:
            # Restore global functions
            if self.original_chat:
                ollama.chat = self.original_chat

            if self.original_generate:
                ollama.generate = self.original_generate

            # Restore Client methods
            if hasattr(Client, "_original_chat"):
                Client.chat = Client._original_chat
                delattr(Client, "_original_chat")

            if hasattr(Client, "_original_generate"):
                Client.generate = Client._original_generate
                delattr(Client, "_original_generate")

            # Restore AsyncClient methods
            if hasattr(AsyncClient, "_original_chat"):
                AsyncClient.chat = AsyncClient._original_chat
                delattr(AsyncClient, "_original_chat")

            if hasattr(AsyncClient, "_original_generate"):
                AsyncClient.generate = AsyncClient._original_generate
                delattr(AsyncClient, "_original_generate")

            self._patched = False
            logger.info("Successfully unpatched Ollama client methods")
            return True

        except Exception as e:
            logger.error(f"Failed to unpatch Ollama client: {e}")
            return False

    def get_client_info(self) -> Dict[str, Any]:
        """Get information about the Ollama client."""
        if not OLLAMA_AVAILABLE:
            return {"available": False, "reason": "ollama not installed"}

        try:
            import ollama

            return {
                "available": True,
                "library": "ollama",
                "version": getattr(ollama, "__version__", "unknown"),
                "patched": self._patched,
            }
        except Exception as e:
            return {"available": False, "reason": str(e)}

    def _apply_outbound_guardrails(self, result: Any) -> Any:
        """Apply outbound guardrails to Ollama results (synchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine

            # Extract content from Ollama response
            response_text = self._extract_response_content(result)
            if not response_text.strip():
                return result

            # Create evaluation context
            context = {"llm_client": "ollama", "function_name": "ollama.chat/generate"}

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
                        "Cannot run outbound guardrails evaluation for Ollama in sync context within async loop. "
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
                    f"Ollama outbound guardrails blocked response: {decision.reason}"
                )
                # Return a modified response with blocked content
                return self._create_blocked_response(
                    result, decision.reason or "Content policy violation detected"
                )

            return result

        except Exception as e:
            logger.error(
                f"Error applying outbound guardrails for Ollama: {e}", exc_info=True
            )
            # Fail open - return original result
            return result

    async def _apply_outbound_guardrails_async(self, result: Any) -> Any:
        """Apply outbound guardrails to Ollama results (asynchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine

            # Extract content from Ollama response
            response_text = self._extract_response_content(result)
            if not response_text.strip():
                return result

            # Create evaluation context
            context = {
                "llm_client": "ollama",
                "function_name": "ollama.async_chat/generate",
            }

            # Get guardrails engine and evaluate
            engine = GuardrailsEngine.get_instance()
            decision = await engine.evaluate(
                response_text, context, direction="outbound"
            )

            if not decision.allowed:
                logger.warning(
                    f"Ollama async outbound guardrails blocked response: {decision.reason}"
                )
                # Return a modified response with blocked content
                return self._create_blocked_response(
                    result, decision.reason or "Content policy violation detected"
                )

            return result

        except Exception as e:
            logger.error(
                f"Error applying outbound guardrails for Ollama async: {e}",
                exc_info=True,
            )
            # Fail open - return original result
            return result

    def _extract_response_content(self, result: Any) -> str:
        """Extract text content from Ollama response object."""
        try:
            # Handle Ollama response format
            if isinstance(result, dict):
                # Check for 'response' field (generate endpoint)
                if "response" in result:
                    return str(result["response"])
                # Check for 'message' field (chat endpoint)
                elif "message" in result and isinstance(result["message"], dict):
                    content = result["message"].get("content", "")
                    return str(content) if content else ""
                # Check for 'content' field directly
                elif "content" in result:
                    return str(result["content"])

            # Handle if result has a 'response' attribute
            if hasattr(result, "response"):
                return str(result.response)

            # Handle if result has a 'message' attribute
            if hasattr(result, "message") and hasattr(result.message, "content"):
                return str(result.message.content)

            # Fallback: try to convert to string
            return str(result) if result else ""

        except Exception as e:
            logger.debug(f"Error extracting content from Ollama response: {e}")
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
            if isinstance(original_result, dict):
                # Modify response field (generate endpoint)
                if "response" in original_result:
                    original_result["response"] = blocked_message
                    return original_result
                # Modify message content (chat endpoint)
                elif "message" in original_result and isinstance(
                    original_result["message"], dict
                ):
                    original_result["message"]["content"] = blocked_message
                    return original_result
                # Modify content field directly
                elif "content" in original_result:
                    original_result["content"] = blocked_message
                    return original_result

            # Handle if result has attributes
            if hasattr(original_result, "response"):
                original_result.response = blocked_message
                return original_result

            if hasattr(original_result, "message") and hasattr(
                original_result.message, "content"
            ):
                original_result.message.content = blocked_message
                return original_result

            # Fallback: return the blocked message as string
            return blocked_message

        except Exception as e:
            logger.error(f"Error creating blocked response: {e}")
            # Ultimate fallback
            return "[BLOCKED BY GUARDRAILS] - Content policy violation detected"

    # Provider-specific extraction methods for LLM span attributes

    def _extract_prompt_text(self, messages: Any, provider: str) -> str:
        """Extract prompt text from Ollama messages format."""
        # Handle direct prompt string (from generate)
        if isinstance(messages, str):
            return messages
        # Handle messages list (from chat)
        elif isinstance(messages, list):
            parts = []
            for msg in messages:
                if isinstance(msg, dict):
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        parts.append(f"{role}: {content}")
            return "\n".join(parts)
        return str(messages)

    def _extract_response_text(self, response: Any, provider: str) -> str:
        """Extract response text from Ollama response format."""
        try:
            # Handle Ollama response format
            if isinstance(response, dict):
                # Check for 'response' field (generate endpoint)
                if "response" in response:
                    return str(response["response"])
                # Check for 'message' field (chat endpoint)
                elif "message" in response and isinstance(response["message"], dict):
                    content = response["message"].get("content", "")
                    return str(content) if content else ""
                # Check for 'content' field directly
                elif "content" in response:
                    return str(response["content"])

            # Handle if result has a 'response' attribute
            if hasattr(response, "response"):
                return str(response.response)

            # Handle if result has a 'message' attribute
            if hasattr(response, "message") and hasattr(response.message, "content"):
                return str(response.message.content)

            return str(response) if response else ""
        except Exception as e:
            logger.debug(f"Error extracting Ollama response text: {e}")
            return ""

    def _extract_token_usage(
        self, response: Any, provider: str
    ) -> Optional[Dict[str, int]]:
        """Extract token usage from Ollama response."""
        try:
            if isinstance(response, dict):
                # Ollama returns prompt_eval_count and eval_count
                prompt_tokens = response.get("prompt_eval_count", 0)
                completion_tokens = response.get("eval_count", 0)
                if prompt_tokens or completion_tokens:
                    return {
                        "input_tokens": prompt_tokens,
                        "output_tokens": completion_tokens,
                    }
            elif hasattr(response, "prompt_eval_count") and hasattr(
                response, "eval_count"
            ):
                return {
                    "input_tokens": getattr(response, "prompt_eval_count", 0),
                    "output_tokens": getattr(response, "eval_count", 0),
                }
            return None
        except Exception as e:
            logger.debug(f"Error extracting Ollama token usage: {e}")
            return None

    def _extract_finish_reason(self, response: Any, provider: str) -> Optional[str]:
        """Extract finish reason from Ollama response."""
        try:
            if isinstance(response, dict):
                # Ollama uses 'done' field
                if "done" in response:
                    return "stop" if response["done"] else "length"
                # Check for done_reason field
                if "done_reason" in response:
                    return str(response["done_reason"])
            elif hasattr(response, "done"):
                return "stop" if response.done else "length"
            elif hasattr(response, "done_reason"):
                return str(response.done_reason)
            return None
        except Exception as e:
            logger.debug(f"Error extracting Ollama finish reason: {e}")
            return None
