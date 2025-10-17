"""Distributed caching system for Klira AI SDK.

This module provides distributed caching capabilities with multiple backends
including Redis for enterprise-scale deployments and intelligent cache hierarchy.
"""

from .redis_adapter import RedisAdapter, RedisConfig, create_redis_adapter
from .cache_hierarchy import (
    CacheHierarchy,
    CacheHierarchyConfig,
    CacheStrategy,
    CacheLevel,
    CacheMetrics,
    create_cache_hierarchy,
)

# Public API exports
__all__ = [
    # Redis adapter
    "RedisAdapter",
    "RedisConfig",
    "create_redis_adapter",
    # Cache hierarchy
    "CacheHierarchy",
    "CacheHierarchyConfig",
    "CacheStrategy",
    "CacheLevel",
    "CacheMetrics",
    "create_cache_hierarchy",
]

# Version info
__version__ = "3.0.0"
