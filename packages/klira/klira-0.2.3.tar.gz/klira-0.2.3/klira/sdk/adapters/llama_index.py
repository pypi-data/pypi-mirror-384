"""Adapter for LlamaIndex framework compatibility."""

import functools
import asyncio
import inspect
import logging
from typing import (
    Callable,
    Any,
    Union,
    Type,
    cast,
    Tuple,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
)

from opentelemetry.trace import Status, StatusCode

# Use try-except for framework imports - Fixed module assignment pattern
if TYPE_CHECKING:
    from llama_index.core.tools.types import BaseTool as LlamaIndexBaseTool
    from llama_index.core.base.base_query_engine import BaseQueryEngine
    from llama_index.core.chat_engine.types import BaseChatEngine

    LLAMA_INDEX_INSTALLED = True
    LlamaIndexBaseToolType = LlamaIndexBaseTool
    BaseQueryEngineType = BaseQueryEngine
    BaseChatEngineType = BaseChatEngine
else:
    try:
        from llama_index.core.tools.types import BaseTool as _ImportedLlamaIndexBaseTool
        from llama_index.core.base.base_query_engine import (
            BaseQueryEngine as _ImportedBaseQueryEngine,
        )

        try:
            from llama_index.core.chat_engine.types import (
                BaseChatEngine as _ImportedBaseChatEngine,
            )
        except ImportError:
            # Fallback for older LlamaIndex versions or different structuring
            from llama_index.core.base.llms.base import (
                BaseChatEngine as _ImportedBaseChatEngine,
            )  # type: ignore
        LLAMA_INDEX_INSTALLED = True
        LlamaIndexBaseToolType = _ImportedLlamaIndexBaseTool
        BaseQueryEngineType = _ImportedBaseQueryEngine
        BaseChatEngineType = _ImportedBaseChatEngine
    except ImportError:
        LLAMA_INDEX_INSTALLED = False

        # Define dummy classes
        class _DummyLlamaIndexBaseTool(object):
            metadata: Any = None

            def __call__(self, *args: Any, **kwargs: Any) -> Any:
                return None

            async def acall(self, *args: Any, **kwargs: Any) -> Any:
                return None

            def call(self, *args: Any, **kwargs: Any) -> Any:
                return None  # For older versions

        class _DummyBaseQueryEngine(object):
            def query(self, *args: Any, **kwargs: Any) -> Any:
                return None

            async def aquery(self, *args: Any, **kwargs: Any) -> Any:
                return None

        class _DummyBaseChatEngine(object):
            def chat(self, *args: Any, **kwargs: Any) -> Any:
                return None

            async def achat(self, *args: Any, **kwargs: Any) -> Any:
                return None

        LlamaIndexBaseToolType = _DummyLlamaIndexBaseTool  # type: ignore
        BaseQueryEngineType = _DummyBaseQueryEngine  # type: ignore
        BaseChatEngineType = _DummyBaseChatEngine  # type: ignore

# Use the type aliases directly instead
LlamaIndexBaseTool = LlamaIndexBaseToolType
BaseQueryEngine = BaseQueryEngineType
BaseChatEngine = BaseChatEngineType


# Use try-except for Traceloop import
TRACELOOP_INSTALLED: bool
_tracer_provider: Optional[Callable[[], Any]] = None
try:
    from traceloop.sdk.tracing import get_tracer as _real_get_tracer

    _tracer_provider = _real_get_tracer
    TRACELOOP_INSTALLED = True
except ImportError:
    TRACELOOP_INSTALLED = False

    class _DummySpan:
        def set_attribute(self, key: str, value: Any) -> None:
            pass

        def set_status(self, status: Status) -> None:
            pass

        def record_exception(self, exception: Exception) -> None:
            pass

        def __enter__(self) -> "_DummySpan":
            return self

        def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            pass

    class _DummyTracer:
        def start_as_current_span(self, name: str, **kwargs: Any) -> _DummySpan:
            return _DummySpan()

    def _dummy_get_tracer_provider() -> _DummyTracer:
        return _DummyTracer()

    _tracer_provider = _dummy_get_tracer_provider

from klira.sdk.adapters.base import BaseAdapter  # noqa: E402
from klira.sdk.telemetry import Telemetry  # noqa: E402

get_tracer = cast(Callable[[], Any], _tracer_provider)

logger = logging.getLogger(__name__)  # Use __name__ for logger


class LlamaIndexAdapter(BaseAdapter):
    """Adapter for LlamaIndex."""

    FRAMEWORK_NAME = "llama_index"

    def __init__(self) -> None:
        """Initialize LlamaIndex adapter and check availability."""
        super().__init__()
        if not LLAMA_INDEX_INSTALLED:
            logger.info(
                "LlamaIndex not detected. LlamaIndexAdapter will not instrument."
            )
        if (
            not TRACELOOP_INSTALLED
        ):  # This check can be part of BaseAdapter or individual methods
            logger.info(
                "Traceloop SDK not detected. Tracing will be disabled for LlamaIndexAdapter."
            )
        self.telemetry = Telemetry()

    def _get_func_name(
        self,
        func_or_class: Union[Callable[..., Any], Type[Any]],
        name: Optional[str] = None,
    ) -> str:
        """Helper to get the best name for a callable or class."""
        res_name: Optional[str] = None
        if inspect.isclass(func_or_class):
            # For classes, try to get name from metadata, then __name__
            metadata = getattr(func_or_class, "metadata", None)  # LlamaIndex specific
            res_name = (
                name
                or getattr(metadata, "name", None)
                or getattr(func_or_class, "__name__", None)
            )
        else:  # It's a Callable
            res_name = name or getattr(func_or_class, "__name__", None)

        final_name = res_name if res_name is not None else "unknown_operation"
        # Ensure it does not return None by providing a default.
        # The cast to str is only safe if res_name is confirmed to be str or a default str is provided.
        return final_name

    def _trace_function_wrapper(
        self,
        func: Callable[..., Any],
        span_name_prefix: str,  # e.g., "tool", "agent", "workflow"
        entity_name: str,  # The specific name of the tool, agent, etc.
        input_transform: Optional[
            Callable[[Tuple[Any, ...], Dict[str, Any]], Dict[str, Any]]
        ] = None,
        output_transform: Optional[Callable[[Any], Dict[str, Any]]] = None,
    ) -> Callable[..., Any]:
        """Generic tracing wrapper for sync and async functions."""
        if not TRACELOOP_INSTALLED:
            # logger.warning(f"Traceloop SDK not found. {self.FRAMEWORK_NAME} tracing for {span_name_prefix} '{entity_name}' will be disabled.")
            return func

        tracer = get_tracer()
        base_span_name = f"{self.FRAMEWORK_NAME}.{span_name_prefix}.{entity_name}"

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            if not self.telemetry.feature_enabled(
                f"{self.FRAMEWORK_NAME}.{span_name_prefix}"
            ):
                return await func(*args, **kwargs)

            attributes = {
                "framework": self.FRAMEWORK_NAME,
                f"{span_name_prefix}.name": entity_name,
            }
            if input_transform:
                attributes.update(input_transform(args, kwargs))
            else:
                # Basic input logging, ensure it's serializable and truncated
                try:
                    attributes[f"{span_name_prefix}.input.args"] = str(args)[:200]
                    attributes[f"{span_name_prefix}.input.kwargs"] = str(kwargs)[:300]
                except Exception:
                    attributes[f"{span_name_prefix}.input"] = "Error serializing input"

            with tracer.start_as_current_span(
                base_span_name, attributes=attributes
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    if output_transform:
                        span.set_attributes(output_transform(result))
                    else:
                        try:
                            span.set_attribute(
                                f"{span_name_prefix}.output", str(result)[:500]
                            )
                        except Exception:
                            span.set_attribute(
                                f"{span_name_prefix}.output", "Error serializing output"
                            )
                    return result
                except Exception as e:
                    logger.error(
                        f"Error in LlamaIndex async {span_name_prefix} '{entity_name}': {e}",
                        exc_info=True,
                    )
                    span.set_status(Status(StatusCode.ERROR, description=str(e)))
                    span.record_exception(e)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            if not self.telemetry.feature_enabled(
                f"{self.FRAMEWORK_NAME}.{span_name_prefix}"
            ):
                return func(*args, **kwargs)

            attributes = {
                "framework": self.FRAMEWORK_NAME,
                f"{span_name_prefix}.name": entity_name,
            }
            if input_transform:
                attributes.update(input_transform(args, kwargs))
            else:
                try:
                    attributes[f"{span_name_prefix}.input.args"] = str(args)[:200]
                    attributes[f"{span_name_prefix}.input.kwargs"] = str(kwargs)[:300]
                except Exception:
                    attributes[f"{span_name_prefix}.input"] = "Error serializing input"

            with tracer.start_as_current_span(
                base_span_name, attributes=attributes
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    if output_transform:
                        span.set_attributes(output_transform(result))
                    else:
                        try:
                            span.set_attribute(
                                f"{span_name_prefix}.output", str(result)[:500]
                            )
                        except Exception:
                            span.set_attribute(
                                f"{span_name_prefix}.output", "Error serializing output"
                            )
                    return result
                except Exception as e:
                    logger.error(
                        f"Error in LlamaIndex sync {span_name_prefix} '{entity_name}': {e}",
                        exc_info=True,
                    )
                    span.set_status(Status(StatusCode.ERROR, description=str(e)))
                    span.record_exception(e)
                    raise

        if asyncio.iscoroutinefunction(func):
            setattr(async_wrapper, "_klira_traced", True)
            return cast(Callable[..., Any], async_wrapper)
        else:
            setattr(sync_wrapper, "_klira_traced", True)
            return cast(Callable[..., Any], sync_wrapper)

    def adapt_tool(
        self,
        func_or_class: Union[Callable[..., Any], Type[Any]],
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[Callable[..., Any], Type[Any]]:
        """Adapts LlamaIndex tools (decorated functions or BaseTool subclasses)."""
        if not LLAMA_INDEX_INSTALLED or not TRACELOOP_INSTALLED:
            # logger.warning("LlamaIndex or Traceloop SDK not found. Skipping tool adaptation.")
            return func_or_class

        tool_name = self._get_func_name(func_or_class, name)
        # logger.debug(f"Adapting LlamaIndex tool: {tool_name}")

        if inspect.isclass(func_or_class) and issubclass(
            func_or_class, LlamaIndexBaseTool
        ):
            OriginalClass = func_or_class

            # Determine which methods to patch (call/acall or __call__/__acall__)
            call_method_name = "call" if hasattr(OriginalClass, "call") else "__call__"
            acall_method_name = (
                "acall" if hasattr(OriginalClass, "acall") else None
            )  # some tools might not have acall

            # Patch synchronous call method
            if hasattr(OriginalClass, call_method_name):
                original_call_method = getattr(OriginalClass, call_method_name)
                if not hasattr(original_call_method, "_klira_traced"):
                    wrapped_call = self._trace_function_wrapper(
                        original_call_method,
                        span_name_prefix="tool",
                        entity_name=tool_name,  # Name of the class, not instance
                    )
                    setattr(OriginalClass, call_method_name, wrapped_call)

            # Patch asynchronous call method
            if acall_method_name and hasattr(OriginalClass, acall_method_name):
                original_acall_method = getattr(OriginalClass, acall_method_name)
                if not hasattr(original_acall_method, "_klira_traced"):
                    wrapped_acall = self._trace_function_wrapper(
                        original_acall_method,
                        span_name_prefix="tool",
                        entity_name=tool_name,  # Name of the class, not instance
                    )
                    setattr(OriginalClass, acall_method_name, wrapped_acall)
            return OriginalClass
        elif callable(func_or_class):
            # It's a function-based tool (e.g. decorated with @tool)
            if not hasattr(func_or_class, "_klira_traced"):
                return self._trace_function_wrapper(
                    func_or_class, span_name_prefix="tool", entity_name=tool_name
                )
            return func_or_class

        return func_or_class  # type: ignore[unreachable]

    def adapt_agent(
        self,
        func: Callable[..., Any],  # Changed from func_or_class
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Callable[..., Any]:  # Changed return type
        """Adapts a LlamaIndex agent (e.g., QueryEngine, ChatEngine execution)."""
        if not LLAMA_INDEX_INSTALLED or not TRACELOOP_INSTALLED:
            return func

        agent_name = self._get_func_name(func, name)
        # logger.debug(f"Attempting to adapt LlamaIndex agent/engine: {agent_name}")

        if callable(func) and not inspect.isclass(
            func
        ):  # Only wrap if it's a callable, not a class
            if not hasattr(func, "_klira_traced"):
                return self._trace_function_wrapper(
                    func, span_name_prefix="agent.run", entity_name=agent_name
                )
        # If it's a class, we don't adapt it here. patch_framework should handle instances.
        return func

    def adapt_workflow(
        self,
        func: Callable[..., Any],  # Changed from func_or_class
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Callable[..., Any]:  # Changed return type
        """Adapts a LlamaIndex workflow (conceptually, could be a multi-step process)."""
        if not LLAMA_INDEX_INSTALLED or not TRACELOOP_INSTALLED:
            return func

        workflow_name = self._get_func_name(func, name)
        # logger.debug(f"Adapting LlamaIndex workflow: {workflow_name}")

        if callable(func) and not inspect.isclass(func):  # Only wrap if it's a callable
            if not hasattr(func, "_klira_traced"):
                return self._trace_function_wrapper(
                    func, span_name_prefix="workflow", entity_name=workflow_name
                )
        return func

    def adapt_task(
        self,
        func: Callable[..., Any],  # Changed from func_or_class
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Callable[..., Any]:  # Changed return type
        """Adapts a LlamaIndex task (conceptually, a single step in a workflow or agent)."""
        if not LLAMA_INDEX_INSTALLED or not TRACELOOP_INSTALLED:
            return func

        task_name = self._get_func_name(func, name)
        # logger.debug(f"Adapting LlamaIndex task: {task_name}")

        if callable(func) and not inspect.isclass(func):  # Only wrap if it's a callable
            if not hasattr(func, "_klira_traced"):
                return self._trace_function_wrapper(
                    func, span_name_prefix="task", entity_name=task_name
                )

        return func

    def patch_framework(self) -> None:
        """Patches key LlamaIndex components for tracing."""
        if not LLAMA_INDEX_INSTALLED or not TRACELOOP_INSTALLED:
            # logger.info("LlamaIndex or Traceloop not available. Skipping framework patching.")
            return

        # Patch QueryEngine methods
        if BaseQueryEngine:
            # Patch 'query'
            if hasattr(BaseQueryEngine, "query") and not hasattr(
                BaseQueryEngine.query, "_klira_traced"
            ):
                original_query_method = BaseQueryEngine.query

                def patched_query(self_instance: Any, *args: Any, **kwargs: Any) -> Any:
                    # `self_instance` is the QueryEngine instance
                    engine_name = (
                        self_instance.__class__.__name__
                    )  # Or a more specific name if available
                    traced_method = self._trace_function_wrapper(
                        functools.partial(
                            original_query_method, self_instance
                        ),  # Bind self_instance
                        span_name_prefix="query_engine.run",  # Changed from agent.run
                        entity_name=engine_name,
                    )
                    result = traced_method(
                        *args, **kwargs
                    )  # Call with original args/kwargs
                    
                    # Apply outbound guardrails
                    result = self._apply_outbound_guardrails(result, engine_name)
                    
                    return result

                setattr(patched_query, "_klira_traced", True)
                BaseQueryEngine.query = patched_query
                # logger.debug("Patched LlamaIndex BaseQueryEngine.query")

            # Patch 'aquery'
            if hasattr(BaseQueryEngine, "aquery") and not hasattr(
                BaseQueryEngine.aquery, "_klira_traced"
            ):
                original_aquery_method = BaseQueryEngine.aquery

                async def patched_aquery(
                    self_instance: Any, *args: Any, **kwargs: Any
                ) -> Any:
                    engine_name = self_instance.__class__.__name__
                    traced_method = self._trace_function_wrapper(
                        functools.partial(original_aquery_method, self_instance),
                        span_name_prefix="query_engine.run",  # Changed from agent.run
                        entity_name=engine_name,
                    )
                    result = await traced_method(*args, **kwargs)
                    
                    # Apply outbound guardrails
                    result = await self._apply_outbound_guardrails_async(result, engine_name)
                    
                    return result

                setattr(patched_aquery, "_klira_traced", True)
                BaseQueryEngine.aquery = patched_aquery
                # logger.debug("Patched LlamaIndex BaseQueryEngine.aquery")

        # Patch ChatEngine methods
        if BaseChatEngine:
            # Patch 'chat'
            if hasattr(BaseChatEngine, "chat") and not hasattr(
                BaseChatEngine.chat, "_klira_traced"
            ):
                original_chat_method = BaseChatEngine.chat

                def patched_chat(self_instance: Any, *args: Any, **kwargs: Any) -> Any:
                    engine_name = self_instance.__class__.__name__
                    traced_method = self._trace_function_wrapper(
                        functools.partial(original_chat_method, self_instance),
                        span_name_prefix="chat_engine.run",  # Changed from agent.run
                        entity_name=engine_name,
                    )
                    result = traced_method(*args, **kwargs)
                    
                    # Apply outbound guardrails
                    result = self._apply_outbound_guardrails(result, engine_name)
                    
                    return result

                setattr(patched_chat, "_klira_traced", True)
                BaseChatEngine.chat = patched_chat
                # logger.debug("Patched LlamaIndex BaseChatEngine.chat")

            # Patch 'achat'
            if hasattr(BaseChatEngine, "achat") and not hasattr(
                BaseChatEngine.achat, "_klira_traced"
            ):
                original_achat_method = BaseChatEngine.achat

                async def patched_achat(
                    self_instance: Any, *args: Any, **kwargs: Any
                ) -> Any:
                    engine_name = self_instance.__class__.__name__
                    traced_method = self._trace_function_wrapper(
                        functools.partial(original_achat_method, self_instance),
                        span_name_prefix="chat_engine.run",  # Changed from agent.run
                        entity_name=engine_name,
                    )
                    result = await traced_method(*args, **kwargs)
                    
                    # Apply outbound guardrails
                    result = await self._apply_outbound_guardrails_async(result, engine_name)
                    
                    return result

                setattr(patched_achat, "_klira_traced", True)
                BaseChatEngine.achat = patched_achat
                # logger.debug("Patched LlamaIndex BaseChatEngine.achat")

        # logger.info("LlamaIndex framework patching applied with outbound guardrails.")

    def apply_input_guardrails(
        self,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        func_name: str,
        injection_strategy: str = "auto",
    ) -> Tuple[Tuple[Any, ...], Dict[str, Any], bool, str]:
        """Apply input guardrails for LlamaIndex."""
        logger.debug(
            f"LlamaIndexAdapter: apply_input_guardrails called for {func_name} with strategy {injection_strategy}"
        )
        # LlamaIndex guardrails implementation would go here
        return args, kwargs, False, ""

    def apply_output_guardrails(
        self, result: Any, func_name: str
    ) -> Tuple[Any, bool, str]:
        """Apply output guardrails for LlamaIndex."""
        logger.debug(
            f"LlamaIndexAdapter: apply_output_guardrails called for {func_name}"
        )
        # LlamaIndex output guardrails implementation would go here
        return result, False, ""

    def apply_augmentation(
        self,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        guidelines: List[str],
        func_name: str,
    ) -> Tuple[Tuple[Any, ...], Dict[str, Any]]:
        """Apply prompt augmentation for LlamaIndex."""
        logger.debug(
            f"LlamaIndexAdapter: apply_augmentation called for {func_name} with {len(guidelines)} guidelines"
        )
        # LlamaIndex augmentation implementation would go here
        return args, kwargs

    def _apply_outbound_guardrails(self, result: Any, engine_name: str) -> Any:
        """Apply outbound guardrails to LlamaIndex results (synchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine
            
            # Convert result to string for evaluation
            result_text = ""
            if hasattr(result, 'response'):
                # LlamaIndex Response object
                result_text = str(result.response)
            elif hasattr(result, 'content'):
                # Some other response format
                result_text = str(result.content)
            else:
                result_text = str(result) if result else ""
            
            if not result_text.strip():
                return result
            
            # Create evaluation context
            context = {
                "engine_name": engine_name,
                "framework": self.FRAMEWORK_NAME,
                "function_name": f"llama_index.{engine_name.lower()}"
            }
            
            # Get guardrails engine and evaluate
            engine = GuardrailsEngine.get_instance()
            
            # Run async evaluation in sync context using asyncio
            import asyncio
            try:
                # Try to get the current event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, we can't use run_until_complete
                    # Return the result without evaluation and log a warning
                    logger.warning(
                        f"Cannot run outbound guardrails evaluation for {engine_name} in sync context within async loop. "
                        "Consider using async methods."
                    )
                    return result
                else:
                    # We can safely run the async evaluation
                    decision = loop.run_until_complete(
                        engine.evaluate(result_text, context, direction="outbound")
                    )
            except RuntimeError:
                # No event loop, create one
                decision = asyncio.run(
                    engine.evaluate(result_text, context, direction="outbound")
                )
            
            if not decision.allowed:
                logger.warning(
                    f"LlamaIndex outbound guardrails blocked result from {engine_name}: {decision.reason}"
                )
                # Return a safe message instead of the original result
                if hasattr(result, 'response'):
                    # Modify the response attribute if it exists
                    result.response = "[BLOCKED BY GUARDRAILS] - Content policy violation detected"
                    return result
                else:
                    return "[BLOCKED BY GUARDRAILS] - Content policy violation detected"
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying outbound guardrails for {engine_name}: {e}", exc_info=True)
            # Fail open - return original result
            return result

    async def _apply_outbound_guardrails_async(self, result: Any, engine_name: str) -> Any:
        """Apply outbound guardrails to LlamaIndex results (asynchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine
            
            # Convert result to string for evaluation
            result_text = ""
            if hasattr(result, 'response'):
                # LlamaIndex Response object
                result_text = str(result.response)
            elif hasattr(result, 'content'):
                # Some other response format
                result_text = str(result.content)
            else:
                result_text = str(result) if result else ""
            
            if not result_text.strip():
                return result
            
            # Create evaluation context
            context = {
                "engine_name": engine_name,
                "framework": self.FRAMEWORK_NAME,
                "function_name": f"llama_index.{engine_name.lower()}"
            }
            
            # Get guardrails engine and evaluate
            engine = GuardrailsEngine.get_instance()
            decision = await engine.evaluate(result_text, context, direction="outbound")
            
            if not decision.allowed:
                logger.warning(
                    f"LlamaIndex outbound guardrails blocked result from {engine_name}: {decision.reason}"
                )
                # Return a safe message instead of the original result
                if hasattr(result, 'response'):
                    # Modify the response attribute if it exists
                    result.response = "[BLOCKED BY GUARDRAILS] - Content policy violation detected"
                    return result
                else:
                    return "[BLOCKED BY GUARDRAILS] - Content policy violation detected"
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying outbound guardrails for {engine_name}: {e}", exc_info=True)
            # Fail open - return original result
            return result

    def unpatch_framework(self) -> None:
        """Restores original LlamaIndex components if they were patched."""
        # Placeholder for unpatching logic. This would involve storing original methods
        # before patching and restoring them here.
        # For now, it does nothing.
        if not LLAMA_INDEX_INSTALLED:
            return

        # logger.info("LlamaIndex framework unpatching called (currently a placeholder).")
        pass  # Implement unpatching if necessary

    def _extract_response_content(self, result: Any) -> str:
        """Extract text content from LlamaIndex response object."""
        try:
            # Handle LlamaIndex response formats
            if hasattr(result, 'response'):
                # LlamaIndex Response object
                return str(result.response)
            elif hasattr(result, 'content'):
                # Some other response format
                return str(result.content)
            elif hasattr(result, 'text'):
                return str(result.text)
            elif isinstance(result, str):
                return result
            elif isinstance(result, dict):
                # Look for common text fields
                for key in ["response", "content", "text", "output", "result"]:
                    if key in result and result[key]:
                        return str(result[key])
            
            # Fallback: try to convert to string
            return str(result) if result else ""
            
        except Exception as e:
            logger.debug(f"Error extracting content from LlamaIndex response: {e}")
            return ""

    def _create_blocked_response(self, original_result: Any, reason: str) -> Any:
        """Create a blocked response that matches the original response format."""
        try:
            blocked_message = f"[BLOCKED BY GUARDRAILS] - {reason}" if reason else "[BLOCKED BY GUARDRAILS] - Content policy violation detected"
            
            # Handle LlamaIndex Response objects
            if hasattr(original_result, 'response'):
                # Modify the response attribute if it exists
                original_result.response = blocked_message
                return original_result
            elif hasattr(original_result, 'content'):
                original_result.content = blocked_message
                return original_result
            elif hasattr(original_result, 'text'):
                original_result.text = blocked_message
                return original_result
            
            # Handle string results
            if isinstance(original_result, str):
                return blocked_message
            
            # Handle dictionary responses
            if isinstance(original_result, dict):
                # Create a copy to avoid modifying the original
                blocked_result = original_result.copy()
                # Look for common text fields to replace
                for key in ["response", "content", "text", "output", "result"]:
                    if key in blocked_result:
                        blocked_result[key] = blocked_message
                        return blocked_result
                # If no specific field found, add a blocked message field
                blocked_result["response"] = blocked_message
                return blocked_result
            
            # Fallback: return the blocked message as string
            return blocked_message
            
        except Exception as e:
            logger.error(f"Error creating blocked response: {e}")
            # Ultimate fallback
            return "[BLOCKED BY GUARDRAILS] - Content policy violation detected"
