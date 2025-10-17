"""The GuardrailsEngine orchestrates policy evaluation and enforcement.

It coordinates multiple guardrail components like fast rules, policy augmentation,
and LLM fallback mechanisms to process messages, check AI outputs, and augment
system prompts based on defined policies.
"""
# mypy: disable-error-code=unreachable

import uuid
import logging
import threading
import asyncio
from typing import Dict, Any, Optional, List, cast, Type

# Attempt to import OpenAI type for checking, but don't fail if not installed
try:
    from openai import AsyncOpenAI

    OPENAI_CLIENT_TYPE: Optional[Type[AsyncOpenAI]] = AsyncOpenAI
except ImportError:
    OPENAI_CLIENT_TYPE = None  # Use None as a placeholder if library isn't present

from klira.sdk.utils.error_handler import handle_errors
from klira.sdk.guardrails.fast_rules import FastRulesEngine
from klira.sdk.guardrails.policy_augmentation import PolicyAugmentation
from klira.sdk.guardrails.llm_fallback import LLMFallback
from klira.sdk.guardrails.llm_service import (
    LLMServiceProtocol,
    DefaultLLMService,
    OpenAILLMService,
)
from klira.sdk.guardrails.state_manager import StateManager
from klira.sdk.config import get_policies_path
from klira.sdk.telemetry import Telemetry

# Import decision routing functions
from .decision import route_message_decision, route_output_decision

# Import the new types
from .types import GuardrailProcessingResult, GuardrailOutputCheckResult, Decision
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, Tracer
from klira.sdk.utils.span_utils import safe_set_span_attribute

# Import dependency injection components
from klira.sdk.guardrails._service_locator import (
    GuardrailsServiceLocator,
    get_service_locator,
)

logger = logging.getLogger("klira.guardrails")


class GuardrailsEngine:
    """Main engine for Klira AI guardrails policy enforcement (Thread-safe Singleton with DI support).

    Orchestrates FastRulesEngine, PolicyAugmentation, LLMFallback, and StateManager
    to evaluate messages and AI responses against policies.

    Can be used in two modes:
    1. Singleton mode (backward compatibility) - Use GuardrailsEngine.get_instance()
    2. Dependency injection mode - Create instances with injected dependencies

    Attributes:
        fast_rules: Engine for fast, pattern-based rule checks.
        policy_augmentation: Component for augmenting prompts and matching policies.
        llm_fallback: Component for LLM-based policy evaluation.
        state_manager: Manages conversation-specific state.
        tracer: OpenTelemetry tracer instance.
    """

    _instance: Optional["GuardrailsEngine"] = None
    _lock = threading.RLock()  # Reentrant lock for thread safety
    _initialized = threading.Event()  # Thread-safe initialization flag

    def __init__(
        self,
        fast_rules: Optional[FastRulesEngine] = None,
        policy_augmentation: Optional[PolicyAugmentation] = None,
        llm_fallback: Optional[LLMFallback] = None,
        state_manager: Optional[StateManager] = None,
        tracer: Optional[Tracer] = None,
        service_locator: Optional[GuardrailsServiceLocator] = None,
        use_dependency_injection: bool = False,
    ) -> None:
        """Initialize GuardrailsEngine with optional dependency injection.

        Args:
            fast_rules: FastRulesEngine instance (optional, will be injected if None)
            policy_augmentation: PolicyAugmentation instance (optional, will be injected if None)
            llm_fallback: LLMFallback instance (optional, will be injected if None)
            state_manager: StateManager instance (optional, will be injected if None)
            tracer: OpenTelemetry tracer instance (optional, will be injected if None)
            service_locator: Service locator for dependency resolution
            use_dependency_injection: If True, use DI for missing dependencies
        """
        self._use_di = use_dependency_injection or any(
            [
                fast_rules is not None,
                policy_augmentation is not None,
                llm_fallback is not None,
                state_manager is not None,
                tracer is not None,
                service_locator is not None,
            ]
        )

        self._service_locator = service_locator or get_service_locator()

        # Initialize components - either use provided instances or DI
        if self._use_di:
            self.fast_rules = fast_rules
            self.policy_augmentation = policy_augmentation
            self.llm_fallback = llm_fallback
            self.state_manager = state_manager
            self.tracer = tracer or trace.get_tracer("klira.guardrails")
            self._di_initialized = False
        else:
            # Legacy mode - initialize to None for lazy loading
            self.fast_rules = None
            self.policy_augmentation = None
            self.llm_fallback = None
            self.state_manager = None
            self.tracer = trace.get_tracer("klira.guardrails")
            self._di_initialized = False

        # Initialize _config attribute for singleton mode
        self._config: Dict[str, Any] = {}

        logger.debug(
            f"GuardrailsEngine created (DI mode: {self._use_di}, components initialized: {self._di_initialized})"
        )

    @classmethod
    def get_instance(
        cls, config: Optional[Dict[str, Any]] = None
    ) -> "GuardrailsEngine":
        """Gets or creates the singleton GuardrailsEngine instance (thread-safe).

        Creates the singleton instance if needed, but doesn't initialize components.
        To initialize components, call initialize_components().

        Args:
            config: Optional configuration dictionary. Expected keys:
                - "policies_path" (str): Path to policies. Defaults via `get_policies_path()`.
                - "llm_service" (LLMServiceProtocol): LLM service instance.
                                Defaults to `DefaultLLMService()`.
                - "state_ttl_seconds" (int): TTL for conversation state.
                - "state_cleanup_interval" (int): Cleanup interval for state.
                - "llm_cache_size" (int): Size of LLM fallback cache.

        Returns:
            The singleton GuardrailsEngine instance.
        """
        # Double-checked locking pattern for thread safety
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls._create_singleton_instance(config or {})
                    
        return cls._instance

    @classmethod
    def _create_singleton_instance(cls, config: Dict[str, Any]) -> "GuardrailsEngine":
        """Factory method for creating singleton instances with consistent patterns."""
        instance = cls(use_dependency_injection=False)
        # Store config for later initialization
        instance._config = config
        logger.debug("Singleton GuardrailsEngine instance created")
        return instance

    @classmethod
    def create_with_di(
        cls,
        service_locator: Optional[GuardrailsServiceLocator] = None,
        fast_rules: Optional[FastRulesEngine] = None,
        policy_augmentation: Optional[PolicyAugmentation] = None,
        llm_fallback: Optional[LLMFallback] = None,
        state_manager: Optional[StateManager] = None,
        tracer: Optional[Tracer] = None,
    ) -> "GuardrailsEngine":
        """Factory method for creating DI-enabled GuardrailsEngine instances.
        
        This provides a consistent way to create DI instances separate from singleton pattern.
        
        Args:
            service_locator: Service locator for dependency resolution
            fast_rules: Pre-configured FastRulesEngine instance
            policy_augmentation: Pre-configured PolicyAugmentation instance
            llm_fallback: Pre-configured LLMFallback instance
            state_manager: Pre-configured StateManager instance
            tracer: Pre-configured OpenTelemetry tracer
            
        Returns:
            New GuardrailsEngine instance configured for dependency injection
        """
        instance = cls(
            fast_rules=fast_rules,
            policy_augmentation=policy_augmentation,
            llm_fallback=llm_fallback,
            state_manager=state_manager,
            tracer=tracer,
            service_locator=service_locator,
            use_dependency_injection=True
        )
        logger.debug("DI GuardrailsEngine instance created")
        return instance
    
    def get_component_status(self) -> Dict[str, Any]:
        """Get the current status of all components for debugging and monitoring.
        
        Returns:
            Dictionary containing component initialization status and basic info
        """
        return {
            "use_di": self._use_di,
            "di_initialized": getattr(self, "_di_initialized", False),
            "singleton_initialized": self.__class__._initialized.is_set() if hasattr(self.__class__, "_initialized") else False,
            "components": {
                "fast_rules": self.fast_rules is not None,
                "policy_augmentation": self.policy_augmentation is not None,
                "llm_fallback": self.llm_fallback is not None,
                "state_manager": self.state_manager is not None,
                "tracer": self.tracer is not None,
            },
            "service_locator": self._service_locator is not None,
            "config_keys": list(getattr(self, "_config", {}).keys())
        }
        
    def reset_for_testing(self) -> None:
        """Reset the engine state for testing purposes (not for production use)."""
        logger.warning("Resetting GuardrailsEngine state for testing - not for production use")
        
        # Reset components
        self.fast_rules = None
        self.policy_augmentation = None
        self.llm_fallback = None
        self.state_manager = None
        
        # Reset initialization flags
        self._di_initialized = False
        if hasattr(self.__class__, "_initialized"):
            self.__class__._initialized.clear()
            
        # Clear config
        self._config = {}

    @classmethod
    def lazy_initialize(cls) -> None:
        """Initialize components if not already initialized (thread-safe)."""
        instance = cls.get_instance()

        # Use the threading event for thread-safe initialization check
        if not cls._initialized.is_set():
            with cls._lock:
                if not cls._initialized.is_set():
                    logger.debug("Lazy initializing GuardrailsEngine components...")
                    if instance._use_di:
                        instance._initialize_with_di()
                    else:
                        instance._initialize_components()
                    cls._initialized.set()
                    logger.debug(
                        "GuardrailsEngine components initialized successfully."
                    )

    def _initialize_with_di(self) -> None:
        """Initialize components using dependency injection."""
        if self._di_initialized:
            return

        logger.debug(
            "Initializing GuardrailsEngine components with dependency injection..."
        )

        # Get config if available (for singleton mode)
        config = getattr(self, "_config", {})

        # Configure service locator with config
        self._service_locator.configure_defaults(config)

        try:
            # Resolve dependencies if not already provided
            if self.fast_rules is None:
                self.fast_rules = self._service_locator.get_fast_rules()

            if self.policy_augmentation is None:
                self.policy_augmentation = (
                    self._service_locator.get_policy_augmentation()
                )

            if self.llm_fallback is None:
                self.llm_fallback = self._service_locator.get_llm_fallback()

            if self.state_manager is None:
                self.state_manager = self._service_locator.get_state_manager()

            if self.tracer is None:
                self.tracer = self._service_locator.get_tracer()

            self._di_initialized = True
            logger.debug(
                "GuardrailsEngine components initialized via dependency injection"
            )

        except Exception as e:
            logger.error(f"Failed to initialize components via DI: {e}", exc_info=True)
            # Fall back to legacy initialization
            self._use_di = False
            logger.warning("Falling back to legacy component initialization due to DI failure")
            self._initialize_components()

    def _initialize_components(self) -> None:
        """Initialize components with stored config (legacy mode)."""
        logger.debug("Initializing GuardrailsEngine components (legacy mode)...")
        conf = getattr(self, "_config", {})

        policies_path = conf.get("policies_path") or get_policies_path()
        llm_service = conf.get("llm_service")
        state_ttl = conf.get("state_ttl_seconds", 3600)
        state_cleanup = conf.get("state_cleanup_interval", 300)
        llm_cache_size = conf.get("llm_cache_size", 1000)

        logger.info(f"Using policies path: {policies_path}")

        try:
            self.fast_rules = FastRulesEngine(policies_path)
        except Exception as e:
            logger.error(f"Failed to initialize FastRulesEngine: {e}", exc_info=True)
            self.fast_rules = None  # Ensure it's None on failure

        # Process the provided llm_service
        processed_llm_service: Optional[LLMServiceProtocol] = None
        if llm_service is None:
            logger.info(
                "No LLM service provided. LLM Fallback/Evaluation will use DefaultLLMService."
            )
            processed_llm_service = DefaultLLMService()
        # Check if openai library is available and the service is an instance of its client
        elif OPENAI_CLIENT_TYPE is not None and isinstance(
            llm_service, OPENAI_CLIENT_TYPE
        ):
            logger.info(
                "Provided service is AsyncOpenAI client. Wrapping with OpenAILLMService."
            )
            processed_llm_service = OpenAILLMService(client=llm_service)
        # Otherwise, check if the provided object adheres to the protocol
        elif hasattr(llm_service, "evaluate"):
            logger.info(
                f"Using provided LLM service directly: {type(llm_service).__name__}"
            )
            processed_llm_service = cast(LLMServiceProtocol, llm_service)
        # If none of the above, use the default service
        else:
            logger.error(
                f"Provided llm_service ({type(llm_service).__name__}) is not a supported type (e.g., openai.AsyncOpenAI) and does not have an 'evaluate' method. Using DefaultLLMService."
            )
            processed_llm_service = DefaultLLMService()

        # Ensure processed_llm_service is not None (should always be assigned by logic above)
        if processed_llm_service is None:
            logger.error(
                "LLM service processing failed unexpectedly. Using DefaultLLMService."
            )
            processed_llm_service = DefaultLLMService()

        # Use the processed service for components
        try:
            # PolicyAugmentation needs the service
            self.policy_augmentation = PolicyAugmentation(
                policies_path, processed_llm_service
            )
        except Exception as e:
            logger.error(f"Failed to initialize PolicyAugmentation: {e}", exc_info=True)
            self.policy_augmentation = None

        try:
            self.llm_fallback = LLMFallback(
                processed_llm_service, cache_size=llm_cache_size
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLMFallback: {e}", exc_info=True)
            self.llm_fallback = None

        try:
            self.state_manager = StateManager(
                ttl_seconds=state_ttl, cleanup_interval=state_cleanup
            )
        except Exception as e:
            logger.error(f"Failed to initialize StateManager: {e}", exc_info=True)
            self.state_manager = None

        # Ensure tracer exists (already set in __init__, but double-check)
        if self.tracer is None:
            self.tracer = trace.get_tracer("klira.guardrails")

        logger.debug("GuardrailsEngine components initialized (legacy mode).")

    async def _initialize_components_async(self) -> None:
        """Async version of component initialization for better performance."""
        logger.debug("Initializing GuardrailsEngine components (async mode)...")
        conf = getattr(self, "_config", {})

        policies_path = conf.get("policies_path") or get_policies_path()
        llm_service = conf.get("llm_service")
        state_ttl = conf.get("state_ttl_seconds", 3600)
        state_cleanup = conf.get("state_cleanup_interval", 300)
        llm_cache_size = conf.get("llm_cache_size", 1000)

        logger.info(f"Using policies path: {policies_path}")

        # Initialize components concurrently where possible
        initialization_tasks = []

        # FastRulesEngine initialization (run in executor for better performance)
        async def init_fast_rules() -> None:
            try:
                loop = asyncio.get_event_loop()
                self.fast_rules = await loop.run_in_executor(
                    None, lambda: FastRulesEngine(policies_path)
                )
            except Exception as e:
                logger.error(f"Failed to initialize FastRulesEngine: {e}", exc_info=True)
                self.fast_rules = None

        initialization_tasks.append(init_fast_rules())

        # Process LLM service (mostly sync but prepare for future async improvements)
        processed_llm_service = await self._process_llm_service_async(llm_service)

        # Wait for FastRules to complete
        await asyncio.gather(*initialization_tasks, return_exceptions=True)

        # Initialize remaining components
        try:
            self.policy_augmentation = PolicyAugmentation(
                policies_path, processed_llm_service
            )
        except Exception as e:
            logger.error(f"Failed to initialize PolicyAugmentation: {e}", exc_info=True)
            self.policy_augmentation = None

        try:
            self.llm_fallback = LLMFallback(
                processed_llm_service, cache_size=llm_cache_size
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLMFallback: {e}", exc_info=True)
            self.llm_fallback = None

        try:
            self.state_manager = StateManager(
                ttl_seconds=state_ttl, cleanup_interval=state_cleanup
            )
        except Exception as e:
            logger.error(f"Failed to initialize StateManager: {e}", exc_info=True)
            self.state_manager = None

        # Ensure tracer exists
        if self.tracer is None:
            self.tracer = trace.get_tracer("klira.guardrails")

        logger.debug("GuardrailsEngine components initialized (async mode).")

    async def _process_llm_service_async(
        self, llm_service: Optional["LLMServiceProtocol"]
    ) -> Optional["LLMServiceProtocol"]:
        """Process the provided LLM service asynchronously."""
        processed_llm_service: Optional[LLMServiceProtocol] = None
        
        if llm_service is None:
            logger.info(
                "No LLM service provided. LLM Fallback/Evaluation will use DefaultLLMService."
            )
            processed_llm_service = DefaultLLMService()
        elif OPENAI_CLIENT_TYPE is not None and isinstance(
            llm_service, OPENAI_CLIENT_TYPE
        ):
            logger.info(
                "Provided service is AsyncOpenAI client. Wrapping with OpenAILLMService."
            )
            processed_llm_service = OpenAILLMService(client=llm_service)
        elif hasattr(llm_service, "evaluate"):
            logger.info(
                f"Using provided LLM service directly: {type(llm_service).__name__}"
            )
            processed_llm_service = llm_service
        else:
            logger.error(
                f"Provided llm_service ({type(llm_service).__name__}) is not a supported type "
                f"and does not have an 'evaluate' method. Using DefaultLLMService."
            )
            processed_llm_service = DefaultLLMService()

        if processed_llm_service is None:
            logger.error(
                "LLM service processing failed unexpectedly. Using DefaultLLMService."
            )
            processed_llm_service = DefaultLLMService()

        return processed_llm_service

    def _ensure_initialized(self) -> None:
        """Ensure components are initialized (works for both DI and legacy modes)."""
        if self._use_di and not self._di_initialized:
            self._initialize_with_di()
        elif not self._use_di:
            # For singleton mode, use lazy_initialize
            GuardrailsEngine.lazy_initialize()

    async def _ensure_initialized_async(self) -> None:
        """Async version of _ensure_initialized for better performance in async contexts."""
        if self._use_di and not self._di_initialized:
            self._initialize_with_di()
        elif not self._use_di:
            # For singleton mode, use async lazy initialization if not already initialized
            if not GuardrailsEngine._initialized.is_set():
                with GuardrailsEngine._lock:
                    if not GuardrailsEngine._initialized.is_set():
                        logger.debug("Async lazy initializing GuardrailsEngine components...")
                        if hasattr(self, '_initialize_components_async'):
                            await self._initialize_components_async()
                        else:
                            # Fallback to sync initialization in executor
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(None, self._initialize_components)
                        GuardrailsEngine._initialized.set()
                        logger.debug("GuardrailsEngine async initialization completed.")

    # This internal method is only used by augment_system_prompt, which might be refactored.
    # Keep it for now, ensure type hints are correct based on PolicyAugmentation method.
    @handle_errors(fail_closed=False, default_return_on_error=None)
    def _get_augmentation_guidelines(self, message: str) -> Optional[List[str]]:
        """Internal helper to get guidelines by matching policies.

        Delegates to PolicyAugmentation._match_policies and _extract_guidelines.
        Returns None if PolicyAugmentation is unavailable or an error occurs.
        """
        # Ensure components are initialized (sync version for backward compatibility)
        self._ensure_initialized()

        if not self.policy_augmentation:
            logger.warning(
                "_get_augmentation_guidelines called but PolicyAugmentation not initialized."
            )
            return None

        matched = self.policy_augmentation._match_policies(message)
        return self.policy_augmentation._extract_guidelines(matched)

    async def _get_augmentation_guidelines_async(self, message: str) -> Optional[List[str]]:
        """Async version of _get_augmentation_guidelines for better performance."""
        # Ensure components are initialized (async version)
        await self._ensure_initialized_async()

        if not self.policy_augmentation:
            logger.warning(
                "_get_augmentation_guidelines_async called but PolicyAugmentation not initialized."
            )
            return None

        matched = self.policy_augmentation._match_policies(message)
        return self.policy_augmentation._extract_guidelines(matched)

    @classmethod
    def get_current_guidelines(cls, conversation_id: Optional[str] = None) -> List[str]:
        """
        Get guidelines from the current OpenTelemetry context or persistent cache.

        Args:
            conversation_id: Optional conversation ID to look up guidelines in cache

        Returns:
            List of guideline strings, or empty list if none found.
        """
        try:
            # First try OpenTelemetry context
            try:
                from opentelemetry import context as otel_context

                current_ctx = otel_context.get_current()
                guidelines = otel_context.get_value(
                    "klira.augmentation.guidelines", current_ctx
                )
                if guidelines is not None and isinstance(guidelines, list):
                    return guidelines
            except ImportError:
                pass  # OpenTelemetry not available

            # If not found in OTel context and conversation_id provided, try cache
            if conversation_id:
                try:
                    from .decision import _get_guidelines_from_cache

                    cached_guidelines = _get_guidelines_from_cache(conversation_id)
                    if cached_guidelines:
                        return cached_guidelines
                except ImportError:
                    pass  # Cache not available

            return []
        except Exception as e:
            print(f"[Klira AI] Error retrieving guidelines: {e}")
            return []

    @classmethod
    def clear_current_guidelines(cls) -> None:
        """
        Clear guidelines from the current OpenTelemetry context.
        """
        try:
            # Import here to avoid circular imports
            try:
                from opentelemetry import context as otel_context
            except ImportError:
                return

            current_ctx = otel_context.get_current()
            # Create a new context without the guidelines
            # Setting to None effectively removes the value
            new_ctx = otel_context.set_value(
                "klira.augmentation.guidelines", None, current_ctx
            )
            otel_context.attach(new_ctx)
        except Exception as e:
            print(f"[Klira AI] Error clearing guidelines from context: {e}")

    @handle_errors(
        fail_closed=False,
        default_return_on_error=GuardrailProcessingResult(
            allowed=False,
            confidence=1.0,
            decision_layer="error",
            error="Guardrails processing failed",
            violated_policies=[],
            blocked_reason="Guardrails internal error",
        ),
    )
    async def process_message(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> GuardrailProcessingResult:
        """Processes a user message using the configured guardrail decision logic.

        Orchestrates context setup, tracing, calling the decision router,
        and handling state/telemetry based on the decision.

        Args:
            message: The user message string to evaluate.
            context: Optional dictionary containing context (e.g., conversation_id).

        Returns:
            A GuardrailProcessingResult dictionary summarizing the outcome.
        """
        # Automatic performance instrumentation
        try:
            from klira.sdk.performance import timed_operation

            with timed_operation(
                "process_message", "guardrails", {"message_length": str(len(message))}
            ):
                return await self._process_message_internal(message, context)
        except ImportError:
            # Fallback if performance module not available
            return await self._process_message_internal(message, context)

    async def _process_message_internal(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> GuardrailProcessingResult:
        """Internal process_message method (extracted for performance instrumentation)."""
        # Ensure components are initialized (async for better performance)
        await self._ensure_initialized_async()

        if not self.tracer or not self.state_manager or not self.fast_rules:
            logger.error(
                "GuardrailsEngine core components missing. Cannot process message."
            )
            raise RuntimeError("GuardrailsEngine core components not initialized.")

        context = context or {}
        conversation_id = context.get("conversation_id") or str(uuid.uuid4())
        context["conversation_id"] = conversation_id  # Ensure it's present
        state = self.state_manager.get_state(conversation_id)
        context["state"] = state

        with self.tracer.start_as_current_span(
            "klira.guardrails.process_message"
        ) as span:
            safe_set_span_attribute(span, "conversation.id", conversation_id)
            safe_set_span_attribute(span, "input.message.length", len(message))

            # --- Call Decision Router ---
            # Delegate the core logic to the decision module
            final_result = await route_message_decision(
                message=message,
                context=context,
                fast_rules_engine=self.fast_rules,
                augmentation_engine=self.policy_augmentation,
                llm_fallback_engine=self.llm_fallback,
            )

            # Guidelines are now stored in the decision router when policies are matched
            # No need to duplicate the logic here

            # --- Finalization (Tracing, State, Telemetry) ---
            safe_set_span_attribute(
                span, "decision.layer", final_result["decision_layer"]
            )
            safe_set_span_attribute(span, "decision.allowed", final_result["allowed"])
            safe_set_span_attribute(
                span, "decision.confidence", final_result["confidence"]
            )
            # Add results from individual layers to span if present in final_result
            if fr_res := final_result.get("fast_rules_result"):
                safe_set_span_attribute(
                    span, "guardrails.fast_rules.allowed", fr_res["allowed"]
                )
                safe_set_span_attribute(
                    span, "guardrails.fast_rules.confidence", fr_res["confidence"]
                )
            if aug_res := final_result.get("augmentation_result"):
                safe_set_span_attribute(
                    span,
                    "guardrails.augmentation.matched_policies",
                    [p["id"] for p in aug_res.get("matched_policies", [])],
                )
            if llm_res := final_result.get("llm_evaluation_result"):
                safe_set_span_attribute(
                    span, "guardrails.llm.allowed", llm_res["allowed"]
                )
                safe_set_span_attribute(
                    span, "guardrails.llm.confidence", llm_res["confidence"]
                )
                safe_set_span_attribute(
                    span, "guardrails.llm.action", llm_res.get("action")
                )

            if final_result["allowed"]:
                span.set_status(StatusCode.OK)
            else:
                # Set span status based on reason/layer
                desc = final_result.get(
                    "blocked_reason", f"Blocked by {final_result['decision_layer']}"
                )
                span.set_status(Status(StatusCode.ERROR, description=desc))

            # Update state based on final decision
            state_update: Dict[str, Any] = {}
            if not final_result["allowed"] and (
                violated := final_result.get("violated_policies")
            ):
                state_update["policy_violations"] = [
                    {
                        "policy_id": pid,
                        "layer": final_result["decision_layer"],
                        "confidence": final_result["confidence"],
                    }
                    for pid in violated
                ]
            if state_update:
                self.state_manager.update_state(conversation_id, state_update)

            # Capture telemetry for the final decision
            Telemetry().capture(
                "guardrails.decision",
                {
                    "layer": final_result["decision_layer"],
                    "allowed": final_result["allowed"],
                    "confidence": final_result["confidence"],
                    "conversation_id": conversation_id,
                    "violated_policies": final_result.get("violated_policies", []),
                },
            )

            # Capture analytics events for blocked messages and policy violations
            try:
                from klira.sdk.analytics import track_event, EventType
                import hashlib

                # Generate privacy-safe message hash
                message_hash = hashlib.sha256(message.encode("utf-8")).hexdigest()[:16]

                if not final_result["allowed"]:
                    # Track blocked message event
                    track_event(
                        EventType.GUARDRAILS_BLOCKED,
                        data={
                            "message_hash": message_hash,
                            "decision_layer": final_result["decision_layer"],
                            "confidence": final_result["confidence"],
                            "violated_policies": final_result.get(
                                "violated_policies", []
                            ),
                            "blocked_reason": final_result.get("blocked_reason"),
                        },
                        conversation_id=conversation_id,
                        organization_id=context.get("organization_id"),
                        project_id=context.get("project_id"),
                    )

                    # Track policy violation events for each violated policy
                    violated_policies = final_result.get("violated_policies") or []
                    for policy_id in violated_policies:
                        track_event(
                            EventType.POLICY_VIOLATED,
                            data={
                                "policy_id": policy_id,
                                "decision_layer": final_result["decision_layer"],
                                "confidence": final_result["confidence"],
                                "message_hash": message_hash,
                                "action": "block",
                            },
                            conversation_id=conversation_id,
                            organization_id=context.get("organization_id"),
                            project_id=context.get("project_id"),
                        )
                else:
                    # Track allowed message event
                    track_event(
                        EventType.GUARDRAILS_ALLOWED,
                        data={
                            "message_hash": message_hash,
                            "decision_layer": final_result["decision_layer"],
                            "confidence": final_result["confidence"],
                        },
                        conversation_id=conversation_id,
                    )

            except ImportError:
                # Analytics not available, continue without it
                logger.debug("Analytics module not available for event tracking")
            except Exception as e:
                # Don't fail the guardrails decision if analytics fails
                logger.warning(f"Failed to track analytics events: {e}")

            return final_result

    @handle_errors(
        fail_closed=False,
        default_return_on_error=GuardrailOutputCheckResult(
            allowed=False,
            confidence=1.0,
            decision_layer="error",
            error="Guardrails output check failed",
            violated_policies=[],
            blocked_reason="Guardrails internal error",
        ),
    )
    async def check_output(
        self, ai_response: str, context: Optional[Dict[str, Any]] = None
    ) -> GuardrailOutputCheckResult:
        """Evaluates an AI-generated response using the configured guardrail decision logic.

        Orchestrates context setup, tracing, calling the decision router for output,
        and handling state/telemetry based on the decision.

        Args:
            ai_response: The AI-generated text response string.
            context: Optional dictionary containing context (e.g., conversation_id).

        Returns:
            A GuardrailOutputCheckResult dictionary summarizing the outcome.
        """
        # Ensure components are initialized (async for better performance)
        await self._ensure_initialized_async()

        if not self.tracer or not self.state_manager or not self.fast_rules:
            logger.error(
                "GuardrailsEngine core components missing. Cannot check output."
            )
            raise RuntimeError("GuardrailsEngine core components not initialized.")

        context = context or {}
        conversation_id = context.get("conversation_id") or str(uuid.uuid4())
        context["conversation_id"] = conversation_id
        state = self.state_manager.get_state(conversation_id)
        context["state"] = state

        with self.tracer.start_as_current_span("klira.guardrails.check_output") as span:
            safe_set_span_attribute(span, "conversation.id", conversation_id)
            safe_set_span_attribute(span, "output.response.length", len(ai_response))

            # --- Call Decision Router for Output ---
            final_result = await route_output_decision(
                ai_response=ai_response,
                context=context,
                fast_rules_engine=self.fast_rules,
                llm_fallback_engine=self.llm_fallback,
            )

            # --- Finalization (Tracing, State, Telemetry) ---
            safe_set_span_attribute(
                span, "decision.layer", final_result["decision_layer"]
            )
            safe_set_span_attribute(span, "decision.allowed", final_result["allowed"])
            safe_set_span_attribute(
                span, "decision.confidence", final_result["confidence"]
            )
            if fr_res := final_result.get("fast_rules_result"):
                safe_set_span_attribute(
                    span, "guardrails.fast_rules.allowed", fr_res["allowed"]
                )
                safe_set_span_attribute(
                    span, "guardrails.fast_rules.confidence", fr_res["confidence"]
                )
            if llm_res := final_result.get("llm_evaluation_result"):
                safe_set_span_attribute(
                    span, "guardrails.llm.allowed", llm_res["allowed"]
                )
                safe_set_span_attribute(
                    span, "guardrails.llm.confidence", llm_res["confidence"]
                )
                safe_set_span_attribute(
                    span, "guardrails.llm.action", llm_res.get("action")
                )

            if final_result["allowed"]:
                span.set_status(StatusCode.OK)
            else:
                desc = final_result.get(
                    "blocked_reason",
                    f"Output blocked by {final_result['decision_layer']}",
                )
                span.set_status(Status(StatusCode.ERROR, description=desc))

            # Capture analytics events for output checks
            try:
                from klira.sdk.analytics import track_event, EventType
                import hashlib

                # Generate privacy-safe response hash
                response_hash = hashlib.sha256(ai_response.encode("utf-8")).hexdigest()[
                    :16
                ]

                track_event(
                    EventType.GUARDRAILS_OUTPUT_CHECKED,
                    data={
                        "response_hash": response_hash,
                        "decision_layer": final_result["decision_layer"],
                        "confidence": final_result["confidence"],
                        "allowed": final_result["allowed"],
                        "violated_policies": final_result.get("violated_policies", []),
                    },
                    conversation_id=conversation_id,
                    organization_id=context.get("organization_id"),
                    project_id=context.get("project_id"),
                )

                if not final_result["allowed"]:
                    # Track policy violations for blocked outputs
                    violated_policies = final_result.get("violated_policies") or []
                    for policy_id in violated_policies:
                        track_event(
                            EventType.POLICY_VIOLATED,
                            data={
                                "policy_id": policy_id,
                                "decision_layer": final_result["decision_layer"],
                                "confidence": final_result["confidence"],
                                "response_hash": response_hash,
                                "action": "block",
                                "check_type": "output",
                            },
                            conversation_id=conversation_id,
                            organization_id=context.get("organization_id"),
                            project_id=context.get("project_id"),
                        )

            except ImportError:
                logger.debug("Analytics module not available for output check tracking")
            except Exception as e:
                logger.warning(f"Failed to track output check analytics: {e}")

            return final_result

    @handle_errors(
        fail_closed=True,
        default_return_on_error=Decision(
            allowed=False, reason="Guardrail evaluation failed due to an internal error"
        ),
    )
    async def evaluate(
        self, input_text: str, context: Optional[Dict[str, Any]] = None, direction: str = "inbound"
    ) -> Decision:
        """
        Evaluate input text against guardrail policies for framework adapters.

        This is a simplified interface for external adapters to use, which returns
        a Decision object rather than the more complex GuardrailProcessingResult.

        Args:
            input_text: The text to evaluate against policies
            context: Optional dictionary with context information
            direction: Direction of the evaluation ("inbound" or "outbound")

        Returns:
            Decision object indicating whether the input is allowed
        """
        span = self.tracer.start_span("klira.guardrails.evaluate")
        safe_set_span_attribute(span, "input.length", len(input_text))
        safe_set_span_attribute(span, "guardrails.direction", direction)

        try:
            # Ensure we have a context dictionary
            ctx = context or {}
            conversation_id = ctx.get("conversation_id", str(uuid.uuid4()))
            safe_set_span_attribute(span, "conversation_id", conversation_id)

            # Add direction to context for downstream processing
            ctx["direction"] = direction

            # Process the message using the full guardrail logic
            if direction == "outbound":
                # For outbound evaluation, use check_output logic
                result = await self.check_output(input_text, ctx)
            else:
                # For inbound evaluation, use process_message logic
                result = await self.process_message(input_text, ctx)

            # Extract the essential decision information
            allowed = result.get("allowed", False)
            confidence = result.get("confidence", 1.0)
            blocked_reason = result.get("blocked_reason")

            # Get the policy ID if available
            policy_id = None
            violated_policies = result.get("violated_policies", [])
            if violated_policies and len(violated_policies) > 0:
                policy_id = violated_policies[0]

            # Create and return a Decision object
            decision = Decision(
                allowed=allowed,
                reason=blocked_reason,
                policy_id=policy_id,
                confidence=confidence,
            )

            # Set span attributes for the decision
            safe_set_span_attribute(span, "decision.allowed", decision.allowed)
            if decision.reason:
                safe_set_span_attribute(span, "decision.reason", decision.reason)
            if decision.policy_id:
                safe_set_span_attribute(span, "decision.policy_id", decision.policy_id)

            return decision
        finally:
            span.end()

    @handle_errors(
        fail_closed=False, default_return_on_error=None
    )  # Returns None on error means original prompt is returned by logic below
    async def augment_system_prompt(
        self, system_prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Augments a system prompt based on context or message content.

        Matches policies against the context (e.g., a sample message if provided)
        and injects guidelines into the system prompt.

        Args:
            system_prompt: The original system prompt string.
            context: Optional dictionary. Expected keys:
                - "message_for_guideline_matching" (str): A representative message
                  to determine which policy guidelines are relevant.

        Returns:
            The augmented system prompt string, or the original if augmentation fails
            or no guidelines are found.
        """
        if not self.policy_augmentation:
            logger.warning(
                "augment_system_prompt called but PolicyAugmentation not initialized."
            )
            return system_prompt

        context = context or {}
        message_for_matching = context.get("message_for_guideline_matching")

        if not message_for_matching or not isinstance(message_for_matching, str):
            logger.debug(
                "No message provided in context for guideline matching. Cannot augment prompt."
            )
            return system_prompt

        # Match policies based on the provided message
        matched_policies = self.policy_augmentation._match_policies(
            message_for_matching
        )
        if not matched_policies:
            logger.debug(
                "No policies matched the provided message. Returning original prompt."
            )
            return system_prompt

        # Create messages list in the format expected by augment_prompt
        messages = [{"role": "system", "content": system_prompt}]

        # Delegate actual augmentation to the component
        # The decorator handles errors, returning the *original* prompt on failure.
        augmented_messages = await self.policy_augmentation.augment_prompt(
            messages, context
        )

        # Extract the augmented system prompt
        if augmented_messages and len(augmented_messages) > 0:
            return augmented_messages[0].get("content", system_prompt)

        return system_prompt
