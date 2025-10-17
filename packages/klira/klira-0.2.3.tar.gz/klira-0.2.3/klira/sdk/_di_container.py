"""Dependency Injection Container for Klira AI SDK.

This module provides a lightweight but powerful dependency injection system
to improve testability and modularity of the SDK components.
"""
# mypy: disable-error-code=unreachable

import threading
import inspect
import weakref
from typing import (
    cast,
    Dict,
    Type,
    Any,
    Callable,
    TypeVar,
    Optional,
    Union,
    get_type_hints,
    Protocol,
    runtime_checkable,
)
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DIError(Exception):
    """Base exception for dependency injection errors."""

    pass


class CircularDependencyError(DIError):
    """Raised when a circular dependency is detected."""

    pass


class UnresolvableDependencyError(DIError):
    """Raised when a dependency cannot be resolved."""

    pass


@runtime_checkable
class Injectable(Protocol):
    """Protocol for objects that can be injected."""

    pass


class LifecycleScope:
    """Defines the lifecycle scope of dependencies."""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class DIContainer:
    """Lightweight dependency injection container with auto-wiring support.

    Features:
    - Singleton and transient lifecycle management
    - Automatic constructor injection based on type hints
    - Factory function support
    - Circular dependency detection
    - Thread-safe operations
    - Weak reference support to prevent memory leaks
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()

        # Registry for different types of services
        self._singletons: Dict[Type[Any], Any] = {}
        self._singleton_instances: Dict[Type[Any], Any] = {}
        self._factories: Dict[Type[Any], Callable[[], Any]] = {}
        self._transients: Dict[Type[Any], Type[Any]] = {}
        self._scoped: Dict[Type[Any], Any] = {}

        # Weak references to prevent memory leaks
        self._weak_references: weakref.WeakValueDictionary[str, Any] = (
            weakref.WeakValueDictionary()
        )

        # Circular dependency detection
        self._resolution_stack: Dict[int, set[Type[Any]]] = {}

        # Configuration
        self._auto_wire_enabled = True
        self._strict_mode = False  # If True, requires explicit registration

    def register_singleton(
        self, interface: Type[T], implementation: Optional[Union[T, Type[T]]] = None
    ) -> "DIContainer":
        """Register a singleton instance or class.

        Args:
            interface: The interface/type to register
            implementation: The implementation instance or class. If None, interface is used as implementation.

        Returns:
            Self for method chaining
        """
        with self._lock:
            if implementation is None:
                implementation = interface

            if inspect.isclass(implementation):
                self._singletons[interface] = implementation
                interface_name = getattr(interface, "__name__", str(interface))
                implementation_name = getattr(
                    implementation, "__name__", str(implementation)
                )
                logger.debug(
                    f"Registered singleton class {implementation_name} for {interface_name}"
                )
            else:
                self._singleton_instances[interface] = implementation
                interface_name = getattr(interface, "__name__", str(interface))
                logger.debug(f"Registered singleton instance for {interface_name}")

        return self

    def register_transient(
        self, interface: Type[T], implementation: Optional[Type[T]] = None
    ) -> "DIContainer":
        """Register a transient (new instance each time) class.

        Args:
            interface: The interface/type to register
            implementation: The implementation class. If None, interface is used.

        Returns:
            Self for method chaining
        """
        with self._lock:
            if implementation is None:
                implementation = interface

            self._transients[interface] = implementation
            interface_name = getattr(interface, "__name__", str(interface))
            implementation_name = getattr(
                implementation, "__name__", str(implementation)
            )
            logger.debug(
                f"Registered transient {implementation_name} for {interface_name}"
            )

        return self

    def register_factory(
        self, interface: Type[T], factory: Callable[[], T]
    ) -> "DIContainer":
        """Register a factory function for creating instances.

        Args:
            interface: The interface/type to register
            factory: Function that creates instances

        Returns:
            Self for method chaining
        """
        with self._lock:
            self._factories[interface] = factory
            interface_name = getattr(interface, "__name__", str(interface))
            logger.debug(f"Registered factory for {interface_name}")

        return self

    def register_scoped(self, interface: Type[T], implementation: T) -> "DIContainer":
        """Register a scoped instance (lives for the duration of a scope).

        Args:
            interface: The interface/type to register
            implementation: The scoped instance

        Returns:
            Self for method chaining
        """
        with self._lock:
            self._scoped[interface] = implementation
            interface_name = getattr(interface, "__name__", str(interface))
            logger.debug(f"Registered scoped instance for {interface_name}")

        return self

    def get(self, interface: Type[T], thread_id: Optional[int] = None) -> T:
        """Get an instance of the requested type.

        Args:
            interface: The type to resolve
            thread_id: Optional thread ID for tracking circular dependencies

        Returns:
            Instance of the requested type

        Raises:
            CircularDependencyError: If circular dependency detected
            UnresolvableDependencyError: If type cannot be resolved
        """
        if thread_id is None:
            thread_id = threading.get_ident()

        # Check for circular dependencies
        if thread_id not in self._resolution_stack:
            self._resolution_stack[thread_id] = set()

        if interface in self._resolution_stack[thread_id]:
            raise CircularDependencyError(
                f"Circular dependency detected for {interface.__name__}"
            )

        self._resolution_stack[thread_id].add(interface)

        try:
            return self._resolve(interface, thread_id)
        finally:
            # Clean up resolution stack
            if thread_id in self._resolution_stack:
                self._resolution_stack[thread_id].discard(interface)
                if not self._resolution_stack[thread_id]:
                    del self._resolution_stack[thread_id]

    def _resolve(self, interface: Type[T], thread_id: int) -> T:
        """Internal method to resolve dependencies."""
        with self._lock:
            # Check singleton instances first (already created)
            if interface in self._singleton_instances:
                return cast(T, self._singleton_instances[interface])

            # Check factories
            if interface in self._factories:
                factory = self._factories[interface]
                return cast(T, self._create_from_factory(factory, thread_id))

            # Check scoped instances
            if interface in self._scoped:
                return cast(T, self._scoped[interface])

            # Check singleton classes (need to create instance)
            if interface in self._singletons:
                if interface not in self._singleton_instances:
                    implementation_class = self._singletons[interface]
                    instance = self._auto_wire(implementation_class, thread_id)
                    self._singleton_instances[interface] = instance
                return cast(T, self._singleton_instances[interface])

            # Check transient classes
            if interface in self._transients:
                implementation_class = self._transients[interface]
                return cast(T, self._auto_wire(implementation_class, thread_id))

            # Try auto-wiring if enabled and not in strict mode
            if self._auto_wire_enabled and not self._strict_mode:
                try:
                    return self._auto_wire(interface, thread_id)
                except Exception as e:
                    interface_name = getattr(interface, "__name__", str(interface))
                    logger.debug(f"Auto-wiring failed for {interface_name}: {e}")

            interface_name = getattr(interface, "__name__", str(interface))
            raise UnresolvableDependencyError(
                f"Cannot resolve dependency for {interface_name}"
            )

    def _create_from_factory(self, factory: Callable[[], Any], thread_id: int) -> Any:
        """Create instance from factory with dependency injection."""
        # Check if factory needs dependencies
        sig = inspect.signature(factory)
        if not sig.parameters:
            return factory()

        # Inject dependencies into factory
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                kwargs[param_name] = self.get(param.annotation, thread_id)

        return factory(**kwargs)

    def _auto_wire(self, cls: Type[T], thread_id: int) -> T:
        """Automatically inject dependencies based on constructor type hints."""
        if not inspect.isclass(cls):
            cls_name = getattr(cls, "__name__", str(cls))
            raise DIError(f"Cannot auto-wire non-class type: {cls_name}")

        # Get constructor signature
        try:
            sig = inspect.signature(cls.__init__)
        except (ValueError, TypeError) as e:
            raise DIError(f"Cannot inspect constructor of {cls.__name__}: {e}")

        # Get type hints
        try:
            hints = get_type_hints(cls.__init__)
        except (NameError, AttributeError):
            hints = {}

        # Build constructor arguments
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # Skip parameters with default values if no type hint
            if (
                param.annotation == inspect.Parameter.empty
                and param.default != inspect.Parameter.empty
            ):
                continue

            # Get type from hints or annotation
            param_type = hints.get(param_name) or param.annotation

            if param_type == inspect.Parameter.empty:
                if param.default == inspect.Parameter.empty:
                    raise DIError(
                        f"Cannot auto-wire parameter '{param_name}' in {cls.__name__}: no type annotation"
                    )
                continue

            # Handle forward references (string annotations)
            if isinstance(param_type, str):
                # For forward references, we can't resolve them directly
                # Skip them if they have defaults, or raise error if required
                if param.default != inspect.Parameter.empty:
                    continue
                else:
                    raise DIError(
                        f"Cannot resolve forward reference '{param_type}' for parameter '{param_name}' in {cls.__name__}"
                    )

            # Handle Optional types
            if hasattr(param_type, "__origin__") and param_type.__origin__ is Union:
                args = getattr(param_type, "__args__", ())
                # Fix: Check args length before accessing indices to prevent tuple index out of range
                if len(args) >= 2 and type(None) in args:
                    # This is Optional[T] - find the non-None type
                    actual_type = None
                    for arg in args:
                        if arg is not type(None):
                            actual_type = arg
                            break

                    if actual_type is not None:
                        try:
                            kwargs[param_name] = self.get(actual_type, thread_id)
                        except UnresolvableDependencyError:
                            # Optional dependency - use None if can't resolve
                            kwargs[param_name] = None
                    else:
                        # This shouldn't happen for Optional[T], but handle gracefully
                        kwargs[param_name] = None
                    continue

            # Resolve required dependency
            try:
                kwargs[param_name] = self.get(param_type, thread_id)
            except UnresolvableDependencyError:
                if param.default != inspect.Parameter.empty:
                    # Use default value
                    continue
                else:
                    raise

        try:
            instance = cls(**kwargs)
            logger.debug(
                f"Auto-wired {cls.__name__} with dependencies: {list(kwargs.keys())}"
            )
            return cast(T, instance)
        except Exception as e:
            raise DIError(f"Failed to create instance of {cls.__name__}: {e}")

    def is_registered(self, interface: Type[Any]) -> bool:
        """Check if a type is registered in the container."""
        with self._lock:
            return (
                interface in self._singletons
                or interface in self._singleton_instances
                or interface in self._factories
                or interface in self._transients
                or interface in self._scoped
            )

    def clear_scoped(self) -> None:
        """Clear all scoped instances (useful for request/response cycles)."""
        with self._lock:
            self._scoped.clear()
            logger.debug("Cleared all scoped instances")

    def clear_all(self) -> None:
        """Clear all registrations and instances."""
        with self._lock:
            self._singletons.clear()
            self._singleton_instances.clear()
            self._factories.clear()
            self._transients.clear()
            self._scoped.clear()
            self._weak_references.clear()
            self._resolution_stack.clear()
            logger.debug("Cleared all DI container registrations")

    def configure(
        self, auto_wire: bool = True, strict_mode: bool = False
    ) -> "DIContainer":
        """Configure container behavior.

        Args:
            auto_wire: Enable automatic dependency injection
            strict_mode: If True, only explicitly registered types can be resolved

        Returns:
            Self for method chaining
        """
        self._auto_wire_enabled = auto_wire
        self._strict_mode = strict_mode
        logger.debug(
            f"Configured DI container: auto_wire={auto_wire}, strict_mode={strict_mode}"
        )
        return self


# Global container instance
_global_container: Optional[DIContainer] = None
_container_lock = threading.RLock()


def get_container() -> DIContainer:
    """Get the global DI container instance."""
    global _global_container
    if _global_container is None:
        with _container_lock:
            if _global_container is None:
                _global_container = DIContainer()
    return _global_container


def set_container(container: DIContainer) -> None:
    """Set the global DI container instance (useful for testing)."""
    global _global_container
    with _container_lock:
        _global_container = container


# Convenience decorators for dependency injection


def injectable(cls: Type[T]) -> Type[T]:
    """Decorator to mark a class as injectable (auto-register as transient)."""
    get_container().register_transient(cls)
    return cls


def singleton(cls: Type[T]) -> Type[T]:
    """Decorator to mark a class as singleton (auto-register as singleton)."""
    get_container().register_singleton(cls)
    return cls


def inject(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to inject dependencies into function parameters."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        container = get_container()
        sig = inspect.signature(func)

        # Get type hints
        try:
            hints = get_type_hints(func)
        except (NameError, AttributeError):
            hints = {}

        # Inject missing parameters
        bound_args = sig.bind_partial(*args, **kwargs)
        bound_args.apply_defaults()

        for param_name, param in sig.parameters.items():
            if param_name not in bound_args.arguments:
                param_type = hints.get(param_name) or param.annotation
                if param_type != inspect.Parameter.empty:
                    try:
                        bound_args.arguments[param_name] = container.get(param_type)
                    except UnresolvableDependencyError:
                        if param.default == inspect.Parameter.empty:
                            raise

        return func(**bound_args.arguments)

    return wrapper
