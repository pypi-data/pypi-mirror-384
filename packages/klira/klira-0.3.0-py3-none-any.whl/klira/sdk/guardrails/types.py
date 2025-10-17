"""Type definitions for Klira AI SDK Guardrails components."""

from typing import Dict, Any, Optional, List, TypedDict

# Import dependent types from other modules if necessary
# (Ensure these imports don't create new circular dependencies)
from klira.sdk.guardrails.llm_service import (
    LLMEvaluationResult,
)  # Already defined here?


class Policy(TypedDict, total=False):
    """Definition of a single policy rule."""

    id: str
    name: str
    description: Optional[str]
    enabled: bool
    category: Optional[str]
    rules: List[Dict[str, Any]]
    llm_prompt: Optional[str]


class PolicySet:
    """Collection of policies to be applied by the guardrails engine."""

    def __init__(self, policies: Optional[List[Policy]] = None):
        """
        Initialize a PolicySet with optional list of policies.

        Args:
            policies: List of Policy objects defining rules to apply
        """
        self.policies = policies or []

    def add_policy(self, policy: Policy) -> None:
        """Add a policy to the set."""
        self.policies.append(policy)

    def get_policies(self) -> List[Policy]:
        """Get all policies in the set."""
        return self.policies

    def get_policy_by_id(self, policy_id: str) -> Optional[Policy]:
        """Get a specific policy by ID."""
        for policy in self.policies:
            if policy.get("id") == policy_id:
                return policy
        return None


class Decision:
    """Result of a guardrail policy evaluation."""

    def __init__(
        self,
        allowed: bool,
        reason: Optional[str] = None,
        policy_id: Optional[str] = None,
        confidence: float = 1.0,
    ):
        """
        Initialize a Decision object.

        Args:
            allowed: Whether the input is allowed
            reason: Optional reason for the decision
            policy_id: ID of the policy that made the decision
            confidence: Confidence score for the decision (0.0-1.0)
        """
        self.allowed = allowed
        self.reason = reason
        self.policy_id = policy_id
        self.confidence = confidence


# Re-defining based on engine.py content:
class GuardrailProcessingResult(TypedDict, total=False):
    """Structure of the result returned by GuardrailsEngine.process_message."""

    allowed: bool  # Required
    confidence: float  # Required
    decision_layer: (
        str  # Required (e.g., 'fast_rules', 'llm_fallback', 'augmentation', 'default')
    )
    violated_policies: Optional[List[str]]
    applied_policies: Optional[List[str]]
    response: Optional[str]  # Modified/generated response from a layer
    blocked_reason: Optional[str]
    error: Optional[str]  # Description of error if one occurred and fallback was used
    evaluation_method: Optional[
        str
    ]  # Evaluation method used: "fast_rules", "policy_augmentation", "llm_fallback"
    # Include results from sub-components if needed by consumers
    fast_rules_result: Optional[Dict[str, Any]]  # Sanitized dict representation
    augmentation_result: Optional[Dict[str, Any]]  # Sanitized dict representation
    llm_evaluation_result: Optional["LLMEvaluationResult"]  # Forward reference


class GuardrailOutputCheckResult(TypedDict, total=False):
    """Structure of the result returned by GuardrailsEngine.check_output."""

    allowed: bool  # Required
    confidence: float  # Required
    decision_layer: str  # Required (e.g., 'fast_rules', 'llm_fallback')
    violated_policies: Optional[List[str]]
    transformed_response: Optional[str]  # Redacted/modified response
    blocked_reason: Optional[str]
    error: Optional[str]
    evaluation_method: Optional[
        str
    ]  # Evaluation method used: "fast_rules", "llm_fallback"
    fast_rules_result: Optional[Dict[str, Any]]  # Sanitized dict representation
    llm_evaluation_result: Optional["LLMEvaluationResult"]  # Forward reference


# If FastRulesEvaluationResult, AugmentationResult, LLMEvaluationResult are NOT defined
# in their respective modules and were defined *only* in engine.py originally,
# uncomment and move their definitions here as well.
# Example:
# class FastRulesEvaluationResult(TypedDict):
#    ... definition ...
