"""Adapter for LangChain framework compatibility."""

import functools
import asyncio
import inspect
import logging
from typing import Callable, Any, Union, Type, List, Tuple, Dict

from opentelemetry.trace import Status, StatusCode

# Use try-except for framework imports
try:
    from langchain_core.tools import BaseTool
    from langchain.agents import AgentExecutor

    # Might need RunnableSequence if we patch that too
    # from langchain_core.runnables import RunnableSequence
    LANGCHAIN_INSTALLED = True
except ImportError:
    LANGCHAIN_INSTALLED = False

    # Define dummy classes for type hinting if not installed
    class BaseTool(object):  # type: ignore[no-redef]
        name: str = "unknown_tool"
        description: str = "Dummy tool"

        # Add common methods if needed, e.g., _run, _arun
        def _run(self, *args: Any, **kwargs: Any) -> Any:
            return None

        async def _arun(self, *args: Any, **kwargs: Any) -> Any:
            return None

    class AgentExecutor(object):  # type: ignore[no-redef]
        # Add common methods/attributes
        agent: Any = None
        tools: List[BaseTool] = []

        def invoke(self, *args: Any, **kwargs: Any) -> Any:
            return None

        async def ainvoke(self, *args: Any, **kwargs: Any) -> Any:
            return None

    # class RunnableSequence(object): # type: ignore[no-redef, misc]
    #     pass

# Use try-except for Traceloop import
try:
    from traceloop.sdk.tracing import get_tracer

    TRACELOOP_INSTALLED = True
except ImportError:
    TRACELOOP_INSTALLED = False

    # Define a dummy tracer if not installed (copy from openai_agents adapter)
    class DummySpan:  # ... (same as in openai_agents adapter)
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

    class DummyTracer:  # ... (same as in openai_agents adapter)
        def start_as_current_span(self, name: str) -> DummySpan:
            return DummySpan()

    def get_tracer() -> DummyTracer:
        return DummyTracer()


from klira.sdk.adapters.base import BaseAdapter

logger = logging.getLogger("klira.adapters.langchain")


class LangChainAdapter(BaseAdapter):
    """Adapter for LangChain."""

    FRAMEWORK_NAME = "langchain"

    def _get_func_name(
        self,
        func_or_class: Union[Callable[..., Any], Type[Any]],
        name: str | None = None,
    ) -> str:
        """Helper to get the best name for a function or class."""
        if inspect.isclass(func_or_class):
            class_name = (
                name or getattr(func_or_class, "name", None) or func_or_class.__name__
            )  # LangChain tools have a 'name' attribute
            return class_name
        func_name = (
            name or getattr(func_or_class, "__name__", None) or "unknown_function"
        )
        return func_name

    def _trace_function(
        self,
        func: Callable[..., Any],
        span_name_prefix: str,
        name_attribute: str,
        func_name: str,
    ) -> Callable[..., Any]:
        """Generic tracing wrapper (similar to OpenAI adapter's)."""
        if not TRACELOOP_INSTALLED:
            logger.warning(
                "Traceloop SDK not found. LangChain tracing via Klira AI adapter will be disabled."
            )
            return func

        tracer = get_tracer()

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            span_name = f"{self.FRAMEWORK_NAME}.{span_name_prefix}.{func_name}"
            input_args_str = str(args)[:200] + str(kwargs)[:300]  # Basic input logging

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

    def adapt_tool(
        self,
        func_or_class: Union[Callable[..., Any], Type[Any]],
        name: str | None = None,
        **kwargs: Any,
    ) -> Union[Callable[..., Any], Type[Any]]:
        """Adapts LangChain tools (decorated functions or BaseTool subclasses)."""
        if not LANGCHAIN_INSTALLED:
            logger.warning("LangChain not found. Skipping tool adaptation.")
            return func_or_class
        if not TRACELOOP_INSTALLED:
            logger.warning(
                "Traceloop SDK not found. Skipping LangChain tool adaptation."
            )
            return func_or_class

        tool_name = self._get_func_name(func_or_class, name)
        logger.debug(f"Adapting LangChain tool: {tool_name}")
        tracer = get_tracer()

        if inspect.isclass(func_or_class) and issubclass(func_or_class, BaseTool):
            # It's a BaseTool subclass, wrap its execution methods
            if hasattr(func_or_class, "_run") and not hasattr(
                func_or_class._run, "_klira_traced"
            ):
                original_run = func_or_class._run

                @functools.wraps(original_run)
                def wrapped_run(
                    self_instance: BaseTool, *args: Any, **tool_kwargs: Any
                ) -> Any:
                    instance_tool_name = getattr(self_instance, "name", tool_name)
                    span_name = f"{self.FRAMEWORK_NAME}.tool.{instance_tool_name}"
                    input_args_str = str(args)[:200] + str(tool_kwargs)[:300]
                    with tracer.start_as_current_span(span_name) as span:
                        span.set_attribute("tool.name", instance_tool_name)
                        span.set_attribute("framework", self.FRAMEWORK_NAME)
                        span.set_attribute("tool.input", input_args_str)
                        try:
                            result = original_run(self_instance, *args, **tool_kwargs)
                            span.set_attribute("tool.success", True)
                            span.set_status(Status(StatusCode.OK))
                            if result:
                                span.set_attribute("tool.output", str(result)[:500])
                            return result
                        except Exception as e:
                            logger.error(
                                f"Error in LangChain tool {instance_tool_name} (_run): {e}",
                                exc_info=True,
                            )
                            span.set_attribute("tool.error", str(e))
                            span.record_exception(e)
                            span.set_status(
                                Status(StatusCode.ERROR, description=str(e))
                            )
                            raise

                setattr(wrapped_run, "_klira_traced", True)
                func_or_class._run = wrapped_run

            # Wrap _arun similarly for async execution
            if hasattr(func_or_class, "_arun") and not hasattr(
                func_or_class._arun, "_klira_traced"
            ):
                original_arun = func_or_class._arun

                @functools.wraps(original_arun)
                async def wrapped_arun(
                    self_instance: BaseTool, *args: Any, **tool_kwargs: Any
                ) -> Any:
                    instance_tool_name = getattr(self_instance, "name", tool_name)
                    span_name = f"{self.FRAMEWORK_NAME}.tool.{instance_tool_name}"
                    input_args_str = str(args)[:200] + str(tool_kwargs)[:300]
                    with tracer.start_as_current_span(span_name) as span:
                        span.set_attribute("tool.name", instance_tool_name)
                        span.set_attribute("framework", self.FRAMEWORK_NAME)
                        span.set_attribute("tool.input", input_args_str)
                        try:
                            result = await original_arun(
                                self_instance, *args, **tool_kwargs
                            )
                            span.set_attribute("tool.success", True)
                            span.set_status(Status(StatusCode.OK))
                            if result:
                                span.set_attribute("tool.output", str(result)[:500])
                            return result
                        except Exception as e:
                            logger.error(
                                f"Error in LangChain tool {instance_tool_name} (_arun): {e}",
                                exc_info=True,
                            )
                            span.set_attribute("tool.error", str(e))
                            span.record_exception(e)
                            span.set_status(
                                Status(StatusCode.ERROR, description=str(e))
                            )
                            raise

                setattr(wrapped_arun, "_klira_traced", True)
                func_or_class._arun = wrapped_arun
            return func_or_class  # Return the modified class

        elif inspect.isfunction(func_or_class):
            # It's a function, likely decorated with LangChain's @tool
            # Mark it for detection if LangChain doesn't already (detection looks for this)
            setattr(func_or_class, "is_lc_tool", True)
            # Wrap the function directly using the generic tracer
            return self._trace_function(func_or_class, "tool", "tool.name", tool_name)
        else:
            # Not a class or function we recognize as a tool
            logger.warning(
                f"Cannot adapt unrecognized LangChain object as tool: {tool_name}"
            )
            return func_or_class

    def adapt_agent(
        self, func: Callable[..., Any], name: str | None = None, **kwargs: Any
    ) -> Callable[..., Any]:
        func_name = self._get_func_name(func, name)
        logger.debug(f"Adapting LangChain agent creation function: {func_name}")
        # Trace the function that *creates* the agent (e.g., create_tool_calling_agent).
        # Execution is traced by patching AgentExecutor.
        return self._trace_function(func, "agent_creation", "agent.name", func_name)

    def adapt_workflow(
        self, func: Callable[..., Any], name: str | None = None, **kwargs: Any
    ) -> Callable[..., Any]:
        func_name = self._get_func_name(func, name)
        logger.debug(f"Adapting LangChain workflow/chain function: {func_name}")
        # Could be a Chain, Runnable, or just a function.
        # Trace the function call itself. More specific patching handles execution (e.g., AgentExecutor).
        return self._trace_function(func, "workflow", "workflow.name", func_name)

    def adapt_task(
        self, func: Callable[..., Any], name: str | None = None, **kwargs: Any
    ) -> Callable[..., Any]:
        # LangChain doesn't have a distinct top-level 'Task' concept like CrewAI.
        # Map to workflow tracing.
        func_name = self._get_func_name(func, name)
        logger.debug(
            f"Adapting LangChain function as task (mapping to workflow): {func_name}"
        )
        return self.adapt_workflow(func, name, **kwargs)

    def patch_framework(self) -> None:
        """Patch LangChain AgentExecutor invoke/ainvoke methods."""
        if not LANGCHAIN_INSTALLED:
            logger.info("LangChain not found. Skipping AgentExecutor patching.")
            return
        if not TRACELOOP_INSTALLED:
            logger.warning(
                "Traceloop SDK not found. Skipping LangChain AgentExecutor patching."
            )
            return

        try:
            tracer = get_tracer()

            # --- Patch AgentExecutor.invoke ---
            if hasattr(AgentExecutor, "invoke") and not hasattr(
                AgentExecutor.invoke, "_klira_patched"
            ):
                original_invoke = AgentExecutor.invoke

                @functools.wraps(original_invoke)
                def patched_invoke(
                    self_instance: AgentExecutor,
                    input_data: Any,
                    *args: Any,
                    **kwargs: Any,
                ) -> Any:
                    # Try to get agent name (structure might vary)
                    agent_name = "unnamed_lc_agent"
                    if hasattr(self_instance, "agent") and hasattr(
                        self_instance.agent, "name"
                    ):
                        agent_name = (
                            str(self_instance.agent.name)
                            if self_instance.agent.name is not None
                            else "unnamed_lc_agent"
                        )
                    elif hasattr(self_instance, "name"):  # Fallback
                        agent_name = (
                            str(self_instance.name)
                            if self_instance.name is not None
                            else "unnamed_lc_agent"
                        )

                    span_name = f"{self.FRAMEWORK_NAME}.agent.run"
                    input_str = str(input_data)[:500]
                    with tracer.start_as_current_span(span_name) as span:
                        span.set_attribute("agent.name", agent_name)
                        span.set_attribute("framework", self.FRAMEWORK_NAME)
                        span.set_attribute("agent.input", input_str)
                        try:
                            result = original_invoke(
                                self_instance, input_data, *args, **kwargs
                            )
                            span.set_attribute("agent.success", True)
                            span.set_status(Status(StatusCode.OK))
                            if result:
                                span.set_attribute("agent.output", str(result)[:500])
                            
                            # Apply outbound guardrails evaluation
                            result = self._apply_outbound_guardrails(result, agent_name, span)
                            
                            return result
                        except Exception as e:
                            logger.error(
                                f"Error during LangChain AgentExecutor run ({agent_name}): {e}",
                                exc_info=True,
                            )
                            span.set_attribute("agent.error", str(e))
                            span.record_exception(e)
                            span.set_status(
                                Status(StatusCode.ERROR, description=str(e))
                            )
                            raise

                setattr(patched_invoke, "_klira_patched", True)
                AgentExecutor.invoke = patched_invoke

            # --- Patch AgentExecutor.ainvoke ---
            if hasattr(AgentExecutor, "ainvoke") and not hasattr(
                AgentExecutor.ainvoke, "_klira_patched"
            ):
                original_ainvoke = AgentExecutor.ainvoke

                @functools.wraps(original_ainvoke)
                async def patched_ainvoke(
                    self_instance: AgentExecutor,
                    input_data: Any,
                    *args: Any,
                    **kwargs: Any,
                ) -> Any:
                    agent_name = "unnamed_lc_agent"
                    if hasattr(self_instance, "agent") and hasattr(
                        self_instance.agent, "name"
                    ):
                        agent_name = (
                            str(self_instance.agent.name)
                            if self_instance.agent.name is not None
                            else "unnamed_lc_agent"
                        )
                    elif hasattr(self_instance, "name"):
                        agent_name = (
                            str(self_instance.name)
                            if self_instance.name is not None
                            else "unnamed_lc_agent"
                        )

                    span_name = f"{self.FRAMEWORK_NAME}.agent.run"
                    input_str = str(input_data)[:500]
                    with tracer.start_as_current_span(span_name) as span:
                        span.set_attribute("agent.name", agent_name)
                        span.set_attribute("framework", self.FRAMEWORK_NAME)
                        span.set_attribute("agent.input", input_str)
                        try:
                            result = await original_ainvoke(
                                self_instance, input_data, *args, **kwargs
                            )
                            span.set_attribute("agent.success", True)
                            span.set_status(Status(StatusCode.OK))
                            if result:
                                span.set_attribute("agent.output", str(result)[:500])
                            
                            # Apply outbound guardrails evaluation
                            result = await self._apply_outbound_guardrails_async(result, agent_name, span)
                            
                            return result
                        except Exception as e:
                            logger.error(
                                f"Error during LangChain AgentExecutor async run ({agent_name}): {e}",
                                exc_info=True,
                            )
                            span.set_attribute("agent.error", str(e))
                            span.record_exception(e)
                            span.set_status(
                                Status(StatusCode.ERROR, description=str(e))
                            )
                            raise

                setattr(patched_ainvoke, "_klira_patched", True)
                AgentExecutor.ainvoke = patched_ainvoke

            # Check if any patching occurred before logging success
            if hasattr(AgentExecutor.invoke, "_klira_patched") or hasattr(
                AgentExecutor.ainvoke, "_klira_patched"
            ):
                logger.info(
                    "Klira: Patched LangChain AgentExecutor invoke/ainvoke methods with outbound guardrails."
                )
            else:
                logger.debug(
                    "Klira: LangChain AgentExecutor methods already patched or not found."
                )

            # TODO: Optionally patch RunnableSequence invoke/stream/ainvoke/astream methods

        except Exception as e:
            logger.error(
                f"Klira: Failed to patch LangChain AgentExecutor: {e}", exc_info=True
            )

    def apply_input_guardrails(
        self,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        func_name: str,
        injection_strategy: str = "auto",
    ) -> Tuple[Tuple[Any, ...], Dict[str, Any], bool, str]:
        """Apply input guardrails for LangChain."""
        logger.debug(
            f"LangChainAdapter: apply_input_guardrails called for {func_name} with strategy {injection_strategy}"
        )
        # LangChain guardrails implementation would go here
        # For now, fail open (allow) until full implementation
        return args, kwargs, False, ""

    def apply_output_guardrails(
        self, result: Any, func_name: str
    ) -> Tuple[Any, bool, str]:
        """Apply output guardrails for LangChain."""
        logger.debug(
            f"LangChainAdapter: apply_output_guardrails called for {func_name}"
        )
        # LangChain output guardrails implementation would go here
        return result, False, ""

    def apply_augmentation(
        self,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        guidelines: list[str],
        func_name: str,
    ) -> Tuple[Tuple[Any, ...], Dict[str, Any]]:
        """Apply prompt augmentation for LangChain."""
        logger.debug(
            f"LangChainAdapter: apply_augmentation called for {func_name} with {len(guidelines)} guidelines"
        )
        # LangChain augmentation implementation would go here
        return args, kwargs

    def _apply_outbound_guardrails(self, result: Any, agent_name: str, span: Any) -> Any:
        """Apply outbound guardrails to LangChain results (synchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine
            
            # Convert result to string for evaluation
            result_text = str(result) if result else ""
            if not result_text.strip():
                return result
            
            # Create evaluation context
            context = {
                "agent_name": agent_name,
                "framework": self.FRAMEWORK_NAME,
                "function_name": f"langchain.agent.{agent_name}"
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
                        f"Cannot run outbound guardrails evaluation for {agent_name} in sync context within async loop. "
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
            
            # Set span attributes for guardrails decision
            span.set_attribute("guardrails.outbound.allowed", decision.allowed)
            span.set_attribute("guardrails.outbound.confidence", decision.confidence)
            if decision.policy_id:
                span.set_attribute("guardrails.outbound.policy_id", decision.policy_id)
            if decision.reason:
                span.set_attribute("guardrails.outbound.reason", decision.reason)
            
            if not decision.allowed:
                logger.warning(
                    f"LangChain outbound guardrails blocked result from {agent_name}: {decision.reason}"
                )
                # Return a safe message instead of the original result
                return {"output": "[BLOCKED BY GUARDRAILS] - Content policy violation detected"}
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying outbound guardrails for {agent_name}: {e}", exc_info=True)
            # Fail open - return original result
            return result

    async def _apply_outbound_guardrails_async(self, result: Any, agent_name: str, span: Any) -> Any:
        """Apply outbound guardrails to LangChain results (asynchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine
            
            # Convert result to string for evaluation
            result_text = str(result) if result else ""
            if not result_text.strip():
                return result
            
            # Create evaluation context
            context = {
                "agent_name": agent_name,
                "framework": self.FRAMEWORK_NAME,
                "function_name": f"langchain.agent.{agent_name}"
            }
            
            # Get guardrails engine and evaluate
            engine = GuardrailsEngine.get_instance()
            decision = await engine.evaluate(result_text, context, direction="outbound")
            
            # Set span attributes for guardrails decision
            span.set_attribute("guardrails.outbound.allowed", decision.allowed)
            span.set_attribute("guardrails.outbound.confidence", decision.confidence)
            if decision.policy_id:
                span.set_attribute("guardrails.outbound.policy_id", decision.policy_id)
            if decision.reason:
                span.set_attribute("guardrails.outbound.reason", decision.reason)
            
            if not decision.allowed:
                logger.warning(
                    f"LangChain outbound guardrails blocked result from {agent_name}: {decision.reason}"
                )
                # Return a safe message instead of the original result
                return {"output": "[BLOCKED BY GUARDRAILS] - Content policy violation detected"}
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying outbound guardrails for {agent_name}: {e}", exc_info=True)
            # Fail open - return original result
            return result

    def _extract_response_content(self, result: Any) -> str:
        """Extract text content from LangChain response object."""
        try:
            # Handle LangChain response formats
            if isinstance(result, str):
                return result
            elif isinstance(result, dict):
                # Look for common text fields in LangChain results
                for key in ["output", "content", "text", "response", "result"]:
                    if key in result and result[key]:
                        return str(result[key])
                # If no specific field found, try to convert the whole dict
                return str(result)
            elif hasattr(result, 'content'):
                return str(result.content)
            elif hasattr(result, 'output'):
                return str(result.output)
            
            # Fallback: try to convert to string
            return str(result) if result else ""
            
        except Exception as e:
            logger.debug(f"Error extracting content from LangChain response: {e}")
            return ""

    def _create_blocked_response(self, original_result: Any, reason: str) -> Any:
        """Create a blocked response that matches the original response format."""
        try:
            blocked_message = f"[BLOCKED BY GUARDRAILS] - {reason}" if reason else "[BLOCKED BY GUARDRAILS] - Content policy violation detected"
            
            # Handle string results
            if isinstance(original_result, str):
                return blocked_message
            
            # Handle dictionary responses (most common for LangChain)
            if isinstance(original_result, dict):
                # Create a copy to avoid modifying the original
                blocked_result = original_result.copy()
                # Look for common text fields to replace
                for key in ["output", "content", "text", "response", "result"]:
                    if key in blocked_result:
                        blocked_result[key] = blocked_message
                        return blocked_result
                # If no specific field found, add a blocked message field
                blocked_result["output"] = blocked_message
                return blocked_result
            
            # Handle object results with attributes
            if hasattr(original_result, 'content'):
                original_result.content = blocked_message
                return original_result
            elif hasattr(original_result, 'output'):
                original_result.output = blocked_message
                return original_result
            
            # Fallback: return the blocked message as string
            return blocked_message
            
        except Exception as e:
            logger.error(f"Error creating blocked response: {e}")
            # Ultimate fallback
            return "[BLOCKED BY GUARDRAILS] - Content policy violation detected"
