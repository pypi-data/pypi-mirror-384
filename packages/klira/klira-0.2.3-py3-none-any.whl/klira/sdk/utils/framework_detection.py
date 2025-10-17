"""
Framework detection utilities for automatically identifying the LLM framework being used.
"""

import re
import sys
import time
import inspect
import logging
import threading
from functools import lru_cache, wraps
from typing import Any, Callable, Dict, List, Optional, Type, Union, Pattern
from weakref import WeakKeyDictionary
from ..config import get_config

logger = logging.getLogger("klira.utils.framework_detection")

# Supported frameworks and their detection patterns
FRAMEWORK_DETECTION_PATTERNS = {
    "agents_sdk": {
        "modules": ["agents", "agents.exceptions"],
        "classes": ["Agent", "Runner", "Workflow", "Task"],
        "import_names": ["agents"],
        "module_patterns": [r"^agents(\.|$)", r"^agents\.exceptions(\.|$)"],
    },
    "openai_agents": {
        "modules": ["agents", "agents.exceptions"],
        "classes": ["Agent", "Runner", "Workflow", "Task"],
        "import_names": ["agents"],
        "module_patterns": [r"^agents(\.|$)", r"^agents\.exceptions(\.|$)"],
    },
    "langchain": {
        "modules": ["langchain", "langchain.agents", "langchain.chains"],
        "classes": ["AgentExecutor", "BaseLLM", "Chain", "BaseChain"],
        "import_names": ["langchain"],
        "module_patterns": [
            r"^langchain(\.|$)",
            r"^langchain\.agents(\.|$)",
            r"^langchain\.chains(\.|$)",
        ],
    },
    "crewai": {
        "modules": ["crewai", "crewai.agent", "crewai.crew", "crewai.task"],
        "classes": ["Agent", "Crew", "Task", "Process"],
        "import_names": ["crewai"],
        "module_patterns": [
            r"^crewai(\.|$)",
            r"^crewai\.agent(\.|$)",
            r"^crewai\.crew(\.|$)",
            r"^crewai\.task(\.|$)",
        ],
    },
    "llama_index": {
        "modules": ["llama_index", "llama_index.agent", "llama_index.indices"],
        "classes": ["Agent", "ReActAgent", "SimpleIndex", "VectorStoreIndex"],
        "import_names": ["llama_index"],
        "module_patterns": [
            r"^llama_index(\.|$)",
            r"^llama_index\.agent(\.|$)",
            r"^llama_index\.indices(\.|$)",
        ],
    },
    "langgraph": {
        "modules": ["langgraph", "langgraph.graph", "langgraph.checkpoint"],
        "classes": ["Graph", "StateGraph", "MessageGraph", "CompiledGraph"],
        "import_names": ["langgraph"],
        "module_patterns": [
            r"^langgraph(\.|$)",
            r"^langgraph\.graph(\.|$)",
            r"^langgraph\.checkpoint(\.|$)",
        ],
    },
}


class FrameworkDetectionCache:
    """Thread-safe cache for framework detection results with weak references."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self._cache: Dict[str, tuple[str, float]] = {}  # key -> (framework, timestamp)
        # Weak reference cache for function objects to prevent memory leaks
        self._function_cache: WeakKeyDictionary[Callable[..., Any], tuple[str, float]] = WeakKeyDictionary()
        self._lock = threading.RLock()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._hits = 0
        self._misses = 0
        self._weak_hits = 0
        self._weak_misses = 0

    def _create_cache_key(
        self, func_or_class: Any, args: tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> str:
        """Create a unique cache key for the detection parameters."""
        try:
            # Include function/class signature
            if func_or_class:
                if hasattr(func_or_class, "__module__") and hasattr(
                    func_or_class, "__qualname__"
                ):
                    func_key = (
                        f"{func_or_class.__module__}.{func_or_class.__qualname__}"
                    )
                elif hasattr(func_or_class, "__name__"):
                    func_key = f"{getattr(func_or_class, '__module__', 'unknown')}.{func_or_class.__name__}"
                else:
                    func_key = str(type(func_or_class))
            else:
                func_key = "None"

            # Include arg types (but not values for memory efficiency)
            arg_types = ",".join(type(arg).__name__ for arg in args)

            # Include kwargs keys and explicit framework if present
            kwargs_key = ""
            if kwargs:
                if "framework" in kwargs:
                    kwargs_key = f"framework:{kwargs['framework']}"
                else:
                    kwargs_key = ",".join(sorted(kwargs.keys()))

            return f"{func_key}|{arg_types}|{kwargs_key}"
        except Exception:
            # Fallback to basic key if signature extraction fails
            return f"{type(func_or_class).__name__}|{len(args)}|{len(kwargs)}"

    def get(
        self,
        func_or_class: Any,
        args: tuple[Any, ...] = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Get cached framework detection result using weak references when possible."""
        kwargs = kwargs or {}

        with self._lock:
            # First try weak reference cache for callable objects
            if callable(func_or_class):
                try:
                    if func_or_class in self._function_cache:
                        framework, timestamp = self._function_cache[func_or_class]
                        # Check if cache entry is still valid
                        if time.time() - timestamp < self.ttl_seconds:
                            self._weak_hits += 1
                            logger.debug(f"Weak cache HIT: {getattr(func_or_class, '__name__', str(func_or_class))} -> {framework}")
                            return framework
                        else:
                            # Remove expired entry (WeakKeyDictionary handles this automatically)
                            try:
                                del self._function_cache[func_or_class]
                            except KeyError:
                                pass  # Already removed
                except TypeError:
                    # func_or_class might not be hashable for WeakKeyDictionary
                    pass

            # Fallback to string-based cache
            cache_key = self._create_cache_key(func_or_class, args, kwargs)
            
            if cache_key in self._cache:
                framework, timestamp = self._cache[cache_key]
                # Check if cache entry is still valid
                if time.time() - timestamp < self.ttl_seconds:
                    self._hits += 1
                    logger.debug(f"String cache HIT: {cache_key} -> {framework}")
                    return framework
                else:
                    # Remove expired entry
                    del self._cache[cache_key]

            # Record miss (prefer weak miss if we tried weak cache first)
            if callable(func_or_class):
                self._weak_misses += 1
            else:
                self._misses += 1
            return None

    def set(
        self,
        func_or_class: Any,
        framework: str,
        args: tuple[Any, ...] = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Cache framework detection result using weak references when possible."""
        kwargs = kwargs or {}

        with self._lock:
            # Try to use weak reference cache for callable objects
            if callable(func_or_class):
                try:
                    self._function_cache[func_or_class] = (framework, time.time())
                    logger.debug(f"Weak cache SET: {getattr(func_or_class, '__name__', str(func_or_class))} -> {framework}")
                    return  # Success with weak reference, no need for string cache
                except TypeError:
                    # func_or_class might not be hashable for WeakKeyDictionary
                    # Fall through to string-based cache
                    pass

            # Fallback to string-based cache
            cache_key = self._create_cache_key(func_or_class, args, kwargs)

            # Implement simple LRU eviction if cache is full
            if len(self._cache) >= self.max_size:
                # Remove oldest entry (simple FIFO for performance)
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                logger.debug(f"String cache evicted oldest entry: {oldest_key}")

            self._cache[cache_key] = (framework, time.time())
            logger.debug(f"String cache SET: {cache_key} -> {framework}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics including weak reference cache."""
        with self._lock:
            total_string_requests = self._hits + self._misses
            total_weak_requests = self._weak_hits + self._weak_misses
            total_requests = total_string_requests + total_weak_requests
            
            string_hit_rate = (self._hits / total_string_requests * 100) if total_string_requests > 0 else 0
            weak_hit_rate = (self._weak_hits / total_weak_requests * 100) if total_weak_requests > 0 else 0
            overall_hit_rate = ((self._hits + self._weak_hits) / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "string_cache": {
                    "size": len(self._cache),
                    "max_size": self.max_size,
                    "hits": self._hits,
                    "misses": self._misses,
                    "hit_rate": string_hit_rate,
                },
                "weak_cache": {
                    "size": len(self._function_cache),
                    "hits": self._weak_hits,
                    "misses": self._weak_misses,
                    "hit_rate": weak_hit_rate,
                },
                "overall": {
                    "total_requests": total_requests,
                    "total_hits": self._hits + self._weak_hits,
                    "total_misses": self._misses + self._weak_misses,
                    "hit_rate": overall_hit_rate,
                    "ttl_seconds": self.ttl_seconds,
                },
            }

    def clear(self) -> None:
        """Clear both string and weak reference caches."""
        with self._lock:
            self._cache.clear()
            self._function_cache.clear()
            self._hits = 0
            self._misses = 0
            self._weak_hits = 0
            self._weak_misses = 0


class OptimizedFrameworkDetection:
    """Optimized framework detection with pre-compiled patterns and caching."""

    def __init__(self) -> None:
        self._compiled_patterns: Dict[str, List[Pattern[str]]] = {}
        self._imported_frameworks_cache: Optional[List[str]] = None
        self._imported_frameworks_cache_time: float = 0
        self._imported_frameworks_cache_ttl: float = 60  # 1 minute TTL
        self._lock = threading.RLock()
        self._precompile_patterns()

    def _precompile_patterns(self) -> None:
        """Pre-compile regex patterns for better performance."""
        for framework, patterns in FRAMEWORK_DETECTION_PATTERNS.items():
            self._compiled_patterns[framework] = [
                re.compile(pattern) for pattern in patterns.get("module_patterns", [])
            ]
        logger.debug(
            f"Pre-compiled patterns for {len(self._compiled_patterns)} frameworks"
        )

    def _fast_module_match(self, module_name: str) -> Optional[str]:
        """Fast module matching using pre-compiled regex patterns."""
        if not module_name:
            return None

        for framework, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.match(module_name):
                    return framework
        return None

    def _get_cached_imported_frameworks(self) -> List[str]:
        """Get imported frameworks with caching."""
        current_time = time.time()

        with self._lock:
            # Check if cache is valid
            if (
                self._imported_frameworks_cache is not None
                and current_time - self._imported_frameworks_cache_time
                < self._imported_frameworks_cache_ttl
            ):
                return self._imported_frameworks_cache

            # Refresh cache
            imported_frameworks = []
            for framework, patterns in FRAMEWORK_DETECTION_PATTERNS.items():
                for module_name in patterns["import_names"]:
                    if _check_module_imported(module_name):
                        logger.debug(
                            f"Detected imported framework module: {module_name} for {framework}"
                        )
                        if framework not in imported_frameworks:
                            imported_frameworks.append(framework)

            self._imported_frameworks_cache = imported_frameworks
            self._imported_frameworks_cache_time = current_time
            return imported_frameworks

    def identify_object_framework(self, obj: Any) -> Optional[str]:
        """Fast object framework identification."""
        obj_module = getattr(obj, "__module__", None)
        obj_class = obj.__class__.__name__ if hasattr(obj, "__class__") else None

        if not obj_module and not obj_class:
            return None

        # Use fast module matching first
        if obj_module:
            framework = self._fast_module_match(obj_module)
            if framework:
                logger.debug(f"Fast detected {framework} from module: {obj_module}")
                return framework

        # Fallback to class-based detection if needed
        if obj_class:
            for framework, patterns in FRAMEWORK_DETECTION_PATTERNS.items():
                if obj_class in patterns["classes"]:
                    # Verify module match to avoid false positives
                    if obj_module and self._fast_module_match(obj_module) == framework:
                        logger.debug(
                            f"Detected {framework} from class: {obj_class} in module {obj_module}"
                        )
                        return framework

        return None


# Global instances - initialized lazily to avoid circular imports
_detection_cache: Optional[FrameworkDetectionCache] = None
_optimized_detector: Optional[OptimizedFrameworkDetection] = None

# Additional weak reference cache specifically for decorator performance
_weak_function_cache: WeakKeyDictionary[Callable[..., Any], str] = WeakKeyDictionary()
_weak_cache_lock = threading.RLock()


def framework_cached(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that caches framework detection for a specific function using weak references.
    
    This prevents repeated framework detection for the same function while avoiding
    memory leaks by using weak references. When the function is garbage collected,
    the cache entry is automatically removed.
    
    Note: This decorator is primarily for testing and demonstration of weak reference caching.
    The actual framework detection in decorators happens in detect_framework_cached().
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Try to get framework from weak cache first
        with _weak_cache_lock:
            if func in _weak_function_cache:
                framework = _weak_function_cache[func]
                logger.debug(f"Weak function cache HIT for {func.__name__}: {framework}")
            else:
                # Detect framework and cache it
                framework = detect_framework(func, *args, **kwargs)
                _weak_function_cache[func] = framework
                logger.debug(f"Weak function cache SET for {func.__name__}: {framework}")
        
        # Don't modify the function signature - just call the original function
        return func(*args, **kwargs)
    
    return wrapper


def _get_detection_cache() -> FrameworkDetectionCache:
    """Get or create the global detection cache."""
    global _detection_cache
    if _detection_cache is None:
        try:
            config = get_config()
            cache_size = config.framework_detection_cache_size
        except Exception:
            # Fallback to default if config is not available
            cache_size = 1000
        _detection_cache = FrameworkDetectionCache(max_size=cache_size)
    return _detection_cache


def _get_optimized_detector() -> OptimizedFrameworkDetection:
    """Get or create the global optimized detector."""
    global _optimized_detector
    if _optimized_detector is None:
        _optimized_detector = OptimizedFrameworkDetection()
    return _optimized_detector


def _check_module_imported(module_name: str) -> bool:
    """Check if a module is imported in the current Python environment."""
    return module_name in sys.modules


@lru_cache(maxsize=256)
def _identify_object_framework_cached(
    obj_type: type, obj_module: str, obj_class: str
) -> Optional[str]:
    """Cached version of object framework identification."""
    return _get_optimized_detector().identify_object_framework(
        type(
            "obj",
            (obj_type,),
            {
                "__module__": obj_module,
                "__class__": type("cls", (), {"__name__": obj_class}),
            },
        )()
    )


def _identify_object_framework(obj: Any) -> Optional[str]:
    """
    Try to identify the framework an object belongs to based on its module or class.
    Now optimized with caching.
    """
    if obj is None:
        return None

    # Use optimized detector for better performance
    return _get_optimized_detector().identify_object_framework(obj)


def _check_imported_frameworks() -> List[str]:
    """Check which known frameworks are imported (with caching)."""
    return _get_optimized_detector()._get_cached_imported_frameworks()


def detect_framework_cached(
    func_or_class: Optional[Union[Callable[..., Any], Type[Any]]] = None,
    *args: Any,
    **kwargs: Any,
) -> str:
    """
    Optimized framework detection with caching.
    This is the recommended function to use for best performance.
    """
    # Check cache first
    cached_result = _get_detection_cache().get(func_or_class, args, kwargs)
    if cached_result is not None:
        return cached_result

    # Perform detection
    framework = detect_framework(func_or_class, *args, **kwargs)

    # Cache result
    _get_detection_cache().set(func_or_class, framework, args, kwargs)

    return framework


def detect_framework(
    func_or_class: Optional[Union[Callable[..., Any], Type[Any]]] = None,
    *args: Any,
    **kwargs: Any,
) -> str:
    """
    Detect which LLM framework is being used based on the decorated function/class,
    its arguments, or imported modules in the current environment.

    Args:
        func_or_class: The function or class being decorated
        *args: Optional positional arguments to check
        **kwargs: Optional keyword arguments to check

    Returns:
        The detected framework name or "standard" if none is detected
    """
    # Check if we have an explicit framework hint in kwargs (used by guardrails)
    if kwargs and "framework" in kwargs and isinstance(kwargs["framework"], str):
        explicit_framework = kwargs["framework"]
        logger.debug(f"Using explicitly specified framework: {explicit_framework}")
        return explicit_framework

    # Step 1: Check the function or class itself
    if func_or_class:
        # If it's a class or function, check its module
        framework = _identify_object_framework(func_or_class)
        if framework:
            return framework

        # If it's a method, check the class it belongs to
        if inspect.isfunction(func_or_class) or inspect.ismethod(func_or_class):
            # Get the module where the function is defined
            module = inspect.getmodule(func_or_class)
            if module:
                framework = _identify_object_framework(module)
                if framework:
                    return framework

    # Step 2: Check the args and kwargs for framework-specific objects
    all_objects = list(args) if args else []
    if kwargs:
        all_objects.extend(kwargs.values())

    for obj in all_objects:
        framework = _identify_object_framework(obj)
        if framework:
            return framework

    # Step 3: Check if any framework is imported (now cached)
    imported_frameworks = _check_imported_frameworks()
    if imported_frameworks:
        # If multiple frameworks are imported, OpenAI Agents takes precedence,
        # otherwise use the first one found
        if (
            "agents_sdk" in imported_frameworks
            or "openai_agents" in imported_frameworks
        ):
            return "agents_sdk"  # Unified OpenAI Agents SDK
        return imported_frameworks[0]

    # Step 4: Fallback to default
    logger.debug("No specific framework detected, using 'standard'")
    return "standard"


def get_detection_cache_stats() -> Dict[str, Any]:
    """Get framework detection cache statistics."""
    main_stats = _get_detection_cache().get_stats()
    
    # Add weak function cache stats
    with _weak_cache_lock:
        weak_function_cache_size = len(_weak_function_cache)
    
    main_stats["weak_function_cache"] = {
        "size": weak_function_cache_size,
        "description": "Direct function-to-framework mapping using weak references"
    }
    
    return main_stats


def clear_detection_cache() -> None:
    """Clear all framework detection caches."""
    _get_detection_cache().clear()
    
    with _weak_cache_lock:
        _weak_function_cache.clear()
    
    logger.info("All framework detection caches cleared")


def get_weak_cache_stats() -> Dict[str, Any]:
    """Get statistics about weak reference caches specifically."""
    with _weak_cache_lock:
        return {
            "weak_function_cache_size": len(_weak_function_cache),
            "main_cache_stats": _get_detection_cache().get_stats(),
        }


def is_openai_agent(obj: Any) -> bool:
    """Check if an object is an OpenAI Agent"""
    try:
        from agents import Agent

        return isinstance(obj, Agent)
    except ImportError:
        return False


def is_langchain_agent(obj: Any) -> bool:
    """Check if an object is a LangChain agent"""
    try:
        # Check both old and new LangChain imports
        try:
            from langchain.agents import AgentExecutor

            return isinstance(obj, AgentExecutor)
        except ImportError:
            from langchain.agents.agent import AgentExecutor

            return isinstance(obj, AgentExecutor)
    except ImportError:
        return False


def is_crewai_agent(obj: Any) -> bool:
    """Check if an object is a CrewAI agent"""
    try:
        from crewai import Agent

        return isinstance(obj, Agent)
    except ImportError:
        return False


def is_llamaindex_agent(obj: Any) -> bool:
    """Check if an object is a LlamaIndex agent"""
    try:
        from llama_index.agent import Agent

        return isinstance(obj, Agent)
    except ImportError:
        return False


def is_langgraph_object(obj: Any) -> bool:
    """Check if an object is a LangGraph object"""
    try:
        # Check by module and class name for better compatibility
        obj_module = getattr(obj, "__module__", "")
        obj_class = getattr(obj, "__class__", type(obj)).__name__

        # LangGraph patterns
        langgraph_modules = ["langgraph.graph", "langgraph.checkpoint", "langgraph"]
        langgraph_classes = ["Graph", "StateGraph", "MessageGraph", "CompiledGraph"]

        is_langgraph_module = any(
            obj_module.startswith(mod) for mod in langgraph_modules
        )
        is_langgraph_class = obj_class in langgraph_classes

        if is_langgraph_module or is_langgraph_class:
            return True

        # Fallback to isinstance check if available
        try:
            from langgraph.graph import Graph, StateGraph, MessageGraph, CompiledGraph

            return isinstance(obj, (Graph, StateGraph, MessageGraph, CompiledGraph))
        except ImportError:
            pass

        return False
    except Exception:
        return False
