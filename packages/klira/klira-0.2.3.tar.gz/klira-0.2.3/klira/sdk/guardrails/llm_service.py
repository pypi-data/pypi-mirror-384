"""Defines the interface and implementations for LLM services used by guardrails."""

import logging
import re
from typing import Dict, Any, Optional, List, Protocol, TypedDict, TypeAlias

# Use TYPE_CHECKING for type hinting external libraries like OpenAI
try:
    from openai import AsyncOpenAI

    AsyncOpenAIClientType: TypeAlias = AsyncOpenAI
except ImportError:
    AsyncOpenAIClientType: TypeAlias = Any  # type: ignore

logger = logging.getLogger("klira.guardrails.llm_service")


# Define the expected structure for LLM evaluation results
class LLMEvaluationResult(TypedDict):
    allowed: bool
    confidence: float
    violated_policies: List[str]
    action: str  # e.g., 'allow', 'block', 'transform'
    reasoning: str
    response: Optional[str]  # Optional raw LLM response


# Define the protocol that LLM services must implement
class LLMServiceProtocol(Protocol):
    """Protocol defining the interface for LLM services used in guardrails."""

    async def evaluate(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        fast_result: Optional[Dict[str, Any]] = None,
    ) -> LLMEvaluationResult:
        """Evaluates a message for policy compliance using the LLM.

        Args:
            message: The user message or content to evaluate.
            context: Additional context dictionary (e.g., conversation state).
            fast_result: Optional results from preceding fast rule checks.

        Returns:
            An LLMEvaluationResult dictionary containing the compliance decision,
            confidence, violated policies, recommended action, and reasoning.
        """
        ...


class DefaultLLMService:
    """Default LLM service providing a permissive passthrough.

    This service should NOT be used if LLM-based policy checks are required.
    It always returns an 'allowed' result with default values.
    """

    async def evaluate(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        fast_result: Optional[Dict[str, Any]] = None,
    ) -> LLMEvaluationResult:
        """Returns a default permissive evaluation result."""
        logger.warning(
            "Using DefaultLLMService. No actual LLM evaluation will be performed."
        )
        return LLMEvaluationResult(
            allowed=True,
            confidence=0.7,
            violated_policies=[],
            action="allow",
            reasoning="No LLM service configured for policy evaluation. Default passthrough response.",
            response=None,
        )


class OpenAILLMService:
    """LLM service implementation using the OpenAI API.

    Requires an initialized OpenAI client (`openai.AsyncOpenAI`).
    """

    client: "AsyncOpenAIClientType"  # Use the type alias
    model: str

    def __init__(self, client: "AsyncOpenAIClientType", model: str = "gpt-4o-mini"):
        """Initializes the OpenAI LLM service.

        Args:
            client: An initialized `openai.AsyncOpenAI` client instance.
            model: The OpenAI model identifier to use (e.g., "gpt-4o-mini").
        """
        self.client = client
        self.model = model
        logger.info(f"OpenAILLMService initialized with model: {self.model}")

    async def _complete(
        self, prompt: str, temperature: float = 0.2, max_tokens: int = 500
    ) -> str:
        """Internal helper to call the OpenAI Chat Completion API."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            return content if content else ""
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}", exc_info=True)
            # Return a string indicating failure to parse downstream
            return "ERROR: OpenAI API call failed"

    def _parse_evaluation_response(self, response_text: str) -> LLMEvaluationResult:
        """Parses the structured text response from the LLM evaluation prompt."""
        lines = response_text.strip().split("\n")
        result = LLMEvaluationResult(
            allowed=False,  # Default to not allowed if parsing fails
            confidence=0.5,
            violated_policies=[],
            action="block",
            reasoning="Failed to parse LLM response.",
            response=response_text,
        )

        if not lines or "ERROR:" in lines[0]:
            result["reasoning"] = (
                f"LLM evaluation failed: {lines[0] if lines else 'Empty response'}"
            )
            return result

        # Line 0: Compliance status
        result["allowed"] = (
            "COMPLIANT" in lines[0].upper() and "NON-COMPLIANT" not in lines[0].upper()
        )
        result["action"] = (
            "allow" if result["allowed"] else "block"
        )  # Initial action based on compliance

        # Parse subsequent lines
        for line in lines[1:]:
            line_upper = line.upper()
            if line_upper.startswith("CONFIDENCE:"):
                match = re.search(r"\d\.\d+", line)
                if match:
                    try:
                        result["confidence"] = float(match.group())
                    except ValueError:
                        logger.warning(
                            f"Could not parse confidence value from line: {line}"
                        )
            elif line_upper.startswith("REASONING:"):
                result["reasoning"] = line.split(":", 1)[-1].strip()
            elif line_upper.startswith("VIOLATED_POLICIES:"):
                policies_str = line.split(":", 1)[-1].strip()
                # Handle variations like [], [policy1], [policy1, policy2]
                if policies_str and policies_str != "[]":
                    result["violated_policies"] = [
                        p.strip()
                        for p in policies_str.strip("[] ").split(",")
                        if p.strip()
                    ]
            elif line_upper.startswith("RECOMMENDED_ACTION:"):
                action_str = line.split(":", 1)[-1].strip().lower()
                if action_str in ["allow", "block", "transform"]:
                    result["action"] = action_str

        # If parsing somehow failed but LLM said compliant, adjust reasoning
        if result["allowed"] and result["reasoning"] == "Failed to parse LLM response.":
            result["reasoning"] = (
                "LLM indicated compliance, but details might be missing from response."
            )

        return result

    async def evaluate(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        fast_result: Optional[Dict[str, Any]] = None,
    ) -> LLMEvaluationResult:
        """Evaluates a message for policy compliance using OpenAI.

        Constructs a specific prompt asking the LLM to evaluate the message
        based on general policy principles (or specific policies if provided
        in context) and parse the structured response.

        Args:
            message: The message to evaluate.
            context: Additional context (potentially including specific policies).
            fast_result: Results from fast rule checks (can inform the LLM).

        Returns:
            An LLMEvaluationResult dictionary.
        """
        # Basic prompt structure
        prompt_lines = [
            "You are an AI assistant evaluating content for policy compliance. Analyze the following MESSAGE critically.",
            "Consider potential policy violations related to safety, ethics, legality, and appropriateness.",
            f"\nMESSAGE:\n{message}",
        ]

        # Optionally include context or fast results
        if context and context.get("active_policies"):  # Example context key
            prompt_lines.insert(2, f"\nRelevant Policies: {context['active_policies']}")
        if fast_result and fast_result.get(
            "flagged_keywords"
        ):  # Example fast result key
            prompt_lines.insert(
                3,
                f"\nNote: Fast rules flagged keywords: {fast_result['flagged_keywords']}",
            )

        prompt_lines.extend(
            [
                "\nProvide your analysis STRICTLY in the following format, with each item on a new line:",
                "COMPLIANT or NON-COMPLIANT",
                "CONFIDENCE: [a float between 0.0 and 1.0]",
                "REASONING: [a concise explanation for your decision]",
                "VIOLATED_POLICIES: [a comma-separated list of specific policy IDs violated, or [] if none]",
                "RECOMMENDED_ACTION: [allow, block, or transform]",
            ]
        )

        eval_prompt = "\n".join(prompt_lines)
        logger.debug(f"Sending evaluation prompt to OpenAI: {eval_prompt}")

        # Get response from OpenAI
        llm_response = await self._complete(
            eval_prompt, temperature=0.1, max_tokens=200
        )
        logger.debug(f"Received evaluation response from OpenAI: {llm_response}")

        # Parse the response
        parsed_result = self._parse_evaluation_response(llm_response)

        logger.info(
            f"LLM evaluation result: Allowed={parsed_result['allowed']}, Confidence={parsed_result['confidence']:.2f}, "
            f"Action={parsed_result['action']}, Violated={parsed_result['violated_policies']}"
        )
        return parsed_result


# Ensure the implementations conform to the protocol (for static analysis)
_default_service: LLMServiceProtocol = DefaultLLMService()
_openai_service: Optional[LLMServiceProtocol] = None  # Only if initialized

