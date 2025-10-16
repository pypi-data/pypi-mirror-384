"""Streaming graph execution handler for TAF workflows.

This module provides the StreamHandler class, which manages the execution of graph workflows
with support for streaming output, interrupts, state persistence, and event publishing.
It enables incremental result processing, pause/resume capabilities, and robust error handling
for agent workflows that require real-time or chunked responses.
"""

from __future__ import annotations  # isort: skip_file

import logging
import time
from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any, TypeVar

from injectq import inject

from agentflow.exceptions import GraphRecursionError
from agentflow.graph.edge import Edge
from agentflow.graph.node import Node
from agentflow.publisher.events import ContentType, Event, EventModel, EventType
from agentflow.publisher.publish import publish_event
from agentflow.state import AgentState, ExecutionStatus, Message, ErrorBlock
from agentflow.state.message_block import RemoteToolCallBlock
from agentflow.state.stream_chunks import StreamChunk, StreamEvent
from agentflow.utils import END, START, ResponseGranularity, add_messages

from .handler_mixins import (
    BaseLoggingMixin,
    InterruptConfigMixin,
)
from .utils import (
    call_realtime_sync,
    get_next_node,
    load_or_create_state,
    process_node_result,
    reload_state,
    sync_data,
)


StateT = TypeVar("StateT", bound=AgentState)

logger = logging.getLogger(__name__)


class StreamHandler[StateT: AgentState](
    BaseLoggingMixin,
    InterruptConfigMixin,
):
    """Handles streaming execution for graph workflows in TAF.

    StreamHandler manages the execution of agent workflows as directed graphs,
    supporting streaming output, pause/resume via interrupts, state persistence,
    and event publishing for monitoring and debugging. It enables incremental
    result processing and robust error handling for complex agent workflows.

    Attributes:
        nodes: Dictionary mapping node names to Node instances.
        edges: List of Edge instances defining graph connections and routing.
        interrupt_before: List of node names where execution should pause before execution.
        interrupt_after: List of node names where execution should pause after execution.

    Example:
        ```python
        handler = StreamHandler(nodes, edges)
        async for chunk in handler.stream(input_data, config, state):
            print(chunk)
        ```
    """

    @inject
    def __init__(
        self,
        nodes: dict[str, Node],
        edges: list[Edge],
        interrupt_before: list[str] | None = None,
        interrupt_after: list[str] | None = None,
    ):
        self.nodes: dict[str, Node] = nodes
        self.edges: list[Edge] = edges
        self.interrupt_before = interrupt_before or []
        self.interrupt_after = interrupt_after or []
        self._set_interrupts(interrupt_before, interrupt_after)

    async def _check_interrupted(
        self,
        state: StateT,
        input_data: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        if state.is_interrupted():
            logger.info(
                "Resuming from interrupted state at node '%s'", state.execution_meta.current_node
            )
            # This is a resume case - clear interrupt and merge input data
            if input_data:
                config["resume_data"] = input_data
                logger.debug("Added resume data with %d keys", len(input_data))
            state.clear_interrupt()
        elif not input_data.get("messages") and not state.context:
            # This is a fresh execution - validate input data
            error_msg = "Input data must contain 'messages' for new execution."
            logger.error(error_msg)
            raise ValueError(error_msg)
        elif state.execution_meta.status == ExecutionStatus.COMPLETED:
            # Previous execution completed - reset to entry point for new execution
            logger.info(
                "Previous execution completed. Resetting to entry point for new execution "
                "with %d messages",
                len(input_data.get("messages", [])),
            )
            # Reset execution metadata for fresh start
            state.execution_meta.current_node = START
            state.execution_meta.step = 0
            state.execution_meta.status = ExecutionStatus.RUNNING
            state.execution_meta.interrupted_node = None
            state.execution_meta.interrupt_reason = None
            state.execution_meta.interrupt_data = None
        else:
            # Fresh execution, state is already at START
            logger.info(
                "Starting fresh execution with %d messages", len(input_data.get("messages", []))
            )

        return config

    async def _check_and_handle_interrupt(
        self,
        current_node: str,
        interrupt_type: str,
        state: StateT,
        config: dict[str, Any],
    ) -> bool:
        """Check for interrupts and save state if needed. Returns True if interrupted."""
        interrupt_nodes: list[str] = (
            self.interrupt_before if interrupt_type == "before" else self.interrupt_after
        ) or []

        if current_node in interrupt_nodes:
            status = (
                ExecutionStatus.INTERRUPTED_BEFORE
                if interrupt_type == "before"
                else ExecutionStatus.INTERRUPTED_AFTER
            )
            state.set_interrupt(
                current_node,
                f"interrupt_{interrupt_type}: {current_node}",
                status,
            )
            # Save state and interrupt
            await sync_data(
                state=state,
                config=config,
                messages=[],
                trim=True,
            )
            logger.debug("Node '%s' interrupted", current_node)
            return True

        logger.debug(
            "No interrupts found for node '%s', continuing execution",
            current_node,
        )
        return False

    async def _interrupt_graph(
        self,
        current_node: str,
        state: StateT,
        config: dict[str, Any],
    ) -> bool:
        """Check for interrupts and save state if needed. Returns True if interrupted."""
        status = ExecutionStatus.INTERRUPTED_AFTER
        state.set_interrupt(
            current_node,
            f"interrupt_after: {current_node}",
            status,
        )
        # Save state and interrupt
        await sync_data(
            state=state,
            config=config,
            messages=[],
            trim=False,
        )
        logger.debug("Node '%s' interrupted", current_node)
        return True

    async def _check_stop_requested(
        self,
        state: StateT,
        current_node: str,
        event: EventModel,
        messages: list[Message],
        config: dict[str, Any],
    ) -> bool:
        """Check if a stop has been requested externally."""
        state = await reload_state(config, state)  # type: ignore

        # Check if a stop was requested externally (e.g., frontend)
        if state.is_stopped_requested():
            logger.info(
                "Stop requested for thread '%s' at node '%s'",
                config.get("thread_id"),
                current_node,
            )
            state.set_interrupt(
                current_node,
                "stop_requested",
                ExecutionStatus.INTERRUPTED_AFTER,
                data={"source": "stop", "info": "requested via is_stopped_requested"},
            )
            await sync_data(state=state, config=config, messages=messages, trim=True)
            event.event_type = EventType.INTERRUPTED
            event.metadata["interrupted"] = "Stop"
            event.metadata["status"] = "Graph execution stopped by request"
            event.data["state"] = state.model_dump()
            publish_event(event)
            return True
        return False

    async def _execute_graph(  # noqa: PLR0912, PLR0915
        self,
        state: StateT,
        input_data: dict[str, Any],
        config: dict[str, Any],
    ) -> AsyncIterable[StreamChunk]:
        """
        Execute the entire graph with support for interrupts and resuming.

        Why so many chunks are yielded?
        We allow user to set response type, if they want low granularity
        Only few chunks like Message will be sent to user
        """
        logger.info(
            "Starting graph execution from node '%s' at step %d",
            state.execution_meta.current_node,
            state.execution_meta.step,
        )
        messages: list[Message] = []
        messages_ids = set()
        max_steps = config.get("recursion_limit", 25)
        logger.debug("Max steps limit set to %d", max_steps)

        last_human_messages = input_data.get("messages", []) or []
        # Stream initial input messages (e.g., human messages) so callers see full conversation
        # Only emit when present and avoid duplicates by tracking message_ids and existing context
        for m in last_human_messages:
            if m.message_id not in messages_ids:
                messages.append(m)
                messages_ids.add(m.message_id)
                yield StreamChunk(
                    event=StreamEvent.MESSAGE,
                    message=m,
                    metadata={
                        "status": "invoking_graph",
                        "reason": "initial human message",
                    },
                    thread_id=config.get("thread_id"),
                    run_id=config.get("run_id"),
                )

        # Get current execution info from state
        current_node = state.execution_meta.current_node
        step = state.execution_meta.step

        # Create event for graph execution
        event = EventModel.default(
            config,
            data={"state": state.model_dump(exclude={"execution_meta"})},
            content_type=[ContentType.STATE],
            extra={"step": step, "current_node": current_node},
            event=Event.GRAPH_EXECUTION,
            node_name=current_node,
        )

        yield StreamChunk(
            event=StreamEvent.UPDATES,
            data={
                "status": "invoking_graph",
                "node": current_node,
                "step": step,
                "max_steps": max_steps,
            },
            thread_id=config.get("thread_id"),
            run_id=config.get("run_id"),
        )

        try:
            while current_node != END and step < max_steps:
                logger.debug("Executing step %d at node '%s'", step, current_node)

                # TODO: check if ai called for a tool in that case we should remove last message
                res = await self._check_stop_requested(
                    state,
                    current_node,
                    event,
                    messages,
                    config,
                )
                if res:
                    event.event_type = EventType.INTERRUPTED
                    event.metadata["status"] = "Graph execution stopped by request"
                    event.data["state"] = state.model_dump()
                    publish_event(event)
                    # stream updated state and updates
                    yield StreamChunk(
                        event=StreamEvent.UPDATES,
                        data={
                            "status": "invoking_node",
                            "node": current_node,
                            "step": step,
                            "max_steps": max_steps,
                            "reason": "Graph execution stopped by request",
                        },
                        thread_id=config.get("thread_id"),
                        run_id=config.get("run_id"),
                    )
                    return

                # Update execution metadata
                state.set_current_node(current_node)
                state.execution_meta.step = step
                await call_realtime_sync(state, config)

                # Update event with current step info
                event.data["step"] = step
                event.data["current_node"] = current_node
                event.event_type = EventType.PROGRESS
                event.metadata["status"] = f"Executing step {step} at node '{current_node}'"
                publish_event(event)

                # Check for interrupt_before
                if await self._check_and_handle_interrupt(
                    current_node,
                    "before",
                    state,
                    config,
                ):
                    logger.info("Graph execution interrupted before node '%s'", current_node)
                    event.event_type = EventType.INTERRUPTED
                    event.metadata["status"] = "Graph execution interrupted before node execution"
                    event.metadata["interrupted"] = "Before"
                    event.data["interrupted"] = "Before"
                    publish_event(event)
                    yield StreamChunk(
                        event=StreamEvent.UPDATES,
                        data={
                            "status": "invoking_node",
                            "node": current_node,
                            "step": step,
                            "max_steps": max_steps,
                            "reason": "Graph execution interrupted before node execution",
                        },
                        thread_id=config.get("thread_id"),
                        run_id=config.get("run_id"),
                    )
                    return

                # Execute current node
                logger.debug("Executing node '%s'", current_node)
                node = self.nodes[current_node]

                ####################################################
                ############ Execute Node ##########################
                ####################################################
                result = node.stream(config, state)  # type: ignore
                logger.debug("Node '%s' execution completed", current_node)
                ####################################################
                ############ Execute Node ##########################
                ####################################################

                res = await self._check_stop_requested(
                    state,
                    current_node,
                    event,
                    messages,
                    config,
                )
                if res:
                    event.event_type = EventType.INTERRUPTED
                    event.metadata["status"] = "Graph execution stopped by request"
                    event.data["state"] = state.model_dump()
                    publish_event(event)
                    yield StreamChunk(
                        event=StreamEvent.UPDATES,
                        data={
                            "status": "invoking_node",
                            "node": current_node,
                            "step": step,
                            "max_steps": max_steps,
                            "reason": "Graph execution stopped by request",
                        },
                        thread_id=config.get("thread_id"),
                        run_id=config.get("run_id"),
                    )
                    return

                # Process result and get next node
                yield StreamChunk(
                    event=StreamEvent.UPDATES,
                    data={
                        "status": "node_invoked",
                        "node": current_node,
                        "step": step,
                        "max_steps": max_steps,
                    },
                    thread_id=config.get("thread_id"),
                    run_id=config.get("run_id"),
                )

                # From Here message no need to stream its already streamed
                # from execute node function, only stream updates and state
                next_node = None
                async for rs in result:
                    # Allow stop to break inner result loop as well
                    if isinstance(rs, StreamChunk):
                        yield rs

                    # if message and remote tool call then yield immediately
                    elif isinstance(rs, Message) and RemoteToolCallBlock in rs.content:
                        # now interrupt the graph
                        await self._interrupt_graph(
                            current_node,
                            state,
                            config,
                        )
                        yield StreamChunk(
                            event=StreamEvent.UPDATES,
                            data={
                                "status": "node_invoked",
                                "node": current_node,
                                "step": step,
                                "max_steps": max_steps,
                                "reason": "Remote tool call - graph interrupted",
                            },
                            thread_id=config.get("thread_id"),
                            run_id=config.get("run_id"),
                        )
                        return

                    elif isinstance(rs, Message) and not rs.delta:
                        if rs.message_id not in messages_ids:
                            messages.append(rs)
                            messages_ids.add(rs.message_id)

                    elif isinstance(rs, dict) and "is_non_streaming" in rs:
                        if rs["is_non_streaming"]:
                            new_state = rs.get("state", None)
                            if new_state:
                                state = new_state
                                yield StreamChunk(
                                    event=StreamEvent.STATE,
                                    state=state,
                                    metadata={
                                        "node": current_node,
                                        "step": step,
                                    },
                                    thread_id=config.get("thread_id"),
                                    run_id=config.get("run_id"),
                                )

                            new_messages = rs.get("messages", [])
                            for m in new_messages:
                                if m.message_id not in messages_ids and not m.delta:
                                    messages.append(m)
                                    messages_ids.add(m.message_id)
                            next_node = rs.get("next_node", next_node)
                        else:
                            # Streaming path completed: ensure any collected messages are persisted
                            new_messages = rs.get("messages", [])
                            for m in new_messages:
                                if m.message_id not in messages_ids and not m.delta:
                                    messages.append(m)
                                    messages_ids.add(m.message_id)
                            next_node = rs.get("next_node", next_node)
                    else:
                        # Process as node result (non-streaming path)
                        try:
                            state, new_messages, next_node = await process_node_result(
                                rs,
                                state,
                                [],
                            )
                            for m in new_messages:
                                if m.message_id not in messages_ids and not m.delta:
                                    messages.append(m)
                                    messages_ids.add(m.message_id)
                        except Exception as e:
                            logger.error("Failed to process node result: %s", e)

                logger.debug(
                    "Node result processed, next_node=%s, total_messages=%d",
                    next_node,
                    len(messages),
                )

                # Add collected messages to state context
                if messages:
                    state.context = add_messages(state.context, messages)
                    logger.debug("Added %d messages to state context", len(messages))
                    yield StreamChunk(
                        event=StreamEvent.STATE,
                        state=state,
                        metadata={
                            "node": current_node,
                            "step": step,
                        },
                        thread_id=config.get("thread_id"),
                        run_id=config.get("run_id"),
                    )

                # Call realtime sync after node execution
                await call_realtime_sync(state, config)
                event.event_type = EventType.UPDATE
                event.data["state"] = state.model_dump()
                event.data["messages"] = [m.model_dump() for m in messages] if messages else []
                if messages:
                    lm = messages[-1]
                    event.content = lm.text() if isinstance(lm.content, list) else lm.content
                    if isinstance(lm.content, list):
                        event.content_blocks = lm.content
                event.content_type = [ContentType.STATE, ContentType.MESSAGE]
                publish_event(event)

                # Check for interrupt_after
                if await self._check_and_handle_interrupt(
                    current_node,
                    "after",
                    state,
                    config,
                ):
                    logger.info("Graph execution interrupted after node '%s'", current_node)
                    # For interrupt_after, advance to next node before pausing
                    if next_node is None:
                        next_node = get_next_node(current_node, state, self.edges)
                    state.set_current_node(next_node)

                    event.event_type = EventType.INTERRUPTED
                    event.data["interrupted"] = "After"
                    event.metadata["interrupted"] = "After"
                    event.data["state"] = state.model_dump()
                    publish_event(event)

                    yield StreamChunk(
                        event=StreamEvent.UPDATES,
                        data={
                            "status": "node_invoked",
                            "node": current_node,
                            "step": step,
                            "max_steps": max_steps,
                            "reason": "Graph execution interrupted before node execution",
                        },
                        thread_id=config.get("thread_id"),
                        run_id=config.get("run_id"),
                    )
                    return

                # Get next node
                if next_node is None:
                    current_node = get_next_node(current_node, state, self.edges)
                    logger.debug("Next node determined by graph logic: '%s'", current_node)
                else:
                    current_node = next_node
                    logger.debug("Next node determined by command: '%s'", current_node)

                # Advance step after successful node execution
                step += 1
                state.advance_step()
                await call_realtime_sync(state, config)

                event.event_type = EventType.UPDATE
                event.metadata["State_Updated"] = "State Updated"
                event.data["state"] = state.model_dump()
                publish_event(event)

                yield StreamChunk(
                    event=StreamEvent.UPDATES,
                    state=state,
                    data={
                        "status": "node_invoked",
                        "node": current_node,
                        "step": step,
                        "max_steps": max_steps,
                    },
                    thread_id=config.get("thread_id"),
                    run_id=config.get("run_id"),
                )

                if step >= max_steps:
                    error_msg = "Graph execution exceeded maximum steps"
                    logger.error(error_msg)
                    state.error(error_msg)
                    await call_realtime_sync(state, config)

                    event.event_type = EventType.ERROR
                    event.data["state"] = state.model_dump()
                    event.metadata["error"] = error_msg
                    event.metadata["step"] = step
                    event.metadata["current_node"] = current_node
                    publish_event(event)

                    yield Message(
                        role="assistant",
                        content=[ErrorBlock(text=error_msg)],  # type: ignore
                    )

                    yield StreamChunk(
                        event=StreamEvent.ERROR,
                        state=state,
                        data={
                            "status": "graph_invoked",
                            "node": current_node,
                            "step": step,
                            "max_steps": max_steps,
                            "reason": error_msg,
                        },
                        thread_id=config.get("thread_id"),
                        run_id=config.get("run_id"),
                    )

                    raise GraphRecursionError(
                        message=f"Graph execution exceeded recursion limit: {max_steps}",
                        error_code="RECURSION_001",
                        context={
                            "max_steps": max_steps,
                            "current_step": step,
                            "current_node": current_node,
                        },
                    )

            # Execution completed successfully
            logger.info(
                "Graph execution completed successfully at node '%s' after %d steps",
                current_node,
                step,
            )
            state.complete()
            is_context_trimmed = await sync_data(
                state=state,
                config=config,
                messages=messages,
                trim=True,
            )

            # Create completion event
            event.event_type = EventType.END
            event.data["state"] = state.model_dump()
            event.data["messages"] = [m.model_dump() for m in messages] if messages else []
            if messages:
                fm = messages[-1]
                event.content = fm.text() if isinstance(fm.content, list) else fm.content
                if isinstance(fm.content, list):
                    event.content_blocks = fm.content
            event.content_type = [ContentType.STATE, ContentType.MESSAGE]
            event.metadata["status"] = "Graph execution completed"
            event.metadata["step"] = step
            event.metadata["current_node"] = current_node
            event.metadata["is_context_trimmed"] = is_context_trimmed
            publish_event(event)

            yield StreamChunk(
                event=StreamEvent.UPDATES,
                state=state,
                data={
                    "status": "graph_invoked",
                    "node": current_node,
                    "step": step,
                    "max_steps": max_steps,
                    "is_context_trimmed": is_context_trimmed,
                    "reason": "Graph execution completed successfully",
                },
                thread_id=config.get("thread_id"),
                run_id=config.get("run_id"),
            )

        except Exception as e:
            # Handle execution errors
            logger.exception("Graph execution failed: %s", e)
            state.error(str(e))

            # Publish error event
            event.event_type = EventType.ERROR
            event.metadata["error"] = str(e)
            event.data["state"] = state.model_dump()
            publish_event(event)

            await sync_data(
                state=state,
                config=config,
                messages=messages,
                trim=True,
            )

            yield StreamChunk(
                event=StreamEvent.ERROR,
                state=state,
                data={
                    "status": "invoked_graph",
                    "node": current_node,
                    "step": step,
                    "max_steps": max_steps,
                    "reason": str(e),
                },
                thread_id=config.get("thread_id"),
                run_id=config.get("run_id"),
            )

            raise e

    async def stream(
        self,
        input_data: dict[str, Any],
        config: dict[str, Any],
        default_state: StateT,
        response_granularity: ResponseGranularity = ResponseGranularity.LOW,
    ) -> AsyncGenerator[StreamChunk]:
        """Execute the graph asynchronously with streaming output.

        Runs the graph workflow from start to finish, yielding incremental results
        as they become available. Automatically detects whether to start a fresh
        execution or resume from an interrupted state, supporting pause/resume
        and checkpointing.

        Args:
            input_data: Input dictionary for graph execution. For new executions,
                should contain 'messages' key with initial messages. For resumed
                executions, can contain additional data to merge.
            config: Configuration dictionary containing execution settings and context.
            default_state: Initial or template AgentState for workflow execution.
            response_granularity: Level of detail in the response (LOW, PARTIAL, FULL).

        Yields:
            Message objects representing incremental results from graph execution.
            The exact type and frequency of yields depends on node implementations
            and workflow configuration.

        Raises:
            GraphRecursionError: If execution exceeds recursion limit.
            ValueError: If input_data is invalid for new execution.
            Various exceptions: Depending on node execution failures.

        Example:
            ```python
            async for chunk in handler.stream(input_data, config, state):
                print(chunk)
            ```
        """
        logger.info(
            "Starting asynchronous graph execution with %d input keys, granularity=%s",
            len(input_data) if input_data else 0,
            response_granularity,
        )
        config = config or {}
        input_data = input_data or {}

        start_time = time.time()

        # Load or initialize state
        logger.debug("Loading or creating state from input data")
        new_state = await load_or_create_state(
            input_data,
            config,
            default_state,
        )
        state: StateT = new_state  # type: ignore[assignment]
        logger.debug(
            "State loaded: interrupted=%s, current_node=%s, step=%d",
            state.is_interrupted(),
            state.execution_meta.current_node,
            state.execution_meta.step,
        )

        cfg = config.copy()
        if "user" in cfg:
            # This will be available when you are calling
            # vi agentflow api
            del cfg["user"]

        event = EventModel.default(
            config,
            data={"state": state},
            content_type=[ContentType.STATE],
            extra={
                "is_interrupted": state.is_interrupted(),
                "current_node": state.execution_meta.current_node,
                "step": state.execution_meta.step,
                "config": cfg,
                "response_granularity": response_granularity.value,
            },
        )

        # Publish graph initialization event
        publish_event(event)

        # Check if this is a resume case
        config = await self._check_interrupted(state, input_data, config)

        # Now start Execution
        # Execute graph
        logger.debug("Beginning graph execution")
        result = self._execute_graph(state, input_data, config)

        # Stream results based on response granularity
        async for chunk in result:
            match response_granularity:
                case ResponseGranularity.FULL:
                    yield chunk
                case ResponseGranularity.PARTIAL:
                    if chunk.event != StreamEvent.UPDATES:
                        yield chunk
                case ResponseGranularity.LOW:
                    if chunk.event in [StreamEvent.MESSAGE, StreamEvent.ERROR]:
                        yield chunk

        # Publish graph completion event
        time_taken = time.time() - start_time
        logger.info("Graph execution finished in %.2f seconds", time_taken)

        event.event_type = EventType.END
        event.metadata.update(
            {
                "time_taken": time_taken,
                "state": state.model_dump(),
                "step": state.execution_meta.step,
                "current_node": state.execution_meta.current_node,
                "is_interrupted": state.is_interrupted(),
                "total_messages": len(state.context) if state.context else 0,
            }
        )
        publish_event(event)
        yield StreamChunk(
            event=StreamEvent.UPDATES,
            state=state,
            data={
                "status": "graph_invoked",
                "reason": "Graph execution finished",
                "time_taken": time_taken,
                "is_interrupted": state.is_interrupted(),
                "total_messages": len(state.context) if state.context else 0,
            },
            thread_id=config.get("thread_id"),
            run_id=config.get("run_id"),
        )
