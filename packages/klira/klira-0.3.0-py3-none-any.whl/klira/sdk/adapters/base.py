"""Base interface for framework-specific adapters."""

from abc import ABC, abstractmethod
from typing import Callable, Any, Dict, Tuple


class BaseAdapter(ABC):
    """Abstract base class for framework adapters."""

    FRAMEWORK_NAME: str = "base"  # Should be overridden by subclasses

    @abstractmethod
    def adapt_workflow(
        self, func: Callable[..., Any], name: str | None = None, **kwargs: Any
    ) -> Callable[..., Any]:
        """Adapt a workflow function/method for tracing."""
        raise NotImplementedError

    @abstractmethod
    def adapt_task(
        self, func: Callable[..., Any], name: str | None = None, **kwargs: Any
    ) -> Callable[..., Any]:
        """Adapt a task function/method for tracing."""
        raise NotImplementedError

    @abstractmethod
    def adapt_agent(
        self, func: Callable[..., Any], name: str | None = None, **kwargs: Any
    ) -> Callable[..., Any]:
        """Adapt an agent function/method/class for tracing."""
        raise NotImplementedError

    @abstractmethod
    def adapt_tool(
        self,
        func_or_class: Callable[..., Any] | type,
        name: str | None = None,
        **kwargs: Any,
    ) -> Callable[..., Any] | type:
        """Adapt a tool function/class for tracing."""
        raise NotImplementedError

    # Added guardrail adaptation method as per plan
    def adapt_guardrail(
        self, func: Callable[..., Any], **kwargs: Any
    ) -> Callable[..., Any]:
        """Adapt a guardrail function for tracing (specific frameworks)."""
        # Default implementation raises error, expect override
        print(
            f"Klira Warning: adapt_guardrail not implemented for {self.FRAMEWORK_NAME}. Guardrail tracing disabled for this function."
        )
        return func

    # Added patching method as per plan
    def patch_framework(self) -> None:
        """Apply necessary patches to the underlying framework for automatic tracing."""
        pass  # Default is no-op

    # --- Guardrail and Augmentation Methods ---

    @abstractmethod
    def apply_input_guardrails(
        self,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        func_name: str,
        injection_strategy: str = "auto",
    ) -> Tuple[Tuple[Any, ...], Dict[str, Any], bool, str]:
        """
        Apply input guardrails to the function arguments.

        Args:
            args: Original positional arguments.
            kwargs: Original keyword arguments.
            func_name: Name of the function being decorated.
            injection_strategy: Strategy for injecting guidelines - 'auto', 'instructions', 'completion'.

        Returns:
            A tuple containing:
            - Modified positional arguments (or original if no changes).
            - Modified keyword arguments (or original if no changes).
            - Boolean indicating if the execution should be blocked.
            - A string containing the block reason if blocked.
        """
        raise NotImplementedError

    @abstractmethod
    def apply_output_guardrails(
        self, result: Any, func_name: str
    ) -> Tuple[Any, bool, str]:
        """
        Apply output guardrails to the function result.

        Args:
            result: The original result of the function execution.
            func_name: Name of the function being decorated.

        Returns:
            A tuple containing:
            - Modified result (or original if no changes/allowed).
            - Boolean indicating if the output should be blocked/replaced.
            - A string containing the alternative response if blocked/replaced.
        """
        raise NotImplementedError

    @abstractmethod
    def apply_augmentation(
        self,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        guidelines: list[str],
        func_name: str,
    ) -> Tuple[Tuple[Any, ...], Dict[str, Any]]:
        """
        Apply prompt augmentation based on guardrail guidelines.

        Args:
            args: Original positional arguments.
            kwargs: Original keyword arguments.
            guidelines: List of augmentation guidelines from guardrails.
            func_name: Name of the function being decorated.

        Returns:
            A tuple containing:
            - Modified positional arguments.
            - Modified keyword arguments.
        """
        raise NotImplementedError
