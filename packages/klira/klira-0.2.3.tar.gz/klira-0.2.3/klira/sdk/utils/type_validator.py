"""Runtime type validation for Klira AI SDK.

This module provides decorators and utilities for runtime type checking,
complementing the static type annotations for improved type safety.
"""

import functools
import inspect
import logging
from typing import (
    Any,
    Callable,
    get_type_hints,
    get_origin,
    get_args,
    Union,
    Optional,
    cast,
    Type,
)

from klira.sdk.types import F

logger = logging.getLogger("klira.types.validator")


# Type validation configuration
class TypeValidationConfig:
    """Configuration for runtime type validation."""

    def __init__(
        self,
        validate_args: bool = True,
        validate_return: bool = True,
        strict_mode: bool = False,
        log_violations: bool = True,
        raise_on_violation: bool = False,
    ):
        self.validate_args = validate_args
        self.validate_return = validate_return
        self.strict_mode = strict_mode
        self.log_violations = log_violations
        self.raise_on_violation = raise_on_violation


# Default configuration
DEFAULT_CONFIG = TypeValidationConfig()


class TypeValidationError(TypeError):
    """Raised when runtime type validation fails."""

    def __init__(
        self,
        message: str,
        function_name: str,
        parameter_name: Optional[str] = None,
        expected_type: Optional[Type[Any]] = None,
        actual_type: Optional[Type[Any]] = None,
    ):
        self.function_name = function_name
        self.parameter_name = parameter_name
        self.expected_type = expected_type
        self.actual_type = actual_type
        super().__init__(message)


def _is_instance_of_type(value: Any, expected_type: Type[Any]) -> bool:
    """Check if value is an instance of the expected type.

    Handles Union types, Optional types, and generic types.
    """
    # Handle Any type specially
    try:
        # Use string comparison for Any type to avoid identity check issues
        if str(expected_type) == str(Any):
            return True
    except TypeError:
        # Fallback for typing special forms
        if str(expected_type) == str(Any):
            return True

    # Handle None values
    if value is None:
        origin = get_origin(expected_type)
        if origin is Union:
            return type(None) in get_args(expected_type)
        return expected_type is type(None)

    # Handle Union types (including Optional)
    origin = get_origin(expected_type)
    if origin is Union:
        return any(_is_instance_of_type(value, arg) for arg in get_args(expected_type))

    # Handle generic types like List[str], Dict[str, Any], etc.
    if origin is not None:
        # Check the origin type (e.g., list for List[str])
        if not isinstance(value, origin):
            return False

        # For basic container types, we can check contents if in strict mode
        # This is simplified - full generic type checking is complex
        return True

    # Basic type check
    try:
        return isinstance(value, expected_type)
    except TypeError:
        # Some types might not work with isinstance
        return False


def _validate_parameter(
    param_name: str,
    value: Any,
    expected_type: Type[Any],
    function_name: str,
    config: TypeValidationConfig,
) -> None:
    """Validate a single parameter against its expected type."""
    if not _is_instance_of_type(value, expected_type):
        actual_type = type(value)
        message = (
            f"Type mismatch in {function_name}(): "
            f"parameter '{param_name}' expected {expected_type}, "
            f"got {actual_type} (value: {repr(value)})"
        )

        if config.log_violations:
            logger.warning(message)

        if config.raise_on_violation or config.strict_mode:
            raise TypeValidationError(
                message=message,
                function_name=function_name,
                parameter_name=param_name,
                expected_type=expected_type,
                actual_type=actual_type,
            )


def _validate_return_value(
    value: Any,
    expected_type: Type[Any],
    function_name: str,
    config: TypeValidationConfig,
) -> None:
    """Validate return value against its expected type."""
    if not _is_instance_of_type(value, expected_type):
        actual_type = type(value)
        message = (
            f"Return type mismatch in {function_name}(): "
            f"expected {expected_type}, got {actual_type} (value: {repr(value)})"
        )

        if config.log_violations:
            logger.warning(message)

        if config.raise_on_violation or config.strict_mode:
            raise TypeValidationError(
                message=message,
                function_name=function_name,
                parameter_name="return",
                expected_type=expected_type,
                actual_type=actual_type,
            )


def validate_types(config: Optional[TypeValidationConfig] = None) -> Callable[[F], F]:
    """Decorator for runtime type validation.

    Args:
        config: Type validation configuration. Uses default if None.

    Returns:
        Decorator function.

    Example:
        @validate_types()
        def process_data(name: str, count: int) -> str:
            return f"Processed {count} items for {name}"

        # This will log a warning or raise an error:
        process_data("test", "not_an_int")
    """
    if config is None:
        config = DEFAULT_CONFIG

    def decorator(func: F) -> F:
        # Get type hints for the function
        try:
            type_hints = get_type_hints(func)
        except (NameError, AttributeError, TypeError) as e:
            logger.debug(f"Could not get type hints for {func.__name__}: {e}")
            # Return function unchanged if we can't get type hints
            return func

        # Get function signature
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Validate arguments if enabled
            if config.validate_args:
                # Bind arguments to parameters
                try:
                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()
                except TypeError as e:
                    if config.log_violations:
                        logger.warning(
                            f"Argument binding failed for {func.__name__}: {e}"
                        )
                    if config.raise_on_violation:
                        raise
                    # Continue execution even if binding fails
                    bound_args = None

                if bound_args:
                    for param_name, value in bound_args.arguments.items():
                        if param_name in type_hints:
                            expected_type = type_hints[param_name]
                            _validate_parameter(
                                param_name, value, expected_type, func.__name__, config
                            )

            # Call the original function
            result = func(*args, **kwargs)

            # Validate return value if enabled
            if config.validate_return and "return" in type_hints:
                expected_return_type = type_hints["return"]
                _validate_return_value(
                    result, expected_return_type, func.__name__, config
                )

            return result

        return cast(F, wrapper)

    return decorator


# Convenience decorators with different configurations
def strict_types(func: F) -> F:
    """Decorator for strict type validation (raises exceptions on violations)."""
    config = TypeValidationConfig(
        validate_args=True,
        validate_return=True,
        strict_mode=True,
        log_violations=True,
        raise_on_violation=True,
    )
    return validate_types(config)(func)


def log_type_violations(func: F) -> F:
    """Decorator that logs type violations but doesn't raise exceptions."""
    config = TypeValidationConfig(
        validate_args=True,
        validate_return=True,
        strict_mode=False,
        log_violations=True,
        raise_on_violation=False,
    )
    return validate_types(config)(func)


def validate_args_only(func: F) -> F:
    """Decorator that only validates function arguments."""
    config = TypeValidationConfig(
        validate_args=True,
        validate_return=False,
        strict_mode=False,
        log_violations=True,
        raise_on_violation=False,
    )
    return validate_types(config)(func)


def validate_return_only(func: F) -> F:
    """Decorator that only validates return values."""
    config = TypeValidationConfig(
        validate_args=False,
        validate_return=True,
        strict_mode=False,
        log_violations=True,
        raise_on_violation=False,
    )
    return validate_types(config)(func)


# Type checking utilities
def check_type(value: Any, expected_type: Type[Any]) -> bool:
    """Check if a value matches the expected type.

    Args:
        value: Value to check
        expected_type: Expected type

    Returns:
        True if value matches expected type, False otherwise.
    """
    return _is_instance_of_type(value, expected_type)


def assert_type(
    value: Any, expected_type: Type[Any], message: Optional[str] = None
) -> None:
    """Assert that a value matches the expected type.

    Args:
        value: Value to check
        expected_type: Expected type
        message: Optional custom error message

    Raises:
        TypeValidationError: If type doesn't match
    """
    if not _is_instance_of_type(value, expected_type):
        if message is None:
            message = f"Expected {expected_type}, got {type(value)}"
        raise TypeValidationError(
            message=message,
            function_name="assert_type",
            expected_type=expected_type,
            actual_type=type(value),
        )


# Export key functions and classes
__all__ = [
    "TypeValidationConfig",
    "TypeValidationError",
    "validate_types",
    "strict_types",
    "log_type_violations",
    "validate_args_only",
    "validate_return_only",
    "check_type",
    "assert_type",
]
