"""Plugin Manager for Klira SDK.

This module provides comprehensive plugin lifecycle management,
integrating with the dependency injection system and providing
safe loading, unloading, and coordination of plugins.
"""

import threading
import time
from typing import Dict, List, Type, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging

from . import (
    KliraPlugin,
    FrameworkPlugin,
    GuardrailsPlugin,
    AnalyticsPlugin,
    LLMServicePlugin,
    PluginStatus,
    PluginCapability,
    PluginLoadError,
    PluginConfigError,
    PluginDependencyError,
)
from .discovery import PluginDiscovery, get_global_discovery

# Import our DI container
try:
    from .._di_container import DIContainer, get_container as get_global_container

    DI_AVAILABLE = True
except ImportError:
    DI_AVAILABLE = False
    DIContainer = None  # type: ignore[misc, assignment]
    get_global_container = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass
class PluginLoadResult:
    """Result of plugin loading operation."""

    plugin_name: str
    success: bool
    plugin_instance: Optional[KliraPlugin] = None
    error: Optional[Exception] = None
    load_time_ms: float = 0.0
    dependencies_loaded: List[str] = field(default_factory=list)


@dataclass
class PluginStats:
    """Statistics for a loaded plugin."""

    load_time: datetime
    initialization_time_ms: float
    usage_count: int = 0
    last_used: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[Exception] = None


class PluginManager:
    """Manages plugin lifecycle and coordination."""

    def __init__(
        self,
        discovery: Optional[PluginDiscovery] = None,
        di_container: Optional[DIContainer] = None,
        auto_discover: bool = True,
    ):
        """Initialize plugin manager.

        Args:
            discovery: Plugin discovery instance (uses global if None)
            di_container: Dependency injection container (uses global if None)
            auto_discover: Whether to automatically discover plugins
        """
        self.discovery = discovery or get_global_discovery()

        # DI integration
        self.di_container: Optional[DIContainer]
        if DI_AVAILABLE and di_container is None:
            self.di_container = get_global_container()
        else:
            self.di_container = di_container

        # Plugin state
        self.loaded_plugins: Dict[str, KliraPlugin] = {}
        self.plugin_stats: Dict[str, PluginStats] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}

        # Capability mappings
        self.framework_plugins: Dict[str, FrameworkPlugin] = {}
        self.guardrails_plugins: Dict[str, GuardrailsPlugin] = {}
        self.analytics_plugins: Dict[str, AnalyticsPlugin] = {}
        self.llm_service_plugins: Dict[str, LLMServicePlugin] = {}

        # Lifecycle management
        self.plugin_load_order: List[str] = []
        self.plugin_dependencies: Dict[str, Set[str]] = {}

        # Thread safety
        self._lock = threading.RLock()
        self._loading_plugins: Set[str] = set()

        # Event hooks
        self._load_hooks: List[Callable[[str, KliraPlugin], None]] = []
        self._unload_hooks: List[Callable[[str], None]] = []
        self._error_hooks: List[Callable[[str, Exception], None]] = []

        if auto_discover:
            self.discover_plugins()

    def add_load_hook(self, hook: Callable[[str, KliraPlugin], None]) -> None:
        """Add hook called when plugin is loaded."""
        self._load_hooks.append(hook)

    def add_unload_hook(self, hook: Callable[[str], None]) -> None:
        """Add hook called when plugin is unloaded."""
        self._unload_hooks.append(hook)

    def add_error_hook(self, hook: Callable[[str, Exception], None]) -> None:
        """Add hook called when plugin error occurs."""
        self._error_hooks.append(hook)

    def discover_plugins(
        self, force_rediscover: bool = False
    ) -> Dict[str, Type[KliraPlugin]]:
        """Discover available plugins.

        Args:
            force_rediscover: Whether to force rediscovery

        Returns:
            Dictionary of discovered plugin classes
        """
        logger.info("Discovering plugins...")
        discovered = self.discovery.discover_plugins(force_rediscover)
        logger.info(f"Discovered {len(discovered)} plugins")
        return discovered

    def load_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None,
        force_reload: bool = False,
    ) -> PluginLoadResult:
        """Load a specific plugin.

        Args:
            plugin_name: Name of plugin to load
            config: Plugin configuration
            force_reload: Whether to reload if already loaded

        Returns:
            Plugin load result
        """
        start_time = time.time()

        with self._lock:
            # Check if already loaded
            if plugin_name in self.loaded_plugins and not force_reload:
                return PluginLoadResult(
                    plugin_name=plugin_name,
                    success=True,
                    plugin_instance=self.loaded_plugins[plugin_name],
                    load_time_ms=0.0,
                )

            # Check if currently loading (prevent circular loading)
            if plugin_name in self._loading_plugins:
                raise PluginLoadError(
                    f"Circular dependency detected while loading {plugin_name}"
                )

            try:
                self._loading_plugins.add(plugin_name)

                # Get plugin class
                discovered_plugins = self.discovery.discovered_plugins
                if plugin_name not in discovered_plugins:
                    raise PluginLoadError(f"Plugin not found: {plugin_name}")

                plugin_class = discovered_plugins[plugin_name]

                # Load dependencies first
                dependencies_loaded = self._load_plugin_dependencies(plugin_name)

                # Create and configure plugin instance
                plugin_instance = self._create_plugin_instance(
                    plugin_class, plugin_name, config or {}
                )

                # Register with DI container if available
                if self.di_container and DI_AVAILABLE:
                    self._register_plugin_with_di(plugin_name, plugin_instance)

                # Store plugin state
                self.loaded_plugins[plugin_name] = plugin_instance
                self.plugin_configs[plugin_name] = config or {}
                self.plugin_load_order.append(plugin_name)

                # Create stats
                load_time_ms = (time.time() - start_time) * 1000
                self.plugin_stats[plugin_name] = PluginStats(
                    load_time=datetime.now(), initialization_time_ms=load_time_ms
                )

                # Update capability mappings
                self._update_capability_mappings(plugin_name, plugin_instance)

                # Call load hooks
                for hook in self._load_hooks:
                    try:
                        hook(plugin_name, plugin_instance)
                    except Exception as e:
                        logger.warning(f"Error in load hook for {plugin_name}: {e}")

                logger.info(
                    f"Successfully loaded plugin: {plugin_name} ({load_time_ms:.2f}ms)"
                )

                return PluginLoadResult(
                    plugin_name=plugin_name,
                    success=True,
                    plugin_instance=plugin_instance,
                    load_time_ms=load_time_ms,
                    dependencies_loaded=dependencies_loaded,
                )

            except Exception as e:
                load_time_ms = (time.time() - start_time) * 1000
                logger.error(f"Failed to load plugin {plugin_name}: {e}")

                # Call error hooks
                for error_hook in self._error_hooks:
                    try:
                        error_hook(plugin_name, e)
                    except Exception as hook_error:
                        logger.warning(
                            f"Error in error hook for {plugin_name}: {hook_error}"
                        )

                return PluginLoadResult(
                    plugin_name=plugin_name,
                    success=False,
                    error=e,
                    load_time_ms=load_time_ms,
                )
            finally:
                self._loading_plugins.discard(plugin_name)

    def _load_plugin_dependencies(self, plugin_name: str) -> List[str]:
        """Load plugin dependencies."""
        dependencies_loaded: List[str] = []

        metadata = self.discovery.plugin_metadata.get(plugin_name)
        if not metadata:
            return dependencies_loaded

        for dep in metadata.dependencies:
            # Check if it's a plugin dependency (format: "plugin:plugin_name")
            if dep.startswith("plugin:"):
                dep_plugin_name = dep[7:]  # Remove "plugin:" prefix
                if dep_plugin_name not in self.loaded_plugins:
                    result = self.load_plugin(dep_plugin_name)
                    if result.success:
                        dependencies_loaded.append(dep_plugin_name)
                        # Include transitive dependencies too
                        dependencies_loaded.extend(result.dependencies_loaded)
                    else:
                        raise PluginDependencyError(
                            f"Failed to load dependency {dep_plugin_name} for {plugin_name}"
                        )

        return dependencies_loaded

    def _create_plugin_instance(
        self, plugin_class: Type[KliraPlugin], plugin_name: str, config: Dict[str, Any]
    ) -> KliraPlugin:
        """Create and initialize plugin instance."""
        # Validate configuration
        temp_instance = plugin_class()
        config_errors = temp_instance.validate_config(config)
        if config_errors:
            raise PluginConfigError(
                f"Invalid config for {plugin_name}: {config_errors}"
            )

        # Create actual instance
        plugin_instance = plugin_class()
        plugin_instance._set_status(PluginStatus.INITIALIZING)

        try:
            # Initialize plugin
            plugin_instance.initialize(config)
            plugin_instance._set_status(PluginStatus.ACTIVE)

            return plugin_instance

        except Exception as e:
            plugin_instance._set_status(PluginStatus.ERROR)
            raise PluginLoadError(
                f"Plugin initialization failed for {plugin_name}: {e}"
            )

    def _register_plugin_with_di(
        self, plugin_name: str, plugin_instance: KliraPlugin
    ) -> None:
        """Register plugin components with DI container."""
        if not self.di_container:
            return

        try:
            # Register the plugin itself
            self.di_container.register_singleton(type(plugin_instance), plugin_instance)

            # Register plugin by interface if it implements specific plugin types
            if isinstance(plugin_instance, FrameworkPlugin):
                adapter_class = plugin_instance.get_adapter_class()
                if adapter_class:
                    adapter_instance = adapter_class()
                    self.di_container.register_singleton(
                        adapter_class, adapter_instance
                    )

            if isinstance(plugin_instance, GuardrailsPlugin):
                component = plugin_instance.create_component(
                    self.plugin_configs.get(plugin_name, {})
                )
                if component:
                    self.di_container.register_singleton(type(component), component)

            if isinstance(plugin_instance, AnalyticsPlugin):
                processor_class = plugin_instance.get_processor_class()
                if processor_class:
                    processor_instance = processor_class()
                    self.di_container.register_singleton(
                        processor_class, processor_instance
                    )

            if isinstance(plugin_instance, LLMServicePlugin):
                service_class = plugin_instance.get_service_class()
                if service_class:
                    service_instance = service_class()
                    self.di_container.register_singleton(
                        service_class, service_instance
                    )

        except Exception as e:
            logger.warning(
                f"Failed to register plugin {plugin_name} with DI container: {e}"
            )

    def _update_capability_mappings(
        self, plugin_name: str, plugin_instance: KliraPlugin
    ) -> None:
        """Update capability-specific plugin mappings."""
        capabilities = plugin_instance.capabilities

        if PluginCapability.FRAMEWORK_ADAPTER in capabilities and isinstance(
            plugin_instance, FrameworkPlugin
        ):
            framework_name = plugin_instance.get_framework_name()
            self.framework_plugins[framework_name] = plugin_instance

        if PluginCapability.GUARDRAILS_COMPONENT in capabilities and isinstance(
            plugin_instance, GuardrailsPlugin
        ):
            component_type = plugin_instance.get_component_type()
            self.guardrails_plugins[component_type] = plugin_instance

        if PluginCapability.ANALYTICS_PROCESSOR in capabilities and isinstance(
            plugin_instance, AnalyticsPlugin
        ):
            self.analytics_plugins[plugin_name] = plugin_instance

        if PluginCapability.LLM_SERVICE in capabilities and isinstance(
            plugin_instance, LLMServicePlugin
        ):
            service_name = plugin_instance.get_service_name()
            self.llm_service_plugins[service_name] = plugin_instance

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin.

        Args:
            plugin_name: Name of plugin to unload

        Returns:
            True if successfully unloaded
        """
        with self._lock:
            if plugin_name not in self.loaded_plugins:
                logger.warning(f"Plugin not loaded: {plugin_name}")
                return False

            try:
                plugin_instance = self.loaded_plugins[plugin_name]

                # Call cleanup
                plugin_instance.cleanup()
                plugin_instance._set_status(PluginStatus.DISABLED)

                # Remove from mappings
                self._remove_from_capability_mappings(plugin_name, plugin_instance)

                # Clean up state
                del self.loaded_plugins[plugin_name]
                self.plugin_configs.pop(plugin_name, None)
                if plugin_name in self.plugin_load_order:
                    self.plugin_load_order.remove(plugin_name)

                # Call unload hooks
                for hook in self._unload_hooks:
                    try:
                        hook(plugin_name)
                    except Exception as e:
                        logger.warning(f"Error in unload hook for {plugin_name}: {e}")

                logger.info(f"Successfully unloaded plugin: {plugin_name}")
                return True

            except Exception as e:
                logger.error(f"Error unloading plugin {plugin_name}: {e}")

                # Call error hooks
                for error_hook in self._error_hooks:
                    try:
                        error_hook(plugin_name, e)
                    except Exception:
                        pass

                return False

    def _remove_from_capability_mappings(
        self, plugin_name: str, plugin_instance: KliraPlugin
    ) -> None:
        """Remove plugin from capability mappings."""
        # Remove from framework plugins
        frameworks_to_remove = [
            framework
            for framework, plugin in self.framework_plugins.items()
            if plugin is plugin_instance
        ]
        for framework in frameworks_to_remove:
            del self.framework_plugins[framework]

        # Remove from other mappings
        self.guardrails_plugins = {
            k: v for k, v in self.guardrails_plugins.items() if v is not plugin_instance
        }
        self.analytics_plugins = {
            k: v for k, v in self.analytics_plugins.items() if v is not plugin_instance
        }
        self.llm_service_plugins = {
            k: v
            for k, v in self.llm_service_plugins.items()
            if v is not plugin_instance
        }

    def load_all_plugins(
        self, configs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, PluginLoadResult]:
        """Load all discovered plugins.

        Args:
            configs: Plugin-specific configurations

        Returns:
            Dictionary of load results
        """
        configs = configs or {}
        results = {}

        discovered_plugins = self.discovery.discovered_plugins
        logger.info(f"Loading {len(discovered_plugins)} discovered plugins...")

        for plugin_name in discovered_plugins:
            plugin_config = configs.get(plugin_name, {})
            result = self.load_plugin(plugin_name, plugin_config)
            results[plugin_name] = result

        successful_loads = sum(1 for r in results.values() if r.success)
        logger.info(
            f"Successfully loaded {successful_loads}/{len(discovered_plugins)} plugins"
        )

        return results

    def get_framework_adapter(self, framework_name: str) -> Optional[Type[Any]]:
        """Get framework adapter from plugins.

        Args:
            framework_name: Name of the framework

        Returns:
            Adapter class if available
        """
        plugin = self.framework_plugins.get(framework_name)
        if plugin:
            return plugin.get_adapter_class()
        return None

    def get_plugin_stats(self) -> Dict[str, PluginStats]:
        """Get statistics for all loaded plugins."""
        return self.plugin_stats.copy()

    def get_load_report(self) -> Dict[str, Any]:
        """Get comprehensive plugin load report."""
        return {
            "total_discovered": len(self.discovery.discovered_plugins),
            "total_loaded": len(self.loaded_plugins),
            "framework_plugins": len(self.framework_plugins),
            "guardrails_plugins": len(self.guardrails_plugins),
            "analytics_plugins": len(self.analytics_plugins),
            "llm_service_plugins": len(self.llm_service_plugins),
            "load_order": self.plugin_load_order.copy(),
            "discovery_report": self.discovery.get_discovery_report(),
            "stats": {
                name: {
                    "load_time": stats.load_time.isoformat(),
                    "initialization_time_ms": stats.initialization_time_ms,
                    "usage_count": stats.usage_count,
                    "error_count": stats.error_count,
                }
                for name, stats in self.plugin_stats.items()
            },
        }


# Global plugin manager
_global_plugin_manager: Optional[PluginManager] = None
_global_manager_lock = threading.Lock()


def get_global_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    global _global_plugin_manager

    if _global_plugin_manager is None:
        with _global_manager_lock:
            if _global_plugin_manager is None:
                _global_plugin_manager = PluginManager()

    return _global_plugin_manager


def load_plugin(
    plugin_name: str, config: Optional[Dict[str, Any]] = None
) -> PluginLoadResult:
    """Convenience function to load a plugin using global manager."""
    return get_global_plugin_manager().load_plugin(plugin_name, config)


def get_framework_adapter(framework_name: str) -> Optional[Type[Any]]:
    """Convenience function to get framework adapter."""
    return get_global_plugin_manager().get_framework_adapter(framework_name)
