from __future__ import annotations  # isort: skip_file

import logging
from typing import Any, TypeVar

from injectq import inject

from agentflow.exceptions import GraphRecursionError
from agentflow.graph.edge import Edge
from agentflow.graph.node import Node
from agentflow.graph.utils.utils import (
    call_realtime_sync,
    get_next_node,
    load_or_create_state,
    parse_response,
    reload_state,
    sync_data,
)
from agentflow.publisher.events import ContentType, Event, EventModel, EventType
from agentflow.publisher.publish import publish_event
from agentflow.state import AgentState, ExecutionStatus, Message
from agentflow.state.message_block import RemoteToolCallBlock
from agentflow.utils import END, START, ResponseGranularity
from agentflow.state.reducers import add_messages

from .handler_mixins import (
    BaseLoggingMixin,
    InterruptConfigMixin,
)


StateT = TypeVar("StateT", bound=AgentState)

logger = logging.getLogger(__name__)


class InvokeHandler[StateT: AgentState](
    BaseLoggingMixin,
    InterruptConfigMixin,
):
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
        # Keep existing attributes for backward-compatibility
        self.interrupt_before = interrupt_before or []
        self.interrupt_after = interrupt_after or []
        # And set via mixin for a single source of truth
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
        config: dict[str, Any],
    ) -> tuple[StateT, list[Message]]:
        """Execute the entire graph with support for interrupts and resuming."""
        logger.info(
            "Starting graph execution from node '%s' at step %d",
            state.execution_meta.current_node,
            state.execution_meta.step,
        )
        logger.debug("DEBUG: Current node value: %r", state.execution_meta.current_node)
        logger.debug("DEBUG: END constant value: %r", END)
        logger.debug("DEBUG: Are they equal? %s", state.execution_meta.current_node == END)
        messages: list[Message] = []
        max_steps = config.get("recursion_limit", 25)
        logger.debug("Max steps limit set to %d", max_steps)

        # get the last message from state as that is human message
        last_human_message = state.context[-1] if state.context else None
        if last_human_message and last_human_message.role != "user":
            msg = [msg for msg in reversed(state.context) if msg.role == "user"]
            last_human_message = msg[0] if msg else None

        if last_human_message:
            logger.debug("Last human message: %s", last_human_message.content)
            messages.append(last_human_message)

        # Get current execution info from state
        current_node = state.execution_meta.current_node
        step = state.execution_meta.step

        # Create event for graph execution
        event = EventModel.default(
            config,
            data={"state": state.model_dump()},
            event=Event.GRAPH_EXECUTION,
            content_type=[ContentType.STATE],
            node_name=current_node,
            extra={
                "current_node": current_node,
                "step": step,
                "max_steps": max_steps,
            },
        )

        try:
            while current_node != END and step < max_steps:
                logger.debug("Executing step %d at node '%s'", step, current_node)
                # Reload state in each iteration to get latest (in case of external updates)
                res = await self._check_stop_requested(
                    state,
                    current_node,
                    event,
                    messages,
                    config,
                )
                if res:
                    return state, messages

                # Update execution metadata
                state.set_current_node(current_node)
                state.execution_meta.step = step
                await call_realtime_sync(state, config)
                event.data["state"] = state.model_dump()
                event.metadata["step"] = step
                event.metadata["current_node"] = current_node
                event.event_type = EventType.PROGRESS
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
                    event.metadata["interrupted"] = "Before"
                    event.metadata["status"] = "Graph execution interrupted before node execution"
                    event.data["interrupted"] = "Before"
                    publish_event(event)
                    return state, messages

                # Execute current node
                logger.debug("Executing node '%s'", current_node)
                node = self.nodes[current_node]

                # Publish node invocation event

                ###############################################
                ##### Node Execution Started ##################
                ###############################################

                result = await node.execute(config, state)  # type: ignore

                ###############################################
                ##### Node Execution Finished #################
                ###############################################

                logger.debug("Node '%s' execution completed", current_node)

                next_node = None

                # check frontend nodes
                if isinstance(result, Message) and RemoteToolCallBlock in result.content:
                    # now interrupt the graph
                    await self._interrupt_graph(
                        current_node,
                        state,
                        config,
                    )
                    messages.append(result)
                    return state, messages

                # Process result and get next node
                if isinstance(result, list):
                    # If result is a list of Message, append to messages
                    messages.extend(result)
                    logger.debug(
                        "Node '%s' returned %d messages, total messages now %d",
                        current_node,
                        len(result),
                        len(messages),
                    )
                    # Add messages to state context so they're visible to subsequent nodes
                    state.context = add_messages(state.context, result)

                # No state change beyond adding messages, just advance to next node
                if isinstance(result, dict):
                    state = result.get("state", state)
                    next_node = result.get("next_node")
                    new_messages = result.get("messages", [])
                    if new_messages:
                        messages.extend(new_messages)
                        logger.debug(
                            "Node '%s' returned %d messages, total messages now %d",
                            current_node,
                            len(new_messages),
                            len(messages),
                        )

                logger.debug(
                    "Node result processed, next_node=%s, total_messages=%d",
                    next_node,
                    len(messages),
                )

                # Check stop again after node execution
                res = await self._check_stop_requested(
                    state,
                    current_node,
                    event,
                    messages,
                    config,
                )
                if res:
                    return state, messages

                # Call realtime sync after node execution (if state/messages changed)
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
                    return state, messages

                # Get next node (only if no explicit navigation from Command)
                if next_node is None:
                    current_node = get_next_node(current_node, state, self.edges)
                    logger.debug("Next node determined by graph logic: '%s'", current_node)
                else:
                    current_node = next_node
                    logger.debug("Next node determined by command: '%s'", current_node)

                # Check if we've reached the end after determining next node
                logger.debug("Checking if current_node '%s' == END '%s'", current_node, END)
                if current_node == END:
                    logger.info("Graph execution reached END node, completing")
                    break

                # Advance step after successful node execution
                step += 1
                state.advance_step()
                await call_realtime_sync(state, config)
                event.event_type = EventType.UPDATE

                event.metadata["State_Updated"] = "State Updated"
                event.data["state"] = state.model_dump()
                publish_event(event)

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
            res = await sync_data(
                state=state,
                config=config,
                messages=messages,
                trim=True,
            )
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
            event.metadata["is_context_trimmed"] = res

            publish_event(event)

            return state, messages

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
            raise

    async def invoke(
        self,
        input_data: dict[str, Any],
        config: dict[str, Any],
        default_state: StateT,
        response_granularity: ResponseGranularity = ResponseGranularity.LOW,
    ):
        """Execute the graph asynchronously with event publishing."""
        logger.info(
            "Starting asynchronous graph execution with %d input keys, granularity=%s",
            len(input_data) if input_data else 0,
            response_granularity,
        )
        input_data = input_data or {}

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

        # Event publishing logic
        event = EventModel.default(
            config,
            data={"state": state.model_dump()},
            event=Event.GRAPH_EXECUTION,
            content_type=[ContentType.STATE],
            node_name=state.execution_meta.current_node,
            extra={
                "current_node": state.execution_meta.current_node,
                "step": state.execution_meta.step,
            },
        )
        event.event_type = EventType.START
        publish_event(event)

        # Check if this is a resume case
        config = await self._check_interrupted(state, input_data, config)

        event.event_type = EventType.UPDATE
        event.metadata["status"] = "Graph invoked"
        publish_event(event)

        try:
            logger.debug("Beginning graph execution")
            event.event_type = EventType.PROGRESS
            event.metadata["status"] = "Graph execution started"
            publish_event(event)

            final_state, messages = await self._execute_graph(state, config)
            logger.info("Graph execution completed with %d final messages", len(messages))

            event.event_type = EventType.END
            event.metadata["status"] = "Graph execution completed"
            event.data["state"] = final_state.model_dump()
            event.data["messages"] = [m.model_dump() for m in messages] if messages else []
            publish_event(event)

            return await parse_response(
                final_state,
                messages,
                response_granularity,
            )
        except Exception as e:
            logger.exception("Graph execution failed: %s", e)
            event.event_type = EventType.ERROR
            event.metadata["status"] = f"Graph execution failed: {e}"
            event.data["error"] = str(e)
            publish_event(event)
            raise
