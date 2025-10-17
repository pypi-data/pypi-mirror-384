"""
Base class for all framework adapters in Klira AI SDK.
"""

import logging
import asyncio
from typing import Any, Callable, TypeVar

from .base import BaseAdapter

logger = logging.getLogger("klira.adapters.base")

F = TypeVar("F", bound=Callable[..., Any])


class KliraFrameworkAdapter(BaseAdapter):
    """
    Base class for all framework adapters.

    Framework adapters provide a common interface for adapting Klira AI decorators
    to different LLM frameworks (like OpenAI Agents, LangChain, CrewAI, etc).
    """

    # Framework name - should be overridden by subclasses
    FRAMEWORK_NAME = "base"

    def __init__(self) -> None:
        """Initialize the adapter."""
        pass

    # Methods are inherited from BaseAdapter


# Utility functions for framework detection


def is_async_function(func: Callable[..., Any]) -> bool:
    """Check if a function is asynchronous."""
    return asyncio.iscoroutinefunction(func)


def detect_framework(func_or_obj: Any, **kwargs: Any) -> str:
    """
    Detect the framework based on function/class or arguments.
    This is a convenience wrapper around the main framework detection utility.

    Args:
        func_or_obj: Function, class, or other object to inspect
        **kwargs: Optional keyword arguments that might contain framework hints

    Returns:
        String identifying the detected framework
    """
    # Import here to avoid circular imports
    from klira.sdk.utils.framework_detection import detect_framework_cached as detect

    # Check if we have a framework hint in kwargs
    if "framework" in kwargs:
        return str(kwargs["framework"])  # Ensure return type is str

    # Pass only the object to detect and ensure return type is str
    result = detect(func_or_obj)
    return str(result)
