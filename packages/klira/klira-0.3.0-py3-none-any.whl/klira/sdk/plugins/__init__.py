"""Klira SDK Plugin Architecture.

This module provides a comprehensive plugin system for extending the Klira SDK
with custom adapters, guardrails components, and analytics processors.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type, List, Protocol, TypeVar, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
import logging

if TYPE_CHECKING:
    from ..adapters.base import BaseAdapter as KliraFrameworkAdapter
    from ..guardrails.llm_service import LLMServiceProtocol

    # Define AnalyticsProcessor protocol for type checking
    class AnalyticsProcessor(Protocol):
        def process_event(self, event: Dict[str, Any]) -> None: ...
        def get_metrics(self) -> Dict[str, Any]: ...


logger = logging.getLogger(__name__)

T = TypeVar("T")


class PluginStatus(Enum):
    """Plugin lifecycle status."""

    DISCOVERED = "discovered"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginMetadata:
    """Metadata for a Klira plugin."""

    name: str
    version: str
    author: str
    description: str
    sdk_version_required: str = ">=0.1.0"
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


class PluginCapability(Enum):
    """Plugin capability types."""

    FRAMEWORK_ADAPTER = "framework_adapter"
    GUARDRAILS_COMPONENT = "guardrails_component"
    ANALYTICS_PROCESSOR = "analytics_processor"
    LLM_SERVICE = "llm_service"
    POLICY_ENGINE = "policy_engine"
    STATE_MANAGER = "state_manager"


class KliraPlugin(ABC):
    """Base class for all Klira plugins.

    All plugins must inherit from this class and implement the required methods.
    """

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Plugin metadata including name, version, and dependencies."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[PluginCapability]:
        """List of capabilities this plugin provides."""
        pass

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with configuration.

        Args:
            config: Plugin-specific configuration dictionary

        Raises:
            PluginError: If initialization fails
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources when plugin is unloaded.

        This method should release any resources, close connections,
        and perform any necessary cleanup operations.
        """
        pass

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate plugin configuration.

        Args:
            config: Configuration to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        return []  # Default implementation - no validation errors

    def get_status(self) -> PluginStatus:
        """Get current plugin status."""
        return getattr(self, "_status", PluginStatus.DISCOVERED)

    def _set_status(self, status: PluginStatus) -> None:
        """Set plugin status (internal use)."""
        self._status = status


class FrameworkPlugin(KliraPlugin):
    """Plugin for custom framework adapters.

    Framework plugins provide adapters for new AI/ML frameworks
    that are not natively supported by Klira AI SDK.
    """

    @abstractmethod
    def get_adapter_class(self) -> Type["KliraFrameworkAdapter"]:
        """Return the adapter class for this framework.

        Returns:
            Adapter class that implements KliraFrameworkAdapter interface
        """
        pass

    @abstractmethod
    def detect_framework(self, obj: Any) -> bool:
        """Detect if this plugin handles the given object.

        Args:
            obj: Object to check (function, class, etc.)

        Returns:
            True if this plugin can handle the object
        """
        pass

    @abstractmethod
    def get_framework_name(self) -> str:
        """Get the name of the framework this plugin supports.

        Returns:
            Framework name (e.g., "custom_ml_framework")
        """
        pass

    def get_detection_priority(self) -> int:
        """Get detection priority (higher = checked first).

        Returns:
            Priority value (default: 100)
        """
        return 100


class GuardrailsPlugin(KliraPlugin):
    """Plugin for custom guardrails components.

    Guardrails plugins can provide custom policy engines,
    content filters, or decision makers.
    """

    @abstractmethod
    def get_component_type(self) -> str:
        """Get the type of guardrails component.

        Returns:
            Component type (e.g., "policy_engine", "content_filter")
        """
        pass

    @abstractmethod
    def create_component(self, config: Dict[str, Any]) -> Any:
        """Create an instance of the guardrails component.

        Args:
            config: Component-specific configuration

        Returns:
            Component instance
        """
        pass


class AnalyticsPlugin(KliraPlugin):
    """Plugin for custom analytics processors.

    Analytics plugins can process events, generate metrics,
    and provide custom reporting capabilities.
    """

    @abstractmethod
    def get_processor_class(self) -> Type["AnalyticsProcessor"]:
        """Return the analytics processor class.

        Returns:
            Processor class that implements AnalyticsProcessor interface
        """
        pass

    @abstractmethod
    def get_supported_events(self) -> List[str]:
        """Get list of event types this processor supports.

        Returns:
            List of event type names
        """
        pass


class LLMServicePlugin(KliraPlugin):
    """Plugin for custom LLM services.

    LLM service plugins provide integration with new LLM providers
    or custom LLM implementations.
    """

    @abstractmethod
    def get_service_class(self) -> Type["LLMServiceProtocol"]:
        """Return the LLM service class.

        Returns:
            Service class that implements LLMServiceProtocol
        """
        pass

    @abstractmethod
    def get_service_name(self) -> str:
        """Get the name of the LLM service.

        Returns:
            Service name (e.g., "custom_llm_provider")
        """
        pass


# Plugin Exceptions
class PluginError(Exception):
    """Base exception for plugin-related errors."""

    pass


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""

    pass


class PluginConfigError(PluginError):
    """Raised when plugin configuration is invalid."""

    pass


class PluginDependencyError(PluginError):
    """Raised when plugin dependencies are not met."""

    pass


# Plugin Registry Protocol
class PluginRegistryProtocol(Protocol):
    """Protocol for plugin registries."""

    def register_plugin(self, plugin: KliraPlugin) -> None:
        """Register a plugin."""
        ...

    def unregister_plugin(self, plugin_name: str) -> None:
        """Unregister a plugin."""
        ...

    def get_plugin(self, plugin_name: str) -> Optional[KliraPlugin]:
        """Get a plugin by name."""
        ...

    def get_plugins_by_capability(
        self, capability: PluginCapability
    ) -> List[KliraPlugin]:
        """Get plugins by capability."""
        ...


# Export main plugin types
__all__ = [
    "KliraPlugin",
    "FrameworkPlugin",
    "GuardrailsPlugin",
    "AnalyticsPlugin",
    "LLMServicePlugin",
    "PluginMetadata",
    "PluginCapability",
    "PluginStatus",
    "PluginError",
    "PluginLoadError",
    "PluginConfigError",
    "PluginDependencyError",
    "PluginRegistryProtocol",
]
