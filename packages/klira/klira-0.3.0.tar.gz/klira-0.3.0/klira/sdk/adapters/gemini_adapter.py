"""
Gemini LLM Adapter for Klira AI SDK

This adapter provides integration with Google's Gemini API for LLM guardrails and observability.
It patches the Gemini client to inject guidelines and apply policy enforcement.
"""

import copy
import logging
from typing import Any, Dict, List, Optional, Callable

from klira.sdk.adapters.llm_base_adapter import BaseLLMAdapter
from klira.sdk.utils.error_handler import handle_errors

logger = logging.getLogger(__name__)

# Check if google-generativeai is available
try:
    import google.generativeai as genai  # noqa: F401
    from google.generativeai.types import GenerateContentResponse  # noqa: F401

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.debug("google-generativeai not available, Gemini adapter will be disabled")


class GeminiAdapter(BaseLLMAdapter):
    """Adapter for Google Gemini API integration with Klira AI SDK guardrails."""

    is_available = GEMINI_AVAILABLE

    # Type annotations for original methods
    original_generate_content: Optional[Callable[..., Any]]
    original_generate_content_async: Optional[Callable[..., Any]]
    _patched: bool

    def __init__(self) -> None:
        super().__init__()
        self.original_generate_content = None
        self.original_generate_content_async = None
        self._patched = False

    def patch(self) -> None:
        """Patch Gemini client methods to inject guidelines."""
        if not GEMINI_AVAILABLE:
            logger.debug("Gemini not available, skipping patching")
            return

        if self._patched:
            logger.debug("Gemini client already patched")
            return

        try:
            # Patch the GenerativeModel.generate_content method
            from google.generativeai import GenerativeModel

            if hasattr(GenerativeModel, "generate_content"):
                self.original_generate_content = GenerativeModel.generate_content
                GenerativeModel.generate_content = self._patched_generate_content

            if hasattr(GenerativeModel, "generate_content_async"):
                self.original_generate_content_async = (
                    GenerativeModel.generate_content_async
                )
                GenerativeModel.generate_content_async = (
                    self._patched_generate_content_async
                )

            self._patched = True
            logger.info("Successfully patched Gemini GenerativeModel methods")

        except Exception as e:
            logger.error(f"Failed to patch Gemini client: {e}")

    def _patched_generate_content(
        self, model_instance: Any, contents: Any, **kwargs: Any
    ) -> Any:
        """Patched version of GenerativeModel.generate_content that injects guidelines."""
        from klira.sdk.tracing.tracing import get_tracer
        from opentelemetry.trace import StatusCode

        tracer = get_tracer()

        # Extract model name from model_instance
        model_name = getattr(model_instance, "_model_name", "unknown")

        # Create LLM request span
        with tracer.start_span("klira.llm.request") as llm_span:
            try:
                # Store original content before augmentation
                original_contents = copy.deepcopy(contents) if contents else None

                # Set request attributes
                self._create_llm_request_span(
                    llm_span,
                    provider="gemini",
                    model=model_name,
                    messages=contents,
                    **kwargs,
                )

                # Add augmentation tracking if guidelines present (pass original contents)
                self._add_augmentation_attributes(
                    llm_span, original_messages=original_contents
                )

                # Get guidelines from guardrails engine
                guidelines = self._get_guidelines_for_content(contents)

                if guidelines:
                    # Inject guidelines into the content
                    modified_contents = self._inject_guidelines_into_content(
                        contents, guidelines
                    )
                    logger.debug(
                        f"Injected guidelines into Gemini content: {len(guidelines)} guidelines"
                    )
                    contents_to_use = modified_contents
                else:
                    contents_to_use = contents

            except Exception as e:
                logger.error(f"Policy injection error: {str(e)}")
                contents_to_use = contents

            try:
                # Call the original method
                if self.original_generate_content is not None:
                    result = self.original_generate_content(
                        model_instance, contents_to_use, **kwargs
                    )

                    # Add response attributes
                    self._add_llm_response_attributes(llm_span, result, "gemini")

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

    async def _patched_generate_content_async(
        self, model_instance: Any, contents: Any, **kwargs: Any
    ) -> Any:
        """Patched version of GenerativeModel.generate_content_async that injects guidelines."""
        from klira.sdk.tracing.tracing import get_tracer
        from opentelemetry.trace import StatusCode

        tracer = get_tracer()

        # Extract model name from model_instance
        model_name = getattr(model_instance, "_model_name", "unknown")

        # Create LLM request span
        with tracer.start_span("klira.llm.request") as llm_span:
            try:
                # Store original content before augmentation
                original_contents = copy.deepcopy(contents) if contents else None

                # Set request attributes
                self._create_llm_request_span(
                    llm_span,
                    provider="gemini",
                    model=model_name,
                    messages=contents,
                    **kwargs,
                )

                # Add augmentation tracking if guidelines present (pass original contents)
                self._add_augmentation_attributes(
                    llm_span, original_messages=original_contents
                )

                # Get guidelines from guardrails engine
                guidelines = self._get_guidelines_for_content(contents)

                if guidelines:
                    # Inject guidelines into the content
                    modified_contents = self._inject_guidelines_into_content(
                        contents, guidelines
                    )
                    logger.debug(
                        f"Injected guidelines into Gemini content: {len(guidelines)} guidelines"
                    )
                    contents_to_use = modified_contents
                else:
                    contents_to_use = contents

            except Exception as e:
                logger.error(f"Policy injection error: {str(e)}")
                contents_to_use = contents

            try:
                # Call the original method
                if self.original_generate_content_async is not None:
                    result = await self.original_generate_content_async(
                        model_instance, contents_to_use, **kwargs
                    )

                    # Add response attributes
                    self._add_llm_response_attributes(llm_span, result, "gemini")

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
                result = await self._apply_outbound_guardrails_async(result)

            return result

    def _get_guidelines_for_content(self, contents: Any) -> List[str]:
        """Extract user message and get guidelines from guardrails engine."""
        try:
            from klira.sdk.guardrails.engine import GuardrailsEngine

            # Extract text content from Gemini contents
            user_message = self._extract_user_message(contents)
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
            logger.error(f"Error getting guidelines for Gemini content: {e}")
            return []

    def _extract_user_message(self, contents: Any) -> Optional[str]:
        """Extract user message text from Gemini contents."""
        try:
            if isinstance(contents, str):
                return contents
            elif isinstance(contents, list):
                # Handle list of content parts
                text_parts = []
                for content in contents:
                    if isinstance(content, str):
                        text_parts.append(content)
                    elif hasattr(content, "text"):
                        text_parts.append(str(content.text))
                    elif isinstance(content, dict) and "text" in content:
                        text_parts.append(str(content["text"]))
                return " ".join(text_parts) if text_parts else None
            elif hasattr(contents, "text"):
                return str(contents.text)
            elif isinstance(contents, dict) and "text" in contents:
                return str(contents["text"])
            else:
                logger.debug(f"Unknown Gemini content format: {type(contents)}")
                return None

        except Exception as e:
            logger.error(f"Error extracting user message from Gemini content: {e}")
            return None

    def _inject_guidelines_into_content(
        self, contents: Any, guidelines: List[str]
    ) -> Any:
        """Inject guidelines into Gemini content."""
        try:
            if not guidelines:
                return contents

            # Create guidelines text
            guidelines_text = "\n".join([f"- {guideline}" for guideline in guidelines])
            guideline_prompt = (
                f"\n\nPlease follow these guidelines:\n{guidelines_text}\n"
            )

            if isinstance(contents, str):
                # Simple string content
                return contents + guideline_prompt
            elif isinstance(contents, list):
                # List of content parts - append to the last text part or add new part
                modified_contents = contents.copy()

                # Find the last text content and append guidelines
                for i in range(len(modified_contents) - 1, -1, -1):
                    content = modified_contents[i]
                    if isinstance(content, str):
                        modified_contents[i] = content + guideline_prompt
                        break
                    elif hasattr(content, "text"):
                        content.text += guideline_prompt
                        break
                    elif isinstance(content, dict) and "text" in content:
                        content["text"] += guideline_prompt
                        break
                else:
                    # No text content found, append as new string
                    modified_contents.append(guideline_prompt)

                return modified_contents
            elif hasattr(contents, "text"):
                # Content object with text attribute
                contents.text += guideline_prompt
                return contents
            elif isinstance(contents, dict) and "text" in contents:
                # Dictionary with text key
                contents["text"] += guideline_prompt
                return contents
            else:
                logger.warning(
                    f"Cannot inject guidelines into unknown Gemini content format: {type(contents)}"
                )
                return contents

        except Exception as e:
            logger.error(f"Error injecting guidelines into Gemini content: {e}")
            return contents

    @handle_errors(fail_closed=False, default_return_on_error=False)
    def unpatch_llm_client(self) -> bool:
        """Restore original Gemini client methods."""
        if not GEMINI_AVAILABLE or not self._patched:
            return False

        try:
            from google.generativeai import GenerativeModel

            if self.original_generate_content:
                GenerativeModel.generate_content = self.original_generate_content

            if self.original_generate_content_async:
                GenerativeModel.generate_content_async = (
                    self.original_generate_content_async
                )

            self._patched = False
            logger.info("Successfully unpatched Gemini GenerativeModel methods")
            return True

        except Exception as e:
            logger.error(f"Failed to unpatch Gemini client: {e}")
            return False

    def get_client_info(self) -> Dict[str, Any]:
        """Get information about the Gemini client."""
        if not GEMINI_AVAILABLE:
            return {"available": False, "reason": "google-generativeai not installed"}

        try:
            import google.generativeai as genai

            return {
                "available": True,
                "library": "google-generativeai",
                "version": getattr(genai, "__version__", "unknown"),
                "patched": self._patched,
            }
        except Exception as e:
            return {"available": False, "reason": str(e)}

    def _apply_outbound_guardrails(self, result: Any) -> Any:
        """Apply outbound guardrails to Gemini generation results (synchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine

            # Extract content from Gemini response
            response_text = self._extract_response_content(result)
            if not response_text.strip():
                return result

            # Create evaluation context
            context = {
                "llm_client": "gemini",
                "function_name": "google.generativeai.GenerativeModel.generate_content",
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
                        "Cannot run outbound guardrails evaluation for Gemini generation in sync context within async loop. "
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
                    f"Gemini generation outbound guardrails blocked response: {decision.reason}"
                )
                # Return a modified response with blocked content
                return self._create_blocked_response(
                    result, decision.reason or "Content policy violation detected"
                )

            return result

        except Exception as e:
            logger.error(
                f"Error applying outbound guardrails for Gemini generation: {e}",
                exc_info=True,
            )
            # Fail open - return original result
            return result

    async def _apply_outbound_guardrails_async(self, result: Any) -> Any:
        """Apply outbound guardrails to Gemini generation results (asynchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine

            # Extract content from Gemini response
            response_text = self._extract_response_content(result)
            if not response_text.strip():
                return result

            # Create evaluation context
            context = {
                "llm_client": "gemini",
                "function_name": "google.generativeai.GenerativeModel.generate_content_async",
            }

            # Get guardrails engine and evaluate
            engine = GuardrailsEngine.get_instance()
            decision = await engine.evaluate(
                response_text, context, direction="outbound"
            )

            if not decision.allowed:
                logger.warning(
                    f"Gemini async generation outbound guardrails blocked response: {decision.reason}"
                )
                # Return a modified response with blocked content
                return self._create_blocked_response(
                    result, decision.reason or "Content policy violation detected"
                )

            return result

        except Exception as e:
            logger.error(
                f"Error applying outbound guardrails for Gemini async generation: {e}",
                exc_info=True,
            )
            # Fail open - return original result
            return result

    def _extract_response_content(self, result: Any) -> str:
        """Extract text content from Gemini response object."""
        try:
            # Handle Gemini response format
            if hasattr(result, "text") and result.text:
                return str(result.text)
            elif hasattr(result, "candidates") and result.candidates:
                # Extract from candidates
                content_parts = []
                for candidate in result.candidates:
                    if hasattr(candidate, "content") and hasattr(
                        candidate.content, "parts"
                    ):
                        for part in candidate.content.parts:
                            if hasattr(part, "text"):
                                content_parts.append(str(part.text))
                return " ".join(content_parts) if content_parts else ""
            elif hasattr(result, "parts") and result.parts:
                # Extract from parts directly
                content_parts = []
                for part in result.parts:
                    if hasattr(part, "text"):
                        content_parts.append(str(part.text))
                return " ".join(content_parts) if content_parts else ""

            # Fallback: try to convert to string
            return str(result) if result else ""

        except Exception as e:
            logger.debug(f"Error extracting content from Gemini response: {e}")
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
            if hasattr(original_result, "text"):
                original_result.text = blocked_message
                return original_result
            elif hasattr(original_result, "candidates") and original_result.candidates:
                # Modify first candidate's content
                for candidate in original_result.candidates:
                    if hasattr(candidate, "content") and hasattr(
                        candidate.content, "parts"
                    ):
                        for part in candidate.content.parts:
                            if hasattr(part, "text"):
                                part.text = blocked_message
                                return original_result
            elif hasattr(original_result, "parts") and original_result.parts:
                # Modify first part
                for part in original_result.parts:
                    if hasattr(part, "text"):
                        part.text = blocked_message
                        return original_result

            # Fallback: return the blocked message as string
            return blocked_message

        except Exception as e:
            logger.error(f"Error creating blocked response: {e}")
            # Ultimate fallback
            return "[BLOCKED BY GUARDRAILS] - Content policy violation detected"

    # Provider-specific extraction methods for LLM span attributes

    def _extract_prompt_text(self, messages: Any, provider: str) -> str:
        """Extract prompt text from Gemini contents format."""
        if isinstance(messages, str):
            return messages
        elif isinstance(messages, list):
            # Handle list of content parts
            text_parts = []
            for content in messages:
                if isinstance(content, str):
                    text_parts.append(content)
                elif hasattr(content, "text"):
                    text_parts.append(str(content.text))
                elif isinstance(content, dict) and "text" in content:
                    text_parts.append(str(content["text"]))
            return " ".join(text_parts) if text_parts else ""
        elif hasattr(messages, "text"):
            return str(messages.text)
        elif isinstance(messages, dict) and "text" in messages:
            return str(messages["text"])
        return str(messages)

    def _extract_response_text(self, response: Any, provider: str) -> str:
        """Extract response text from Gemini response format."""
        try:
            # Handle Gemini response format
            if hasattr(response, "text") and response.text:
                return str(response.text)
            elif hasattr(response, "candidates") and response.candidates:
                # Extract from candidates
                content_parts = []
                for candidate in response.candidates:
                    if hasattr(candidate, "content") and hasattr(
                        candidate.content, "parts"
                    ):
                        for part in candidate.content.parts:
                            if hasattr(part, "text"):
                                content_parts.append(str(part.text))
                return " ".join(content_parts) if content_parts else ""
            elif hasattr(response, "parts") and response.parts:
                # Extract from parts directly
                content_parts = []
                for part in response.parts:
                    if hasattr(part, "text"):
                        content_parts.append(str(part.text))
                return " ".join(content_parts) if content_parts else ""
            return str(response) if response else ""
        except Exception as e:
            logger.debug(f"Error extracting Gemini response text: {e}")
            return ""

    def _extract_token_usage(
        self, response: Any, provider: str
    ) -> Optional[Dict[str, int]]:
        """Extract token usage from Gemini response."""
        try:
            if hasattr(response, "usage_metadata"):
                usage = response.usage_metadata
                return {
                    "input_tokens": getattr(usage, "prompt_token_count", 0),
                    "output_tokens": getattr(usage, "candidates_token_count", 0),
                }
            return None
        except Exception as e:
            logger.debug(f"Error extracting Gemini token usage: {e}")
            return None

    def _extract_finish_reason(self, response: Any, provider: str) -> Optional[str]:
        """Extract finish reason from Gemini response."""
        try:
            if hasattr(response, "candidates") and response.candidates:
                # Get finish reason from first candidate
                candidate = response.candidates[0]
                if hasattr(candidate, "finish_reason"):
                    return str(candidate.finish_reason)
            return None
        except Exception as e:
            logger.debug(f"Error extracting Gemini finish reason: {e}")
            return None
