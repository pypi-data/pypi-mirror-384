"""MCP Guardrails decorator for protecting individual functions from memory leaks.

This decorator provides outbound guardrail evaluation for standalone functions,
preventing sensitive information from being leaked through MCP communications.
"""

import logging
import functools
import asyncio
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from inspect import iscoroutinefunction

from klira.sdk.guardrails.engine import GuardrailsEngine
from klira.sdk.guardrails.types import PolicySet
from klira.sdk.utils.error_handler import handle_errors

logger = logging.getLogger("klira.decorators.mcp_guardrails")

# Type variable for the decorated function
F = TypeVar('F', bound=Callable[..., Any])

# Violation handling modes
class ViolationMode:
    BLOCK = "block"
    AUGMENT = "augment"
    WARN = "warn"


class MCPGuardrailsError(Exception):
    """Exception raised when MCP guardrails block a function output."""
    
    def __init__(self, message: str, policy_id: Optional[str] = None, confidence: float = 1.0):
        super().__init__(message)
        self.policy_id = policy_id
        self.confidence = confidence


def mcp_guardrails(
    policy_set: Optional[PolicySet] = None,
    on_violation: str = ViolationMode.AUGMENT,
    conversation_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None,
    enabled: bool = True
) -> Callable[[F], F]:
    """
    Decorator to apply MCP guardrails to function outputs.
    
    This decorator evaluates function outputs using outbound guardrails to prevent
    sensitive information from being leaked through MCP communications.
    
    Args:
        policy_set: Optional custom policy set to use for evaluation
        on_violation: How to handle violations ("block", "augment", "warn")
        conversation_id: Optional conversation ID for context
        organization_id: Optional organization ID for telemetry
        project_id: Optional project ID for telemetry
        enabled: Whether guardrails are enabled (default: True)
        
    Returns:
        Decorated function with MCP guardrail protection
        
    Example:
        @mcp_guardrails(on_violation="block")
        def get_user_data(user_id: str) -> str:
            return f"User data for {user_id}"
            
        @mcp_guardrails(on_violation="augment")
        async def process_message(message: str) -> str:
            return await llm_process(message)
    """
    
    def decorator(func: F) -> F:
        if not enabled:
            logger.debug(f"MCP guardrails disabled for function {func.__name__}")
            return func
            
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Execute the original function
            result = func(*args, **kwargs)
            
            # Apply outbound guardrails
            return _apply_outbound_guardrails_sync(
                result=result,
                func_name=func.__name__,
                policy_set=policy_set,
                on_violation=on_violation,
                conversation_id=conversation_id,
                organization_id=organization_id,
                project_id=project_id
            )
            
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Execute the original function
            if iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Apply outbound guardrails
            return await _apply_outbound_guardrails_async(
                result=result,
                func_name=func.__name__,
                policy_set=policy_set,
                on_violation=on_violation,
                conversation_id=conversation_id,
                organization_id=organization_id,
                project_id=project_id
            )
        
        # Return appropriate wrapper based on function type
        if iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore
            
    return decorator


def _apply_outbound_guardrails_sync(
    result: Any,
    func_name: str,
    policy_set: Optional[PolicySet] = None,
    on_violation: str = ViolationMode.AUGMENT,
    conversation_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None
) -> Any:
    """Apply outbound guardrails synchronously (runs async evaluation in thread)."""
    try:
        # Convert result to string for evaluation
        if isinstance(result, str):
            text_result = result
        else:
            text_result = str(result)
            
        # Run async evaluation in thread
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            pass
            
        if loop and loop.is_running():
            # We're already in an async context, schedule the coroutine
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,  
                    _evaluate_outbound_guardrails(
                        text_result, func_name, policy_set, on_violation,
                        conversation_id, organization_id, project_id
                    )
                )
                evaluated_result = future.result()
        else:
            # No event loop running, can use asyncio.run
            evaluated_result = asyncio.run(
                _evaluate_outbound_guardrails(
                    text_result, func_name, policy_set, on_violation,
                    conversation_id, organization_id, project_id
                )
            )
            
        # Return original result if it's the same as text_result, otherwise return evaluated
        if evaluated_result == text_result:
            return result
        else:
            return evaluated_result
            
    except MCPGuardrailsError:
        # Re-raise our custom exceptions with their attributes intact
        raise
    except Exception as e:
        logger.error(f"Error applying outbound guardrails to {func_name}: {e}")
        if on_violation == ViolationMode.BLOCK:
            raise MCPGuardrailsError(f"Guardrails evaluation failed for {func_name}: {e}")
        return result


async def _apply_outbound_guardrails_async(
    result: Any,
    func_name: str,
    policy_set: Optional[PolicySet] = None,
    on_violation: str = ViolationMode.AUGMENT,
    conversation_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None
) -> Any:
    """Apply outbound guardrails asynchronously."""
    try:
        # Convert result to string for evaluation
        if isinstance(result, str):
            text_result = result
        else:
            text_result = str(result)
            
        # Evaluate with outbound guardrails
        evaluated_result = await _evaluate_outbound_guardrails(
            text_result, func_name, policy_set, on_violation,
            conversation_id, organization_id, project_id
        )
        
        # Return original result if it's the same as text_result, otherwise return evaluated
        if evaluated_result == text_result:
            return result
        else:
            return evaluated_result
            
    except MCPGuardrailsError:
        # Re-raise our custom exceptions with their attributes intact
        raise
    except Exception as e:
        logger.error(f"Error applying outbound guardrails to {func_name}: {e}")
        if on_violation == ViolationMode.BLOCK:
            raise MCPGuardrailsError(f"Guardrails evaluation failed for {func_name}: {e}")
        return result


@handle_errors(fail_closed=False, default_return_on_error=None)
async def _evaluate_outbound_guardrails(
    text: str,
    func_name: str,
    policy_set: Optional[PolicySet] = None,
    on_violation: str = ViolationMode.AUGMENT,
    conversation_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None
) -> str:
    """Evaluate text against outbound guardrail policies."""
    try:
        # Get guardrails engine instance
        engine = GuardrailsEngine.get_instance()
        
        # Ensure engine is initialized
        GuardrailsEngine.lazy_initialize()
        
        # Build evaluation context
        context: Dict[str, Union[str, List[str], None]] = {
            "conversation_id": conversation_id,
            "organization_id": organization_id,
            "project_id": project_id,
            "function_name": func_name,
            "direction": "outbound"
        }
        
        # Add policy filtering if custom policy set provided
        if policy_set and policy_set.get_policies():
            policy_ids: List[str] = []
            for p in policy_set.get_policies():
                policy_id = p.get("id")
                if policy_id is not None and isinstance(policy_id, str):
                    policy_ids.append(policy_id)
            context["policy_ids"] = policy_ids
        
        # Evaluate with outbound direction
        decision = await engine.evaluate(text, context, direction="outbound")
        
        logger.debug(
            f"MCP guardrails evaluation for {func_name}: allowed={decision.allowed}, "
            f"confidence={decision.confidence}, policy_id={decision.policy_id}"
        )
        
        # Handle based on violation mode
        if not decision.allowed:
            if on_violation == ViolationMode.BLOCK:
                raise MCPGuardrailsError(
                    f"Output blocked by policy {decision.policy_id}: {decision.reason}",
                    policy_id=decision.policy_id,
                    confidence=decision.confidence
                )
            elif on_violation == ViolationMode.WARN:
                logger.warning(
                    f"MCP guardrails warning for {func_name}: Policy {decision.policy_id} "
                    f"flagged output with confidence {decision.confidence}. Reason: {decision.reason}"
                )
                return text  # Return original text with warning
            elif on_violation == ViolationMode.AUGMENT:
                # For augment mode, try to get guidelines and apply them
                # This is a simplified implementation - in practice, you might want
                # to apply more sophisticated text transformation
                logger.info(
                    f"MCP guardrails augmentation for {func_name}: Policy {decision.policy_id} "
                    f"triggered. Applying guidelines."
                )
                
                # For now, return a redacted version if PII is detected
                if decision.policy_id and "pii" in decision.policy_id.lower():
                    return "[REDACTED - Sensitive information removed by MCP guardrails]"
                elif decision.policy_id and "memory_leak" in decision.policy_id.lower():
                    return "[REDACTED - Context information filtered by MCP guardrails]"
                else:
                    return "[FILTERED - Content modified by MCP guardrails]"
        
        # Return original text if allowed
        return text
        
    except MCPGuardrailsError:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in MCP guardrails evaluation: {e}")
        if on_violation == ViolationMode.BLOCK:
            raise MCPGuardrailsError(f"Guardrails evaluation failed: {e}")
        return text  # Return original text on error for augment/warn modes 