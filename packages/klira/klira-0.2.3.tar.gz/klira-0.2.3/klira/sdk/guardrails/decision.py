"""Handles the decision routing logic for the GuardrailsEngine.

This module takes results from different guardrail layers (fast rules, augmentation,
LLM fallback) and determines the final action based on predefined sequences.
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, List, Union
import re  # Import re for Pattern type check

# Import necessary components and types
from .fast_rules import FastRulesEngine, FastRulesEvaluationResult
from .policy_augmentation import PolicyAugmentation, AugmentationResult
from .llm_fallback import LLMFallback  # LLMEvaluationResult is imported below
from .llm_service import LLMEvaluationResult  # Import the actual type definition

# Import result types from the new types module
from .types import GuardrailProcessingResult, GuardrailOutputCheckResult

logger = logging.getLogger("klira.guardrails.decision")

# --- Guidelines Cache for Cross-Span Access ---
# This cache stores guidelines by conversation ID so they can be accessed
# across different OpenTelemetry spans during the same conversation

_guidelines_cache: Dict[str, Dict[str, Any]] = {}
_cache_lock = threading.RLock()
_cache_ttl_seconds = 300  # 5 minutes TTL


def _store_guidelines_in_cache(conversation_id: str, guidelines: List[str]) -> None:
    """Store guidelines in a persistent cache with TTL."""
    with _cache_lock:
        _guidelines_cache[conversation_id] = {
            "guidelines": guidelines,
            "timestamp": time.time(),
        }


def _get_guidelines_from_cache(conversation_id: str) -> Optional[List[str]]:
    """Retrieve guidelines from cache if not expired."""
    with _cache_lock:
        if conversation_id in _guidelines_cache:
            entry = _guidelines_cache[conversation_id]
            if time.time() - entry["timestamp"] < _cache_ttl_seconds:
                guidelines = entry["guidelines"]
                # Ensure we return the correct type
                if isinstance(guidelines, list):
                    return guidelines
            else:
                # Remove expired entry
                del _guidelines_cache[conversation_id]
    return None


def _clear_guidelines_from_cache(conversation_id: str) -> None:
    """Clear guidelines from cache for a specific conversation."""
    with _cache_lock:
        _guidelines_cache.pop(conversation_id, None)


def _cleanup_expired_cache_entries() -> None:
    """Clean up expired cache entries."""
    current_time = time.time()
    with _cache_lock:
        expired_keys = [
            conv_id
            for conv_id, entry in _guidelines_cache.items()
            if current_time - entry["timestamp"] >= _cache_ttl_seconds
        ]
        for key in expired_keys:
            del _guidelines_cache[key]


# --- Helper Function to Sanitize Results ---


def _sanitize_dict_for_json(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Recursively remove non-serializable items like re.Pattern."""
    if data is None:
        return None

    sanitized: Dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            sanitized_value = _sanitize_dict_for_json(value)
            if sanitized_value is not None:
                sanitized[key] = sanitized_value
        elif isinstance(value, list):
            sanitized_value = _sanitize_list_for_json(value)  # type: ignore[assignment]
            if sanitized_value is not None:
                sanitized[key] = sanitized_value
        elif not isinstance(value, re.Pattern):
            sanitized[key] = value
        # else: skip re.Pattern objects
    return sanitized


def _sanitize_list_for_json(data: Optional[List[Any]]) -> Optional[List[Any]]:
    """Recursively sanitize lists for JSON serialization."""
    if data is None:
        return None

    sanitized = []
    for item in data:
        if isinstance(item, dict):
            sanitized_item = _sanitize_dict_for_json(item)
            if sanitized_item is not None:
                sanitized.append(sanitized_item)
        elif isinstance(item, list):
            sanitized_item = _sanitize_list_for_json(item)  # type: ignore[assignment]
            if sanitized_item is not None:
                sanitized.append(sanitized_item)
        elif not isinstance(item, re.Pattern):
            sanitized.append(item)
        # else: skip re.Pattern objects
    return sanitized


def _sanitize_typed_dict_for_json(data: Any) -> Optional[Dict[str, Any]]:
    """Convert TypedDict or dict-like objects to sanitized dict for JSON serialization."""
    if data is None:
        return None

    # Convert TypedDict to regular dict
    if hasattr(data, "_asdict"):
        # For NamedTuple-like objects
        data_dict = data._asdict()
    elif isinstance(data, dict):
        # For regular dicts and TypedDict instances
        data_dict = dict(data)
    else:
        # For other objects, try to convert to dict
        try:
            data_dict = dict(data)
        except (TypeError, ValueError):
            # If conversion fails, return None
            return None

    return _sanitize_dict_for_json(data_dict)


# --- Compliance Audit Span Helper ---


def _create_compliance_audit_span(
    result: Union[GuardrailProcessingResult, GuardrailOutputCheckResult, Dict[str, Any]],
    direction: str,
    message_content: str,
    context: Dict[str, Any]
) -> None:
    """Create a compliance audit span for the guardrails decision.

    This span is linked to any active parent span (typically an LLM request span)
    to create a complete audit trail from policy evaluation to LLM execution.

    Args:
        result: The decision result (GuardrailProcessingResult or GuardrailOutputCheckResult)
        direction: Direction of evaluation ("inbound" or "outbound")
        message_content: The message or response content that was evaluated
        context: The processing context
    """
    from klira.sdk.utils.span_utils import safe_set_span_attribute
    from opentelemetry import trace
    from opentelemetry.trace import StatusCode, Link

    tracer = trace.get_tracer("klira.guardrails.compliance")

    # Capture current span context for linking
    current_span = trace.get_current_span()
    span_context = current_span.get_span_context() if current_span else None

    # Create compliance audit span with link to parent span if available
    links = []
    if span_context and span_context.is_valid:
        links.append(Link(span_context))
        logger.debug(f"Linking compliance audit span to parent span: {span_context.span_id}")

    # Start span with links (if any)
    if links:
        audit_span_context_manager = tracer.start_as_current_span(
            name="klira.compliance.audit",
            links=links
        )
    else:
        audit_span_context_manager = tracer.start_as_current_span(
            name="klira.compliance.audit"
        )

    with audit_span_context_manager as audit_span:
        # Basic audit attributes
        audit_attributes = {
            "compliance.direction": direction,
            "compliance.decision.allowed": result.get("allowed", False),
            "compliance.decision.action": "allow" if result.get("allowed") else "block",
            "compliance.decision.confidence": result.get("confidence", 0.0),
            "compliance.input_length": len(message_content),
        }

        # Add evaluation method
        if "evaluation_method" in result:
            audit_attributes["compliance.evaluation.method"] = result["evaluation_method"]

        # Add decision layer
        if "decision_layer" in result:
            audit_attributes["compliance.decision.layer"] = result["decision_layer"]

        # Add context (truncated)
        if context:
            context_str = str(context)[:500]
            audit_attributes["compliance.context"] = context_str

        # Add policy information for inbound (matched policies) - only exists in GuardrailProcessingResult
        if "applied_policies" in result:
            applied_policies = result.get("applied_policies")
            if applied_policies and isinstance(applied_policies, list):
                audit_attributes["compliance.policies.matched"] = applied_policies[:10]
                audit_attributes["compliance.policies.matched_count"] = len(applied_policies)

        # Add violated policies information
        if "violated_policies" in result and result["violated_policies"]:
            audit_attributes["compliance.policies.violated"] = result["violated_policies"][:10]
            audit_attributes["compliance.policies.violated_count"] = len(result["violated_policies"])

        # Add block reason if blocked
        if not result.get("allowed") and "blocked_reason" in result:
            blocked_reason = result["blocked_reason"]
            audit_attributes["compliance.block.reason"] = blocked_reason[:500] if blocked_reason else ""

        # Add augmentation details if present - only exists in GuardrailProcessingResult
        if "augmentation_result" in result:
            aug_result = result.get("augmentation_result")
            if aug_result and isinstance(aug_result, dict) and "matched_policies" in aug_result:
                matched = aug_result["matched_policies"]
                if matched and isinstance(matched, list):
                    policy_names = [p.get("id", p.get("name", "unknown")) for p in matched[:10]]
                    audit_attributes["compliance.augmentation.policies"] = policy_names
                    audit_attributes["compliance.augmentation.policies_count"] = len(matched)

        # Set all attributes at once
        for key, value in audit_attributes.items():
            safe_set_span_attribute(audit_span, key, value)

        # Set span status
        audit_span.set_status(StatusCode.OK)


# --- Decision Routing Functions ---


async def route_message_decision(
    message: str,
    context: Dict[str, Any],
    fast_rules_engine: Optional[FastRulesEngine],
    augmentation_engine: Optional[PolicyAugmentation],
    llm_fallback_engine: Optional[LLMFallback],
) -> GuardrailProcessingResult:
    """Routes the decision logic for processing input messages.

    Executes the sequence: Fast Rules -> Policy Augmentation -> LLM Fallback -> Default.

    Args:
        message: The input message.
        context: The processing context (will be updated with intermediate results).
        fast_rules_engine: Initialized FastRulesEngine instance.
        augmentation_engine: Initialized PolicyAugmentation instance.
        llm_fallback_engine: Initialized LLMFallback instance.

    Returns:
        The final GuardrailProcessingResult.
    """
    conversation_id = context.get("conversation_id", "unknown")
    # Initialize intermediate results
    fast_result: Optional[FastRulesEvaluationResult] = None
    augmentation_data: Optional[AugmentationResult] = None
    llm_eval_result: Optional[LLMEvaluationResult] = None

    # --- Step 1: Fast Rules ---
    if fast_rules_engine:
        logger.debug(
            f"[{conversation_id}] DecisionRouter: Evaluating with FastRules..."
        )
        # Get direction from context if available, default to inbound
        direction = context.get("direction", "inbound")
        fast_result = fast_rules_engine.evaluate(message, context, direction)

        # Check individual violations for blocking actions
        blocking_violation = None
        for violation in fast_result.get("violations", []):
            # Check if policy action is 'block' (no confidence threshold)
            if violation.get("action") == "block":
                blocking_violation = violation
                break  # Block on first block violation

        if blocking_violation:
            policy_id = blocking_violation.get("policy_id", "unknown_policy")
            confidence = blocking_violation.get("confidence", 0.0)
            logger.info(
                f"[{conversation_id}] DecisionRouter: Blocked by FastRules (Policy: {policy_id}, Action: block, Confidence: {confidence:.2f})."
            )
            # Return result immediately if blocked by a specific fast rule
            result = GuardrailProcessingResult(
                allowed=False,
                confidence=confidence,
                decision_layer="fast_rules",
                evaluation_method="fast_rules",
                violated_policies=[policy_id],  # Report the specific blocking policy
                blocked_reason=f"Policy '{policy_id}' violation detected by fast rules.",
                fast_rules_result=_sanitize_typed_dict_for_json(
                    fast_result
                ),  # Sanitize before returning
            )
            # Create compliance audit span
            direction = context.get("direction", "inbound")
            _create_compliance_audit_span(result, direction, message, context)
            return result

        # Log if violations were found but none were blocking
        elif fast_result.get("violations"):
            logger.debug(
                f"[{conversation_id}] DecisionRouter: FastRules found violations, but none had block action. Proceeding..."
            )

    # --- Step 2: Policy Augmentation ---
    # This step gathers information (matched policies, guidelines) even if not blocking.
    if augmentation_engine:
        logger.debug(
            f"[{conversation_id}] DecisionRouter: Processing with PolicyAugmentation..."
        )
        augmentation_data = await augmentation_engine.process_message(message, context)
        # Add matched policies info to context for potential use by LLM
        if augmentation_data and augmentation_data.get("matched_policies"):
            context["augmentation_matched_policies"] = [
                p["id"] for p in augmentation_data["matched_policies"]
            ]

            # Store guidelines in simple storage and OpenTelemetry context for injection
            guidelines = augmentation_data.get("extracted_guidelines")
            if guidelines:
                try:
                    # Store in simple storage for decorator access
                    from klira.sdk.decorators.guardrails import _set_current_guidelines

                    _set_current_guidelines(guidelines)

                    # Also store in OTel context as backup
                    from opentelemetry import context as otel_context

                    current_ctx = otel_context.get_current()
                    new_ctx = otel_context.set_value(
                        "klira.augmentation.guidelines", guidelines, current_ctx
                    )
                    otel_context.attach(new_ctx)
                    logger.info(
                        f"[{conversation_id}] DecisionRouter: Stored {len(guidelines)} guidelines in OTel context."
                    )

                    # Add augmentation attributes to current span for tracking
                    from klira.sdk.tracing.tracing import get_current_span
                    from klira.sdk.utils.span_utils import safe_set_span_attribute

                    current_span = get_current_span()
                    if current_span:
                        safe_set_span_attribute(current_span, "klira.guardrails.augmentation.applied", True)
                        safe_set_span_attribute(current_span, "klira.guardrails.augmentation.policies_count", len(augmentation_data.get("matched_policies", [])))

                        # Store policy names (first 10)
                        policy_names = [p.get("id", p.get("name", "unknown")) for p in augmentation_data.get("matched_policies", [])[:10]]
                        safe_set_span_attribute(current_span, "klira.guardrails.augmentation.policy_names", policy_names)

                        # Store formatted guidelines sample (first 500 chars)
                        formatted_guidelines = "\n".join(guidelines)
                        guidelines_sample = formatted_guidelines[:500] if len(formatted_guidelines) > 500 else formatted_guidelines
                        safe_set_span_attribute(current_span, "klira.guardrails.augmentation.guidelines_sample", guidelines_sample)

                except Exception as e:
                    logger.warning(
                        f"[{conversation_id}] DecisionRouter: Failed to store guidelines: {e}"
                    )

        # Check if augmentation itself provided a direct response (less common)
        if augmentation_data and augmentation_data.get("generated_response"):
            logger.info(
                f"[{conversation_id}] DecisionRouter: Response generated directly by PolicyAugmentation."
            )
            # Return result immediately if augmentation generated a response
            result = GuardrailProcessingResult(
                allowed=True,  # Assume compliant if generated
                confidence=1.0,
                decision_layer="augmentation_response",
                evaluation_method="policy_augmentation",
                response=augmentation_data["generated_response"],
                applied_policies=[
                    p["id"] for p in augmentation_data.get("matched_policies", [])
                ],  # Extract IDs here
                augmentation_result=_sanitize_typed_dict_for_json(
                    augmentation_data
                ),  # Sanitize
                fast_rules_result=_sanitize_typed_dict_for_json(
                    fast_result
                ),  # Sanitize
            )
            # Create compliance audit span
            direction = context.get("direction", "inbound")
            _create_compliance_audit_span(result, direction, message, context)
            return result

    # --- Step 3: LLM Fallback ---
    # This step only runs if no policies were matched in augmentation
    policies_matched = augmentation_data and augmentation_data.get("matched_policies")
    if llm_fallback_engine and not policies_matched:
        logger.debug(
            f"[{conversation_id}] DecisionRouter: No policies matched in augmentation. Evaluating with LLMFallback..."
        )
        # Pass context (which might now include augmentation results) and fast_result
        # Convert FastRulesEvaluationResult to dict for LLM fallback
        fast_result_dict = dict(fast_result) if fast_result else None
        llm_eval_result = await llm_fallback_engine.evaluate(
            message, context, fast_result_dict
        )
        # LLM decides to block or transform?
        if not llm_eval_result["allowed"] or llm_eval_result["action"] in [
            "block",
            "transform",
        ]:
            action = llm_eval_result["action"]
            logger.info(
                f"[{conversation_id}] DecisionRouter: Action '{action}' determined by LLMFallback."
            )
            # Return result immediately if blocked or needs transformation by LLM
            result = GuardrailProcessingResult(
                allowed=False,  # Both block and transform should prevent the original content from proceeding
                confidence=llm_eval_result["confidence"],
                decision_layer="llm_fallback",
                evaluation_method="llm_fallback",
                violated_policies=llm_eval_result["violated_policies"],
                blocked_reason=llm_eval_result["reasoning"],
                llm_evaluation_result=llm_eval_result,
                fast_rules_result=_sanitize_typed_dict_for_json(
                    fast_result
                ),  # Sanitize
                augmentation_result=_sanitize_typed_dict_for_json(
                    augmentation_data
                ),  # Sanitize
            )
            # Create compliance audit span
            direction = context.get("direction", "inbound")
            _create_compliance_audit_span(result, direction, message, context)
            return result
    elif policies_matched:
        logger.debug(
            f"[{conversation_id}] DecisionRouter: Policies matched in augmentation. Skipping LLM fallback."
        )

    # --- Step 4: Default Decision ---
    # Reached only if no prior step explicitly blocked or generated a response.
    if policies_matched:
        logger.debug(
            f"[{conversation_id}] DecisionRouter: Policies matched. Allowing with augmentation."
        )
        decision_layer = "policy_augmentation"
        evaluation_method = "policy_augmentation"
        confidence = 0.8  # High confidence when policies match
    else:
        logger.debug(
            f"[{conversation_id}] DecisionRouter: No blocking action triggered. Defaulting to allowed."
        )
        decision_layer = "llm_fallback" if llm_eval_result else "default_allow"
        evaluation_method = "llm_fallback" if llm_eval_result else "fast_rules"
        confidence = (
            llm_eval_result["confidence"]
            if llm_eval_result and llm_eval_result["allowed"]
            else 0.2
        )

    final_result = GuardrailProcessingResult(
        allowed=True,
        confidence=confidence,
        decision_layer=decision_layer,
        evaluation_method=evaluation_method,
        applied_policies=[
            p["id"] for p in augmentation_data.get("matched_policies", [])
        ]
        if augmentation_data
        else [],
        llm_evaluation_result=llm_eval_result,
        fast_rules_result=_sanitize_typed_dict_for_json(fast_result),  # Sanitize
        augmentation_result=_sanitize_typed_dict_for_json(
            augmentation_data
        ),  # Sanitize
    )

    # Create compliance audit span
    direction = context.get("direction", "inbound")
    _create_compliance_audit_span(final_result, direction, message, context)

    return final_result


async def route_output_decision(
    ai_response: str,
    context: Dict[str, Any],
    fast_rules_engine: Optional[FastRulesEngine],
    llm_fallback_engine: Optional[LLMFallback],
) -> GuardrailOutputCheckResult:
    """Routes the decision logic for checking AI output.

    Executes the sequence: Fast Rules -> LLM Fallback -> Default.

    Args:
        ai_response: The AI response text.
        context: The processing context.
        fast_rules_engine: Initialized FastRulesEngine instance.
        llm_fallback_engine: Initialized LLMFallback instance.

    Returns:
        The final GuardrailOutputCheckResult.
    """
    conversation_id = context.get("conversation_id", "unknown")
    final_result: Optional[GuardrailOutputCheckResult] = None
    fast_result: Optional[FastRulesEvaluationResult] = None
    llm_eval_result: Optional[LLMEvaluationResult] = None

    # --- Step 1: Fast Rules ---
    if fast_rules_engine:
        logger.debug(
            f"[{conversation_id}] DecisionRouter: Evaluating output with FastRules..."
        )
        # Output evaluation is always outbound direction
        fast_result = fast_rules_engine.evaluate(ai_response, context, "outbound")

        # Check individual violations for blocking actions
        blocking_violation = None
        for violation in fast_result.get("violations", []):
            # Check if policy action is 'block' (no confidence threshold)
            if violation.get("action") == "block":
                blocking_violation = violation
                break  # Block on first block violation

        if blocking_violation:
            policy_id = blocking_violation.get("policy_id", "unknown_policy")
            confidence = blocking_violation.get("confidence", 0.0)
            logger.info(
                f"[{conversation_id}] DecisionRouter: Output blocked by FastRules (Policy: {policy_id}, Action: block, Confidence: {confidence:.2f})."
            )
            # Return result immediately if blocked by a specific fast rule
            # TODO: Implement redaction based on fast rule matches if possible/needed
            final_result = GuardrailOutputCheckResult(
                allowed=False,
                confidence=confidence,
                decision_layer="fast_rules",
                evaluation_method="fast_rules",
                violated_policies=[policy_id],
                blocked_reason=f"Harmful content related to policy '{policy_id}' detected in output by fast rules.",
                fast_rules_result=_sanitize_typed_dict_for_json(
                    fast_result
                ),  # Sanitize
                # transformed_response=... # Add if redaction implemented
            )
            # Create compliance audit span
            _create_compliance_audit_span(final_result, "outbound", ai_response, context)
            return final_result  # Early exit

        # Log if violations were found but none were blocking
        elif fast_result.get("violations"):
            logger.debug(
                f"[{conversation_id}] DecisionRouter: FastRules found output violations, but none had block action. Proceeding..."
            )

    # --- Step 2: LLM Fallback ---
    if llm_fallback_engine:
        logger.debug(
            f"[{conversation_id}] DecisionRouter: Evaluating output with LLMFallback..."
        )
        # Convert FastRulesEvaluationResult to dict for LLM fallback
        fast_result_dict = dict(fast_result) if fast_result else None
        llm_eval_result = await llm_fallback_engine.evaluate(
            ai_response, context, fast_result_dict
        )
        if not llm_eval_result["allowed"] or llm_eval_result["action"] != "allow":
            logger.info(
                f"[{conversation_id}] DecisionRouter: Output action '{llm_eval_result['action']}' determined by LLMFallback."
            )
            transformed = None
            if llm_eval_result["action"] == "transform":
                logger.warning(
                    "LLM recommended 'transform' but transformation logic is not implemented."
                )
                # transformed = llm_eval_result.get("transformed_output")
            final_result = GuardrailOutputCheckResult(
                allowed=(llm_eval_result["action"] == "allow"),
                confidence=llm_eval_result["confidence"],
                decision_layer="llm_fallback",
                evaluation_method="llm_fallback",
                violated_policies=llm_eval_result["violated_policies"],
                blocked_reason=llm_eval_result["reasoning"],
                transformed_response=transformed,
                llm_evaluation_result=llm_eval_result,
                fast_rules_result=_sanitize_typed_dict_for_json(
                    fast_result
                ),  # Sanitize
            )
            # Create compliance audit span
            _create_compliance_audit_span(final_result, "outbound", ai_response, context)
            return final_result  # Early exit

    # --- Step 3: Default Allow ---
    logger.debug(
        f"[{conversation_id}] DecisionRouter: Output check passed. Defaulting to allowed."
    )
    evaluation_method = "llm_fallback" if llm_eval_result else "fast_rules"
    final_result = GuardrailOutputCheckResult(
        allowed=True,
        confidence=1.0,
        decision_layer="default_allow",
        evaluation_method=evaluation_method,
        fast_rules_result=_sanitize_typed_dict_for_json(fast_result),  # Sanitize
        llm_evaluation_result=llm_eval_result,
    )

    # Create compliance audit span
    _create_compliance_audit_span(final_result, "outbound", ai_response, context)

    return final_result
