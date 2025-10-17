"""Framework-specific streaming adapters for LLM frameworks."""

import asyncio
import logging
from typing import Dict, Optional, Any, AsyncIterator
import threading

from .types import StreamChunk, StreamAdapter

logger = logging.getLogger("klira.streaming.adapters")


class StreamAdapterRegistry:
    """Registry for framework-specific streaming adapters.

    Integrates with existing Klira AI framework adapters to provide
    streaming capabilities for different LLM frameworks.
    """

    _adapters: Dict[str, StreamAdapter] = {}
    _lock = threading.RLock()

    @classmethod
    def register(cls, framework_name: str, adapter: StreamAdapter) -> None:
        """Register a streaming adapter for a framework."""
        with cls._lock:
            cls._adapters[framework_name] = adapter
            logger.info(f"Registered streaming adapter for {framework_name}")

    @classmethod
    def get_adapter(cls, framework_name: str) -> Optional[StreamAdapter]:
        """Get streaming adapter for framework."""
        with cls._lock:
            return cls._adapters.get(framework_name)

    @classmethod
    def get_available_frameworks(cls) -> list[str]:
        """Get list of frameworks with streaming support."""
        with cls._lock:
            return list(cls._adapters.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered adapters."""
        with cls._lock:
            cls._adapters.clear()


class OpenAIStreamAdapter(StreamAdapter):
    """Streaming adapter for OpenAI models."""

    def supports_streaming(self) -> bool:
        """OpenAI supports streaming."""
        return True

    async def create_stream(self, **kwargs: Any) -> AsyncIterator[Any]:
        """Create OpenAI streaming response."""
        try:
            # Import OpenAI at runtime to avoid dependency issues
            import openai  # noqa: F401

            # Extract OpenAI client from kwargs
            client = kwargs.get("client")
            if not client:
                raise ValueError("OpenAI client required for streaming")

            # Prepare streaming request
            stream_kwargs = dict(kwargs)
            stream_kwargs["stream"] = True
            stream_kwargs.pop("client", None)

            # Create streaming response
            stream = await client.chat.completions.create(**stream_kwargs)

            async for chunk in stream:
                yield chunk

        except ImportError:
            logger.error("OpenAI library not available for streaming")
            raise
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise

    async def process_stream_chunk(self, chunk_data: Any) -> StreamChunk:
        """Process OpenAI streaming chunk."""
        try:
            if hasattr(chunk_data, "choices") and chunk_data.choices:
                choice = chunk_data.choices[0]
                if hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                    content = choice.delta.content or ""

                    # Extract token count if available
                    token_count = None
                    if hasattr(chunk_data, "usage") and chunk_data.usage:
                        token_count = getattr(
                            chunk_data.usage, "completion_tokens", None
                        )

                    # Check if this is the final chunk
                    is_final = getattr(choice, "finish_reason", None) is not None

                    return StreamChunk(
                        content=content,
                        token_count=token_count,
                        is_final=is_final,
                        metadata={
                            "model": getattr(chunk_data, "model", ""),
                            "finish_reason": getattr(choice, "finish_reason", None),
                        },
                    )

            # Default empty chunk
            return StreamChunk(content="")

        except Exception as e:
            logger.warning(f"Error processing OpenAI chunk: {e}")
            return StreamChunk(content=str(chunk_data))


class LangChainStreamAdapter(StreamAdapter):
    """Streaming adapter for LangChain."""

    def supports_streaming(self) -> bool:
        """LangChain supports streaming via callbacks."""
        return True

    async def create_stream(self, **kwargs: Any) -> AsyncIterator[Any]:
        """Create LangChain streaming response using callbacks."""
        try:
            # This would integrate with LangChain's streaming callbacks
            # For now, provide a basic implementation

            agent_executor = kwargs.get("agent_executor")
            input_data = kwargs.get("input")

            if not agent_executor or not input_data:
                raise ValueError("LangChain agent_executor and input required")

            # LangChain streaming would be implemented via streaming callbacks
            # This is a simplified example
            response = await agent_executor.ainvoke(input_data)

            # Simulate streaming by chunking the response
            if isinstance(response, dict) and "output" in response:
                content = response["output"]
                chunk_size = 50  # Characters per chunk

                for i in range(0, len(content), chunk_size):
                    chunk_content = content[i : i + chunk_size]
                    yield {
                        "content": chunk_content,
                        "is_final": i + chunk_size >= len(content),
                    }
                    await asyncio.sleep(0.01)  # Simulate streaming delay

        except ImportError:
            logger.error("LangChain library not available for streaming")
            raise
        except Exception as e:
            logger.error(f"LangChain streaming error: {e}")
            raise

    async def process_stream_chunk(self, chunk_data: Any) -> StreamChunk:
        """Process LangChain streaming chunk."""
        try:
            if isinstance(chunk_data, dict):
                content = chunk_data.get("content", "")
                is_final = chunk_data.get("is_final", False)

                return StreamChunk(
                    content=content,
                    is_final=is_final,
                    metadata={"framework": "langchain"},
                )

            return StreamChunk(content=str(chunk_data))

        except Exception as e:
            logger.warning(f"Error processing LangChain chunk: {e}")
            return StreamChunk(content=str(chunk_data))


class AgentsSDKStreamAdapter(StreamAdapter):
    """Streaming adapter for OpenAI Agents SDK."""

    def supports_streaming(self) -> bool:
        """Agents SDK supports streaming."""
        return True

    async def create_stream(self, **kwargs: Any) -> AsyncIterator[Any]:
        """Create Agents SDK streaming response."""
        try:
            # Import Agents SDK at runtime
            from agents import Runner

            agent = kwargs.get("agent")
            query = kwargs.get("query") or kwargs.get("input")

            if not agent or not query:
                raise ValueError("Agent and query required for streaming")

            # Check if Runner supports streaming
            if hasattr(Runner, "stream"):
                # Use native streaming if available
                async for chunk in Runner.stream(agent, query):
                    yield chunk
            else:
                # Fallback: use regular run and simulate streaming
                result = await Runner.run(agent, query)

                if hasattr(result, "final_output"):
                    content = result.final_output
                    chunk_size = 30  # Characters per chunk

                    for i in range(0, len(content), chunk_size):
                        chunk_content = content[i : i + chunk_size]
                        yield {
                            "content": chunk_content,
                            "is_final": i + chunk_size >= len(content),
                        }
                        await asyncio.sleep(0.02)  # Simulate streaming

        except ImportError:
            logger.error("Agents SDK not available for streaming")
            raise
        except Exception as e:
            logger.error(f"Agents SDK streaming error: {e}")
            raise

    async def process_stream_chunk(self, chunk_data: Any) -> StreamChunk:
        """Process Agents SDK streaming chunk."""
        try:
            if isinstance(chunk_data, dict):
                content = chunk_data.get("content", "")
                is_final = chunk_data.get("is_final", False)

                return StreamChunk(
                    content=content,
                    is_final=is_final,
                    metadata={"framework": "agents_sdk"},
                )

            # Handle Agents SDK response objects
            if hasattr(chunk_data, "content"):
                return StreamChunk(
                    content=chunk_data.content, metadata={"framework": "agents_sdk"}
                )

            return StreamChunk(content=str(chunk_data))

        except Exception as e:
            logger.warning(f"Error processing Agents SDK chunk: {e}")
            return StreamChunk(content=str(chunk_data))


class CrewAIStreamAdapter(StreamAdapter):
    """Streaming adapter for CrewAI."""

    def supports_streaming(self) -> bool:
        """CrewAI basic streaming support."""
        return True

    async def create_stream(self, **kwargs: Any) -> AsyncIterator[Any]:
        """Create CrewAI streaming response."""
        try:
            crew = kwargs.get("crew")
            inputs = kwargs.get("inputs", {})

            if not crew:
                raise ValueError("CrewAI crew required for streaming")

            # CrewAI doesn't have native streaming, so simulate it
            result = await asyncio.get_event_loop().run_in_executor(
                None, crew.kickoff, inputs
            )

            # Simulate streaming by chunking the result
            if hasattr(result, "raw") and result.raw:
                content = result.raw
                chunk_size = 40  # Characters per chunk

                for i in range(0, len(content), chunk_size):
                    chunk_content = content[i : i + chunk_size]
                    yield {
                        "content": chunk_content,
                        "is_final": i + chunk_size >= len(content),
                        "crew_result": result,
                    }
                    await asyncio.sleep(0.03)  # Simulate streaming delay

        except ImportError:
            logger.error("CrewAI library not available for streaming")
            raise
        except Exception as e:
            logger.error(f"CrewAI streaming error: {e}")
            raise

    async def process_stream_chunk(self, chunk_data: Any) -> StreamChunk:
        """Process CrewAI streaming chunk."""
        try:
            if isinstance(chunk_data, dict):
                content = chunk_data.get("content", "")
                is_final = chunk_data.get("is_final", False)

                return StreamChunk(
                    content=content,
                    is_final=is_final,
                    metadata={
                        "framework": "crewai",
                        "crew_result": chunk_data.get("crew_result"),
                    },
                )

            return StreamChunk(content=str(chunk_data))

        except Exception as e:
            logger.warning(f"Error processing CrewAI chunk: {e}")
            return StreamChunk(content=str(chunk_data))


def register_default_adapters() -> None:
    """Register default streaming adapters for common frameworks."""
    try:
        # Register OpenAI adapter
        StreamAdapterRegistry.register("openai", OpenAIStreamAdapter())

        # Register LangChain adapter
        StreamAdapterRegistry.register("langchain", LangChainStreamAdapter())

        # Register Agents SDK adapter
        StreamAdapterRegistry.register("agents_sdk", AgentsSDKStreamAdapter())

        # Register CrewAI adapter
        StreamAdapterRegistry.register("crewai", CrewAIStreamAdapter())

        logger.info("Default streaming adapters registered")

    except Exception as e:
        logger.error(f"Failed to register default streaming adapters: {e}")


def detect_and_get_streaming_adapter(
    framework_hint: Optional[str] = None, **kwargs: Any
) -> Optional[StreamAdapter]:
    """Detect framework and return appropriate streaming adapter.

    Args:
        framework_hint: Hint about which framework to use
        **kwargs: Additional context for framework detection

    Returns:
        Appropriate streaming adapter or None
    """
    try:
        # Use framework hint if provided
        if framework_hint:
            adapter = StreamAdapterRegistry.get_adapter(framework_hint)
            if adapter and adapter.supports_streaming():
                return adapter

        # Try to detect framework from context
        if "client" in kwargs:
            # Looks like OpenAI client
            client = kwargs["client"]
            if hasattr(client, "chat") and hasattr(client.chat, "completions"):
                return StreamAdapterRegistry.get_adapter("openai")

        if "agent_executor" in kwargs:
            # Looks like LangChain
            return StreamAdapterRegistry.get_adapter("langchain")

        if "agent" in kwargs and "query" in kwargs:
            # Looks like Agents SDK
            return StreamAdapterRegistry.get_adapter("agents_sdk")

        if "crew" in kwargs:
            # Looks like CrewAI
            return StreamAdapterRegistry.get_adapter("crewai")

        # Try to detect from existing framework registry
        # Note: FrameworkRegistry doesn't have detect_framework method
        # This would need to be implemented or use a different approach
        # For now, skip this detection method

        logger.warning("Could not detect appropriate streaming adapter")
        return None

    except Exception as e:
        logger.error(f"Error detecting streaming adapter: {e}")
        return None


# Auto-register default adapters when module is imported
register_default_adapters()
