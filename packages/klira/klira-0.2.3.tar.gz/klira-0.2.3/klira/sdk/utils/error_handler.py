import functools
import logging
from typing import Any, Callable, TypeVar, Optional, Type, Dict, Union, Protocol


# Define protocol for Telemetry interface
class TelemetryProtocol(Protocol):
    def log_exception(self, exc: Exception) -> None: ...
    def capture(self, event_name: str, properties: Dict[str, Any]) -> None: ...


# Import Telemetry with proper type handling
telemetry: TelemetryProtocol
try:
    from klira.sdk.telemetry import Telemetry as _TelemetryInstance

    telemetry = _TelemetryInstance()
except ImportError:
    # Define a placeholder if Telemetry isn't available during initial setup
    class _DummyTelemetry:
        @staticmethod
        def log_exception(exc: Exception) -> None:
            logging.getLogger("klira").warning(
                "Telemetry.log_exception called but Telemetry class not found."
            )

        @staticmethod
        def capture(event_name: str, properties: Dict[str, Any]) -> None:
            logging.getLogger("klira").warning(
                "Telemetry.capture called but Telemetry class not found."
            )

    telemetry = _DummyTelemetry()

# Define a generic type variable for the decorated function's return type
R = TypeVar("R")
F = TypeVar("F", bound=Callable[..., Any])

# Define safe default return values based on common types or scenarios
# Adjust these as needed for your specific application's fail-open cases
SAFE_DEFAULTS: Dict[Type[Any], Any] = {
    dict: {},
    list: [],
    str: "",
    int: 0,
    float: 0.0,
    bool: False,
    type(None): None,
}


class PolicyViolationError(Exception):
    """Custom exception to indicate a policy violation occurred."""

    def __init__(self, original_exception: Exception) -> None:
        self.original_exception = original_exception
        super().__init__(
            f"Policy Violation: An error occurred during execution. {original_exception}"
        )


def handle_errors(
    fail_closed: bool = False, default_return_on_error: Optional[Any] = None
) -> Callable[[Callable[..., R]], Callable[..., Union[R, Any]]]:
    """
    Decorator to handle errors in SDK functions, log them, and optionally fail-closed.

    Args:
        fail_closed: If True, raises a PolicyViolationError on exception.
                     If False (default), returns `default_return_on_error`.
        default_return_on_error: The value to return if `fail_closed` is False
                                 and an exception occurs. Defaults to None.

    Returns:
        A decorator function.
    """

    def decorator(func: Callable[..., R]) -> Callable[..., Union[R, Any]]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Union[R, Any]:
            logger = logging.getLogger("klira")
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                try:
                    telemetry.log_exception(e)
                except Exception as telemetry_exc:
                    logger.error(
                        f"Failed to log exception to Telemetry: {telemetry_exc}",
                        exc_info=True,
                    )

                if fail_closed:
                    # Fail-closed: Raise a specific exception
                    raise PolicyViolationError(original_exception=e) from e
                else:
                    # Fail-open: Return the specified default value
                    logger.warning(
                        f"Fail-open: Returning default value '{default_return_on_error}' for {func.__name__}."
                    )
                    return default_return_on_error  # Return the provided default

        return wrapper

    return decorator

