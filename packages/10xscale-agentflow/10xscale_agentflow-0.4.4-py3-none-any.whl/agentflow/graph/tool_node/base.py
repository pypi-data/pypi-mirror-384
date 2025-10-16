"""Tool execution node for TAF graph workflows.

This module provides the ToolNode class, which serves as a unified registry and executor
for callable functions from various sources including local functions, MCP (Model Context Protocol)
tools, Composio adapters, and LangChain tools. The ToolNode is designed with a modular
architecture using mixins to handle different tool providers.

The ToolNode maintains compatibility with TAF's dependency injection system and
publishes execution events for monitoring and debugging purposes.

Typical usage example:
    ```python
    def my_tool(query: str) -> str:
        return f"Result for: {query}"


    tools = ToolNode([my_tool])
    result = await tools.invoke("my_tool", {"query": "test"}, "call_id", config, state)
    ```
"""

from __future__ import annotations

import asyncio
import logging
import sys
import typing as t

from injectq import Inject

from agentflow.adapters.tools import ComposioAdapter
from agentflow.publisher.events import ContentType, Event, EventModel, EventType
from agentflow.publisher.publish import publish_event
from agentflow.state import AgentState, ErrorBlock, Message, ToolCallBlock, ToolResultBlock
from agentflow.state.message_block import RemoteToolCallBlock
from agentflow.utils import CallbackManager

from . import deps
from .executors import ComposioMixin, KwargsResolverMixin, LangChainMixin, LocalExecMixin, MCPMixin
from .schema import SchemaMixin


logger = logging.getLogger(__name__)


class ToolNode(
    SchemaMixin,
    LocalExecMixin,
    MCPMixin,
    ComposioMixin,
    LangChainMixin,
    KwargsResolverMixin,
):
    """A unified registry and executor for callable functions from various tool providers.

    ToolNode serves as the central hub for managing and executing tools from multiple sources:
    - Local Python functions
    - MCP (Model Context Protocol) tools
    - Composio adapter tools
    - LangChain tools

    The class uses a mixin-based architecture to separate concerns and maintain clean
    integration with different tool providers. It provides both synchronous and asynchronous
    execution methods with comprehensive event publishing and error handling.

    Attributes:
        _funcs: Dictionary mapping function names to callable functions.
        _client: Optional MCP client for remote tool execution.
        _composio: Optional Composio adapter for external integrations.
        _langchain: Optional LangChain adapter for LangChain tools.
        mcp_tools: List of available MCP tool names.
        composio_tools: List of available Composio tool names.
        langchain_tools: List of available LangChain tool names.

    Example:
        ```python
        # Define local tools
        def weather_tool(location: str) -> str:
            return f"Weather in {location}: Sunny, 25°C"


        def calculator(a: int, b: int) -> int:
            return a + b


        # Create ToolNode with local functions
        tools = ToolNode([weather_tool, calculator])

        # Execute a tool
        result = await tools.invoke(
            name="weather_tool",
            args={"location": "New York"},
            tool_call_id="call_123",
            config={"user_id": "user1"},
            state=agent_state,
        )
        ```
    """

    def __init__(
        self,
        functions: t.Iterable[t.Callable],
        client: deps.Client | None = None,  # type: ignore
        composio_adapter: ComposioAdapter | None = None,
        langchain_adapter: t.Any | None = None,
    ) -> None:
        """Initialize ToolNode with functions and optional tool adapters.

        Args:
            functions: Iterable of callable functions to register as tools. Each function
                will be registered with its `__name__` as the tool identifier.
            client: Optional MCP (Model Context Protocol) client for remote tool access.
                Requires 'fastmcp' and 'mcp' packages to be installed.
            composio_adapter: Optional Composio adapter for external integrations and
                third-party API access.
            langchain_adapter: Optional LangChain adapter for accessing LangChain tools
                and integrations.

        Raises:
            ImportError: If MCP client is provided but required packages are not installed.
            TypeError: If any item in functions is not callable.

        Note:
            When using MCP client functionality, ensure you have installed the required
            dependencies with: `pip install 10xscale-agentflow[mcp]`
        """
        logger.info("Initializing ToolNode with %d functions", len(list(functions)))

        if client is not None:
            # Read flags dynamically so tests can patch agentflow.graph.tool_node.HAS_*
            mod = sys.modules.get("agentflow.graph.tool_node")
            has_fastmcp = getattr(mod, "HAS_FASTMCP", deps.HAS_FASTMCP) if mod else deps.HAS_FASTMCP
            has_mcp = getattr(mod, "HAS_MCP", deps.HAS_MCP) if mod else deps.HAS_MCP

            if not has_fastmcp or not has_mcp:
                raise ImportError(
                    "MCP client functionality requires 'fastmcp' and 'mcp' packages. "
                    "Install with: pip install 10xscale-agentflow[mcp]"
                )
            logger.debug("ToolNode initialized with MCP client")

        self._funcs: dict[str, t.Callable] = {}
        self._client: deps.Client | None = client  # type: ignore
        self._composio: ComposioAdapter | None = composio_adapter
        self._langchain: t.Any | None = langchain_adapter

        for fn in functions:
            if not callable(fn):
                raise TypeError("ToolNode only accepts callables")
            self._funcs[fn.__name__] = fn

        self.mcp_tools: list[str] = []
        self.composio_tools: list[str] = []
        self.langchain_tools: list[str] = []
        self.frontend_tools: list[dict] = []
        self.frontend_tool_names: list[str] = []

    async def _all_tools_async(self) -> list[dict]:
        tools: list[dict] = self.get_local_tool()
        tools.extend(await self._get_mcp_tool())
        tools.extend(await self._get_composio_tools())
        tools.extend(await self._get_langchain_tools())
        tools.extend(self.frontend_tools)
        return tools

    def set_local_tool(self, tool_names: list[dict]) -> None:
        # already validated tool names
        self.frontend_tools = tool_names
        self.frontend_tool_names = [tool.get("function", {}).get("name") for tool in tool_names]

    async def all_tools(self) -> list[dict]:
        """Get all available tools from all configured providers.

        Retrieves and combines tool definitions from local functions, MCP client,
        Composio adapter, and LangChain adapter. Each tool definition includes
        the function schema with parameters and descriptions.

        Returns:
            List of tool definitions in OpenAI function calling format. Each dict
            contains 'type': 'function' and 'function' with name, description,
            and parameters schema.

        Example:
            ```python
            tools = await tool_node.all_tools()
            # Returns:
            # [
            #   {
            #     "type": "function",
            #     "function": {
            #       "name": "weather_tool",
            #       "description": "Get weather information for a location",
            #       "parameters": {
            #         "type": "object",
            #         "properties": {
            #           "location": {"type": "string"}
            #         },
            #         "required": ["location"]
            #       }
            #     }
            #   }
            # ]
            ```
        """
        return await self._all_tools_async()

    def all_tools_sync(self) -> list[dict]:
        """Synchronously get all available tools from all configured providers.

        This is a synchronous wrapper around the async all_tools() method.
        It uses asyncio.run() to handle async operations from MCP, Composio,
        and LangChain adapters.

        Returns:
            List of tool definitions in OpenAI function calling format.

        Note:
            Prefer using the async `all_tools()` method when possible, especially
            in async contexts, to avoid potential event loop issues.
        """
        tools: list[dict] = self.get_local_tool()
        if self._client:
            result = asyncio.run(self._get_mcp_tool())
            if result:
                tools.extend(result)
        comp = asyncio.run(self._get_composio_tools())
        if comp:
            tools.extend(comp)
        lc = asyncio.run(self._get_langchain_tools())
        if lc:
            tools.extend(lc)
        return tools

    async def invoke(  # noqa: PLR0915
        self,
        name: str,
        args: dict,
        tool_call_id: str,
        config: dict[str, t.Any],
        state: AgentState,
        callback_manager: CallbackManager = Inject[CallbackManager],
    ) -> Message:
        """Execute a specific tool by name with the provided arguments.

        This method handles tool execution across all configured providers (local,
        MCP, Composio, LangChain) with comprehensive error handling, event publishing,
        and callback management.

        Args:
            name: The name of the tool to execute.
            args: Dictionary of arguments to pass to the tool function.
            tool_call_id: Unique identifier for this tool execution, used for
                tracking and result correlation.
            config: Configuration dictionary containing execution context and
                user-specific settings.
            state: Current agent state for context-aware tool execution.
            callback_manager: Manager for executing pre/post execution callbacks.
                Injected via dependency injection if not provided.

        Returns:
            Message object containing tool execution results, either successful
            output or error information with appropriate status indicators.

        Raises:
            The method handles all exceptions internally and returns error Messages
            rather than raising exceptions, ensuring robust execution flow.

        Example:
            ```python
            result = await tool_node.invoke(
                name="weather_tool",
                args={"location": "Paris", "units": "metric"},
                tool_call_id="call_abc123",
                config={"user_id": "user1", "session_id": "session1"},
                state=current_agent_state,
            )

            # result is a Message with tool execution results
            print(result.content)  # Tool output or error information
            ```

        Note:
            The method publishes execution events throughout the process for
            monitoring and debugging purposes. Tool execution is routed based
            on tool provider precedence: MCP → Composio → LangChain → Local.
        """
        logger.info("Executing tool '%s' with %d arguments", name, len(args))
        logger.debug("Tool arguments: %s", args)

        event = EventModel.default(
            config,
            data={"args": args, "tool_call_id": tool_call_id, "function_name": name},
            content_type=[ContentType.TOOL_CALL],
            event=Event.TOOL_EXECUTION,
        )
        event.node_name = name
        # Attach structured tool call block
        event.content_blocks = [ToolCallBlock(id=tool_call_id, name=name, args=args)]
        publish_event(event)
        # Check this is available in frontend tools
        if name in self.frontend_tool_names:
            event.metadata["is_frontend"] = True
            publish_event(event)
            # This tool in frontend tools, so we can not execute it locally
            # so we will return a message
            # And the graph will be interrupted here
            return Message(
                content=[RemoteToolCallBlock(id=tool_call_id, name=name, args=args)],
                role="tool",
                metadata={
                    "is_frontend": True,
                },
            )

        if name in self.mcp_tools:
            event.metadata["is_mcp"] = True
            publish_event(event)
            res = await self._mcp_execute(
                name,
                args,
                tool_call_id,
                config,
                callback_manager,
            )
            event.data["message"] = res.model_dump()
            # Attach tool result block mirroring the tool output
            event.content_blocks = [ToolResultBlock(call_id=tool_call_id, output=res.model_dump())]
            event.event_type = EventType.END
            event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
            publish_event(event)
            return res

        if name in self.composio_tools:
            event.metadata["is_composio"] = True
            publish_event(event)
            res = await self._composio_execute(
                name,
                args,
                tool_call_id,
                config,
                callback_manager,
            )
            event.data["message"] = res.model_dump()
            event.content_blocks = [ToolResultBlock(call_id=tool_call_id, output=res.model_dump())]
            event.event_type = EventType.END
            event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
            publish_event(event)
            return res

        if name in self.langchain_tools:
            event.metadata["is_langchain"] = True
            publish_event(event)
            res = await self._langchain_execute(
                name,
                args,
                tool_call_id,
                config,
                callback_manager,
            )
            event.data["message"] = res.model_dump()
            event.content_blocks = [ToolResultBlock(call_id=tool_call_id, output=res.model_dump())]
            event.event_type = EventType.END
            event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
            publish_event(event)
            return res

        if name in self._funcs:
            event.metadata["is_mcp"] = False
            publish_event(event)
            res = await self._internal_execute(
                name,
                args,
                tool_call_id,
                config,
                state,
                callback_manager,
            )
            event.data["message"] = res.model_dump()
            event.content_blocks = [ToolResultBlock(call_id=tool_call_id, output=res.model_dump())]
            event.event_type = EventType.END
            event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
            publish_event(event)
            return res

        error_msg = f"Tool '{name}' not found."
        event.data["error"] = error_msg
        event.event_type = EventType.ERROR
        event.content_type = [ContentType.TOOL_RESULT, ContentType.ERROR]
        publish_event(event)
        return Message.tool_message(
            content=[
                ErrorBlock(message=error_msg),
                ToolResultBlock(
                    call_id=tool_call_id,
                    output=error_msg,
                    is_error=True,
                    status="failed",
                ),
            ],
        )

    async def stream(  # noqa: PLR0915
        self,
        name: str,
        args: dict,
        tool_call_id: str,
        config: dict[str, t.Any],
        state: AgentState,
        callback_manager: CallbackManager = Inject[CallbackManager],
    ) -> t.AsyncIterator[Message]:
        """Execute a tool with streaming support, yielding incremental results.

        Similar to invoke() but designed for tools that can provide streaming responses
        or when you want to process results as they become available. Currently,
        most tool providers return complete results, so this method typically yields
        a single Message with the full result.

        Args:
            name: The name of the tool to execute.
            args: Dictionary of arguments to pass to the tool function.
            tool_call_id: Unique identifier for this tool execution.
            config: Configuration dictionary containing execution context.
            state: Current agent state for context-aware tool execution.
            callback_manager: Manager for executing pre/post execution callbacks.

        Yields:
            Message objects containing tool execution results or status updates.
            For most tools, this will yield a single complete result Message.

        Example:
            ```python
            async for message in tool_node.stream(
                name="data_processor",
                args={"dataset": "large_data.csv"},
                tool_call_id="call_stream123",
                config={"user_id": "user1"},
                state=current_state,
            ):
                print(f"Received: {message.content}")
                # Process each streamed result
            ```

        Note:
            The streaming interface is designed for future expansion where tools
            may provide true streaming responses. Currently, it provides a
            consistent async iterator interface over tool results.
        """
        logger.info("Executing tool '%s' with %d arguments", name, len(args))
        logger.debug("Tool arguments: %s", args)
        event = EventModel.default(
            config,
            data={"args": args, "tool_call_id": tool_call_id, "function_name": name},
            content_type=[ContentType.TOOL_CALL],
            event=Event.TOOL_EXECUTION,
        )
        event.node_name = "ToolNode"
        event.content_blocks = [ToolCallBlock(id=tool_call_id, name=name, args=args)]

        if name in self.frontend_tool_names:
            event.metadata["is_frontend"] = True
            publish_event(event)
            # This tool in frontend tools, so we can not execute it locally
            # so we will return a message
            # And the graph will be interrupted here
            yield Message(
                content=[RemoteToolCallBlock(id=tool_call_id, name=name, args=args)],
                role="tool",
                metadata={
                    "is_frontend": True,
                },
            )
            return

        if name in self.mcp_tools:
            event.metadata["function_type"] = "mcp"
            publish_event(event)
            message = await self._mcp_execute(
                name,
                args,
                tool_call_id,
                config,
                callback_manager,
            )
            event.data["message"] = message.model_dump()
            event.content_blocks = [
                ToolResultBlock(call_id=tool_call_id, output=message.model_dump())
            ]
            event.event_type = EventType.END
            event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
            publish_event(event)
            yield message
            return

        if name in self.composio_tools:
            event.metadata["function_type"] = "composio"
            publish_event(event)
            message = await self._composio_execute(
                name,
                args,
                tool_call_id,
                config,
                callback_manager,
            )
            event.data["message"] = message.model_dump()
            event.content_blocks = [
                ToolResultBlock(call_id=tool_call_id, output=message.model_dump())
            ]
            event.event_type = EventType.END
            event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
            publish_event(event)
            yield message
            return

        if name in self.langchain_tools:
            event.metadata["function_type"] = "langchain"
            publish_event(event)
            message = await self._langchain_execute(
                name,
                args,
                tool_call_id,
                config,
                callback_manager,
            )
            event.data["message"] = message.model_dump()
            event.content_blocks = [
                ToolResultBlock(call_id=tool_call_id, output=message.model_dump())
            ]
            event.event_type = EventType.END
            event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
            publish_event(event)
            yield message
            return

        if name in self._funcs:
            event.metadata["function_type"] = "internal"
            publish_event(event)

            result = await self._internal_execute(
                name,
                args,
                tool_call_id,
                config,
                state,
                callback_manager,
            )
            event.data["message"] = result.model_dump()
            event.content_blocks = [
                ToolResultBlock(call_id=tool_call_id, output=result.model_dump())
            ]
            event.event_type = EventType.END
            event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
            publish_event(event)
            yield result
            return

        error_msg = f"Tool '{name}' not found."
        event.data["error"] = error_msg
        event.event_type = EventType.ERROR
        event.content_type = [ContentType.TOOL_RESULT, ContentType.ERROR]
        publish_event(event)

        yield Message.tool_message(
            content=[
                ErrorBlock(message=error_msg),
                ToolResultBlock(
                    call_id=tool_call_id,
                    output=error_msg,
                    is_error=True,
                    status="failed",
                ),
            ],
        )
