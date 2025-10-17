"""
Registry for LLM framework and LLM client adapters.
Provides central registries for both types of adapters with lazy loading and memory management.
Enhanced with plugin system integration for extensible adapter discovery.
"""

import logging
import threading
import weakref
import time
from typing import Dict, Optional, Type, Callable, List, TYPE_CHECKING, Any, cast

# Moved E402 imports to be before other module-level code
from klira.sdk.adapters.framework_adapter import KliraFrameworkAdapter
from klira.sdk.adapters.llm_base_adapter import BaseLLMAdapter  # Import LLM base
from klira.sdk.utils.framework_detection import (
    detect_framework_cached as detect_framework,
)
from klira.sdk._lazy_imports import LAZY_FRAMEWORK_ADAPTERS, LAZY_LLM_ADAPTERS

# Plugin system imports with fallback
if TYPE_CHECKING:
    from klira.sdk.plugins.manager import PluginManager, get_global_plugin_manager
    from klira.sdk.plugins import PluginCapability

    PluginManagerType = PluginManager
    GetGlobalPluginManagerType = get_global_plugin_manager
    PluginCapabilityType = PluginCapability
    PLUGINS_AVAILABLE = True
else:
    try:
        from klira.sdk.plugins.manager import get_global_plugin_manager
        from klira.sdk.plugins import PluginCapability

        GetGlobalPluginManagerType = get_global_plugin_manager
        PluginCapabilityType = PluginCapability
        PLUGINS_AVAILABLE = True
    except ImportError:
        PLUGINS_AVAILABLE = False
        GetGlobalPluginManagerType = None  # type: ignore
        PluginCapabilityType = None  # type: ignore

logger = logging.getLogger("klira.utils.framework_registry")



class FrameworkRegistry:
    """
    Registry for LLM framework adapters (e.g., LangChain, Agents SDK) with memory management.
    Uses weak references to prevent memory leaks and lazy loading for better performance.
    Enhanced with plugin system integration for extensible framework support.
    """

    _adapter_classes: Dict[str, Type[KliraFrameworkAdapter]] = {}
    _adapter_instances: "weakref.WeakValueDictionary[str, KliraFrameworkAdapter]" = (
        weakref.WeakValueDictionary()
    )
    _lock = threading.RLock()
    _last_cleanup = time.time()
    _cleanup_interval = 300  # 5 minutes
    _plugin_integration_enabled = PLUGINS_AVAILABLE

    @classmethod
    def register_adapter(
        cls, framework_name: str, adapter_instance: KliraFrameworkAdapter
    ) -> None:
        """Register a framework adapter INSTANCE for a given framework name."""

        with cls._lock:
            cls._adapter_instances[framework_name] = adapter_instance
            # Also store the class type for reference
            cls._adapter_classes[framework_name] = type(adapter_instance)
            cls._schedule_cleanup_if_needed()

        logger.debug(
            f"Registered framework adapter instance {type(adapter_instance).__name__} for framework {framework_name}"
        )

    @classmethod
    def _schedule_cleanup_if_needed(cls) -> None:
        """Schedule cleanup if enough time has passed."""
        current_time = time.time()
        if current_time - cls._last_cleanup > cls._cleanup_interval:
            cls._cleanup_expired_references()
            cls._last_cleanup = current_time

    @classmethod
    def _cleanup_expired_references(cls) -> None:
        """Clean up expired weak references (called automatically)."""
        # WeakValueDictionary automatically removes expired references,
        # but we can force cleanup of the class registry as well
        expired_frameworks = []
        for framework_name in cls._adapter_classes:
            if framework_name not in cls._adapter_instances:
                expired_frameworks.append(framework_name)

        for framework_name in expired_frameworks:
            del cls._adapter_classes[framework_name]
            logger.debug(
                f"Cleaned up expired adapter class reference for {framework_name}"
            )

    @classmethod
    def cleanup_all(cls) -> None:
        """Manually cleanup all expired references."""
        with cls._lock:
            cls._cleanup_expired_references()

    @classmethod
    def get_adapter_class(
        cls, framework_name: str
    ) -> Optional[Type[KliraFrameworkAdapter]]:
        """
        Get the adapter CLASS for a framework.
        Enhanced with plugin system integration.
        """
        # First check registered classes
        adapter_class = cls._adapter_classes.get(framework_name)
        if adapter_class:
            return adapter_class

        # Try plugin system if available
        if cls._plugin_integration_enabled:
            try:
                plugin_manager = GetGlobalPluginManagerType()
                plugin_adapter_class = plugin_manager.get_framework_adapter(
                    framework_name
                )
                if plugin_adapter_class:
                    logger.debug(
                        f"Found framework adapter for {framework_name} via plugin system"
                    )
                    return plugin_adapter_class
            except Exception as e:
                logger.warning(
                    f"Error getting framework adapter from plugins for {framework_name}: {e}"
                )

        return None

    @classmethod
    def get_adapter(cls, framework_name: str) -> Optional[KliraFrameworkAdapter]:
        """
        Get a pre-existing adapter INSTANCE for a framework.
        If not found, attempts to lazily load and instantiate it.
        Enhanced with plugin system integration.
        """
        with cls._lock:
            # First check if we have an existing instance
            instance = cls._adapter_instances.get(framework_name)
            if instance is not None:
                return instance

            # Try to lazily load and create the adapter from built-in adapters
            lazy_adapter = LAZY_FRAMEWORK_ADAPTERS.get(framework_name)
            if lazy_adapter and lazy_adapter.is_available():
                try:
                    adapter_class = lazy_adapter.get_class()
                    if adapter_class:
                        instance = adapter_class()
                        cls.register_adapter(framework_name, instance)
                        logger.debug(
                            f"Lazily loaded and registered {framework_name} adapter"
                        )
                        return cast(Optional[KliraFrameworkAdapter], instance)
                except Exception as e:
                    logger.error(
                        f"Failed to lazily instantiate {framework_name} adapter: {e}"
                    )

            # Try plugin system if available
            if cls._plugin_integration_enabled:
                try:
                    plugin_manager = GetGlobalPluginManagerType()
                    plugin_adapter_class = plugin_manager.get_framework_adapter(
                        framework_name
                    )
                    if plugin_adapter_class:
                        instance = plugin_adapter_class()
                        if instance is not None:
                            cls.register_adapter(framework_name, instance)
                            logger.info(
                                f"Loaded framework adapter for {framework_name} from plugin system"
                            )
                            return cast(Optional[KliraFrameworkAdapter], instance)
                except Exception as e:
                    logger.warning(
                        f"Failed to load framework adapter from plugins for {framework_name}: {e}"
                    )

            logger.debug(
                f"No framework adapter instance found for framework {framework_name}"
            )
            return None

    @classmethod
    def get_adapter_instance_for_function(
        cls, func: Callable[..., Any]
    ) -> Optional[KliraFrameworkAdapter]:
        """
        Detects the framework for a function and returns the corresponding registered adapter instance.
        Enhanced with plugin system integration for framework detection.
        """
        framework_name = detect_framework(func)

        # If built-in detection failed (returned "standard"), try plugin-based detection
        if framework_name == "standard" and cls._plugin_integration_enabled:
            try:
                plugin_manager = GetGlobalPluginManagerType()
                for (
                    plugin_name,
                    framework_plugin,
                ) in plugin_manager.framework_plugins.items():
                    try:
                        if framework_plugin.detect_framework(func):
                            framework_name = framework_plugin.get_framework_name()
                            logger.debug(
                                f"Plugin {plugin_name} detected framework {framework_name} for function {getattr(func, '__name__', 'unknown')}"
                            )
                            break
                    except Exception as e:
                        logger.warning(
                            f"Error in plugin framework detection for {plugin_name}: {e}"
                        )
            except Exception as e:
                logger.warning(
                    f"Error accessing plugin manager for framework detection: {e}"
                )

        if framework_name == "standard":
            logger.debug(
                f"Could not detect framework for function {getattr(func, '__name__', 'unknown')}. Cannot get framework adapter."
            )
            return None

        logger.debug(
            f"Detected framework '{framework_name}' for function {getattr(func, '__name__', 'unknown')}. Getting framework adapter instance."
        )
        adapter_instance = cls.get_adapter(framework_name)
        if adapter_instance is None:
            logger.warning(
                f"Framework adapter instance for detected framework '{framework_name}' not found in registry."
            )

        return adapter_instance

    @classmethod
    def get_all_framework_names(cls) -> List[str]:
        """Get names of all registered frameworks, including plugin-provided ones."""
        framework_names = set(cls._adapter_instances.keys())

        # Add plugin-provided frameworks
        if cls._plugin_integration_enabled:
            try:
                plugin_manager = GetGlobalPluginManagerType()
                framework_names.update(plugin_manager.framework_plugins.keys())
            except Exception as e:
                logger.warning(f"Error getting plugin framework names: {e}")

        return list(framework_names)

    @classmethod
    def get_all_adapter_instances(cls) -> Dict[str, KliraFrameworkAdapter]:
        """Get all registered adapter instances."""
        with cls._lock:
            return dict(cls._adapter_instances)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered frameworks."""
        with cls._lock:
            cls._adapter_classes.clear()
            cls._adapter_instances.clear()
            logger.debug("Cleared all registered framework adapters")

    @classmethod
    def enable_plugin_integration(cls) -> None:
        """Enable plugin system integration."""
        if PLUGINS_AVAILABLE:
            cls._plugin_integration_enabled = True
            logger.info("Plugin integration enabled for FrameworkRegistry")
        else:
            logger.warning(
                "Cannot enable plugin integration: Plugin system not available"
            )

    @classmethod
    def disable_plugin_integration(cls) -> None:
        """Disable plugin system integration."""
        cls._plugin_integration_enabled = False
        logger.info("Plugin integration disabled for FrameworkRegistry")



class LLMClientRegistry:
    """
    Registry for LLM client adapters (e.g., OpenAI, Anthropic) with memory management.
    Used specifically for patching LLM API calls for augmentation.
    """

    _llm_adapter_instances: "weakref.WeakValueDictionary[str, BaseLLMAdapter]" = (
        weakref.WeakValueDictionary()
    )
    _llm_adapter_classes: Dict[str, Type[BaseLLMAdapter]] = {}
    _lock = threading.RLock()
    _last_cleanup = time.time()
    _cleanup_interval = 300  # 5 minutes

    @classmethod
    def register_llm_adapter(
        cls, llm_name: str, adapter_instance: BaseLLMAdapter
    ) -> None:
        """Register an LLM client adapter instance."""

        with cls._lock:
            cls._llm_adapter_instances[llm_name] = adapter_instance
            cls._llm_adapter_classes[llm_name] = type(adapter_instance)
            cls._schedule_cleanup_if_needed()
        logger.debug(
            f"Registered LLM client adapter instance {type(adapter_instance).__name__} for {llm_name}"
        )

    @classmethod
    def _schedule_cleanup_if_needed(cls) -> None:
        """Schedule cleanup if enough time has passed."""
        current_time = time.time()
        if current_time - cls._last_cleanup > cls._cleanup_interval:
            cls._cleanup_expired_references()
            cls._last_cleanup = current_time

    @classmethod
    def _cleanup_expired_references(cls) -> None:
        """Clean up expired weak references."""
        expired_llms = []
        for llm_name in cls._llm_adapter_classes:
            if llm_name not in cls._llm_adapter_instances:
                expired_llms.append(llm_name)

        for llm_name in expired_llms:
            del cls._llm_adapter_classes[llm_name]
            logger.debug(
                f"Cleaned up expired LLM adapter class reference for {llm_name}"
            )

    @classmethod
    def get_llm_adapter(cls, llm_name: str) -> Optional[BaseLLMAdapter]:
        """Get a registered LLM client adapter instance, with lazy loading if available."""
        with cls._lock:
            # Check existing instances first
            instance = cls._llm_adapter_instances.get(llm_name)
            if instance is not None:
                return instance

            # Try lazy loading
            lazy_adapter = LAZY_LLM_ADAPTERS.get(llm_name)
            if lazy_adapter and lazy_adapter.is_available():
                try:
                    adapter_class = lazy_adapter.get_class()
                    if adapter_class:
                        instance = adapter_class()
                        cls.register_llm_adapter(llm_name, instance)
                        logger.debug(
                            f"Lazily loaded and registered {llm_name} LLM adapter"
                        )
                        return cast(Optional[BaseLLMAdapter], instance)
                except Exception as e:
                    logger.error(
                        f"Failed to lazily instantiate {llm_name} LLM adapter: {e}"
                    )

            return None

    @classmethod
    def get_all_llm_adapter_instances(cls) -> Dict[str, BaseLLMAdapter]:
        """Get all registered LLM client adapter instances."""
        with cls._lock:
            return dict(cls._llm_adapter_instances)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered LLM client adapters."""
        with cls._lock:
            cls._llm_adapter_instances.clear()
            cls._llm_adapter_classes.clear()
            logger.debug("Cleared all registered LLM client adapters")

    @classmethod
    def cleanup_all(cls) -> None:
        """Manually cleanup all expired references."""
        with cls._lock:
            cls._cleanup_expired_references()


# --- Registration Functions ---


def register_all_framework_adapters() -> Dict[str, KliraFrameworkAdapter]:
    """
    Register all available framework adapters using lazy loading.
    Only instantiates adapters when they are actually available.
    """
    import sys

    registered_instances = {}

    # Register only currently available adapters to avoid unnecessary imports
    for name, lazy_adapter in LAZY_FRAMEWORK_ADAPTERS.items():
        # Check if the framework is already imported or if we should try to load it
        should_register = False

        if name in ["openai_agents", "agents_sdk"] and "agents" in sys.modules:
            # Only register OpenAI agents if it's actually imported
            should_register = True
        elif name == "langchain" and "langchain" in sys.modules:
            should_register = True
        elif name == "langgraph" and "langgraph" in sys.modules:
            should_register = True
        elif name == "crewai" and "crewai" in sys.modules:
            should_register = True
        elif name == "llama_index" and "llama_index" in sys.modules:
            should_register = True

        if should_register and lazy_adapter.is_available():
            try:
                adapter_class = lazy_adapter.get_class()
                if adapter_class and adapter_class.__name__ != "DummyClass":
                    instance = adapter_class()
                    FrameworkRegistry.register_adapter(name, instance)
                    registered_instances[name] = instance
                    logger.debug(f"Successfully registered framework adapter: {name}")

                    # Special case: register agents_sdk as alias for openai_agents
                    if name == "openai_agents":
                        FrameworkRegistry.register_adapter("agents_sdk", instance)

            except Exception as e:
                logger.error(
                    f"Error instantiating {name} framework adapter: {e}", exc_info=True
                )
        else:
            logger.debug(
                f"Skipping {name} adapter - not available or framework not imported"
            )

    return registered_instances


def register_all_llm_adapters() -> Dict[str, BaseLLMAdapter]:
    """
    Register all available LLM client adapters using lazy loading.
    Only instantiates adapters when they are actually available.
    """
    import sys

    registered_llm_instances = {}

    # Register only available LLM adapters
    for name, lazy_adapter in LAZY_LLM_ADAPTERS.items():
        should_register = False

        # Check if the underlying library is imported
        if name == "openai" and "openai" in sys.modules:
            should_register = True
        elif name == "anthropic" and "anthropic" in sys.modules:
            should_register = True
        elif name == "gemini" and "google.generativeai" in sys.modules:
            should_register = True
        elif name == "ollama" and "ollama" in sys.modules:
            should_register = True

        if should_register and lazy_adapter.is_available():
            try:
                adapter_class = lazy_adapter.get_class()
                if adapter_class and adapter_class.__name__ != "DummyClass":
                    instance = adapter_class()
                    # Check if adapter is available (handle both attribute and method)
                    is_available = False
                    if hasattr(instance, "is_available"):
                        if callable(instance.is_available):
                            is_available = instance.is_available()
                        else:
                            is_available = instance.is_available

                    if is_available:
                        LLMClientRegistry.register_llm_adapter(name, instance)
                        registered_llm_instances[name] = instance
                        logger.debug(
                            f"Successfully registered LLM client adapter: {name}"
                        )
                    else:
                        logger.debug(
                            f"Skipping {name} LLM adapter - underlying library not available"
                        )
            except Exception as e:
                logger.error(
                    f"Error instantiating {name} LLM adapter: {e}", exc_info=True
                )
        else:
            logger.debug(
                f"Skipping {name} LLM adapter - not available or library not imported"
            )

    # Legacy support for specific OpenAI adapters (if they exist)
    openai_imported = "openai" in sys.modules
    if openai_imported:
        # Try to register specific OpenAI adapters if they exist
        legacy_adapters = ["openai_completion", "openai_responses"]
        for adapter_name in legacy_adapters:
            try:
                module_map = {
                    "openai_completion": "klira.sdk.adapters.openai_completion_adapter.OpenAICompletionAdapter",
                    "openai_responses": "klira.sdk.adapters.openai_responses_adapter.OpenAIResponsesAdapter",
                }

                if adapter_name in module_map:
                    module_path, class_name = module_map[adapter_name].rsplit(".", 1)
                    module = __import__(module_path, fromlist=[class_name])
                    adapter_class = getattr(module, class_name)
                    if adapter_class is not None:
                        instance = adapter_class()

                        # Check if adapter is available (handle both attribute and method)
                        is_available = False
                        if hasattr(instance, "is_available"):
                            if callable(instance.is_available):
                                is_available = instance.is_available()
                            else:
                                is_available = instance.is_available

                        if is_available:
                            LLMClientRegistry.register_llm_adapter(
                                adapter_name, instance
                            )
                            registered_llm_instances[adapter_name] = instance
                            logger.debug(
                                f"Successfully registered legacy LLM adapter: {adapter_name}"
                            )

            except (ImportError, AttributeError):
                logger.debug(f"Legacy {adapter_name} adapter not found")
            except Exception as e:
                logger.error(f"Error registering legacy {adapter_name} adapter: {e}")

    return registered_llm_instances


