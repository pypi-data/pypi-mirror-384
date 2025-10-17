"""
Adapters for different LLM frameworks.
"""

from typing import Dict, Type, Optional

from klira.sdk.adapters.framework_adapter import KliraFrameworkAdapter
from klira.sdk.adapters.openai_agents_adapter import OpenAIAgentsAdapter

# Dictionary to store adapter classes by framework name
ADAPTERS: Dict[str, Type[KliraFrameworkAdapter]] = {}


def register_adapter(
    framework_name: str, adapter_class: Type[KliraFrameworkAdapter]
) -> None:
    """Register an adapter class for a framework"""
    global ADAPTERS
    ADAPTERS[framework_name] = adapter_class


def get_adapter(framework_name: str) -> Optional[Type[KliraFrameworkAdapter]]:
    """Get the adapter class for a framework"""
    return ADAPTERS.get(framework_name)


# Register adapters
register_adapter("openai_agents", OpenAIAgentsAdapter)
register_adapter("agents_sdk", OpenAIAgentsAdapter)

# Add __all__ to expose public API
__all__ = ["register_adapter", "get_adapter", "ADAPTERS", "OpenAIAgentsAdapter"]
