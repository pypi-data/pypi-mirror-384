"""Utilities for safe span attribute handling."""

import logging
from typing import Any, Dict
from opentelemetry.trace import Span

logger = logging.getLogger(__name__)


def safe_set_span_attribute(span: Span, key: str, value: Any) -> None:
    """
    Safely set an attribute on a span, filtering out None values and invalid types.

    Args:
        span: The span to set the attribute on
        key: The attribute key
        value: The attribute value
    """
    if value is None:
        logger.debug(f"Skipping None value for span attribute '{key}'")
        return

    # OpenTelemetry only accepts certain types for attribute values
    # Valid types: bool, str, bytes, int, float, or sequences of these
    if isinstance(value, (bool, str, bytes, int, float)):
        span.set_attribute(key, value)
    elif isinstance(value, (list, tuple)):
        # For sequences, ensure all elements are valid types
        try:
            valid_sequence = []
            for item in value:
                if item is not None and isinstance(
                    item, (bool, str, bytes, int, float)
                ):
                    valid_sequence.append(item)
                elif item is not None:
                    # Convert to string if not a valid type
                    valid_sequence.append(str(item))

            if valid_sequence:  # Only set if we have valid items
                span.set_attribute(key, valid_sequence)
        except Exception as e:
            logger.warning(f"Failed to set sequence attribute '{key}': {e}")
            # Fallback to string representation
            span.set_attribute(key, str(value))
    else:
        # Convert other types to string
        try:
            string_value = str(value)
            span.set_attribute(key, string_value)
        except Exception as e:
            logger.warning(f"Failed to convert attribute '{key}' to string: {e}")


def safe_set_span_attributes(span: Span, attributes: Dict[str, Any]) -> None:
    """
    Safely set multiple attributes on a span.

    Args:
        span: The span to set attributes on
        attributes: Dictionary of key-value pairs to set as attributes
    """
    for key, value in attributes.items():
        safe_set_span_attribute(span, key, value)
