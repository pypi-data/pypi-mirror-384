"""Executors for different tool providers and local functions."""

from __future__ import annotations

import inspect
import json
import logging
import typing as t

from agentflow.adapters.tools import ComposioAdapter
from agentflow.publisher.events import ContentType, Event, EventModel, EventType
from agentflow.publisher.publish import publish_event
from agentflow.state import AgentState, ContentBlock, ErrorBlock, Message, ToolResultBlock
from agentflow.utils import CallbackContext, CallbackManager, InvocationType, call_sync_or_async

from .constants import INJECTABLE_PARAMS


logger = logging.getLogger(__name__)


class ComposioMixin:
    _composio: ComposioAdapter | None
    composio_tools: list[str]

    async def _get_composio_tools(self) -> list[dict]:
        tools: list[dict] = []
        if not self._composio:
            return tools
        try:
            raw = self._composio.list_raw_tools_for_llm()
            for tdef in raw:
                fn = tdef.get("function", {})
                name = fn.get("name")
                if name:
                    self.composio_tools.append(name)
                tools.append(tdef)
        except Exception as e:  # pragma: no cover - network/optional
            logger.exception("Failed to fetch Composio tools: %s", e)
        return tools

    async def _composio_execute(  # noqa: PLR0915
        self,
        name: str,
        args: dict,
        tool_call_id: str,
        config: dict[str, t.Any],
        callback_mgr: CallbackManager,
    ) -> Message:
        context = CallbackContext(
            invocation_type=InvocationType.TOOL,
            node_name="ToolNode",
            function_name=name,
            metadata={
                "tool_call_id": tool_call_id,
                "args": args,
                "config": config,
                "composio": True,
            },
        )
        meta = {"function_name": name, "function_argument": args, "tool_call_id": tool_call_id}

        event = EventModel.default(
            base_config=config,
            data={
                "tool_call_id": tool_call_id,
                "args": args,
                "function_name": name,
                "is_composio": True,
            },
            content_type=[ContentType.TOOL_CALL],
            event=Event.TOOL_EXECUTION,
        )
        event.event_type = EventType.PROGRESS
        event.node_name = "ToolNode"
        publish_event(event)

        input_data = {**args}

        def safe_serialize(obj: t.Any) -> dict[str, t.Any]:
            try:
                json.dumps(obj)
                return obj if isinstance(obj, dict) else {"content": obj}
            except (TypeError, OverflowError):
                if hasattr(obj, "model_dump"):
                    dumped = obj.model_dump()  # type: ignore
                    if isinstance(dumped, dict) and dumped.get("type") == "resource":
                        resource = dumped.get("resource", {})
                        if isinstance(resource, dict) and "uri" in resource:
                            resource["uri"] = str(resource["uri"])
                            dumped["resource"] = resource
                    return dumped
                return {"content": str(obj), "type": "fallback"}

        try:
            input_data = await callback_mgr.execute_before_invoke(context, input_data)
            event.event_type = EventType.UPDATE
            event.metadata["status"] = "before_invoke_complete Invoke Composio"
            publish_event(event)

            comp_conf = (config.get("composio") if isinstance(config, dict) else None) or {}
            user_id = comp_conf.get("user_id") or config.get("user_id")
            connected_account_id = comp_conf.get("connected_account_id") or config.get(
                "connected_account_id"
            )

            if not self._composio:
                error_result = Message.tool_message(
                    content=[
                        ErrorBlock(message="Composio adapter not configured"),
                        ToolResultBlock(
                            call_id=tool_call_id,
                            output="Composio adapter not configured",
                            status="failed",
                            is_error=True,
                        ),
                    ],
                    meta=meta,
                )
                event.event_type = EventType.ERROR
                event.metadata["error"] = "Composio adapter not configured"
                publish_event(event)
                return error_result

            res = self._composio.execute(
                slug=name,
                arguments=input_data,
                user_id=user_id,
                connected_account_id=connected_account_id,
            )

            successful = bool(res.get("successful"))
            payload = res.get("data")
            error = res.get("error")

            result_blocks = []
            if error and not successful:
                result_blocks.append(
                    ToolResultBlock(
                        call_id=tool_call_id,
                        output={"success": False, "error": error},
                        status="failed",
                        is_error=True,
                    )
                )
                result_blocks.append(ErrorBlock(message=error))
            else:
                if isinstance(payload, list):
                    output = [safe_serialize(item) for item in payload]
                else:
                    output = [safe_serialize(payload)]
                result_blocks.append(
                    ToolResultBlock(
                        call_id=tool_call_id,
                        output=output,
                        status="completed" if successful else "failed",
                        is_error=not successful,
                    )
                )

            result = Message.tool_message(
                content=result_blocks,
                meta=meta,
            )

            res_msg = await callback_mgr.execute_after_invoke(context, input_data, result)
            event.event_type = EventType.END
            event.data["message"] = result.model_dump()
            event.metadata["status"] = "Composio tool execution complete"
            event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
            publish_event(event)
            return res_msg

        except Exception as e:  # pragma: no cover - error path
            recovery_result = await callback_mgr.execute_on_error(context, input_data, e)
            if isinstance(recovery_result, Message):
                event.event_type = EventType.END
                event.data["message"] = recovery_result.model_dump()
                event.metadata["status"] = "Composio tool execution complete, with recovery"
                event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
                publish_event(event)
                return recovery_result

            event.event_type = EventType.END
            event.data["error"] = str(e)
            event.metadata["status"] = "Composio tool execution complete, with error"
            event.content_type = [ContentType.TOOL_RESULT, ContentType.ERROR]
            publish_event(event)
            return Message.tool_message(
                content=[
                    ToolResultBlock(
                        call_id=tool_call_id,
                        output=f"Composio execution error: {e}",
                        status="failed",
                        is_error=True,
                    ),
                    ErrorBlock(message=f"Composio execution error: {e}"),
                ],
                meta=meta,
            )


class LangChainMixin:
    _langchain: t.Any | None
    langchain_tools: list[str]

    async def _get_langchain_tools(self) -> list[dict]:
        tools: list[dict] = []
        if not self._langchain:
            return tools
        try:
            raw = self._langchain.list_tools_for_llm()
            for tdef in raw:
                fn = tdef.get("function", {})
                name = fn.get("name")
                if name:
                    self.langchain_tools.append(name)
                tools.append(tdef)
        except Exception as e:  # pragma: no cover - optional
            logger.warning("Failed to fetch LangChain tools: %s", e)
        return tools

    async def _langchain_execute(  # noqa: PLR0915
        self,
        name: str,
        args: dict,
        tool_call_id: str,
        config: dict[str, t.Any],
        callback_mgr: CallbackManager,
    ) -> Message:
        context = CallbackContext(
            invocation_type=InvocationType.TOOL,
            node_name="ToolNode",
            function_name=name,
            metadata={
                "tool_call_id": tool_call_id,
                "args": args,
                "config": config,
                "langchain": True,
            },
        )
        meta = {"function_name": name, "function_argument": args, "tool_call_id": tool_call_id}

        event = EventModel.default(
            base_config=config,
            data={
                "tool_call_id": tool_call_id,
                "args": args,
                "function_name": name,
                "is_langchain": True,
            },
            content_type=[ContentType.TOOL_CALL],
            event=Event.TOOL_EXECUTION,
        )
        event.event_type = EventType.PROGRESS
        event.node_name = "ToolNode"
        publish_event(event)

        input_data = {**args}

        def safe_serialize(obj: t.Any) -> dict[str, t.Any]:
            try:
                json.dumps(obj)
                return obj if isinstance(obj, dict) else {"content": obj}
            except (TypeError, OverflowError):
                if hasattr(obj, "model_dump"):
                    dumped = obj.model_dump()  # type: ignore
                    if isinstance(dumped, dict) and dumped.get("type") == "resource":
                        resource = dumped.get("resource", {})
                        if isinstance(resource, dict) and "uri" in resource:
                            resource["uri"] = str(resource["uri"])
                            dumped["resource"] = resource
                    return dumped
                return {"content": str(obj), "type": "fallback"}

        try:
            input_data = await callback_mgr.execute_before_invoke(context, input_data)
            event.event_type = EventType.UPDATE
            event.metadata["status"] = "before_invoke_complete Invoke LangChain"
            publish_event(event)

            if not self._langchain:
                error_result = Message.tool_message(
                    content=[
                        ErrorBlock(message="LangChain adapter not configured"),
                        ToolResultBlock(
                            call_id=tool_call_id,
                            output="LangChain adapter not configured",
                            status="failed",
                            is_error=True,
                        ),
                    ],
                    meta=meta,
                )
                event.event_type = EventType.ERROR
                event.metadata["error"] = "LangChain adapter not configured"
                publish_event(event)
                return error_result

            res = self._langchain.execute(name=name, arguments=input_data)
            successful = bool(res.get("successful"))
            payload = res.get("data")
            error = res.get("error")

            result_blocks = []
            if error and not successful:
                result_blocks.append(
                    ToolResultBlock(
                        call_id=tool_call_id,
                        output={"success": False, "error": error},
                        status="failed",
                        is_error=True,
                    )
                )
                result_blocks.append(ErrorBlock(message=error))
            else:
                if isinstance(payload, list):
                    output = [safe_serialize(item) for item in payload]
                else:
                    output = [safe_serialize(payload)]
                result_blocks.append(
                    ToolResultBlock(
                        call_id=tool_call_id,
                        output=output,
                        status="completed" if successful else "failed",
                        is_error=not successful,
                    )
                )

            result = Message.tool_message(
                content=result_blocks,
                meta=meta,
            )

            res_msg = await callback_mgr.execute_after_invoke(context, input_data, result)
            event.event_type = EventType.END
            event.data["message"] = result.model_dump()
            event.metadata["status"] = "LangChain tool execution complete"
            event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
            publish_event(event)
            return res_msg

        except Exception as e:  # pragma: no cover - error path
            recovery_result = await callback_mgr.execute_on_error(context, input_data, e)
            if isinstance(recovery_result, Message):
                event.event_type = EventType.END
                event.data["message"] = recovery_result.model_dump()
                event.metadata["status"] = "LangChain tool execution complete, with recovery"
                event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
                publish_event(event)
                return recovery_result

            event.event_type = EventType.END
            event.data["error"] = str(e)
            event.metadata["status"] = "LangChain tool execution complete, with error"
            event.content_type = [ContentType.TOOL_RESULT, ContentType.ERROR]
            publish_event(event)
            return Message.tool_message(
                content=[
                    ToolResultBlock(
                        call_id=tool_call_id,
                        output=f"LangChain execution error: {e}",
                        status="failed",
                        is_error=True,
                    ),
                    ErrorBlock(message=f"LangChain execution error: {e}"),
                ],
                meta=meta,
            )


class LocalExecMixin:
    _funcs: dict[str, t.Callable]

    def _prepare_input_data_tool(
        self,
        fn: t.Callable,
        name: str,
        args: dict,
        default_data: dict,
    ) -> dict:
        sig = inspect.signature(fn)
        input_data = {}
        for param_name, param in sig.parameters.items():
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue

            if param_name in ["state", "config", "tool_call_id"]:
                input_data[param_name] = default_data[param_name]
                continue

            if param_name in INJECTABLE_PARAMS:
                continue

            if (
                hasattr(param, "default")
                and param.default is not inspect._empty
                and hasattr(param.default, "__class__")
            ):
                try:
                    if "Inject" in str(type(param.default)):
                        logger.debug(
                            "Skipping injectable parameter '%s' with Inject syntax",
                            param_name,
                        )
                        continue
                except Exception as exc:  # pragma: no cover - defensive
                    logger.exception("Inject detection failed for '%s': %s", param_name, exc)

            if param_name in args:
                input_data[param_name] = args[param_name]
            elif param.default is inspect.Parameter.empty:
                raise TypeError(f"Missing required parameter '{param_name}' for function '{name}'")

        return input_data

    async def _internal_execute(  # noqa: PLR0915
        self,
        name: str,
        args: dict,
        tool_call_id: str,
        config: dict[str, t.Any],
        state: AgentState,
        callback_mgr: CallbackManager,
    ) -> Message:
        context = CallbackContext(
            invocation_type=InvocationType.TOOL,
            node_name="ToolNode",
            function_name=name,
            metadata={"tool_call_id": tool_call_id, "args": args, "config": config},
        )

        fn = self._funcs[name]
        input_data = self._prepare_input_data_tool(
            fn,
            name,
            args,
            {
                "tool_call_id": tool_call_id,
                "state": state,
                "config": config,
            },
        )

        meta = {
            "function_name": name,
            "function_argument": args,
            "tool_call_id": tool_call_id,
        }

        event = EventModel.default(
            base_config=config,
            data={
                "tool_call_id": tool_call_id,
                "args": args,
                "function_name": name,
                "is_mcp": False,
            },
            content_type=[ContentType.TOOL_CALL],
            event=Event.TOOL_EXECUTION,
        )
        event.event_type = EventType.PROGRESS
        event.node_name = "ToolNode"
        publish_event(event)

        def safe_serialize(obj: t.Any) -> dict[str, t.Any]:
            try:
                json.dumps(obj)
                return obj if isinstance(obj, dict) else {"content": obj}
            except (TypeError, OverflowError):
                if hasattr(obj, "model_dump"):
                    dumped = obj.model_dump()  # type: ignore
                    if isinstance(dumped, dict) and dumped.get("type") == "resource":
                        resource = dumped.get("resource", {})
                        if isinstance(resource, dict) and "uri" in resource:
                            resource["uri"] = str(resource["uri"])
                            dumped["resource"] = resource
                    return dumped
                return {"content": str(obj), "type": "fallback"}

        try:
            input_data = await callback_mgr.execute_before_invoke(context, input_data)

            event.event_type = EventType.UPDATE
            event.metadata["status"] = "before_invoke_complete Invoke internal"
            publish_event(event)

            result = await call_sync_or_async(fn, **input_data)

            result = await callback_mgr.execute_after_invoke(
                context,
                input_data,
                result,
            )

            if isinstance(result, Message):
                meta_data = result.metadata or {}
                meta.update(meta_data)
                result.metadata = meta

                event.event_type = EventType.END
                event.data["message"] = result.model_dump()
                event.metadata["status"] = "Internal tool execution complete"
                event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
                publish_event(event)
                return result

            result_blocks = []
            if isinstance(result, str):
                result_blocks.append(
                    ToolResultBlock(
                        call_id=tool_call_id,
                        output=result,
                        status="completed",
                        is_error=False,
                    )
                )
            elif isinstance(result, dict):
                result_blocks.append(
                    ToolResultBlock(
                        call_id=tool_call_id,
                        output=[safe_serialize(result)],
                        status="completed",
                        is_error=False,
                    )
                )
            elif hasattr(result, "model_dump"):
                result_blocks.append(
                    ToolResultBlock(
                        call_id=tool_call_id,
                        output=[safe_serialize(result.model_dump())],
                        status="completed",
                        is_error=False,
                    )
                )
            elif hasattr(result, "__dict__"):
                result_blocks.append(
                    ToolResultBlock(
                        call_id=tool_call_id,
                        output=[safe_serialize(result.__dict__)],
                        status="completed",
                        is_error=False,
                    )
                )
            elif isinstance(result, list):
                output = [safe_serialize(item) for item in result]
                result_blocks.append(
                    ToolResultBlock(
                        call_id=tool_call_id,
                        output=output,
                        status="completed",
                        is_error=False,
                    )
                )
            else:
                result_blocks.append(
                    ToolResultBlock(
                        call_id=tool_call_id,
                        output=str(result),
                        status="completed",
                        is_error=False,
                    )
                )

            msg = Message.tool_message(
                content=result_blocks,
                meta=meta,
            )

            event.event_type = EventType.END
            event.data["message"] = msg.model_dump()
            event.metadata["status"] = "Internal tool execution complete"
            event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
            publish_event(event)

            return msg

        except Exception as e:  # pragma: no cover - error path
            recovery_result = await callback_mgr.execute_on_error(context, input_data, e)

            if isinstance(recovery_result, Message):
                event.event_type = EventType.END
                event.data["message"] = recovery_result.model_dump()
                event.metadata["status"] = "Internal tool execution complete, with recovery"
                event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
                publish_event(event)
                return recovery_result

            event.event_type = EventType.END
            event.data["error"] = str(e)
            event.metadata["status"] = "Internal tool execution complete, with error"
            event.content_type = [ContentType.TOOL_RESULT, ContentType.ERROR]
            publish_event(event)

            return Message.tool_message(
                content=[
                    ToolResultBlock(
                        call_id=tool_call_id,
                        output=f"Internal execution error: {e}",
                        status="failed",
                        is_error=True,
                    ),
                    ErrorBlock(message=f"Internal execution error: {e}"),
                ],
                meta=meta,
            )


class MCPMixin:
    _client: t.Any | None
    # The concrete ToolNode defines this
    mcp_tools: list[str]  # type: ignore[assignment]

    def _serialize_result(
        self,
        tool_call_id: str,
        res: t.Any,
    ) -> list[ContentBlock]:
        def safe_serialize(obj: t.Any) -> dict[str, t.Any]:
            try:
                json.dumps(obj)
                return obj if isinstance(obj, dict) else {"content": obj}
            except (TypeError, OverflowError):
                if hasattr(obj, "model_dump"):
                    dumped = obj.model_dump()  # type: ignore
                    if isinstance(dumped, dict) and dumped.get("type") == "resource":
                        resource = dumped.get("resource", {})
                        if isinstance(resource, dict) and "uri" in resource:
                            resource["uri"] = str(resource["uri"])
                            dumped["resource"] = resource
                    return dumped
                return {"content": str(obj), "type": "fallback"}

        for source in [
            getattr(res, "content", None),
            getattr(res, "structured_content", None),
            getattr(res, "data", None),
        ]:
            if source is None:
                continue
            try:
                if isinstance(source, list):
                    result = [safe_serialize(item) for item in source]
                else:
                    result = [safe_serialize(source)]

                return [
                    ToolResultBlock(
                        call_id=tool_call_id,
                        output=result,
                        is_error=False,
                        status="completed",
                    )
                ]
            except Exception as e:  # pragma: no cover - defensive
                logger.exception("Serialization failure: %s", e)
                continue

        return [
            ToolResultBlock(
                call_id=tool_call_id,
                output=[
                    {
                        "content": str(res),
                        "type": "fallback",
                    }
                ],
                is_error=False,
                status="completed",
            )
        ]

    async def _get_mcp_tool(self) -> list[dict]:
        tools: list[dict] = []
        if self._client:
            async with self._client:
                res = await self._client.ping()
                if not res:
                    return tools
                mcp_tools: list[t.Any] = await self._client.list_tools()
                for i in mcp_tools:
                    # attribute provided by concrete ToolNode
                    self.mcp_tools.append(i.name)  # type: ignore[attr-defined]
                    tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": i.name,
                                "description": i.description,
                                "parameters": i.inputSchema,
                            },
                        }
                    )
        return tools

    async def _mcp_execute(
        self,
        name: str,
        args: dict,
        tool_call_id: str,
        config: dict[str, t.Any],
        callback_mgr: CallbackManager,
    ) -> Message:
        context = CallbackContext(
            invocation_type=InvocationType.MCP,
            node_name="ToolNode",
            function_name=name,
            metadata={
                "tool_call_id": tool_call_id,
                "args": args,
                "config": config,
                "mcp_client": bool(self._client),
            },
        )

        meta = {
            "function_name": name,
            "function_argument": args,
            "tool_call_id": tool_call_id,
        }

        event = EventModel.default(
            base_config=config,
            data={
                "tool_call_id": tool_call_id,
                "args": args,
                "function_name": name,
                "is_mcp": True,
            },
            content_type=[ContentType.TOOL_CALL],
            event=Event.TOOL_EXECUTION,
        )
        event.event_type = EventType.PROGRESS
        event.node_name = "ToolNode"
        publish_event(event)

        input_data = {**args}

        try:
            input_data = await callback_mgr.execute_before_invoke(context, input_data)
            event.event_type = EventType.UPDATE
            event.metadata["status"] = "before_invoke_complete Invoke MCP"
            publish_event(event)

            if not self._client:
                error_result = Message.tool_message(
                    content=[
                        ErrorBlock(
                            message="No MCP client configured",
                        ),
                        ToolResultBlock(
                            call_id=tool_call_id,
                            output="No MCP client configured",
                            is_error=True,
                            status="failed",
                        ),
                    ],
                    meta=meta,
                )
                res = await callback_mgr.execute_after_invoke(context, input_data, error_result)
                event.event_type = EventType.ERROR
                event.metadata["error"] = "No MCP client configured"
                publish_event(event)
                return res

            async with self._client:
                if not await self._client.ping():
                    error_result = Message.tool_message(
                        content=[
                            ErrorBlock(message="MCP Server not available. Ping failed."),
                            ToolResultBlock(
                                call_id=tool_call_id,
                                output="MCP Server not available. Ping failed.",
                                is_error=True,
                                status="failed",
                            ),
                        ],
                        meta=meta,
                    )
                    event.event_type = EventType.ERROR
                    event.metadata["error"] = "MCP server not available, ping failed"
                    publish_event(event)
                    return await callback_mgr.execute_after_invoke(
                        context, input_data, error_result
                    )

                res: t.Any = await self._client.call_tool(name, input_data)

                final_res = self._serialize_result(tool_call_id, res)

                result = Message.tool_message(
                    content=final_res,
                    meta=meta,
                )

                res = await callback_mgr.execute_after_invoke(context, input_data, result)
                event.event_type = EventType.END
                event.data["message"] = result.model_dump()
                event.metadata["status"] = "MCP tool execution complete"
                event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
                publish_event(event)
                return res

        except Exception as e:  # pragma: no cover - error path
            recovery_result = await callback_mgr.execute_on_error(context, input_data, e)

            if isinstance(recovery_result, Message):
                event.event_type = EventType.END
                event.data["message"] = recovery_result.model_dump()
                event.metadata["status"] = "MCP tool execution complete, with recovery"
                event.content_type = [ContentType.TOOL_RESULT, ContentType.MESSAGE]
                publish_event(event)
                return recovery_result

            event.event_type = EventType.END
            event.data["error"] = str(e)
            event.metadata["status"] = "MCP tool execution complete, with recovery"
            event.content_type = [ContentType.TOOL_RESULT, ContentType.ERROR]
            publish_event(event)

            return Message.tool_message(
                content=[
                    ToolResultBlock(
                        call_id=tool_call_id,
                        output=f"MCP execution error: {e}",
                        is_error=True,
                        status="failed",
                    ),
                    ErrorBlock(message=f"MCP execution error: {e}"),
                ],
                meta=meta,
            )


class KwargsResolverMixin:
    def _should_skip_parameter(self, param: inspect.Parameter) -> bool:
        return param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        )

    def _handle_injectable_parameter(
        self,
        p_name: str,
        param: inspect.Parameter,
        injectable_params: dict,
        dependency_container,
    ) -> t.Any | None:
        if p_name in injectable_params:
            injectable_value = injectable_params[p_name]
            if injectable_value is not None:
                return injectable_value

        if dependency_container and dependency_container.has(p_name):
            return dependency_container.get(p_name)

        if param.default is inspect._empty:
            raise TypeError(f"Required injectable parameter '{p_name}' not found")

        return None

    def _get_parameter_value(
        self,
        p_name: str,
        param: inspect.Parameter,
        args: dict,
        injectable_params: dict,
        dependency_container,
    ) -> t.Any | None:
        if p_name in injectable_params:
            return self._handle_injectable_parameter(
                p_name, param, injectable_params, dependency_container
            )

        value_sources = [
            lambda: args.get(p_name),
            lambda: (
                dependency_container.get(p_name)
                if dependency_container and dependency_container.has(p_name)
                else None
            ),
        ]

        for source in value_sources:
            value = source()
            if value is not None:
                return value

        if param.default is not inspect._empty:
            return None

        raise TypeError(f"Missing required parameter '{p_name}' for function")

    def _prepare_kwargs(
        self,
        sig: inspect.Signature,
        args: dict,
        injectable_params: dict,
        dependency_container,
    ) -> dict:
        kwargs: dict = {}
        for p_name, p in sig.parameters.items():
            if self._should_skip_parameter(p):
                continue
            value = self._get_parameter_value(
                p_name, p, args, injectable_params, dependency_container
            )
            if value is not None:
                kwargs[p_name] = value
        return kwargs
