"""Adapter for CrewAI framework compatibility."""

import functools
import logging
import asyncio
import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)
from opentelemetry.trace import Status, StatusCode

# Use try-except for framework imports
_RealCrewAgent: Optional[Type[Any]] = None
_RealCrewTask: Optional[Type[Any]] = None
_RealCrewAICrew: Optional[Type[Any]] = None
_RealToolsHandler: Optional[Type[Any]] = None
_RealToolUsage: Optional[Type[Any]] = None

# CrewAI imports with fallback
CREWAI_INSTALLED: bool
if TYPE_CHECKING:
    from crewai import Agent as CrewAgent, Task as CrewTask, Crew as CrewAICrew
    from crewai.tools.tools_handler import ToolsHandler
    from crewai.tools.tool_usage import ToolUsage

    CrewAgentType = CrewAgent
    CrewTaskType = CrewTask
    CrewAICrewType = CrewAICrew
    ToolsHandlerType = ToolsHandler
    ToolUsageType = ToolUsage
    CREWAI_INSTALLED = True
else:
    try:
        from crewai import (
            Agent as _RealCrewAgent,
            Task as _RealCrewTask,
            Crew as _RealCrewAICrew,
        )
        from crewai.tools.tools_handler import ToolsHandler as _RealToolsHandler
        from crewai.tools.tool_usage import ToolUsage as _RealToolUsage

        CrewAgentType = _RealCrewAgent
        CrewTaskType = _RealCrewTask
        CrewAICrewType = _RealCrewAICrew
        ToolsHandlerType = _RealToolsHandler
        ToolUsageType = _RealToolUsage
        CREWAI_INSTALLED = True
    except ImportError:
        CREWAI_INSTALLED = False

        # Dummy classes for when CrewAI is not installed
        class _DummyCrewAgent(object):
            role: Optional[str] = None
            goal: Optional[str] = None
            backstory: Optional[str] = None
            tools: List[Any] = []

            def execute_task(self, *args: Any, **kwargs: Any) -> Any:
                return None

            def __repr__(self) -> str:
                return f"DummyCrewAgent(role='{self.role}')"

        class _DummyCrewTask(object):
            description: Optional[str] = None
            expected_output: Optional[str] = None
            agent: Optional[Any] = None
            tools: List[Any] = []

            def execute(self, *args: Any, **kwargs: Any) -> Any:
                return None

            def __repr__(self) -> str:
                return f"DummyCrewTask(description='{self.description}')"

        class _DummyCrewAICrew(object):
            tasks: List[Any] = []
            agents: List[Any] = []

            def kickoff(self, *args: Any, **kwargs: Any) -> Any:
                return None

            def __repr__(self) -> str:
                return f"DummyCrewAICrew(id='{id(self)}')"

        class _DummyToolsHandler(object):
            def dispatch(self, *args: Any, **kwargs: Any) -> Any:
                return None

        class _DummyToolUsage(object):
            tool_name: Optional[str] = None
            tool_input: Optional[Dict[str, Any]] = None
            log: Optional[str] = None
            task: Any = None
            agent: Any = None

            def __repr__(self) -> str:
                return f"DummyToolUsage(tool_name='{self.tool_name}')"

        CrewAgentType = _DummyCrewAgent  # type: ignore
        CrewTaskType = _DummyCrewTask  # type: ignore
        CrewAICrewType = _DummyCrewAICrew  # type: ignore
        ToolsHandlerType = _DummyToolsHandler  # type: ignore
        ToolUsageType = _DummyToolUsage  # type: ignore

# Use the type aliases directly instead of problematic cast assignments
CrewAgent = CrewAgentType
CrewTask = CrewTaskType
CrewAICrew = CrewAICrewType
ToolsHandler = ToolsHandlerType
ToolUsage = ToolUsageType

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

        def record_exception(self, exception: BaseException) -> None:
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

logger = logging.getLogger(__name__)


class CrewAIAdapter(BaseAdapter):
    """Adapter for CrewAI."""

    FRAMEWORK_NAME = "crewai"

    def __init__(self) -> None:
        """Initialize CrewAI adapter and check availability."""
        super().__init__()
        if not CREWAI_INSTALLED:
            logger.info("CrewAI not detected. CrewAIAdapter will not instrument.")
        self.telemetry = Telemetry()

    def _get_entity_name(self, entity: Any, name_override: Optional[str] = None) -> str:
        """Helper to get the best name for CrewAI components or functions."""
        if name_override:
            return name_override

        name: Optional[str] = None
        if isinstance(entity, CrewAgent):
            name = getattr(entity, "role", None) or f"agent_{id(entity)}"
        elif isinstance(entity, CrewTask):
            desc = getattr(entity, "description", None)
            name = (
                desc[:50] + "..." if desc and len(desc) > 53 else desc
            ) or f"task_{id(entity)}"
        elif isinstance(entity, CrewAICrew):
            # Crew doesn't have a standard name attribute, use a generic one or ID
            name = f"crew_{id(entity)}"
        elif hasattr(entity, "__name__"):
            name = getattr(entity, "__name__")
        elif inspect.isclass(entity):
            name = entity.__name__

        return name if name is not None else "unknown_crew_entity"

    def _trace_function_wrapper(
        self,
        func: Callable[..., Any],
        span_name_prefix: str,
        entity_name: str,
        input_transform: Optional[
            Callable[[Tuple[Any, ...], Dict[str, Any]], Dict[str, Any]]
        ] = None,
        output_transform: Optional[Callable[[Any], Dict[str, Any]]] = None,
    ) -> Callable[..., Any]:
        """Generic tracing wrapper for sync and async functions for CrewAI."""
        if not TRACELOOP_INSTALLED:
            return func

        tracer = get_tracer()
        base_span_name = f"{self.FRAMEWORK_NAME}.{span_name_prefix}.{entity_name}"

        shared_attributes = {
            "framework": self.FRAMEWORK_NAME,
            f"{span_name_prefix.split('.')[0]}.name": entity_name,  # e.g. agent.name, task.name
        }

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            if not self.telemetry.feature_enabled(
                f"{self.FRAMEWORK_NAME}.{span_name_prefix}"
            ):
                return await func(*args, **kwargs)

            current_attributes = {**shared_attributes}
            if input_transform:
                current_attributes.update(input_transform(args, kwargs))
            else:
                try:
                    current_attributes[f"{span_name_prefix}.input.args"] = str(args)[
                        :200
                    ]
                    current_attributes[f"{span_name_prefix}.input.kwargs"] = str(
                        kwargs
                    )[:300]
                except Exception:
                    current_attributes[f"{span_name_prefix}.input"] = (
                        "Error serializing input"
                    )

            with tracer.start_as_current_span(
                base_span_name, attributes=current_attributes
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
                        f"Error in CrewAI async {span_name_prefix} '{entity_name}': {e}",
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

            current_attributes = {**shared_attributes}
            if input_transform:
                current_attributes.update(input_transform(args, kwargs))
            else:
                try:
                    current_attributes[f"{span_name_prefix}.input.args"] = str(args)[
                        :200
                    ]
                    current_attributes[f"{span_name_prefix}.input.kwargs"] = str(
                        kwargs
                    )[:300]
                except Exception:
                    current_attributes[f"{span_name_prefix}.input"] = (
                        "Error serializing input"
                    )

            with tracer.start_as_current_span(
                base_span_name, attributes=current_attributes
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
                        f"Error in CrewAI sync {span_name_prefix} '{entity_name}': {e}",
                        exc_info=True,
                    )
                    span.set_status(Status(StatusCode.ERROR, description=str(e)))
                    span.record_exception(e)
                    raise

        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        setattr(wrapper, "_klira_traced", True)
        return cast(Callable[..., Any], wrapper)

    def adapt_tool(
        self,
        func_or_class: Union[Callable[..., Any], Type[Any]],
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[Callable[..., Any], Type[Any]]:
        """Adapts a CrewAI tool (function or class). Execution is traced via ToolsHandler patch."""
        if not CREWAI_INSTALLED or not TRACELOOP_INSTALLED:
            return func_or_class

        tool_name = self._get_entity_name(func_or_class, name)
        # logger.debug(f"Adapting CrewAI tool (definition): {tool_name}")
        # For tools, we primarily mark them. Actual execution tracing happens in patched ToolsHandler.dispatch
        # However, if a tool itself is a complex function the user wants to trace independently, this might be useful.
        if callable(func_or_class) and not hasattr(func_or_class, "_klira_traced"):
            # Set an attribute so ToolsHandler can identify it if needed, though not strictly necessary for tracing dispatch
            setattr(func_or_class, "_klira_adapted_tool", True)
            # We generally don't trace the tool function directly here, as ToolsHandler.dispatch covers execution.
            # If users decorate a tool function with @klira.tool, it will be wrapped by _trace_function_wrapper.
            return self._trace_function_wrapper(
                func_or_class, "tool.definition", tool_name
            )
        elif inspect.isclass(func_or_class):
            # If it's a class-based tool, we don't modify it here. Patching handles execution.
            setattr(func_or_class, "_klira_adapted_tool_class", True)

        return func_or_class

    def adapt_agent(
        self, func: Callable[..., Any], name: Optional[str] = None, **kwargs: Any
    ) -> Callable[..., Any]:
        """Adapts a CrewAI Agent creation function or class for definition tracing."""
        if not CREWAI_INSTALLED or not TRACELOOP_INSTALLED:
            return func

        agent_name = self._get_entity_name(func, name)
        # logger.debug(f"Adapting CrewAI Agent (definition): {agent_name}")
        if (
            callable(func)
            and not inspect.isclass(func)
            and not hasattr(func, "_klira_traced")
        ):
            return self._trace_function_wrapper(func, "agent.definition", agent_name)
        return func

    def adapt_task(
        self, func: Callable[..., Any], name: Optional[str] = None, **kwargs: Any
    ) -> Callable[..., Any]:
        """Adapts a CrewAI Task creation function or class for definition tracing."""
        if not CREWAI_INSTALLED or not TRACELOOP_INSTALLED:
            return func

        task_name = self._get_entity_name(func, name)
        # logger.debug(f"Adapting CrewAI Task (definition): {task_name}")
        if (
            callable(func)
            and not inspect.isclass(func)
            and not hasattr(func, "_klira_traced")
        ):
            return self._trace_function_wrapper(func, "task.definition", task_name)
        return func

    def adapt_crew(
        self,
        func_or_class: Union[Callable[..., Any], Type[Any]],
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[Callable[..., Any], Type[Any]]:
        """Adapts a CrewAI Crew creation function or class for definition tracing."""
        if not CREWAI_INSTALLED or not TRACELOOP_INSTALLED:
            return func_or_class

        crew_name = self._get_entity_name(
            func_or_class, name
        )  # Will be generic like crew_id if not named
        # logger.debug(f"Adapting CrewAI Crew (definition): {crew_name}")
        if (
            callable(func_or_class)
            and not inspect.isclass(func_or_class)
            and not hasattr(func_or_class, "_klira_traced")
        ):
            return self._trace_function_wrapper(
                func_or_class, "crew.definition", crew_name
            )
        return func_or_class

    def adapt_workflow(
        self, func: Callable[..., Any], name: Optional[str] = None, **kwargs: Any
    ) -> Callable[..., Any]:
        """Conceptually adapts a workflow function using CrewAI components."""
        if not CREWAI_INSTALLED or not TRACELOOP_INSTALLED:
            return func

        workflow_name = self._get_entity_name(func, name)
        # logger.debug(f"Adapting CrewAI generic workflow (definition): {workflow_name}")
        # This is for user-defined functions that orchestrate CrewAI components.
        if (
            callable(func)
            and not inspect.isclass(func)
            and not hasattr(func, "_klira_traced")
        ):
            return self._trace_function_wrapper(func, "workflow", workflow_name)
        return func

    def patch_framework(self) -> None:
        """Patches key CrewAI methods for tracing."""
        if not CREWAI_INSTALLED or not TRACELOOP_INSTALLED:
            return

        # Patch Agent.execute_task
        if (
            _RealCrewAgent
            and hasattr(_RealCrewAgent, "execute_task")
            and not hasattr(_RealCrewAgent.execute_task, "_klira_traced")
        ):
            original_agent_execute = _RealCrewAgent.execute_task

            def patched_agent_execute(
                self_agent: CrewAgent,
                task: CrewTask,
                context: Optional[str] = None,
                tools: Optional[List[Any]] = None,
            ) -> Any:
                agent_name = self._get_entity_name(self_agent)

                def input_transform_agent_exec(
                    args: Tuple[Any, ...], kwargs_dict: Dict[str, Any]
                ) -> Dict[str, Any]:
                    # self_agent is args[0], task is args[1]
                    _task = args[1] if len(args) > 1 else kwargs_dict.get("task")
                    _context = args[2] if len(args) > 2 else kwargs_dict.get("context")
                    _tools = args[3] if len(args) > 3 else kwargs_dict.get("tools")

                    attrs = {
                        "agent.role": getattr(self_agent, "role", "unknown"),
                        "task.description": self._get_entity_name(_task)
                        if _task
                        else "unknown_task",
                        "agent.goal": str(getattr(self_agent, "goal", ""))[:200],
                    }
                    if _context:
                        attrs["agent.input.context"] = str(_context)[:500]
                    if _tools:
                        attrs["agent.tools_count"] = len(_tools)
                    return attrs

                traced_method = self._trace_function_wrapper(
                    functools.partial(
                        original_agent_execute, self_agent
                    ),  # Bind self_agent
                    span_name_prefix="agent.execute_task",
                    entity_name=agent_name,
                    input_transform=input_transform_agent_exec,
                )
                # Call with original args, excluding self_agent which is already bound
                result = traced_method(task, context=context, tools=tools)
                
                # Apply outbound guardrails evaluation
                result = self._apply_outbound_guardrails(result)
                
                return result

            setattr(patched_agent_execute, "_klira_traced", True)
            _RealCrewAgent.execute_task = patched_agent_execute

        # Patch Task.execute
        if (
            _RealCrewTask
            and hasattr(_RealCrewTask, "execute")
            and not hasattr(_RealCrewTask.execute, "_klira_traced")
        ):
            original_task_execute = _RealCrewTask.execute

            # Signature: execute(self, agent: Optional[Agent] = None, context: Optional[str] = None, tools: Optional[List[Tool]] = None) -> str:
            def patched_task_execute(
                self_task: CrewTask,
                agent: Optional[CrewAgent] = None,
                context: Optional[str] = None,
                tools: Optional[List[Any]] = None,
            ) -> Any:
                task_name = self._get_entity_name(self_task)

                def input_transform_task_exec(
                    args: Tuple[Any, ...], kwargs_dict: Dict[str, Any]
                ) -> Dict[str, Any]:
                    _agent = args[1] if len(args) > 1 else kwargs_dict.get("agent")
                    _context = args[2] if len(args) > 2 else kwargs_dict.get("context")

                    attrs = {
                        "task.description": getattr(
                            self_task, "description", task_name
                        )[:200],
                        "task.expected_output": str(
                            getattr(self_task, "expected_output", "")
                        )[:200],
                        "agent.role": self._get_entity_name(_agent)
                        if _agent
                        else "none",
                    }
                    if _context:
                        attrs["task.input.context"] = str(_context)[:500]
                    return attrs

                traced_method = self._trace_function_wrapper(
                    functools.partial(original_task_execute, self_task),
                    span_name_prefix="task.execute",
                    entity_name=task_name,
                    input_transform=input_transform_task_exec,
                )
                result = traced_method(agent=agent, context=context, tools=tools)
                
                # Apply outbound guardrails evaluation
                result = self._apply_outbound_guardrails(result)
                
                return result

            setattr(patched_task_execute, "_klira_traced", True)
            _RealCrewTask.execute = patched_task_execute

        # Patch Crew.kickoff
        if (
            _RealCrewAICrew
            and hasattr(_RealCrewAICrew, "kickoff")
            and not hasattr(_RealCrewAICrew.kickoff, "_klira_traced")
        ):
            original_crew_kickoff = _RealCrewAICrew.kickoff

            def patched_crew_kickoff(
                self_crew: CrewAICrew, inputs: Optional[Dict[str, Any]] = None
            ) -> Any:
                crew_name = self._get_entity_name(self_crew)

                def input_transform_crew_kickoff(
                    _args: Tuple[Any, ...], kwargs_dict: Dict[str, Any]
                ) -> Dict[str, Any]:
                    _inputs = kwargs_dict.get("inputs")
                    return {
                        "crew.inputs": str(_inputs)[:500] if _inputs else "{}",
                        "crew.agents_count": len(getattr(self_crew, "agents", [])),
                        "crew.tasks_count": len(getattr(self_crew, "tasks", [])),
                    }

                traced_method = self._trace_function_wrapper(
                    functools.partial(original_crew_kickoff, self_crew),
                    span_name_prefix="crew.kickoff",
                    entity_name=crew_name,
                    input_transform=input_transform_crew_kickoff,
                )
                result = traced_method(inputs=inputs)
                
                # Apply outbound guardrails evaluation
                result = self._apply_outbound_guardrails(result)
                
                return result

            setattr(patched_crew_kickoff, "_klira_traced", True)
            _RealCrewAICrew.kickoff = patched_crew_kickoff

        # Patch ToolsHandler.dispatch
        if (
            _RealToolsHandler
            and hasattr(_RealToolsHandler, "dispatch")
            and not hasattr(_RealToolsHandler.dispatch, "_klira_traced")
        ):
            original_dispatch = _RealToolsHandler.dispatch

            # Signature: dispatch(self, tool_usage: ToolUsage) -> Any:
            def patched_dispatch(
                self_handler: ToolsHandler, tool_usage: ToolUsage
            ) -> Any:
                tool_name: str = "unknown_tool"  # Ensure tool_name is always str
                if tool_usage:
                    name_from_tool_usage = getattr(tool_usage, "tool_name", None)
                    if name_from_tool_usage:
                        tool_name = name_from_tool_usage
                    elif (
                        hasattr(tool_usage, "tool")
                        and hasattr(tool_usage.tool, "name")
                        and getattr(tool_usage.tool, "name") is not None
                    ):
                        tool_name = getattr(tool_usage.tool, "name")

                def input_transform_tool_dispatch(
                    args: Tuple[Any, ...], _kwargs_dict: Dict[str, Any]
                ) -> Dict[str, Any]:
                    _tool_usage = args[1]  # tool_usage is the first arg after self
                    attrs = {"tool.name": tool_name}  # Already have tool_name
                    if _tool_usage:
                        # CrewAI ToolUsage has `tool_input` (dict) rather than `arguments` (str)
                        tool_input_val = getattr(_tool_usage, "tool_input", None)
                        if (
                            tool_input_val is None
                        ):  # Fallback for older or different ToolCall structure
                            tool_input_val = getattr(_tool_usage, "arguments", None)
                        attrs["tool.input"] = (
                            str(tool_input_val)[:500] if tool_input_val else "{}"
                        )

                        # Try to get agent/task context if available from ToolUsage
                        task_obj = getattr(_tool_usage, "task", None)
                        agent_obj = getattr(_tool_usage, "agent", None)
                        if task_obj:
                            attrs["task.description"] = self._get_entity_name(task_obj)[
                                :200
                            ]
                        if agent_obj:
                            attrs["agent.role"] = self._get_entity_name(agent_obj)
                    return attrs

                traced_method = self._trace_function_wrapper(
                    functools.partial(original_dispatch, self_handler),
                    span_name_prefix="tool.run",  # Consistent with other tool runs
                    entity_name=tool_name,
                    input_transform=input_transform_tool_dispatch,
                )
                result = traced_method(
                    tool_usage=tool_usage
                )  # Pass tool_usage as kwarg for clarity
                
                # Apply outbound guardrails evaluation
                result = self._apply_outbound_guardrails(result)
                
                return result

            setattr(patched_dispatch, "_klira_traced", True)
            _RealToolsHandler.dispatch = patched_dispatch

        # logger.info("CrewAI framework patching applied.")

    def apply_input_guardrails(
        self,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        func_name: str,
        injection_strategy: str = "auto",
    ) -> Tuple[Tuple[Any, ...], Dict[str, Any], bool, str]:
        """Apply input guardrails for CrewAI."""
        logger.debug(
            f"CrewAIAdapter: apply_input_guardrails called for {func_name} with strategy {injection_strategy}"
        )
        # CrewAI guardrails implementation would go here
        return args, kwargs, False, ""

    def apply_output_guardrails(
        self, result: Any, func_name: str
    ) -> Tuple[Any, bool, str]:
        """Apply output guardrails for CrewAI."""
        logger.debug(f"CrewAIAdapter: apply_output_guardrails called for {func_name}")
        # Use the new outbound guardrails methods
        try:
            result = self._apply_outbound_guardrails(result)
            return result, False, ""
        except Exception as e:
            logger.error(f"Error applying output guardrails: {e}")
            return result, False, ""

    def apply_augmentation(
        self,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        guidelines: List[str],
        func_name: str,
    ) -> Tuple[Tuple[Any, ...], Dict[str, Any]]:
        """Apply prompt augmentation for CrewAI."""
        logger.debug(
            f"CrewAIAdapter: apply_augmentation called for {func_name} with {len(guidelines)} guidelines"
        )
        # CrewAI augmentation implementation would go here
        return args, kwargs

    def unpatch_framework(self) -> None:
        if not CREWAI_INSTALLED:
            return
        # logger.info("CrewAI framework unpatching called (currently a placeholder).")
        pass  # Implement unpatching if necessary

    def _apply_outbound_guardrails(self, result: Any) -> Any:
        """Apply outbound guardrails to CrewAI results (synchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine
            
            # Extract content from CrewAI response
            response_text = self._extract_response_content(result)
            if not response_text.strip():
                return result
            
            # Create evaluation context
            context = {
                "llm_client": "crewai",
                "function_name": "crewai.agent.execute_task/crew.kickoff"
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
                        "Cannot run outbound guardrails evaluation for CrewAI in sync context within async loop. "
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
                    f"CrewAI outbound guardrails blocked response: {decision.reason}"
                )
                # Return a modified response with blocked content
                return self._create_blocked_response(result, decision.reason or "Content policy violation detected")
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying outbound guardrails for CrewAI: {e}", exc_info=True)
            # Fail open - return original result
            return result

    async def _apply_outbound_guardrails_async(self, result: Any) -> Any:
        """Apply outbound guardrails to CrewAI results (asynchronous)."""
        try:
            # Import here to avoid circular imports
            from klira.sdk.guardrails.engine import GuardrailsEngine
            
            # Extract content from CrewAI response
            response_text = self._extract_response_content(result)
            if not response_text.strip():
                return result
            
            # Create evaluation context
            context = {
                "llm_client": "crewai",
                "function_name": "crewai.agent.execute_task/crew.kickoff"
            }
            
            # Get guardrails engine and evaluate
            engine = GuardrailsEngine.get_instance()
            decision = await engine.evaluate(response_text, context, direction="outbound")
            
            if not decision.allowed:
                logger.warning(
                    f"CrewAI async outbound guardrails blocked response: {decision.reason}"
                )
                # Return a modified response with blocked content
                return self._create_blocked_response(result, decision.reason or "Content policy violation detected")
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying outbound guardrails for CrewAI async: {e}", exc_info=True)
            # Fail open - return original result
            return result

    def _extract_response_content(self, result: Any) -> str:
        """Extract text content from CrewAI response object."""
        try:
            # Handle CrewAI response formats
            if isinstance(result, str):
                return result
            
            # Handle CrewAI crew kickoff result (usually a string or dict with result)
            if hasattr(result, 'result') and result.result:
                return str(result.result)
            elif hasattr(result, 'output') and result.output:
                return str(result.output)
            elif hasattr(result, 'content') and result.content:
                return str(result.content)
            
            # Handle dictionary responses
            if isinstance(result, dict):
                # Look for common text fields
                for key in ["result", "output", "content", "response", "text"]:
                    if key in result and result[key]:
                        return str(result[key])
            
            # Handle task execution results
            if hasattr(result, 'description'):
                return str(result.description)
            
            # Fallback: try to convert to string
            return str(result) if result else ""
            
        except Exception as e:
            logger.debug(f"Error extracting content from CrewAI response: {e}")
            return ""

    def _create_blocked_response(self, original_result: Any, reason: str) -> Any:
        """Create a blocked response that matches the original response format."""
        try:
            blocked_message = f"[BLOCKED BY GUARDRAILS] - {reason}" if reason else "[BLOCKED BY GUARDRAILS] - Content policy violation detected"
            
            # Handle string results (most common for CrewAI)
            if isinstance(original_result, str):
                return blocked_message
            
            # Handle object results with attributes
            if hasattr(original_result, 'result'):
                original_result.result = blocked_message
                return original_result
            elif hasattr(original_result, 'output'):
                original_result.output = blocked_message
                return original_result
            elif hasattr(original_result, 'content'):
                original_result.content = blocked_message
                return original_result
            
            # Handle dictionary responses
            if isinstance(original_result, dict):
                # Create a copy to avoid modifying the original
                blocked_result = original_result.copy()
                # Look for common text fields to replace
                for key in ["result", "output", "content", "response", "text"]:
                    if key in blocked_result:
                        blocked_result[key] = blocked_message
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
