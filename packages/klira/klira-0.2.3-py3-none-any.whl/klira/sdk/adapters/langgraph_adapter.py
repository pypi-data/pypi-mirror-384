"""Adapter for LangGraph framework compatibility."""
# mypy: disable-error-code=unreachable

import functools
import asyncio
import inspect
import logging
from typing import Callable, Any, Union, Type, Tuple, Dict

from opentelemetry.trace import Status, StatusCode

# Use try-except for framework imports
try:
    from langgraph.graph import StateGraph
    from langgraph.graph.graph import CompiledGraph
    from langgraph.pregel import Pregel
    from langgraph.constants import START, END

    LANGGRAPH_INSTALLED = True
except ImportError:
    LANGGRAPH_INSTALLED = False

    # Define dummy classes for type hinting if not installed
    class StateGraph(object):  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any):
            pass

        def add_node(self, *args: Any, **kwargs: Any) -> None:
            pass

        def compile(self, *args: Any, **kwargs: Any) -> None:
            return None

    class CompiledStateGraph(object):
        def invoke(self, *args: Any, **kwargs: Any) -> Any:
            return None

        async def ainvoke(self, *args: Any, **kwargs: Any) -> Any:
            return None

        def stream(self, *args: Any, **kwargs: Any) -> Any:
            return None

        async def astream(self, *args: Any, **kwargs: Any) -> Any:
            return None

    class CompiledGraph(object):  # type: ignore[no-redef]
        pass

    class Pregel(object):  # type: ignore[no-redef]
        pass

    START = "__start__"
    END = "__end__"

# Use try-except for Traceloop import
try:
    from traceloop.sdk.tracing import get_tracer

    TRACELOOP_INSTALLED: bool = True
except ImportError:
    TRACELOOP_INSTALLED = False

    # Define a dummy tracer if not installed
    class DummySpan:
        def set_attribute(self, key: str, value: Any) -> None:
            pass

        def set_status(self, status: Any) -> None:
            pass

        def record_exception(self, exception: Any) -> None:
            pass

        def __enter__(self) -> "DummySpan":
            return self

        def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            pass

    class DummyTracer:
        def start_as_current_span(self, name: str) -> DummySpan:
            return DummySpan()

    def get_tracer() -> DummyTracer:
        return DummyTracer()


from klira.sdk.adapters.base import BaseAdapter

logger = logging.getLogger("klira.adapters.langgraph")


class LangGraphAdapter(BaseAdapter):
    """Adapter for LangGraph."""

    FRAMEWORK_NAME = "langgraph"

    def _get_func_name(
        self,
        func_or_class: Union[Callable[..., Any], Type[Any]],
        name: str | None = None,
    ) -> str:
        """Helper to get the best name for a function or class."""
        if inspect.isclass(func_or_class):
            class_name = name or str(
                getattr(func_or_class, "__name__", "unknown_class")
            )
            return class_name
        func_name = name or str(getattr(func_or_class, "__name__", "unknown_function"))
        return func_name

    def _trace_function(
        self,
        func: Callable[..., Any],
        span_name_prefix: str,
        name_attribute: str,
        func_name: str,
    ) -> Callable[..., Any]:
        """Generic tracing wrapper for LangGraph functions."""
        if not TRACELOOP_INSTALLED:
            logger.warning(
                "Traceloop SDK not found. LangGraph tracing via Klira AI adapter will be disabled."
            )
            return func

        tracer = get_tracer()

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            span_name = f"{self.FRAMEWORK_NAME}.{span_name_prefix}.{func_name}"
            input_args_str = str(args)[:200] + str(kwargs)[:300]

            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute(name_attribute, func_name)
                span.set_attribute("framework", self.FRAMEWORK_NAME)
                span.set_attribute(f"{span_name_prefix}.input", input_args_str)

                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute(f"{span_name_prefix}.success", True)
                    span.set_status(Status(StatusCode.OK))
                    if result:
                        span.set_attribute(
                            f"{span_name_prefix}.output", str(result)[:500]
                        )
                    return result
                except Exception as e:
                    logger.error(f"Error in {func_name}: {e}", exc_info=True)
                    span.set_attribute(f"{span_name_prefix}.error", str(e))
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, description=str(e)))
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            span_name = f"{self.FRAMEWORK_NAME}.{span_name_prefix}.{func_name}"
            input_args_str = str(args)[:200] + str(kwargs)[:300]
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute(name_attribute, func_name)
                span.set_attribute("framework", self.FRAMEWORK_NAME)
                span.set_attribute(f"{span_name_prefix}.input", input_args_str)

                try:
                    result = func(*args, **kwargs)
                    span.set_attribute(f"{span_name_prefix}.success", True)
                    span.set_status(Status(StatusCode.OK))
                    if result:
                        span.set_attribute(
                            f"{span_name_prefix}.output", str(result)[:500]
                        )
                    return result
                except Exception as e:
                    logger.error(f"Error in {func_name}: {e}", exc_info=True)
                    span.set_attribute(f"{span_name_prefix}.error", str(e))
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, description=str(e)))
                    raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    def adapt_workflow(
        self, func: Callable[..., Any], name: str | None = None, **kwargs: Any
    ) -> Callable[..., Any]:
        """Adapts LangGraph workflows (StateGraph compilation and execution)."""
        if not LANGGRAPH_INSTALLED:
            logger.warning("LangGraph not found. Skipping workflow adaptation.")
            return func
        if not TRACELOOP_INSTALLED:
            logger.warning(
                "Traceloop SDK not found. Skipping LangGraph workflow adaptation."
            )
            return func

        workflow_name = self._get_func_name(func, name)
        logger.debug(f"Adapting LangGraph workflow: {workflow_name}")

        return self._trace_function(func, "workflow", "workflow.name", workflow_name)

    def adapt_task(
        self, func: Callable[..., Any], name: str | None = None, **kwargs: Any
    ) -> Callable[..., Any]:
        """Adapts LangGraph tasks (individual node functions)."""
        if not LANGGRAPH_INSTALLED:
            logger.warning("LangGraph not found. Skipping task adaptation.")
            return func
        if not TRACELOOP_INSTALLED:
            logger.warning(
                "Traceloop SDK not found. Skipping LangGraph task adaptation."
            )
            return func

        task_name = self._get_func_name(func, name)
        logger.debug(f"Adapting LangGraph task: {task_name}")

        return self._trace_function(func, "task", "task.name", task_name)

    def adapt_agent(
        self, func: Callable[..., Any], name: str | None = None, **kwargs: Any
    ) -> Callable[..., Any]:
        """Adapts LangGraph agents (compiled graphs that act as agents)."""
        if not LANGGRAPH_INSTALLED:
            logger.warning("LangGraph not found. Skipping agent adaptation.")
            return func
        if not TRACELOOP_INSTALLED:
            logger.warning(
                "Traceloop SDK not found. Skipping LangGraph agent adaptation."
            )
            return func

        agent_name = self._get_func_name(func, name)
        logger.debug(f"Adapting LangGraph agent: {agent_name}")

        return self._trace_function(func, "agent", "agent.name", agent_name)

    def adapt_tool(
        self,
        func_or_class: Union[Callable[..., Any], Type[Any]],
        name: str | None = None,
        **kwargs: Any,
    ) -> Union[Callable[..., Any], Type[Any]]:
        """Adapts LangGraph tools (functions used within nodes)."""
        if not LANGGRAPH_INSTALLED:
            logger.warning("LangGraph not found. Skipping tool adaptation.")
            return func_or_class
        if not TRACELOOP_INSTALLED:
            logger.warning(
                "Traceloop SDK not found. Skipping LangGraph tool adaptation."
            )
            return func_or_class

        tool_name = self._get_func_name(func_or_class, name)
        logger.debug(f"Adapting LangGraph tool: {tool_name}")

        if inspect.isfunction(func_or_class):
            return self._trace_function(func_or_class, "tool", "tool.name", tool_name)
        else:
            # For classes, we return as-is since LangGraph tools are typically functions
            logger.debug(f"LangGraph tool {tool_name} is a class, returning as-is")
            return func_or_class

    def patch_framework(self) -> None:
        """Apply patches to LangGraph for automatic tracing."""
        if not LANGGRAPH_INSTALLED:
            logger.warning("LangGraph not found. Skipping framework patching.")
            return
        if not TRACELOOP_INSTALLED:
            logger.warning(
                "Traceloop SDK not found. Skipping LangGraph framework patching."
            )
            return

        logger.debug("Patching LangGraph framework...")

        try:
            # Patch CompiledGraph.invoke method
            if hasattr(CompiledGraph, "invoke") and not hasattr(
                CompiledGraph.invoke, "_klira_traced"
            ):
                original_invoke = CompiledGraph.invoke

                @functools.wraps(original_invoke)
                def patched_invoke(
                    self_instance: CompiledGraph,
                    input_data: Any,
                    *args: Any,
                    **kwargs: Any,
                ) -> Any:
                    graph_name = getattr(self_instance, "name", "unknown_graph")
                    span_name = f"{self.FRAMEWORK_NAME}.graph.invoke.{graph_name}"

                    if not TRACELOOP_INSTALLED:
                        return original_invoke(
                            self_instance, input_data, *args, **kwargs
                        )

                    tracer = get_tracer()
                    with tracer.start_as_current_span(span_name) as span:
                        span.set_attribute("graph.name", graph_name)
                        span.set_attribute("framework", self.FRAMEWORK_NAME)
                        span.set_attribute("graph.input", str(input_data)[:500])

                        try:
                            result = original_invoke(
                                self_instance, input_data, *args, **kwargs
                            )
                            
                            # Apply outbound guardrails evaluation
                            result = self._apply_outbound_guardrails(result)
                            
                            span.set_attribute("graph.success", True)
                            span.set_status(Status(StatusCode.OK))
                            if result:
                                span.set_attribute("graph.output", str(result)[:500])
                            return result
                        except Exception as e:
                            logger.error(
                                f"Error in LangGraph invoke {graph_name}: {e}",
                                exc_info=True,
                            )
                            span.set_attribute("graph.error", str(e))
                            span.record_exception(e)
                            span.set_status(
                                Status(StatusCode.ERROR, description=str(e))
                            )
                            raise

                setattr(patched_invoke, "_klira_traced", True)
                CompiledGraph.invoke = patched_invoke
                logger.info("Successfully patched CompiledGraph.invoke")

            # Patch CompiledGraph.ainvoke method
            if hasattr(CompiledGraph, "ainvoke") and not hasattr(
                CompiledGraph.ainvoke, "_klira_traced"
            ):
                original_ainvoke = CompiledGraph.ainvoke

                @functools.wraps(original_ainvoke)
                async def patched_ainvoke(
                    self_instance: CompiledGraph,
                    input_data: Any,
                    *args: Any,
                    **kwargs: Any,
                ) -> Any:
                    graph_name = getattr(self_instance, "name", "unknown_graph")
                    span_name = f"{self.FRAMEWORK_NAME}.graph.ainvoke.{graph_name}"

                    if not TRACELOOP_INSTALLED:
                        return await original_ainvoke(
                            self_instance, input_data, *args, **kwargs
                        )

                    tracer = get_tracer()
                    with tracer.start_as_current_span(span_name) as span:
                        span.set_attribute("graph.name", graph_name)
                        span.set_attribute("framework", self.FRAMEWORK_NAME)
                        span.set_attribute("graph.input", str(input_data)[:500])

                        try:
                            result = await original_ainvoke(
                                self_instance, input_data, *args, **kwargs
                            )
                            
                            # Apply outbound guardrails evaluation
                            result = await self._apply_outbound_guardrails_async(result)
                            
                            span.set_attribute("graph.success", True)
                            span.set_status(Status(StatusCode.OK))
                            if result:
                                span.set_attribute("graph.output", str(result)[:500])
                            return result
                        except Exception as e:
                            logger.error(
                                f"Error in LangGraph ainvoke {graph_name}: {e}",
                                exc_info=True,
                            )
                            span.set_attribute("graph.error", str(e))
                            span.record_exception(e)
                            span.set_status(
                                Status(StatusCode.ERROR, description=str(e))
                            )
                            raise

                setattr(patched_ainvoke, "_klira_traced", True)
                CompiledGraph.ainvoke = patched_ainvoke
                logger.info("Successfully patched CompiledGraph.ainvoke")

        except Exception as e:
            logger.error(f"Error patching LangGraph framework: {e}", exc_info=True)

    def apply_input_guardrails(
        self,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        func_name: str,
        injection_strategy: str = "auto",
    ) -> Tuple[Tuple[Any, ...], Dict[str, Any], bool, str]:
        """Apply input guardrails to LangGraph function arguments."""
        # For LangGraph, we typically want to check the state/input data
        # This is a placeholder implementation - customize based on your guardrails needs
        try:
            from klira.sdk.guardrails.engine import GuardrailsEngine

            engine = GuardrailsEngine.get_instance()

            if engine and args:
                # Check the first argument which is typically the state in LangGraph
                input_data = args[0] if args else kwargs.get("input", {})

                # Extract text content for guardrails checking
                text_content = ""
                if isinstance(input_data, dict):
                    # Look for common text fields in LangGraph state
                    for key in ["messages", "input", "query", "content", "text"]:
                        if key in input_data:
                            value = input_data[key]
                            if isinstance(value, str):
                                text_content = value
                                break
                            elif isinstance(value, list) and value:
                                # Handle message lists
                                if (
                                    isinstance(value[-1], dict)
                                    and "content" in value[-1]
                                ):
                                    text_content = value[-1]["content"]
                                elif isinstance(value[-1], str):
                                    text_content = value[-1]
                                break

                if text_content:
                    # Apply guardrails to the extracted text
                    try:
                        decision = asyncio.run(
                            engine.evaluate(text_content, {"func_name": func_name})
                        )
                    except Exception as e:
                        logger.error(f"Error evaluating guardrails: {e}")
                        return args, kwargs, False, ""

                    if not decision.allowed:
                        return (
                            args,
                            kwargs,
                            True,
                            decision.reason or "Input blocked by guardrails",
                        )

            return args, kwargs, False, ""

        except Exception as e:
            logger.error(f"Error applying input guardrails: {e}", exc_info=True)
            return args, kwargs, False, ""

    def apply_output_guardrails(
        self, result: Any, func_name: str
    ) -> Tuple[Any, bool, str]:
        """Apply output guardrails to LangGraph function results."""
        try:
            from klira.sdk.guardrails.engine import GuardrailsEngine

            engine = GuardrailsEngine.get_instance()

            if engine and result:
                # Extract text content from result for guardrails checking
                text_content = ""
                if isinstance(result, dict):
                    # Look for common text fields in LangGraph results
                    for key in ["messages", "output", "content", "text", "response"]:
                        if key in result:
                            value = result[key]
                            if isinstance(value, str):
                                text_content = value
                                break
                            elif isinstance(value, list) and value:
                                # Handle message lists
                                if (
                                    isinstance(value[-1], dict)
                                    and "content" in value[-1]
                                ):
                                    text_content = value[-1]["content"]
                                elif isinstance(value[-1], str):
                                    text_content = value[-1]
                                break
                elif isinstance(result, str):
                    text_content = result

                if text_content:
                    # Apply guardrails to the extracted text
                    try:
                        decision = asyncio.run(
                            engine.evaluate(text_content, {"func_name": func_name})
                        )
                    except Exception as e:
                        logger.error(f"Error evaluating guardrails: {e}")
                        return result, False, ""

                    if not decision.allowed:
                        return (
                            result,
                            True,
                            decision.reason or "Output blocked by guardrails",
                        )

            return result, False, ""

        except Exception as e:
            logger.error(f"Error applying output guardrails: {e}", exc_info=True)
            return result, False, ""

    def apply_augmentation(
        self,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        guidelines: list[str],
        func_name: str,
    ) -> Tuple[Tuple[Any, ...], Dict[str, Any]]:
        """Apply prompt augmentation to LangGraph function arguments."""
        if not guidelines:
            return args, kwargs

        try:
            # For LangGraph, we want to inject guidelines into the state or messages
            if args:
                modified_args = list(args)
                input_data = modified_args[0]

                if isinstance(input_data, dict):
                    # Create a copy to avoid modifying the original
                    modified_input = input_data.copy()

                    # Look for message structures to augment
                    if "messages" in modified_input and isinstance(
                        modified_input["messages"], list
                    ):
                        messages = modified_input["messages"].copy()

                        # Find the last user message or system message to augment
                        for i in range(len(messages) - 1, -1, -1):
                            msg = messages[i]
                            if isinstance(msg, dict) and msg.get("role") in [
                                "user",
                                "system",
                            ]:
                                # Augment this message with guidelines
                                augmented_content = msg.get("content", "")
                                if isinstance(augmented_content, str):
                                    guidelines_text = (
                                        "\n\nIMPORTANT GUIDELINES:\n"
                                        + "\n".join([f"• {g}" for g in guidelines])
                                    )
                                    messages[i] = {
                                        **msg,
                                        "content": augmented_content + guidelines_text,
                                    }
                                    break

                        modified_input["messages"] = messages

                    # Also check for direct content fields
                    elif "content" in modified_input and isinstance(
                        modified_input["content"], str
                    ):
                        guidelines_text = "\n\nIMPORTANT GUIDELINES:\n" + "\n".join(
                            [f"• {g}" for g in guidelines]
                        )
                        modified_input["content"] += guidelines_text

                    modified_args[0] = modified_input
                    return tuple(modified_args), kwargs

            return args, kwargs

        except Exception as e:
            logger.error(f"Error applying augmentation: {e}", exc_info=True)
            return args, kwargs

    def _apply_outbound_guardrails(self, result: Any) -> Any:
        """Apply outbound guardrails to LangGraph results (synchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine
            
            # Extract content from LangGraph response
            response_text = self._extract_response_content(result)
            if not response_text.strip():
                return result
            
            # Create evaluation context
            context = {
                "llm_client": "langgraph",
                "function_name": "langgraph.CompiledGraph.invoke"
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
                        "Cannot run outbound guardrails evaluation for LangGraph in sync context within async loop. "
                        "Consider using async methods."
                    )
                    return result
                else:
                    # We can safely run the async evaluation
                    decision = loop.run_until_complete(
                        engine.evaluate(response_text, context, direction="outbound")
                    )
            except RuntimeError:
                # No event loop, create one
                decision = asyncio.run(
                    engine.evaluate(response_text, context, direction="outbound")
                )
            
            if not decision.allowed:
                logger.warning(
                    f"LangGraph outbound guardrails blocked response: {decision.reason}"
                )
                # Return a modified response with blocked content
                return self._create_blocked_response(result, decision.reason or "Content policy violation detected")
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying outbound guardrails for LangGraph: {e}", exc_info=True)
            # Fail open - return original result
            return result

    async def _apply_outbound_guardrails_async(self, result: Any) -> Any:
        """Apply outbound guardrails to LangGraph results (asynchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine
            
            # Extract content from LangGraph response
            response_text = self._extract_response_content(result)
            if not response_text.strip():
                return result
            
            # Create evaluation context
            context = {
                "llm_client": "langgraph",
                "function_name": "langgraph.CompiledGraph.ainvoke"
            }
            
            # Get guardrails engine and evaluate
            engine = GuardrailsEngine.get_instance()
            decision = await engine.evaluate(response_text, context, direction="outbound")
            
            if not decision.allowed:
                logger.warning(
                    f"LangGraph async outbound guardrails blocked response: {decision.reason}"
                )
                # Return a modified response with blocked content
                return self._create_blocked_response(result, decision.reason or "Content policy violation detected")
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying outbound guardrails for LangGraph async: {e}", exc_info=True)
            # Fail open - return original result
            return result

    def _extract_response_content(self, result: Any) -> str:
        """Extract text content from LangGraph response object."""
        try:
            # Handle LangGraph response format
            if isinstance(result, dict):
                # Look for common text fields in LangGraph results
                for key in ["messages", "output", "content", "text", "response"]:
                    if key in result:
                        value = result[key]
                        if isinstance(value, str):
                            return value
                        elif isinstance(value, list) and value:
                            # Handle message lists
                            content_parts = []
                            for item in value:
                                if isinstance(item, dict) and "content" in item:
                                    content_parts.append(str(item["content"]))
                                elif isinstance(item, str):
                                    content_parts.append(item)
                            return " ".join(content_parts) if content_parts else ""
                
                # Try to extract any string values from the result
                text_parts = []
                for key, value in result.items():
                    if isinstance(value, str) and len(value.strip()) > 0:
                        text_parts.append(value)
                return " ".join(text_parts) if text_parts else ""
            
            elif isinstance(result, str):
                return result
            
            # Fallback: try to convert to string
            return str(result) if result else ""
            
        except Exception as e:
            logger.debug(f"Error extracting content from LangGraph response: {e}")
            return ""

    def _create_blocked_response(self, original_result: Any, reason: str) -> Any:
        """Create a blocked response that matches the original response format."""
        try:
            blocked_message = f"[BLOCKED BY GUARDRAILS] - {reason}" if reason else "[BLOCKED BY GUARDRAILS] - Content policy violation detected"
            
            # Try to modify the original response in place
            if isinstance(original_result, dict):
                # Create a copy to avoid modifying the original
                blocked_result = original_result.copy()
                
                # Look for common text fields to replace
                for key in ["messages", "output", "content", "text", "response"]:
                    if key in blocked_result:
                        value = blocked_result[key]
                        if isinstance(value, str):
                            blocked_result[key] = blocked_message
                            return blocked_result
                        elif isinstance(value, list) and value:
                            # Handle message lists - replace the last message content
                            modified_messages = value.copy()
                            for i in range(len(modified_messages) - 1, -1, -1):
                                if isinstance(modified_messages[i], dict) and "content" in modified_messages[i]:
                                    modified_messages[i] = {**modified_messages[i], "content": blocked_message}
                                    blocked_result[key] = modified_messages
                                    return blocked_result
                                elif isinstance(modified_messages[i], str):
                                    modified_messages[i] = blocked_message
                                    blocked_result[key] = modified_messages
                                    return blocked_result
                
                # If no specific field found, add a blocked message field
                blocked_result["blocked_content"] = blocked_message
                return blocked_result
            
            # Fallback: return the blocked message as string
            return blocked_message
            
        except Exception as e:
            logger.error(f"Error creating blocked response: {e}")
            # Ultimate fallback
            return "[BLOCKED BY GUARDRAILS] - Content policy violation detected"
