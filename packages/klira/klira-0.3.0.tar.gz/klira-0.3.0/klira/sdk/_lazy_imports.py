"""
Lazy import system for Klira AI SDK to prevent circular imports and reduce initialization overhead.

This module provides utilities for deferring expensive imports until they are actually needed,
which significantly improves SDK startup time and prevents circular import issues.
"""

import importlib
import logging
import threading
from typing import Optional, Type, Any, Dict, Set

logger = logging.getLogger(__name__)


class LazyImporter:
    """Lazy importer that loads modules and classes only when first accessed."""

    def __init__(
        self,
        module_name: str,
        class_name: str,
        fallback_class: Optional[Type[Any]] = None,
    ):
        """
        Initialize the lazy importer.

        Args:
            module_name: Full module path to import from
            class_name: Name of the class to import
            fallback_class: Optional fallback class if import fails
        """
        self.module_name = module_name
        self.class_name = class_name
        self.fallback_class = fallback_class
        self._cached_import: Optional[Type[Any]] = None
        self._import_attempted = False
        self._lock = threading.RLock()

    def get_class(self) -> Optional[Type[Any]]:
        """Get the imported class, importing it if necessary."""
        if not self._import_attempted:
            with self._lock:
                if not self._import_attempted:
                    try:
                        module = importlib.import_module(self.module_name)
                        self._cached_import = getattr(module, self.class_name, None)
                        if self._cached_import is None:
                            logger.warning(
                                f"Class {self.class_name} not found in module {self.module_name}"
                            )
                            self._cached_import = self.fallback_class
                        else:
                            logger.debug(
                                f"Successfully imported {self.class_name} from {self.module_name}"
                            )
                    except ImportError as e:
                        logger.debug(f"Failed to import {self.module_name}: {e}")
                        self._cached_import = self.fallback_class
                    except Exception as e:
                        logger.error(
                            f"Unexpected error importing {self.module_name}.{self.class_name}: {e}"
                        )
                        self._cached_import = self.fallback_class
                    finally:
                        self._import_attempted = True

        return self._cached_import

    def is_available(self) -> bool:
        """Check if the import is available (will trigger import if not attempted)."""
        cls = self.get_class()
        return cls is not None and cls != self.fallback_class


class LazyModule:
    """Represents a lazily-loaded module with multiple classes/functions."""

    def __init__(self, module_path: str):
        """
        Initialize the lazy module.

        Args:
            module_path: Full path to the module
        """
        self.module_path = module_path
        self._cached_module: Optional[Any] = None
        self._import_attempted = False
        self._lock = threading.RLock()

    def get_module(self) -> Optional[Any]:
        """Get the imported module, importing it if necessary."""
        if not self._import_attempted:
            with self._lock:
                if not self._import_attempted:
                    try:
                        self._cached_module = importlib.import_module(self.module_path)
                        logger.debug(f"Successfully imported module {self.module_path}")
                    except ImportError as e:
                        logger.debug(f"Failed to import module {self.module_path}: {e}")
                        self._cached_module = None
                    except Exception as e:
                        logger.error(
                            f"Unexpected error importing module {self.module_path}: {e}"
                        )
                        self._cached_module = None
                    finally:
                        self._import_attempted = True

        return self._cached_module

    def get_attribute(
        self, attr_name: str, fallback: Optional[Any] = None
    ) -> Optional[Any]:
        """Get an attribute from the module."""
        module = self.get_module()
        if module is None:
            return fallback
        return getattr(module, attr_name, fallback)

    def is_available(self) -> bool:
        """Check if the module is available."""
        return self.get_module() is not None


class DummyClass:
    """Generic dummy class for fallback when imports fail."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        logger.warning("Using dummy implementation for unavailable class")

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        logger.warning("Dummy class method called - functionality not available")
        return None


# Registry of lazy-loaded adapters
LAZY_FRAMEWORK_ADAPTERS: Dict[str, LazyImporter] = {
    "openai_agents": LazyImporter(
        "klira.sdk.adapters.openai_agents_adapter", "OpenAIAgentsAdapter", DummyClass
    ),
    "agents_sdk": LazyImporter(
        "klira.sdk.adapters.openai_agents_adapter", "OpenAIAgentsAdapter", DummyClass
    ),
    "langchain": LazyImporter(
        "klira.sdk.adapters.langchain", "LangChainAdapter", DummyClass
    ),
    "langgraph": LazyImporter(
        "klira.sdk.adapters.langgraph_adapter", "LangGraphAdapter", DummyClass
    ),
    "crewai": LazyImporter("klira.sdk.adapters.crew_ai", "CrewAIAdapter", DummyClass),
    "llama_index": LazyImporter(
        "klira.sdk.adapters.llama_index", "LlamaIndexAdapter", DummyClass
    ),
}

# Registry of lazy-loaded LLM adapters
LAZY_LLM_ADAPTERS: Dict[str, LazyImporter] = {
    "openai": LazyImporter(
        "klira.sdk.adapters.openai_completion_adapter",
        "OpenAICompletionAdapter",
        DummyClass,
    ),
    "anthropic": LazyImporter(
        "klira.sdk.adapters.anthropic_adapter", "AnthropicAdapter", DummyClass
    ),
    "gemini": LazyImporter(
        "klira.sdk.adapters.gemini_adapter", "GeminiAdapter", DummyClass
    ),
    "ollama": LazyImporter(
        "klira.sdk.adapters.ollama_adapter", "OllamaAdapter", DummyClass
    ),
}

# Registry of lazy-loaded functions
LAZY_FUNCTIONS: Dict[str, LazyImporter] = {
    "add_klira_guardrails": LazyImporter(
        "klira.sdk.adapters.agents_adapter", "add_klira_guardrails", DummyClass
    ),
}


def get_lazy_framework_adapter(framework_name: str) -> Optional[LazyImporter]:
    """Get a lazy framework adapter by name."""
    return LAZY_FRAMEWORK_ADAPTERS.get(framework_name)


def get_lazy_llm_adapter(llm_name: str) -> Optional[LazyImporter]:
    """Get a lazy LLM adapter by name."""
    return LAZY_LLM_ADAPTERS.get(llm_name)


def get_lazy_function(function_name: str) -> Optional[LazyImporter]:
    """Get a lazy function by name."""
    return LAZY_FUNCTIONS.get(function_name)


def get_available_frameworks() -> Set[str]:
    """Get the set of framework adapters that are actually available."""
    available = set()
    for name, lazy_adapter in LAZY_FRAMEWORK_ADAPTERS.items():
        if lazy_adapter.is_available():
            available.add(name)
    return available


def get_available_llm_adapters() -> Set[str]:
    """Get the set of LLM adapters that are actually available."""
    available = set()
    for name, lazy_adapter in LAZY_LLM_ADAPTERS.items():
        if lazy_adapter.is_available():
            available.add(name)
    return available


def preload_available_adapters() -> Dict[str, Any]:
    """
    Preload all available adapters (useful for testing or explicit initialization).

    Returns:
        Dictionary mapping adapter names to loaded classes
    """
    loaded = {}

    # Load framework adapters
    for name, lazy_adapter in LAZY_FRAMEWORK_ADAPTERS.items():
        cls = lazy_adapter.get_class()
        if cls and cls != DummyClass:
            loaded[f"framework_{name}"] = cls

    # Load LLM adapters
    for name, lazy_adapter in LAZY_LLM_ADAPTERS.items():
        cls = lazy_adapter.get_class()
        if cls and cls != DummyClass:
            loaded[f"llm_{name}"] = cls

    # Load functions
    for name, lazy_func in LAZY_FUNCTIONS.items():
        func = lazy_func.get_class()
        if func and func != DummyClass:
            loaded[f"function_{name}"] = func

    return loaded
