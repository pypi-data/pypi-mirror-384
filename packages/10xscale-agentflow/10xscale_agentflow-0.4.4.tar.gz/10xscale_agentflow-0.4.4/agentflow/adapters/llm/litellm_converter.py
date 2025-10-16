from __future__ import annotations

import inspect
import json
import logging
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any, cast

from agentflow.state.message import (
    Message,
    TokenUsages,
    generate_id,
)
from agentflow.state.message_block import ReasoningBlock, TextBlock, ToolCallBlock

from .base_converter import BaseConverter


logger = logging.getLogger(__name__)


try:
    from litellm import CustomStreamWrapper
    from litellm.types.utils import ModelResponse, ModelResponseStream

    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False
    CustomStreamWrapper = None
    ModelResponse = None
    ModelResponseStream = None


class LiteLLMConverter(BaseConverter):
    """
    Converter for LiteLLM responses to agentflow Message format.

    Handles both standard and streaming responses, extracting content, reasoning,
    tool calls, and token usage details.
    """

    async def convert_response(self, response: ModelResponse) -> Message:  # pyright: ignore[reportInvalidTypeForm]
        """
        Convert a LiteLLM ModelResponse to a Message.

        Args:
            response (ModelResponse): The LiteLLM model response object.

        Returns:
            Message: The converted message object.

        Raises:
            ImportError: If LiteLLM is not installed.
        """
        if not HAS_LITELLM:
            raise ImportError("litellm is not installed. Please install it to use this converter.")

        data = response.model_dump()

        usages_data = data.get("usage", {})

        usages = TokenUsages(
            completion_tokens=usages_data.get("completion_tokens", 0),
            prompt_tokens=usages_data.get("prompt_tokens", 0),
            total_tokens=usages_data.get("total_tokens", 0),
            cache_creation_input_tokens=usages_data.get("cache_creation_input_tokens", 0),
            cache_read_input_tokens=usages_data.get("cache_read_input_tokens", 0),
            reasoning_tokens=usages_data.get("prompt_tokens_details", {}).get(
                "reasoning_tokens", 0
            ),
        )

        created_date = data.get("created", datetime.now().timestamp())

        # Extract tool calls from response
        tools_calls = data.get("choices", [{}])[0].get("message", {}).get("tool_calls", []) or []

        logger.debug("Creating message from model response with id: %s", response.id)
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
        reasoning_content = (
            data.get("choices", [{}])[0].get("message", {}).get("reasoning_content", "") or ""
        )

        blocks = []
        if content:
            blocks.append(TextBlock(text=content))
        if reasoning_content:
            blocks.append(ReasoningBlock(summary=reasoning_content))
        final_tool_calls = []
        for tool_call in tools_calls:
            tool_id = tool_call.get("id", None)
            args = tool_call.get("function", {}).get("arguments", None)
            name = tool_call.get("function", {}).get("name", None)

            if not tool_id or not args or not name:
                continue

            blocks.append(
                ToolCallBlock(
                    name=name,
                    args=json.loads(args),
                    id=tool_id,
                )
            )

            if hasattr(tool_call, "model_dump"):
                final_tool_calls.append(tool_call.model_dump())
            else:
                final_tool_calls.append(tool_call)

        return Message(
            message_id=generate_id(response.id),
            role="assistant",
            content=blocks,
            reasoning=reasoning_content,
            timestamp=created_date,
            metadata={
                "provider": "litellm",
                "model": data.get("model", ""),
                "finish_reason": data.get("choices", [{}])[0].get("finish_reason", "UNKNOWN"),
                "object": data.get("object", ""),
                "prompt_tokens_details": usages_data.get("prompt_tokens_details", {}),
                "completion_tokens_details": usages_data.get("completion_tokens_details", {}),
            },
            usages=usages,
            raw=data,
            tools_calls=final_tool_calls if final_tool_calls else None,
        )

    def _process_chunk(
        self,
        chunk: ModelResponseStream | None,  # type: ignore
        seq: int,
        accumulated_content: str,
        accumulated_reasoning_content: str,
        tool_calls: list,
        tool_ids: set,
    ) -> tuple[str, str, list, int, Message | None]:
        """
        Process a single chunk from a LiteLLM streaming response.

        Args:
            chunk (ModelResponseStream | None): The current chunk from the stream.
            seq (int): Sequence number of the chunk.
            accumulated_content (str): Accumulated text content so far.
            accumulated_reasoning_content (str): Accumulated reasoning content so far.
            tool_calls (list): List of tool calls detected so far.
            tool_ids (set): Set of tool call IDs to avoid duplicates.

        Returns:
            tuple: Updated accumulated content, reasoning, tool calls, sequence,
                and Message (if any).
        """
        if not chunk:
            return accumulated_content, accumulated_reasoning_content, tool_calls, seq, None

        msg: ModelResponseStream = chunk  # type: ignore
        if msg is None:
            return accumulated_content, accumulated_reasoning_content, tool_calls, seq, None
        if msg.choices is None or len(msg.choices) == 0:
            return accumulated_content, accumulated_reasoning_content, tool_calls, seq, None
        delta = msg.choices[0].delta
        if delta is None:
            return accumulated_content, accumulated_reasoning_content, tool_calls, seq, None

        # update text delta
        text_part = delta.content or ""
        content_blocks = []
        if text_part:
            content_blocks.append(TextBlock(text=text_part))
        reasoning_part = getattr(delta, "reasoning_content", "") or ""
        if reasoning_part:
            content_blocks.append(ReasoningBlock(summary=reasoning_part))
        accumulated_content += text_part
        accumulated_reasoning_content += reasoning_part
        # handle tool calls if present
        if getattr(delta, "tool_calls", None):
            for tc in delta.tool_calls:  # type: ignore[attr-defined]
                if not tc:
                    continue
                if tc.id in tool_ids:
                    continue
                tool_ids.add(tc.id)
                tool_calls.append(tc.model_dump())
                content_blocks.append(
                    ToolCallBlock(
                        name=tc.function.name,  # type: ignore
                        args=json.loads(tc.function.arguments),  # type: ignore
                        id=tc.id,  # type: ignore
                    )
                )

        output_message = Message(
            message_id=generate_id(msg.id),
            role="assistant",
            content=content_blocks,
            reasoning=accumulated_reasoning_content,
            tools_calls=tool_calls,
            delta=True,
        )

        return accumulated_content, accumulated_reasoning_content, tool_calls, seq, output_message

    async def _handle_stream(
        self,
        config: dict,
        node_name: str,
        stream: CustomStreamWrapper,  # type: ignore
        meta: dict | None = None,
    ) -> AsyncGenerator[Message]:
        """
        Handle a LiteLLM streaming response and yield Message objects for each chunk.

        Args:
            config (dict): Node configuration parameters.
            node_name (str): Name of the node processing the response.
            stream (CustomStreamWrapper): The LiteLLM streaming response object.
            meta (dict | None): Optional metadata for conversion.

        Yields:
            Message: Converted message chunk from the stream.
        """
        accumulated_content = ""
        tool_calls = []
        tool_ids = set()
        accumulated_reasoning_content = ""
        seq = 0

        is_awaitable = inspect.isawaitable(stream)

        # Await stream if necessary
        if is_awaitable:
            stream = await stream

        # Try async iteration (acompletion)
        try:
            async for chunk in stream:  # type: ignore
                accumulated_content, accumulated_reasoning_content, tool_calls, seq, message = (
                    self._process_chunk(
                        chunk,
                        seq,
                        accumulated_content,
                        accumulated_reasoning_content,
                        tool_calls,
                        tool_ids,
                    )
                )

                if message:
                    yield message
        except Exception:  # noqa: S110 # nosec B110
            pass

        # Try sync iteration (completion)
        try:
            for chunk in stream:
                accumulated_content, accumulated_reasoning_content, tool_calls, seq, message = (
                    self._process_chunk(
                        chunk,
                        seq,
                        accumulated_content,
                        accumulated_reasoning_content,
                        tool_calls,
                        tool_ids,
                    )
                )

                if message:
                    yield message
        except Exception:  # noqa: S110 # nosec B110
            pass

        # After streaming, yield final message
        metadata = meta or {}
        metadata["provider"] = "litellm"
        metadata["node_name"] = node_name
        metadata["thread_id"] = config.get("thread_id")

        blocks = []
        if accumulated_content:
            blocks.append(TextBlock(text=accumulated_content))
        if accumulated_reasoning_content:
            blocks.append(ReasoningBlock(summary=accumulated_reasoning_content))
        if tool_calls:
            for tc in tool_calls:
                blocks.append(
                    ToolCallBlock(
                        name=tc.get("function", {}).get("name", ""),
                        args=json.loads(tc.get("function", {}).get("arguments", "{}")),
                        id=tc.get("id", ""),
                    )
                )

        logger.debug(
            "Loop done Content: %s  Reasoning: %s Tool Calls: %s",
            accumulated_content,
            accumulated_reasoning_content,
            len(tool_calls),
        )
        message = Message(
            role="assistant",
            message_id=generate_id(None),
            content=blocks,
            delta=False,
            reasoning=accumulated_reasoning_content,
            tools_calls=tool_calls,
            metadata=metadata,
        )
        yield message

    async def convert_streaming_response(  # type: ignore
        self,
        config: dict,
        node_name: str,
        response: Any,
        meta: dict | None = None,
    ) -> AsyncGenerator[Message]:
        """
        Convert a LiteLLM streaming or standard response to Message(s).

        Args:
            config (dict): Node configuration parameters.
            node_name (str): Name of the node processing the response.
            response (Any): The LiteLLM response object (stream or standard).
            meta (dict | None): Optional metadata for conversion.

        Yields:
            Message: Converted message(s) from the response.

        Raises:
            ImportError: If LiteLLM is not installed.
            Exception: If response type is unsupported.
        """
        if not HAS_LITELLM:
            raise ImportError("litellm is not installed. Please install it to use this converter.")

        if isinstance(response, CustomStreamWrapper):  # type: ignore
            stream = cast(CustomStreamWrapper, response)  # type: ignore
            async for event in self._handle_stream(
                config or {},
                node_name or "",
                stream,
                meta,
            ):
                yield event
        elif isinstance(response, ModelResponse):  # type: ignore
            message = await self.convert_response(cast(ModelResponse, response))  # type: ignore
            yield message
        else:
            raise Exception("Unsupported response type for LiteLLMConverter")
