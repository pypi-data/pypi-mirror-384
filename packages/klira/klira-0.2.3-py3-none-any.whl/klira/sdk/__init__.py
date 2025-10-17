"""Core SDK module for Klira AI."""

import os
import sys
import logging
import asyncio
from typing import Optional, Set, Dict, Any, TYPE_CHECKING, List, Type, Callable
from urllib.parse import urlparse

from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import SpanExporter
from opentelemetry.propagators.textmap import TextMapPropagator

from klira.version import __version__
from klira.sdk.client import Client
from klira.sdk.decorators import workflow, task, agent, tool, add_policies, crew
from klira.sdk.guardrails.engine import GuardrailsEngine
from klira.sdk.config import (
    get_policies_path,
    get_config,
    set_config,
    KliraConfig,
    reset_config,
)
from klira.sdk.utils.error_handler import handle_errors
from klira.sdk.utils.framework_registry import (
    FrameworkRegistry,
    LLMClientRegistry,
    register_all_framework_adapters,
    register_all_llm_adapters,
)
from klira.sdk.decorators.guardrails import guardrails
from klira.sdk._lazy_imports import get_lazy_framework_adapter, get_lazy_function

# --- Traceloop and its dummy definitions must come after all top-level package imports ---
# Use try-except for Traceloop import
try:
    from traceloop.sdk import Traceloop
    from traceloop.sdk.instruments import Instruments

    TRACELOOP_INSTALLED = True
except ImportError:
    TRACELOOP_INSTALLED = False

    # Define dummy Traceloop and Instruments if not installed
    class _DummyTraceloop:
        @staticmethod
        def init(*args: Any, **kwargs: Any) -> None:
            # Logger not available yet, use print for this critical fallback message
            print(
                "[Klira AI SDK Fallback] Traceloop SDK not found. Klira AI tracing disabled.",
                file=sys.stderr,
            )
            return None

        @staticmethod
        def set_association_properties(*args: Any, **kwargs: Any) -> None:
            pass

        @staticmethod
        def set_prompt(*args: Any, **kwargs: Any) -> None:
            pass

    class _DummyInstruments:
        pass

    # Assign dummy classes to the expected names
    Traceloop = _DummyTraceloop
    Instruments = _DummyInstruments

# Logger initialization must be AFTER all imports and crucial try/except blocks like Traceloop
logger = logging.getLogger(__name__)

# --- Lazy Adapter Loading ---
# Adapters are now loaded on-demand to prevent circular imports and improve startup time


def _get_openai_agents_adapter() -> Optional[Type[Any]]:
    """Get OpenAI Agents adapter with fallback support."""
    lazy_adapter = get_lazy_framework_adapter("openai_agents")
    if lazy_adapter:
        return lazy_adapter.get_class()
    return None


def _get_langchain_adapter() -> Optional[Type[Any]]:
    """Get LangChain adapter."""
    lazy_adapter = get_lazy_framework_adapter("langchain")
    if lazy_adapter:
        return lazy_adapter.get_class()
    return None


def _get_llama_index_adapter() -> Optional[Type[Any]]:
    """Get LlamaIndex adapter."""
    lazy_adapter = get_lazy_framework_adapter("llama_index")
    if lazy_adapter:
        return lazy_adapter.get_class()
    return None


def _get_crew_ai_adapter() -> Optional[Type[Any]]:
    """Get CrewAI adapter."""
    lazy_adapter = get_lazy_framework_adapter("crewai")
    if lazy_adapter:
        return lazy_adapter.get_class()
    return None


def _get_add_klira_guardrails() -> Callable[..., Any]:
    """Get add_klira_guardrails function with fallback."""
    lazy_func = get_lazy_function("add_klira_guardrails")
    if lazy_func:
        func_class = lazy_func.get_class()
        if func_class is not None:
            return func_class

    # Fallback function if not available
    def _dummy_add_klira_guardrails(*args: Any, **kwargs: Any) -> None:
        logger.warning("add_klira_guardrails is not available in this installation")

    return _dummy_add_klira_guardrails


# Expose adapters for backward compatibility with lazy loading
# These will be loaded when first accessed
OpenAIAgentsAdapter: Optional[Type[Any]] = None  # Will be loaded lazily
LangChainAdapter: Optional[Type[Any]] = None  # Will be loaded lazily
LlamaIndexAdapter: Optional[Type[Any]] = None  # Will be loaded lazily
CrewAIAdapter: Optional[Type[Any]] = None  # Will be loaded lazily
add_klira_guardrails = _get_add_klira_guardrails()


def get_openai_agents_adapter() -> Optional[Type[Any]]:
    """Get OpenAI Agents adapter, loading it if necessary."""
    global OpenAIAgentsAdapter
    if OpenAIAgentsAdapter is None:
        OpenAIAgentsAdapter = _get_openai_agents_adapter()
    return OpenAIAgentsAdapter


def get_langchain_adapter() -> Optional[Type[Any]]:
    """Get LangChain adapter, loading it if necessary."""
    global LangChainAdapter
    if LangChainAdapter is None:
        LangChainAdapter = _get_langchain_adapter()
    return LangChainAdapter


def get_llama_index_adapter() -> Optional[Type[Any]]:
    """Get LlamaIndex adapter, loading it if necessary."""
    global LlamaIndexAdapter
    if LlamaIndexAdapter is None:
        LlamaIndexAdapter = _get_llama_index_adapter()
    return LlamaIndexAdapter


def get_crew_ai_adapter() -> Optional[Type[Any]]:
    """Get CrewAI adapter, loading it if necessary."""
    global CrewAIAdapter
    if CrewAIAdapter is None:
        CrewAIAdapter = _get_crew_ai_adapter()
    return CrewAIAdapter


# Track if adapters already registered/patched
_framework_adapters_registered = False
_frameworks_patched = False
_llm_adapters_registered = False
_llm_clients_patched = False
_lazy_registration_scheduled = False

# --- Lazy Registration System ---


def schedule_lazy_registration() -> None:
    """Schedule lazy registration to happen on first use instead of upfront."""
    global _lazy_registration_scheduled
    if not _lazy_registration_scheduled:
        logger.debug(
            "Klira AI: Lazy registration scheduled - adapters will load on first use"
        )
        _lazy_registration_scheduled = True


def ensure_adapters_registered() -> None:
    """Ensure adapters are registered when needed (called on first use)."""
    global _framework_adapters_registered, _llm_adapters_registered

    if not _framework_adapters_registered:
        logger.debug("Klira AI: Lazy loading framework adapters on first use...")
        framework_instances = register_all_framework_adapters()
        # Explicitly ensure 'standard' maps to None if not set by registration
        if "standard" not in FrameworkRegistry.get_all_adapter_instances():
            if "standard" not in FrameworkRegistry._adapter_classes:
                # Fix: Use Optional type instead of None assignment
                FrameworkRegistry._adapter_classes["standard"] = None  # type: ignore[assignment]
                logger.debug("Registered None adapter class for 'standard' framework.")
        _framework_adapters_registered = True
        logger.info(
            f"Klira: Framework adapters lazy loaded: {list(framework_instances.keys())}"
        )

    if not _llm_adapters_registered:
        logger.debug("Klira: Lazy loading LLM client adapters on first use...")
        llm_instances = register_all_llm_adapters()
        _llm_adapters_registered = True
        logger.info(
            f"Klira: LLM client adapters lazy loaded: {list(llm_instances.keys())}"
        )


def ensure_frameworks_patched() -> None:
    """Ensure frameworks are patched when needed (called on first use)."""
    global _frameworks_patched, _llm_clients_patched

    # Ensure adapters are registered first
    ensure_adapters_registered()

    if not _frameworks_patched:
        logger.debug("Klira: Lazy patching frameworks on first use...")
        patched_count = _patch_frameworks_sync_fallback()
        _frameworks_patched = True
        logger.info(
            f"Klira: Framework patching completed for {patched_count} adapters (sync)."
        )

    if not _llm_clients_patched:
        logger.debug("Klira: Lazy patching LLM clients on first use...")
        patched_llm_count = _patch_llm_clients_sync()
        _llm_clients_patched = True
        logger.info(
            f"Klira: LLM client patching completed for {patched_llm_count} adapters."
        )


def _patch_frameworks_sync_fallback() -> int:
    """Patch framework adapters synchronously as fallback."""
    framework_adapters = FrameworkRegistry.get_all_adapter_instances()
    patched_count = 0
    
    for name, adapter_instance in framework_adapters.items():
        if adapter_instance is not None and hasattr(adapter_instance, "patch_framework"):
            try:
                logger.debug(f"Klira: Calling patch_framework for {name} framework adapter")
                # Check if patch_framework is async and handle accordingly
                if asyncio.iscoroutinefunction(adapter_instance.patch_framework):
                    # For async patch methods, create a simple sync wrapper
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(adapter_instance.patch_framework())
                        loop.close()
                    except Exception as async_e:
                        logger.warning(f"Async patching failed for {name}, trying sync: {async_e}")
                        # If async fails, check if there's a sync alternative
                        if hasattr(adapter_instance, "patch_framework_sync"):
                            adapter_instance.patch_framework_sync()
                        else:
                            raise async_e
                else:
                    # Sync patch method
                    adapter_instance.patch_framework()
                patched_count += 1
            except Exception as e:
                logger.error(f"Klira AI Error patching framework {name}: {e}", exc_info=True)
    
    return patched_count


def _patch_llm_clients_sync() -> int:
    """Patch LLM client adapters synchronously."""
    llm_adapters = LLMClientRegistry.get_all_llm_adapter_instances()
    patched_llm_count = 0
    
    for name, llm_adapter_instance in llm_adapters.items():
        if llm_adapter_instance is not None:
            try:
                logger.debug(f"Klira AI: Calling patch for {name} LLM client adapter")
                if hasattr(llm_adapter_instance, "patch"):
                    # Check if patch method is async
                    if asyncio.iscoroutinefunction(llm_adapter_instance.patch):
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(llm_adapter_instance.patch())
                            loop.close()
                        except Exception as async_e:
                            logger.warning(f"Async patching failed for {name}, trying sync: {async_e}")
                            if hasattr(llm_adapter_instance, "patch_sync"):
                                llm_adapter_instance.patch_sync()
                            else:
                                raise async_e
                    else:
                        # Sync patch method
                        llm_adapter_instance.patch()
                patched_llm_count += 1
            except Exception as e:
                logger.error(f"Klira AI Error patching LLM client {name}: {e}", exc_info=True)
    
    return patched_llm_count


async def ensure_frameworks_patched_async() -> None:
    """Async version of ensure_frameworks_patched for use in async contexts."""
    global _frameworks_patched, _llm_clients_patched

    # Ensure adapters are registered first
    ensure_adapters_registered()

    if not _frameworks_patched:
        logger.debug("Klira AI: Lazy patching frameworks on first use (async)...")
        patched_count = await patch_all_frameworks_async()
        _frameworks_patched = True
        logger.info(
            f"Klira AI: Framework patching completed for {patched_count} adapters (async)."
        )

    if not _llm_clients_patched:
        logger.debug("Klira AI: Lazy patching LLM clients on first use (async)...")
        patched_llm_count = await _patch_llm_clients_async()
        _llm_clients_patched = True
        logger.info(
            f"Klira AI: LLM client patching completed for {patched_llm_count} adapters (async)."
        )


async def _patch_llm_clients_async() -> int:
    """Patch LLM client adapters asynchronously."""
    llm_adapters = LLMClientRegistry.get_all_llm_adapter_instances()
    patch_tasks = []
    
    for name, llm_adapter_instance in llm_adapters.items():
        if llm_adapter_instance is not None and hasattr(llm_adapter_instance, "patch"):
            patch_tasks.append(_patch_llm_client_async(name, llm_adapter_instance))
    
    results = await asyncio.gather(*patch_tasks, return_exceptions=True)
    return sum(1 for r in results if r is True)


async def _patch_llm_client_async(name: str, adapter_instance: Any) -> bool:
    """Patch a single LLM client adapter asynchronously."""
    try:
        logger.debug(f"Klira AI: Calling patch for {name} LLM client adapter (async)")
        if asyncio.iscoroutinefunction(adapter_instance.patch):
            await adapter_instance.patch()
        else:
            # Run sync method in thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(None, adapter_instance.patch)
        return True
    except Exception as e:
        logger.error(f"Klira AI Error patching LLM client {name}: {e}", exc_info=True)
        return False


def register_and_patch_all() -> None:
    """Register and patch both framework and LLM client adapters. Idempotent.

    DEPRECATED: Use schedule_lazy_registration() for better performance.
    This function is kept for backward compatibility.
    """
    logger.warning(
        "register_and_patch_all() is deprecated. Consider using lazy registration for better performance."
    )
    ensure_adapters_registered()
    ensure_frameworks_patched()


async def patch_framework_async(name: str, adapter_instance: Any) -> bool:
    """Asynchronously patch a framework adapter.

    Args:
        name: Name of the framework adapter
        adapter_instance: The adapter instance to patch

    Returns:
        bool: True if patching was successful, False otherwise
    """
    if adapter_instance is not None and hasattr(adapter_instance, "patch_framework"):
        try:
            logger.debug(f"Klira AI: Calling patch_framework for {name} framework adapter (async)")
            # If patch_framework is async, await it, otherwise run in executor
            if asyncio.iscoroutinefunction(adapter_instance.patch_framework):
                await adapter_instance.patch_framework()
            else:
                # Run sync method in thread pool to avoid blocking the event loop
                await asyncio.get_event_loop().run_in_executor(
                    None, adapter_instance.patch_framework
                )
            return True
        except Exception as e:
            logger.error(f"Klira AI Error patching framework {name}: {e}", exc_info=True)
    return False


async def patch_all_frameworks_async() -> int:
    """Patch all framework adapters in parallel.

    Returns:
        int: Number of successfully patched adapters
    """
    framework_adapters = FrameworkRegistry.get_all_adapter_instances()
    patch_tasks: List[asyncio.Task[bool]] = []

    # Create tasks for all adapters
    for name, adapter_instance in framework_adapters.items():
        patching_task = asyncio.create_task(
            patch_framework_async(name, adapter_instance)
        )
        patch_tasks.append(patching_task)

    # Wait for all tasks to complete
    results = await asyncio.gather(*patch_tasks, return_exceptions=True)

    # Count successful patches
    patched_count = sum(1 for r in results if r is True)
    return patched_count


async def async_patch_frameworks() -> None:
    """Asynchronously patch frameworks in background."""
    patched_count = await patch_all_frameworks_async()
    logger.info(
        f"Klira AI: Framework patching completed for {patched_count} adapters (parallel background)."
    )
    global _frameworks_patched
    _frameworks_patched = True


# Configure logger for Klira AI SDK
logger = logging.getLogger("klira")
# Set log level to WARNING by default to reduce verbosity
logger.setLevel(logging.WARNING)

# Import the protocol for type hinting
if TYPE_CHECKING:
    from klira.sdk.guardrails.llm_service import LLMServiceProtocol


class Klira:
    """Main Klira AI SDK class for initializing observability and policy enforcement."""

    __client: Optional[Client] = None
    __guardrails: Optional[GuardrailsEngine] = None
    __initialized = (
        False  # Flag to prevent multiple initializations / adapter registrations
    )

    @staticmethod
    def init(
        api_key: str,
        app_name: str = sys.argv[0],
        opentelemetry_endpoint: Optional[str] = None,
        enabled: bool = True,
        telemetry_enabled: bool = False,  # Klira AI defaults this to False
        headers: Dict[str, str] = {},
        disable_batch: bool = False,
        exporter: Optional[SpanExporter] = None,
        processor: Optional[SpanProcessor] = None,
        propagator: Optional[TextMapPropagator] = None,
        instruments: Optional[Set[Any]] = None,
        block_instruments: Optional[Set[Any]] = None,
        resource_attributes: Dict[str, Any] = {},
        policies_path: Optional[str] = None,
        llm_service: Optional["LLMServiceProtocol"] = None,
        verbose: bool = False,  # Enable this to get more detailed logs
        **kwargs: Any,
    ) -> Optional[Client]:
        """
        Initialize the Klira AI SDK.

        Args:
            api_key: Your Klira AI API key (required). Can also be set via KLIRA_API_KEY env var.
            app_name: Name of your application.
            opentelemetry_endpoint: OTLP endpoint (KLIRA_OPENTELEMETRY_ENDPOINT env var).
            enabled: Whether tracing is enabled.
            telemetry_enabled: Allow Traceloop's telemetry (default: False).
            headers: Custom headers for API requests.
            disable_batch: Disable batch processing.
            exporter: Custom span exporter.
            processor: Custom span processor.
            propagator: Custom propagator.
            instruments: Instruments to enable.
            block_instruments: Instruments to block.
            resource_attributes: Additional OTel resource attributes.
            policies_path: Path to guardrail policies.
            llm_service: LLM service for guardrails.
            verbose: Set to True to get detailed INFO-level logs.
            **kwargs: Additional args for Traceloop.

        Returns:
            Optional[Client]: Klira AI client or None.
            
        Raises:
            ValueError: If API key is missing or has invalid format.
        """
        # Validate API key requirement
        if not api_key:
            # Try environment variable as fallback
            env_api_key = os.getenv("KLIRA_API_KEY")
            if not env_api_key:
                raise ValueError(
                    "Klira AI API key is required. Provide via 'api_key' parameter or KLIRA_API_KEY environment variable. "
                    "Get your API key at https://getklira.com"
                )
            api_key = env_api_key
        
        # Validate API key format
        if not api_key.startswith("klira_"):
            raise ValueError(
                "Invalid Klira AI API key format. API key must start with 'klira_'. "
                "Get your API key at https://klira.ai"
            )
        
        # Call internal initialization method with error handling
        return Klira._init_internal(
            api_key, app_name, opentelemetry_endpoint, enabled, telemetry_enabled,
            headers, disable_batch, exporter, processor, propagator, instruments,
            block_instruments, resource_attributes, policies_path, llm_service,
            verbose, **kwargs
        )

    @staticmethod
    @handle_errors(fail_closed=False, default_return_on_error=None)
    def _init_internal(
        api_key: str,
        app_name: str,
        opentelemetry_endpoint: Optional[str],
        enabled: bool,
        telemetry_enabled: bool,
        headers: Dict[str, str],
        disable_batch: bool,
        exporter: Optional[SpanExporter],
        processor: Optional[SpanProcessor],
        propagator: Optional[TextMapPropagator],
        instruments: Optional[Set[Any]],
        block_instruments: Optional[Set[Any]],
        resource_attributes: Dict[str, Any],
        policies_path: Optional[str],
        llm_service: Optional["LLMServiceProtocol"],
        verbose: bool,
        **kwargs: Any,
    ) -> Optional[Client]:
        """Internal initialization method with error handling."""
        # Create centralized configuration from parameters
        config_overrides: Dict[str, Any] = {}
        if app_name != sys.argv[0]:  # Only override if explicitly provided
            config_overrides["app_name"] = app_name
        # API key is now guaranteed to be set after validation above
        config_overrides["api_key"] = api_key
        if opentelemetry_endpoint is not None:
            config_overrides["opentelemetry_endpoint"] = opentelemetry_endpoint
        if not enabled:  # Only override if explicitly disabled
            config_overrides["tracing_enabled"] = enabled
        if telemetry_enabled:  # Only override if explicitly enabled
            config_overrides["telemetry_enabled"] = telemetry_enabled
        if policies_path is not None:
            config_overrides["policies_path"] = policies_path
        if verbose:  # Only override if explicitly enabled
            config_overrides["verbose"] = verbose

        # Get existing config or create new one
        try:
            # If we have an existing global config, use it as base
            existing_config = get_config()
            if config_overrides:
                # Apply overrides to existing config
                for key, value in config_overrides.items():
                    if hasattr(existing_config, key):
                        setattr(existing_config, key, value)
                config = existing_config
            else:
                # No overrides, use existing config as-is
                config = existing_config
        except Exception:
            # No existing config, create new one from environment
            config = KliraConfig.from_env(**config_overrides)

        # Validate configuration
        validation_errors = config.validate()
        if validation_errors:
            logger.warning(f"Configuration validation issues: {validation_errors}")

        # Set as global configuration
        set_config(config)

        # Set logging level based on verbose flag or config
        if config.verbose or config.debug_mode:
            logger.setLevel(logging.INFO)
            # Also set the package-level loggers to INFO
            for name in [
                "klira.decorators",
                "klira.adapters",
                "klira.guardrails",
                "klira.utils",
            ]:
                pkg_logger = logging.getLogger(name)
                pkg_logger.setLevel(logging.INFO)

        if Klira.__initialized:
            logger.warning(
                "Klira.init() called multiple times. Skipping re-initialization."
            )
            # Always return a client instance for testing compatibility
            if Klira.__client is None:
                Klira.__client = "dummy_client"  # type: ignore[assignment]
            return Klira.__client

        # Ensure Traceloop is available
        if not TRACELOOP_INSTALLED:
            logger.error(
                "Traceloop SDK is not installed. Klira AI SDK requires Traceloop for tracing. Please install it: pip install traceloop-sdk"
            )
            # Decide whether to proceed without tracing or halt. Let's proceed but disable.
            config.tracing_enabled = False

        # Force disable Traceloop's anonymous usage telemetry unless explicitly enabled
        if not config.telemetry_enabled and "TRACELOOP_TELEMETRY" not in os.environ:
            os.environ["TRACELOOP_TELEMETRY"] = "FALSE"
            logger.debug(
                "Klira AI: Traceloop telemetry explicitly disabled (set telemetry_enabled=True to override)."
            )
        elif os.environ.get("TRACELOOP_TELEMETRY", "").upper() == "TRUE":
            logger.debug("Klira AI: Traceloop telemetry enabled via environment variable.")
        elif config.telemetry_enabled:
            logger.debug("Klira AI: Traceloop telemetry enabled via configuration.")
            # Optionally set the env var if needed by Traceloop internal checks
            os.environ["TRACELOOP_TELEMETRY"] = "TRUE"

        actual_api_key = config.api_key
        user_provided_endpoint = config.opentelemetry_endpoint
        klira_default_endpoint = "https://api.getklira.com"

        # --- Configuration Validation (Simplified) ---
        final_endpoint: Optional[str] = None
        final_headers = headers.copy()
        final_api_key = actual_api_key

        if actual_api_key:
            final_endpoint = klira_default_endpoint
            # Add Klira AI API key header if using Klira AI endpoint
            final_headers["Authorization"] = f"Bearer {actual_api_key}"
            if (
                user_provided_endpoint
                and user_provided_endpoint != klira_default_endpoint
            ):
                logger.warning(
                    f"KLIRA_API_KEY is set, ignoring provided opentelemetry_endpoint ('{user_provided_endpoint}') "
                    f"and using the default Klira AI endpoint ('{final_endpoint}')."
                )
        elif user_provided_endpoint:
            # Validate the provided endpoint URL
            try:
                parsed_url = urlparse(user_provided_endpoint)
                if not all([parsed_url.scheme, parsed_url.netloc]):
                    raise ValueError("Invalid KLIRA_OPENTELEMETRY_ENDPOINT URL format.")
                logger.debug(f"Using provided OTLP endpoint: {user_provided_endpoint}")
                final_endpoint = user_provided_endpoint
                final_api_key = None  # No API key if using custom endpoint
            except ValueError as e:
                logger.error(f"Configuration error: {e}. Disabling Klira AI tracing.")
                config.tracing_enabled = False
        # Note: The else branch is no longer reachable since API key is now mandatory
        # and validated at the beginning of this method
        # --- End Configuration Validation ---

        if not config.tracing_enabled:
            logger.warning(
                "Klira AI tracing is disabled due to configuration issues or explicit setting."
            )

        # --- Initialize Traceloop ---
        # Pass telemetry_enabled=False explicitly if we disabled it
        traceloop_telemetry_flag = config.telemetry_enabled or (
            os.environ.get("TRACELOOP_TELEMETRY", "").upper() == "TRUE"
        )

        # Skip expensive exporter initialization if telemetry is disabled
        if not config.tracing_enabled or (not final_endpoint and not exporter):
            logger.debug(
                "Klira AI: Skipping OpenTelemetry exporter initialization as tracing is disabled."
            )
            # Use minimal Traceloop initialization for internal tracing only
            traceloop_params = {
                "app_name": config.app_name,
                "enabled": False,  # Explicitly disable external tracing
                "telemetry_enabled": traceloop_telemetry_flag,
            }
            # No exporter or processor needed when disabled
        else:
            # Full Traceloop initialization with exporters
            traceloop_params = {
                "app_name": config.app_name,
                "api_endpoint": final_endpoint,
                "api_key": final_api_key,  # Pass None if using custom endpoint
                "enabled": config.tracing_enabled,
                "disable_batch": disable_batch,
                "headers": final_headers,
                "exporter": exporter,
                "processor": processor,
                "propagator": propagator,
                "instruments": instruments,
                "block_instruments": block_instruments,
                "resource_attributes": resource_attributes,
                "telemetry_enabled": traceloop_telemetry_flag,
            }

        # Add any additional kwargs
        for key, value in kwargs.items():
            if key not in traceloop_params:  # Avoid overriding our explicit settings
                traceloop_params[key] = value

        # Initialize Traceloop
        try:
            logger.debug(f"Klira AI: Initializing Traceloop with endpoint={final_endpoint}")
            Traceloop.init(**traceloop_params)
            logger.info(
                f"Klira AI: Traceloop initialized for telemetry. Endpoint: {final_endpoint}"
            )
        except Exception as e:
            logger.error(f"Error initializing Traceloop: {e}", exc_info=True)

        # Initialize performance instrumentation
        if config.tracing_enabled:
            try:
                from klira.sdk.performance import init_performance_instrumentation

                init_performance_instrumentation(config.app_name)
                logger.debug("Klira AI: Performance instrumentation initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize performance instrumentation: {e}")
        # --- End Traceloop Initialization ---

        # --- Klira AI Adapter Registration & Patching ---
        # Use modern lazy registration approach instead of deprecated register_and_patch_all()
        if config.tracing_enabled:  # Only register/patch if Klira AI/tracing is enabled
            try:
                logger.debug("Klira AI: Scheduling lazy adapter registration...")
                schedule_lazy_registration()
                # Ensure adapters are registered immediately for critical functionality
                ensure_adapters_registered()
                ensure_frameworks_patched()
            except Exception as e:
                logger.error(
                    f"Error during Klira AI adapter registration/patching: {e}",
                    exc_info=True,
                )
        else:
            logger.info(
                "Klira AI tracing/guardrails disabled, skipping adapter registration and patching."
            )

        # --- Client and Guardrails Initialization ---
        # Initialize GuardrailsEngine with proper LLM service
        try:
            # Create OpenAI client if we have an API key and no custom LLM service provided
            if llm_service is None and os.environ.get("OPENAI_API_KEY"):
                try:
                    from openai import AsyncOpenAI

                    openai_client = AsyncOpenAI(
                        api_key=os.environ.get("OPENAI_API_KEY")
                    )
                    # Cast to proper type to resolve the assignment error
                    llm_service = openai_client 
                    logger.debug("Created OpenAI client for guardrails LLM service")
                except ImportError:
                    logger.warning(
                        "OpenAI library not available. Guardrails will use DefaultLLMService."
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to create OpenAI client: {e}. Guardrails will use DefaultLLMService."
                    )

            # Initialize guardrails engine with configuration
            guardrails_config: Dict[str, Any] = {
                "policies_path": config.policies_path,
                "llm_service": llm_service,
            }
            Klira.__guardrails = GuardrailsEngine.get_instance(guardrails_config)
            GuardrailsEngine.lazy_initialize()  # Ensure components are initialized
            logger.debug("GuardrailsEngine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GuardrailsEngine: {e}", exc_info=True)
            Klira.__guardrails = None

        # Initialize Client (placeholder for now)
        # For now, return a dummy client to indicate successful initialization
        Klira.__client = "klira_client"  # type: ignore[assignment] # TODO: Implement actual client initialization

        Klira.__initialized = True
        logger.info(f"Klira AI SDK initialized successfully (version {__version__})")
        return Klira.__client

    @staticmethod
    def _reset_instance() -> None:
        """Reset the Klira SDK instance state (for testing purposes only).

        WARNING: This is intended for test isolation only and should not be used in production code.
        """
        Klira.__initialized = False
        Klira.__client = None
        Klira.__guardrails = None

        # Reset GuardrailsEngine singleton state
        from klira.sdk.guardrails.engine import GuardrailsEngine
        GuardrailsEngine._instance = None
        GuardrailsEngine._initialized.clear()

        logger.debug("Klira SDK instance state reset")

    @staticmethod
    @handle_errors(fail_closed=True)
    def get() -> Client:
        """Get the Klira AI client instance."""
        if not Klira.__initialized:
            raise Exception("Klira AI SDK not initialized. Please call Klira.init() first.")
        if not Klira.__client:
            # Check if init was called but failed/disabled
            logger.warning(
                "Klira AI client requested but is not available. Tracing might be disabled or initialization failed."
            )
            raise Exception(
                "Klira AI Client not available. SDK might not be initialized properly (check API key/endpoint) or tracing is disabled."
            )
        return Klira.__client

    @staticmethod
    @handle_errors(fail_closed=True)
    def get_guardrails() -> GuardrailsEngine:
        """Get the Klira AI guardrails instance."""
        if not Klira.__initialized:
            raise Exception("Klira AI SDK not initialized. Please call Klira.init() first.")
        if not Klira.__guardrails:
            logger.warning(
                "Klira AI guardrails requested but are not available. Initialization might have failed."
            )
            raise Exception(
                "Klira AI Guardrails engine not available. SDK might not be initialized properly or guardrail init failed."
            )
        return Klira.__guardrails

    @staticmethod
    def set_association_properties(properties: Dict[str, Any]) -> None:
        """Set association properties for the current trace."""
        if not Klira.__initialized or not Klira.__client:
            logger.warning(
                "Klira AI SDK not initialized or client not available. Cannot set association properties."
            )
            return
        # Delegate to Traceloop (assuming it was installed and init succeeded implicitly via __client check)
        if TRACELOOP_INSTALLED:
            Traceloop.set_association_properties(properties)
        else:
            logger.warning(
                "Traceloop SDK not found. Cannot set association properties."
            )


# Public API
__all__ = [
    "Klira",
    "Client",
    "GuardrailsEngine",
    "guardrails",  # Main decorator for guardrails
    "workflow",  # Decorators re-exported
    "task",
    "agent",
    "tool",
    "add_policies",
    "crew",
    "get_policies_path",  # Configuration utility
    "get_config",  # Centralized configuration access
    "set_config",  # Centralized configuration setting
    "reset_config",  # Centralized configuration reset
    "KliraConfig",  # Centralized configuration class
    "add_klira_guardrails",  # Specific guardrail utility for agents_adapter, if public
    "__version__",  # Version information
    "TRACELOOP_INSTALLED",  # Status flag for Traceloop
    # Traceloop and Instruments might be internal details unless users need to interact with the dummy versions.
    # If they are purely internal fallbacks, they might not need to be in __all__.
    # For now, let's keep them if they were added previously, assuming a reason.
    "Traceloop",
    "Instruments",
    "OpenAIAgentsAdapter",
    "LangChainAdapter",
    "LlamaIndexAdapter",
    "CrewAIAdapter",
]
