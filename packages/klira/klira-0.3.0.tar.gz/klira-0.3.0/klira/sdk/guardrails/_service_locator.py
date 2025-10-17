"""Service Locator for Guardrails Components.

This module provides a service locator pattern specifically designed for
guardrails components, using the DI container as the underlying mechanism.
"""

from typing import Optional, Dict, Any, TypeVar, TYPE_CHECKING
import logging
from opentelemetry.trace import Tracer

from klira.sdk._di_container import DIContainer, get_container
from klira.sdk.guardrails.llm_service import LLMServiceProtocol, DefaultLLMService

if TYPE_CHECKING:
    from klira.sdk.guardrails.fast_rules import FastRulesEngine
    from klira.sdk.guardrails.policy_augmentation import PolicyAugmentation
    from klira.sdk.guardrails.llm_fallback import LLMFallback
    from klira.sdk.guardrails.state_manager import StateManager

logger = logging.getLogger(__name__)

T = TypeVar("T")


class GuardrailsServiceLocator:
    """Service locator for guardrails components.

    This provides a focused interface for managing guardrails-specific
    dependencies while using the DI container underneath.
    """

    def __init__(self, container: Optional[DIContainer] = None):
        self._container = container or get_container()
        self._initialized = False

    def configure_defaults(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Configure default services for guardrails components.

        Args:
            config: Configuration dictionary with component settings
        """
        if self._initialized:
            logger.debug(
                "GuardrailsServiceLocator already initialized, skipping defaults"
            )
            return

        config = config or {}

        # Import here to avoid circular imports

        # Register core guardrails services
        self._register_llm_service(config)
        self._register_fast_rules(config)
        self._register_policy_augmentation(config)
        self._register_llm_fallback(config)
        self._register_state_manager(config)
        self._register_tracer()

        self._initialized = True
        logger.debug("GuardrailsServiceLocator configured with defaults")

    def _register_llm_service(self, config: Dict[str, Any]) -> None:
        """Register LLM service based on configuration."""
        llm_service = config.get("llm_service")

        # If no service provided, register default
        if llm_service is None:
            self._container.register_singleton(
                LLMServiceProtocol,  # type: ignore[type-abstract]
                DefaultLLMService(),
            )
            logger.debug("Registered DefaultLLMService")
            return

        # Handle OpenAI client
        try:
            from openai import AsyncOpenAI

            if isinstance(llm_service, AsyncOpenAI):
                from klira.sdk.guardrails.llm_service import OpenAILLMService

                wrapped_service = OpenAILLMService(client=llm_service)
                self._container.register_singleton(LLMServiceProtocol, wrapped_service)  # type: ignore[type-abstract]
                logger.debug("Registered OpenAILLMService wrapper")
                return
        except ImportError:
            pass

        # Handle protocol-compliant service
        if hasattr(llm_service, "evaluate"):
            self._container.register_singleton(LLMServiceProtocol, llm_service)
            logger.debug(f"Registered custom LLM service: {type(llm_service).__name__}")
        else:
            logger.error(
                f"Invalid LLM service type: {type(llm_service).__name__}, using default"
            )
            self._container.register_singleton(LLMServiceProtocol, DefaultLLMService())  # type: ignore[type-abstract]

    def _register_fast_rules(self, config: Dict[str, Any]) -> None:
        """Register FastRulesEngine."""
        from klira.sdk.guardrails.fast_rules import FastRulesEngine
        from klira.sdk.config import get_policies_path

        policies_path = config.get("policies_path") or get_policies_path()

        def create_fast_rules() -> FastRulesEngine:
            return FastRulesEngine(policies_path)

        self._container.register_factory(FastRulesEngine, create_fast_rules)
        logger.debug(
            f"Registered FastRulesEngine factory with policies_path: {policies_path}"
        )

    def _register_policy_augmentation(self, config: Dict[str, Any]) -> None:
        """Register PolicyAugmentation with dependency injection."""
        from klira.sdk.guardrails.policy_augmentation import PolicyAugmentation
        from klira.sdk.config import get_policies_path

        policies_path = config.get("policies_path") or get_policies_path()

        def create_policy_augmentation() -> PolicyAugmentation:
            llm_service = self._container.get(LLMServiceProtocol)  # type: ignore[type-abstract]
            return PolicyAugmentation(policies_path, llm_service)

        self._container.register_factory(PolicyAugmentation, create_policy_augmentation)
        logger.debug(
            f"Registered PolicyAugmentation factory with policies_path: {policies_path}"
        )

    def _register_llm_fallback(self, config: Dict[str, Any]) -> None:
        """Register LLMFallback with dependency injection."""
        from klira.sdk.guardrails.llm_fallback import LLMFallback

        cache_size = config.get("llm_cache_size", 1000)

        def create_llm_fallback() -> LLMFallback:
            llm_service = self._container.get(LLMServiceProtocol)  # type: ignore[type-abstract]
            return LLMFallback(llm_service, cache_size=cache_size)

        self._container.register_factory(LLMFallback, create_llm_fallback)
        logger.debug(f"Registered LLMFallback factory with cache_size: {cache_size}")

    def _register_state_manager(self, config: Dict[str, Any]) -> None:
        """Register StateManager as singleton."""
        from klira.sdk.guardrails.state_manager import StateManager

        ttl_seconds = config.get("state_ttl_seconds", 3600)
        cleanup_interval = config.get("state_cleanup_interval", 300)

        def create_state_manager() -> StateManager:
            return StateManager(
                ttl_seconds=ttl_seconds, cleanup_interval=cleanup_interval
            )

        self._container.register_factory(StateManager, create_state_manager)
        logger.debug(
            f"Registered StateManager factory with ttl: {ttl_seconds}s, cleanup: {cleanup_interval}s"
        )

    def _register_tracer(self) -> None:
        """Register OpenTelemetry tracer."""
        from opentelemetry import trace

        tracer = trace.get_tracer("klira.guardrails")
        self._container.register_singleton(Tracer, tracer)  # type: ignore[type-abstract]
        logger.debug("Registered OpenTelemetry tracer")

    def get_fast_rules(self) -> "FastRulesEngine":
        """Get FastRulesEngine instance."""
        from klira.sdk.guardrails.fast_rules import FastRulesEngine

        return self._container.get(FastRulesEngine)

    def get_policy_augmentation(self) -> "PolicyAugmentation":
        """Get PolicyAugmentation instance."""
        from klira.sdk.guardrails.policy_augmentation import PolicyAugmentation

        return self._container.get(PolicyAugmentation)

    def get_llm_fallback(self) -> "LLMFallback":
        """Get LLMFallback instance."""
        from klira.sdk.guardrails.llm_fallback import LLMFallback

        return self._container.get(LLMFallback)

    def get_state_manager(self) -> "StateManager":
        """Get StateManager instance."""
        from klira.sdk.guardrails.state_manager import StateManager

        return self._container.get(StateManager)

    def get_tracer(self) -> Tracer:
        """Get OpenTelemetry tracer instance."""
        return self._container.get(Tracer)  # type: ignore[type-abstract]

    def get_llm_service(self) -> LLMServiceProtocol:
        """Get LLM service instance."""
        return self._container.get(LLMServiceProtocol)  # type: ignore[type-abstract]

    def override_service(self, interface: type, implementation: Any) -> None:
        """Override a service registration (useful for testing).

        Args:
            interface: The interface/type to override
            implementation: The new implementation
        """
        self._container.register_singleton(interface, implementation)
        logger.debug(
            f"Overrode service {interface.__name__} with {type(implementation).__name__}"
        )

    def clear_overrides(self) -> None:
        """Clear all service overrides."""
        self._container.clear_all()
        self._initialized = False
        logger.debug("Cleared all service overrides")


# Global service locator instance
_global_service_locator: Optional[GuardrailsServiceLocator] = None


def get_service_locator() -> GuardrailsServiceLocator:
    """Get the global guardrails service locator."""
    global _global_service_locator
    if _global_service_locator is None:
        _global_service_locator = GuardrailsServiceLocator()
    return _global_service_locator


def set_service_locator(locator: GuardrailsServiceLocator) -> None:
    """Set the global service locator (useful for testing)."""
    global _global_service_locator
    _global_service_locator = locator
