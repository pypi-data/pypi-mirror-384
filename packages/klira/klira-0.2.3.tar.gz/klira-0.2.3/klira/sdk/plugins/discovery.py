"""Plugin Discovery System for Klira SDK.

This module provides automatic discovery of Klira plugins from various sources:
- Local directories
- Installed Python packages
- Entry points
- Custom discovery paths
"""

import os
import importlib
import importlib.util
import pkgutil
import threading
from pathlib import Path
from typing import Dict, List, Type, Optional, Callable, Any
import logging
import json
from dataclasses import asdict

from . import (
    KliraPlugin,
    PluginMetadata,
    PluginCapability,
    PluginLoadError,
    PluginDependencyError,
)

logger = logging.getLogger(__name__)


class PluginDiscovery:
    """Discovers Klira AI plugins from multiple sources."""

    def __init__(
        self,
        plugin_dirs: Optional[List[str]] = None,
        scan_installed_packages: bool = True,
        scan_entry_points: bool = True,
    ):
        """Initialize plugin discovery.

        Args:
            plugin_dirs: Custom directories to scan for plugins
            scan_installed_packages: Whether to scan installed packages
            scan_entry_points: Whether to scan entry points
        """
        self.plugin_dirs = plugin_dirs or self._get_default_plugin_dirs()
        self.scan_installed_packages = scan_installed_packages
        self.scan_entry_points = scan_entry_points

        # Discovery results
        self.discovered_plugins: Dict[str, Type[KliraPlugin]] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.plugin_errors: Dict[str, Exception] = {}

        # Thread safety
        self._lock = threading.RLock()
        self._discovery_complete = False

        # Discovery hooks
        self._discovery_hooks: List[Callable[[Dict[str, Type[KliraPlugin]]], None]] = []

    def _get_default_plugin_dirs(self) -> List[str]:
        """Get default plugin directories."""
        dirs = []

        # User-specific plugin directory
        home_dir = Path.home()
        user_plugin_dir = home_dir / ".klira" / "plugins"
        dirs.append(str(user_plugin_dir))

        # System-wide plugin directory (Unix-like systems)
        if os.name != "nt":  # Not Windows
            dirs.append("/etc/klira/plugins")
            dirs.append("/usr/local/lib/klira/plugins")

        # Current working directory plugins
        dirs.append("./klira_plugins")
        dirs.append("./plugins")

        # Environment variable override
        env_dirs = os.getenv("KLIRA_PLUGIN_DIRS")
        if env_dirs:
            dirs.extend(env_dirs.split(os.pathsep))

        return dirs

    def add_discovery_hook(
        self, hook: Callable[[Dict[str, Type[KliraPlugin]]], None]
    ) -> None:
        """Add a hook to be called after plugin discovery.

        Args:
            hook: Function to call with discovered plugins
        """
        self._discovery_hooks.append(hook)

    def discover_plugins(
        self, force_rediscover: bool = False
    ) -> Dict[str, Type[KliraPlugin]]:
        """Discover all available plugins.

        Args:
            force_rediscover: Whether to force rediscovery even if already done

        Returns:
            Dictionary mapping plugin names to plugin classes
        """
        with self._lock:
            if self._discovery_complete and not force_rediscover:
                return self.discovered_plugins.copy()

            logger.info("Starting plugin discovery...")

            # Reset discovery state
            self.discovered_plugins.clear()
            self.plugin_metadata.clear()
            self.plugin_errors.clear()

            try:
                # Discover from directories
                self._scan_directories()

                # Discover from installed packages
                if self.scan_installed_packages:
                    self._scan_installed_packages()

                # Discover from entry points
                if self.scan_entry_points:
                    self._scan_entry_points()

                # Validate discovered plugins
                self._validate_plugins()

                self._discovery_complete = True

                logger.info(
                    f"Plugin discovery complete. Found {len(self.discovered_plugins)} plugins."
                )

                # Call discovery hooks
                for hook in self._discovery_hooks:
                    try:
                        hook(self.discovered_plugins.copy())
                    except Exception as e:
                        logger.error(f"Error in discovery hook: {e}")

                return self.discovered_plugins.copy()

            except Exception as e:
                logger.error(f"Plugin discovery failed: {e}")
                raise PluginLoadError(f"Plugin discovery failed: {e}")

    def _scan_directories(self) -> None:
        """Scan configured directories for plugins."""
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                logger.debug(f"Plugin directory not found: {plugin_dir}")
                continue

            logger.debug(f"Scanning plugin directory: {plugin_dir}")

            try:
                self._scan_directory(plugin_dir)
            except Exception as e:
                logger.warning(f"Error scanning directory {plugin_dir}: {e}")

    def _scan_directory(self, plugin_dir: str) -> None:
        """Scan a single directory for plugins."""
        plugin_path = Path(plugin_dir)

        # Look for Python packages (directories with __init__.py)
        for item in plugin_path.iterdir():
            if not item.is_dir():
                continue

            init_file = item / "__init__.py"
            if not init_file.exists():
                continue

            # Check for plugin manifest
            manifest_file = item / "plugin.json"
            plugin_name = item.name

            try:
                # Try to import the plugin module
                spec = importlib.util.spec_from_file_location(plugin_name, init_file)
                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Extract plugins from module
                self._extract_plugins_from_module(module, plugin_name, manifest_file)

            except Exception as e:
                logger.warning(f"Failed to load plugin from {item}: {e}")
                self.plugin_errors[plugin_name] = e

    def _scan_installed_packages(self) -> None:
        """Scan installed packages for Klira AI plugins."""
        logger.debug("Scanning installed packages for plugins...")

        # Look for packages with 'klira_plugin_' prefix
        for finder, name, ispkg in pkgutil.iter_modules():
            if name.startswith("klira_plugin_"):
                try:
                    module = importlib.import_module(name)
                    plugin_name = name.replace("klira_plugin_", "")
                    self._extract_plugins_from_module(module, plugin_name)
                except ImportError as e:
                    logger.warning(f"Failed to import plugin package {name}: {e}")
                    self.plugin_errors[name] = e

    def _scan_entry_points(self) -> None:
        """Scan entry points for Klira AI plugins."""
        try:
            # Try new importlib.metadata first (Python 3.8+)
            eps: Any = None
            try:
                from importlib.metadata import entry_points

                eps_result = entry_points(group="klira.plugins")
                # Convert EntryPoints to iterator for consistent handling
                eps = iter(eps_result)
            except ImportError:
                # Fallback to pkg_resources (older Python or missing importlib.metadata)
                try:
                    import pkg_resources

                    eps = pkg_resources.iter_entry_points("klira.plugins")
                except ImportError:
                    logger.debug("No entry point scanning available")
                    return

            logger.debug("Scanning entry points for plugins...")

            for ep in eps:
                try:
                    plugin_class = ep.load()
                    if issubclass(plugin_class, KliraPlugin):
                        plugin_name = ep.name
                        self.discovered_plugins[plugin_name] = plugin_class

                        # Try to get metadata
                        try:
                            instance = plugin_class()
                            self.plugin_metadata[plugin_name] = instance.metadata
                        except Exception as e:
                            logger.warning(
                                f"Could not get metadata for plugin {plugin_name}: {e}"
                            )

                        logger.debug(
                            f"Discovered plugin via entry point: {plugin_name}"
                        )

                except Exception as e:
                    logger.warning(
                        f"Failed to load plugin from entry point {ep.name}: {e}"
                    )
                    self.plugin_errors[ep.name] = e

        except Exception as e:
            logger.warning(f"Entry point scanning failed: {e}")

    def _extract_plugins_from_module(
        self, module: Any, default_name: str, manifest_file: Optional[Path] = None
    ) -> None:
        """Extract plugin classes from a module."""
        # Load manifest if available
        manifest_data = None
        if manifest_file and manifest_file.exists():
            try:
                with open(manifest_file, "r") as f:
                    manifest_data = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load plugin manifest {manifest_file}: {e}")

        # Look for plugin classes in the module
        plugin_classes = []
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, KliraPlugin)
                and attr is not KliraPlugin
            ):
                plugin_classes.append(attr)

        # Register discovered plugin classes
        for plugin_class in plugin_classes:
            try:
                # Create instance to get metadata
                instance = plugin_class()
                metadata = instance.metadata

                # Use manifest data to override metadata if available
                if manifest_data:
                    for key, value in manifest_data.items():
                        if hasattr(metadata, key):
                            setattr(metadata, key, value)

                plugin_name = metadata.name if metadata.name else default_name

                self.discovered_plugins[plugin_name] = plugin_class
                self.plugin_metadata[plugin_name] = metadata

                logger.debug(f"Discovered plugin: {plugin_name} (v{metadata.version})")

            except Exception as e:
                logger.warning(f"Failed to extract plugin {plugin_class.__name__}: {e}")
                self.plugin_errors[plugin_class.__name__] = e

    def _validate_plugins(self) -> None:
        """Validate discovered plugins."""
        invalid_plugins = []

        for plugin_name, plugin_class in self.discovered_plugins.items():
            try:
                # Basic validation
                if not issubclass(plugin_class, KliraPlugin):
                    raise PluginLoadError(
                        f"Plugin {plugin_name} does not inherit from KliraPlugin"
                    )

                # Try to instantiate to check for basic errors
                instance = plugin_class()

                # Validate metadata
                metadata = instance.metadata
                if not metadata.name:
                    raise PluginLoadError(
                        f"Plugin {plugin_name} has no name in metadata"
                    )

                # Validate capabilities
                capabilities = instance.capabilities
                if not capabilities:
                    logger.warning(f"Plugin {plugin_name} declares no capabilities")

                # Check dependencies
                self._check_plugin_dependencies(metadata)

            except Exception as e:
                logger.error(f"Plugin validation failed for {plugin_name}: {e}")
                invalid_plugins.append(plugin_name)
                self.plugin_errors[plugin_name] = e

        # Remove invalid plugins
        for plugin_name in invalid_plugins:
            self.discovered_plugins.pop(plugin_name, None)
            self.plugin_metadata.pop(plugin_name, None)

    def _check_plugin_dependencies(self, metadata: PluginMetadata) -> None:
        """Check if plugin dependencies are satisfied."""
        for dep in metadata.dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                raise PluginDependencyError(f"Plugin dependency not found: {dep}")

    def get_plugins_by_capability(
        self, capability: PluginCapability
    ) -> Dict[str, Type[KliraPlugin]]:
        """Get plugins that provide a specific capability.

        Args:
            capability: The capability to search for

        Returns:
            Dictionary of plugin names to plugin classes
        """
        matching_plugins = {}

        for plugin_name, plugin_class in self.discovered_plugins.items():
            try:
                instance = plugin_class()
                if capability in instance.capabilities:
                    matching_plugins[plugin_name] = plugin_class
            except Exception as e:
                logger.warning(
                    f"Error checking capabilities for plugin {plugin_name}: {e}"
                )

        return matching_plugins

    def get_discovery_report(self) -> Dict[str, Any]:
        """Get a detailed discovery report.

        Returns:
            Dictionary containing discovery statistics and errors
        """
        return {
            "discovered_count": len(self.discovered_plugins),
            "error_count": len(self.plugin_errors),
            "plugins": {
                name: asdict(metadata)
                for name, metadata in self.plugin_metadata.items()
            },
            "errors": {name: str(error) for name, error in self.plugin_errors.items()},
            "directories_scanned": self.plugin_dirs,
            "discovery_complete": self._discovery_complete,
        }


# Global discovery instance
_global_discovery: Optional[PluginDiscovery] = None
_global_discovery_lock = threading.Lock()


def get_global_discovery() -> PluginDiscovery:
    """Get the global plugin discovery instance."""
    global _global_discovery

    if _global_discovery is None:
        with _global_discovery_lock:
            if _global_discovery is None:
                _global_discovery = PluginDiscovery()

    return _global_discovery


def discover_plugins(force_rediscover: bool = False) -> Dict[str, Type[KliraPlugin]]:
    """Convenience function to discover plugins using global discovery."""
    return get_global_discovery().discover_plugins(force_rediscover)


def get_plugins_by_capability(
    capability: PluginCapability,
) -> Dict[str, Type[KliraPlugin]]:
    """Convenience function to get plugins by capability."""
    return get_global_discovery().get_plugins_by_capability(capability)
