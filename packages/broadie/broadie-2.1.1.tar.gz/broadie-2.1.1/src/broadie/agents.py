"""Refactored agents using LangGraph swarm architecture."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Optional

from broadie.channels import ChannelsAgent
from broadie.schemas import AgentSchema, SubAgentSchema
from broadie.tracing import add_trace_metadata, log_trace_event, safe_trace
from broadie.utils import slugify

logger = logging.getLogger(__name__)


class Agent:
    """Agent adapter wrapping LangGraph swarm graph.

    Follows SOLID principles:
    - Single Responsibility: Manages agent execution and lifecycle
    - Open/Closed: Extensible without modification
    - Dependency Inversion: Depends on abstractions (persistence interface)
    """

    def __init__(
        self,
        config: AgentSchema,
        graph: Any,
        persistence_manager: Optional[Any] = None,
    ):
        """Initialize agent with config, graph, and persistence.

        Args:
            config: Agent configuration schema
            graph: Compiled LangGraph swarm graph
            persistence_manager: PersistenceManager instance (owned by this agent)
        """
        self.config = config
        self.graph = graph
        self.persistence = persistence_manager  # Agent owns its persistence

        self.name = config.name
        self.id = slugify(config.name)
        self.label = config.description or config.name
        self.model = config.model
        self.tools = config.tools
        self.channels = config.channels
        self.subagents = config.subagents
        self.channels_agent = ChannelsAgent(self.model) if self.channels else None

        logger.info(f"Agent '{self.name}' initialized with {len(self.subagents)} subagents")

    def get_identity(self) -> dict[str, Any]:
        """Return agent identity and metadata."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.label,
            "model": self.model,
            "tools": [str(tool) if callable(tool) else str(tool) for tool in self.tools],
            "subagents": [{"name": sa.name, "description": sa.description} for sa in self.subagents],
            "channels": [{"type": ch.type, "config": ch.config} for ch in self.channels] if self.channels else [],
            "has_output_schema": self.config.output_schema is not None,
            "interrupt_before": self.config.interrupt_before,
            "interrupt_after": self.config.interrupt_after,
        }

    async def run(
        self,
        message: str,
        user_id: str | None = None,
        thread_id: str | None = None,
        message_id: str | None = None,
    ) -> Any:
        """Execute agent with message using swarm graph."""
        user_id = user_id or "anonymous"
        thread_id = thread_id or str(uuid.uuid4())
        message_id = message_id or str(uuid.uuid4())

        logger.info("=" * 80)
        logger.info(f"🚀 [AGENT START] {self.name}")
        logger.info(f"   Thread ID: {thread_id}")
        logger.info(f"   User ID: {user_id}")
        logger.info(f"   Message ID: {message_id}")
        logger.info(f"   Query: {message[:100]}..." if len(message) > 100 else f"   Query: {message}")
        logger.info("=" * 80)

        from broadie.config import settings

        recursion_limit = self.config.recursion_limit or settings.SWARM_RECURSION_LIMIT

        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id,
            },
            "recursion_limit": recursion_limit,
        }

        logger.info(f"⚙️  [CONFIG] Recursion limit: {recursion_limit}")
        logger.info(f"⚙️  [CONFIG] Max transfers: {self.config.max_transfers or settings.SWARM_MAX_TRANSFERS}")
        logger.info(
            f"⚙️  [CONFIG] Output schema: {self.config.output_schema.__name__ if self.config.output_schema else 'None'}"
        )
        logger.info(f"⚙️  [CONFIG] Subagents: {len(self.subagents)}")
        logger.info(f"⚙️  [CONFIG] Tools: {len(self.tools)}")

        if self.config.interrupt_before:
            logger.info(f"🛑 [INTERRUPT] Interrupt before: {self.config.interrupt_before}")
        if self.config.interrupt_after:
            logger.info(f"🛑 [INTERRUPT] Interrupt after: {self.config.interrupt_after}")

        # Use safe_trace context manager
        with safe_trace(
            name=f"agent_{self.name}_run",
            run_type="chain",
            metadata={
                "agent_name": self.name,
                "agent_id": self.id,
                "user_id": user_id,
                "thread_id": thread_id,
                "message_id": message_id,
                "message_preview": message[:200],
                "tool_count": len(self.tools),
                "subagent_count": len(self.subagents),
                "has_output_schema": self.config.output_schema is not None,
                "recursion_limit": recursion_limit,
            },
            tags=["agent", "run", self.name],
        ):
            log_trace_event("agent_run_started", agent=self.name)

            try:
                logger.info("📤 [INVOKE] Sending message to graph...")

                result = await self.graph.ainvoke(
                    {"messages": [{"role": "user", "content": message}]},
                    config=config,
                )

                logger.info("📥 [RESULT] Received result from graph")
                logger.debug(f"   Result type: {type(result)}")
                logger.debug(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")

                if self._is_interrupted(result):
                    logger.warning("🛑 [INTERRUPTED] Execution was interrupted!")
                    interrupt_data = result.get("__interrupt__", [])
                    if isinstance(interrupt_data, list) and interrupt_data:
                        logger.warning(f"   Interrupt info: {interrupt_data[0]}")
                    else:
                        logger.warning(f"   Interrupt info: {interrupt_data}")

                    log_trace_event("agent_interrupted", agent=self.name, interrupt_type="approval_required")
                    add_trace_metadata({"interrupted": True, "interrupt_type": "approval"})

                    return self._create_interrupt_response(result, thread_id)

                # Check if structured output is available and expected
                if self.config.output_schema and "structured_response" in result:
                    structured_output = result["structured_response"]
                    logger.info(f"✅ [STRUCTURED OUTPUT] Returning {type(structured_output).__name__}")
                    logger.debug(f"   Schema: {self.config.output_schema.__name__}")

                    log_trace_event("structured_output_returned", schema=self.config.output_schema.__name__)

                    if self.channels_agent:
                        logger.info(f"📢 [CHANNELS] Delivering to {len(self.channels)} channel(s)...")
                        asyncio.create_task(self._deliver_to_channels(structured_output, thread_id, message_id))

                    logger.info("=" * 80)
                    logger.info(f"✅ [AGENT COMPLETE] {self.name}")
                    logger.info("=" * 80)
                    return structured_output

                final_message = result["messages"][-1]
                logger.info("📝 [MESSAGE] Returning final message")
                logger.debug(f"   Content length: {len(str(final_message.content))} chars")

                add_trace_metadata({"response_length": len(str(final_message.content))})

                if self.channels_agent:
                    logger.info(f"📢 [CHANNELS] Delivering to {len(self.channels)} channel(s)...")
                    asyncio.create_task(self._deliver_to_channels(final_message, thread_id, message_id))

                logger.info("=" * 80)
                logger.info(f"✅ [AGENT COMPLETE] {self.name}")
                logger.info("=" * 80)

                log_trace_event("agent_run_completed", agent=self.name)

                return final_message

            except Exception as e:
                logger.error("=" * 80)
                logger.error(f"❌ [AGENT ERROR] {self.name}")
                logger.error(f"   Error type: {type(e).__name__}")
                logger.error(f"   Error message: {str(e)}")
                logger.error("=" * 80)
                logger.error("Full traceback:", exc_info=True)

                log_trace_event("agent_run_failed", agent=self.name, error=str(e), error_type=type(e).__name__)
                add_trace_metadata({"error": str(e), "error_type": type(e).__name__})

                raise

    async def arun(
        self,
        message: str,
        user_id: str | None = None,
        thread_id: str | None = None,
        message_id: str | None = None,
    ) -> Any:
        """Execute agent with message using ainvoke (alternative async method).

        This method uses graph.ainvoke() internally and provides the same
        functionality as run() but as a separate named method.

        Args:
            message: User message to process
            user_id: User identifier (default: "anonymous")
            thread_id: Thread identifier for conversation context (auto-generated if not provided)
            message_id: Message identifier (auto-generated if not provided)

        Returns:
            Final agent response (structured output or AIMessage)
        """
        user_id = user_id or "anonymous"
        thread_id = thread_id or str(uuid.uuid4())
        message_id = message_id or str(uuid.uuid4())

        logger.info("=" * 80)
        logger.info(f"🚀 [AGENT START - arun] {self.name}")
        logger.info(f"   Thread ID: {thread_id}")
        logger.info(f"   User ID: {user_id}")
        logger.info(f"   Message ID: {message_id}")
        logger.info(f"   Query: {message[:100]}..." if len(message) > 100 else f"   Query: {message}")
        logger.info("=" * 80)

        from broadie.config import settings

        recursion_limit = self.config.recursion_limit or settings.SWARM_RECURSION_LIMIT

        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id,
            },
            "recursion_limit": recursion_limit,
        }

        logger.info(f"⚙️  [CONFIG] Recursion limit: {recursion_limit}")
        logger.info("⚙️  [CONFIG] Using graph.ainvoke()")

        with safe_trace(
            name=f"agent_{self.name}_arun",
            run_type="chain",
            metadata={
                "agent_name": self.name,
                "agent_id": self.id,
                "user_id": user_id,
                "thread_id": thread_id,
                "message_id": message_id,
                "message_preview": message[:200],
            },
            tags=["agent", "arun", self.name],
        ):
            log_trace_event("agent_arun_started", agent=self.name)

            try:
                logger.info("📤 [AINVOKE] Sending message to graph using ainvoke...")

                result = await self.graph.ainvoke(
                    {"messages": [{"role": "user", "content": message}]},
                    config=config,
                )

                logger.info("📥 [RESULT] Received result from graph")

                if self._is_interrupted(result):
                    logger.warning("🛑 [INTERRUPTED] Execution was interrupted!")
                    log_trace_event("agent_interrupted", agent=self.name, interrupt_type="approval_required")
                    return self._create_interrupt_response(result, thread_id)

                # Check if structured output is available and expected
                if self.config.output_schema and "structured_response" in result:
                    structured_output = result["structured_response"]
                    logger.info(f"✅ [STRUCTURED OUTPUT] Returning {type(structured_output).__name__}")

                    if self.channels_agent:
                        logger.info(f"📢 [CHANNELS] Delivering to {len(self.channels)} channel(s)...")
                        asyncio.create_task(self._deliver_to_channels(structured_output, thread_id, message_id))

                    logger.info("=" * 80)
                    logger.info(f"✅ [AGENT COMPLETE - arun] {self.name}")
                    logger.info("=" * 80)
                    return structured_output

                final_message = result["messages"][-1]
                logger.info("📝 [MESSAGE] Returning final message")

                if self.channels_agent:
                    logger.info(f"📢 [CHANNELS] Delivering to {len(self.channels)} channel(s)...")
                    asyncio.create_task(self._deliver_to_channels(final_message, thread_id, message_id))

                logger.info("=" * 80)
                logger.info(f"✅ [AGENT COMPLETE - arun] {self.name}")
                logger.info("=" * 80)

                log_trace_event("agent_arun_completed", agent=self.name)

                return final_message

            except Exception as e:
                logger.error(f"❌ [AGENT ERROR - arun] {self.name}: {e}", exc_info=True)
                log_trace_event("agent_arun_failed", agent=self.name, error=str(e))
                raise

    async def stream(
        self,
        message: str,
        user_id: str | None = None,
        thread_id: str | None = None,
        message_id: str | None = None,
        stream_mode: str = "values",
    ):
        """Stream agent execution events.

        Args:
            message: User message to process
            user_id: User identifier (default: "anonymous")
            thread_id: Thread identifier for conversation context (auto-generated if not provided)
            message_id: Message identifier (auto-generated if not provided)
            stream_mode: Streaming mode - "values" (default), "updates", or "messages"

        Yields:
            Stream of execution events from the graph

        Example:
            ```python
            async for event in agent.stream("Hello"):
                print(event)
            ```
        """
        user_id = user_id or "anonymous"
        thread_id = thread_id or str(uuid.uuid4())
        message_id = message_id or str(uuid.uuid4())

        logger.info(f"🌊 [STREAM START] {self.name} (mode: {stream_mode})")
        logger.info(f"   Thread ID: {thread_id}")
        logger.info(f"   User ID: {user_id}")

        from broadie.config import settings

        recursion_limit = self.config.recursion_limit or settings.SWARM_RECURSION_LIMIT

        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id,
            },
            "recursion_limit": recursion_limit,
        }

        with safe_trace(
            name=f"agent_{self.name}_stream",
            run_type="chain",
            metadata={
                "agent_name": self.name,
                "thread_id": thread_id,
                "stream_mode": stream_mode,
            },
            tags=["agent", "stream", self.name],
        ):
            try:
                async for event in self.graph.astream(
                    {"messages": [{"role": "user", "content": message}]},
                    config=config,
                    stream_mode=stream_mode,
                ):
                    yield event

                logger.info(f"✅ [STREAM COMPLETE] {self.name}")

            except Exception as e:
                logger.error(f"❌ [STREAM ERROR] {self.name}: {e}", exc_info=True)
                raise

    async def astream(
        self,
        message: str,
        user_id: str | None = None,
        thread_id: str | None = None,
        message_id: str | None = None,
        stream_mode: str = "values",
    ):
        """Stream agent execution events (alias for stream()).

        This method is provided for API consistency with LangGraph.
        Identical to stream() method.

        Args:
            message: User message to process
            user_id: User identifier (default: "anonymous")
            thread_id: Thread identifier for conversation context (auto-generated if not provided)
            message_id: Message identifier (auto-generated if not provided)
            stream_mode: Streaming mode - "values" (default), "updates", or "messages"

        Yields:
            Stream of execution events from the graph

        Example:
            ```python
            async for event in agent.astream("Hello"):
                print(event)
            ```
        """
        async for event in self.stream(message, user_id, thread_id, message_id, stream_mode):
            yield event

    def _is_interrupted(self, result: dict) -> bool:
        """Check if execution was interrupted."""
        return "__interrupt__" in result or result.get("status") == "interrupted"

    def _create_interrupt_response(self, result: dict, thread_id: str) -> dict:
        """Create response for interrupted execution."""
        interrupt_data_list = result.get("__interrupt__", [])

        # Extract the actual interrupt data
        interrupt_value = {}
        if isinstance(interrupt_data_list, list) and interrupt_data_list:
            # Each interrupt is a tuple (Interrupt object, )
            interrupt_obj = interrupt_data_list[0]
            if hasattr(interrupt_obj, "value"):
                interrupt_value = interrupt_obj.value
            elif isinstance(interrupt_obj, tuple) and len(interrupt_obj) > 0:
                interrupt_value = interrupt_obj[0].value if hasattr(interrupt_obj[0], "value") else {}

        return {
            "status": "interrupted",
            "thread_id": thread_id,
            "interrupt_data": interrupt_value,
            "message": "Agent is waiting for approval to proceed.",
        }

    async def resume(
        self,
        thread_id: str,
        approval: bool = True,
        feedback: str | None = None,
        updated_input: dict | None = None,
    ):
        """Resume interrupted execution with human input."""
        from langgraph.types import Command

        logger.info(f"Resuming execution for thread {thread_id}: approval={approval}")

        # Use safe_trace context manager for resume operation
        with safe_trace(
            name=f"agent_{self.name}_resume",
            run_type="chain",
            metadata={
                "agent_name": self.name,
                "thread_id": thread_id,
                "approval": approval,
                "has_feedback": feedback is not None,
                "has_updated_input": updated_input is not None,
            },
            tags=["agent", "resume", "approval", self.name],
        ):
            log_trace_event("agent_resume_started", approved=approval)

            try:
                config = {"configurable": {"thread_id": thread_id}}

                # Build approval decision to pass back to interrupt()
                if not approval:
                    approval_decision = {"approved": False, "reason": feedback or "Rejected by user"}
                    logger.info(f"Rejecting with reason: {approval_decision['reason']}")
                    log_trace_event("approval_rejected", reason=approval_decision["reason"])
                elif updated_input:
                    approval_decision = updated_input
                    logger.info("Resuming with custom input")
                    log_trace_event("approval_custom_input")
                elif feedback and feedback != "Approved by user":
                    approval_decision = {"approved": True, "comment": feedback}
                    logger.info(f"Approving with feedback: {feedback}")
                    log_trace_event("approval_approved_with_feedback", feedback=feedback)
                else:
                    approval_decision = {"approved": True}
                    logger.info("Approving and continuing execution")
                    log_trace_event("approval_approved")

                resume_command = Command(resume=approval_decision)

                result = await self.graph.ainvoke(resume_command, config=config)

                if self._is_interrupted(result):
                    log_trace_event("resume_interrupted_again")
                    return self._create_interrupt_response(result, thread_id)

                log_trace_event("resume_completed")
                return result["messages"][-1]

            except Exception as e:
                logger.error(f"Failed to resume: {e}", exc_info=True)
                log_trace_event("resume_failed", error=str(e))
                raise

    async def _deliver_to_channels(self, message: Any, thread_id: str, message_id: str):
        """Deliver message to configured channels."""
        if not self.channels_agent:
            return

        try:
            await self.channels_agent.deliver(
                message=message,
                channels=self.channels,
                thread_id=thread_id,
                message_id=message_id,
            )
        except Exception as e:
            logger.error(f"Failed to deliver to channels: {e}", exc_info=True)

    async def close(self) -> None:
        """Close agent and cleanup resources.

        Properly closes persistence connections and releases resources.
        Should be called when agent is no longer needed.
        """
        logger.info(f"Closing agent '{self.name}'...")

        if self.persistence:
            try:
                await self.persistence.close()
                logger.info(f"Agent '{self.name}' persistence closed successfully")
            except Exception as e:
                logger.error(f"Error closing persistence for agent '{self.name}': {e}")
                raise

        logger.info(f"Agent '{self.name}' closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures cleanup."""
        await self.close()
        return False


class SubAgent:
    """SubAgent adapter for swarm execution."""

    def __init__(self, config: SubAgentSchema, parent: Agent = None, graph: Any = None):
        self.config = config
        self.parent = parent
        self.graph = graph

        self.name = config.name
        self.id = slugify(config.name)
        self.label = config.description or config.name

        logger.info(f"SubAgent '{self.name}' initialized")

    async def run(
        self,
        message: str,
        user_id: str | None = None,
        thread_id: str | None = None,
        message_id: str | None = None,
    ):
        """Execute subagent."""
        if self.parent and self.parent.graph:
            logger.info(f"SubAgent {self.name} delegating to parent swarm")
            return await self.parent.run(
                message=f"[Transfer to {self.name}] {message}",
                user_id=user_id,
                thread_id=thread_id,
            )

        if self.graph:
            config = {
                "configurable": {"thread_id": thread_id or str(uuid.uuid4())},
            }

            result = await self.graph.ainvoke(
                {"messages": [{"role": "user", "content": message}]},
                config=config,
            )

            return result["messages"][-1]

        raise RuntimeError(f"SubAgent {self.name} has no parent or graph to execute")
