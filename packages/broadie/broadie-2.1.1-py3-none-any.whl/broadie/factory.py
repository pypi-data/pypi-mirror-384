"""Factory functions for creating agents using LangGraph swarm architecture."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from pydantic import BaseModel

from .agents import Agent
from .graph_builder import build_single_agent_graph, build_supervisor_graph
from .persistence.manager import PersistenceManager
from .schemas import AgentSchema, BaseDefaultOutput, ChannelSchema, ModelProvider, ModelSchema, SubAgentSchema

logger = logging.getLogger(__name__)


def _build_channels(channels: list[ChannelSchema | dict[str, Any]] | None) -> list[ChannelSchema]:
    """Build channel schemas from various input formats."""
    if not channels:
        return []
    built = []
    for ch in channels:
        if isinstance(ch, ChannelSchema):
            built.append(ch)
        elif isinstance(ch, dict):
            built.append(ChannelSchema(**ch))
        else:
            raise ValueError(f"Invalid channel type: {type(ch)}")
    return built


class LazyAgent:
    """Lazy-initialized agent wrapper for simple sync-style API.

    This wrapper allows users to write simple code like:
        agent = create_agent(...)
        result = agent.run("message")

    The agent initializes on first use and handles async internally.
    """

    def __init__(
        self,
        name: str,
        instruction: str,
        model: ModelSchema,
        tools: list[Any],
        description: str | None,
        channels: list[ChannelSchema],
        subagents: list[SubAgentSchema],
        output_schema: type[BaseModel],
        strict_mode: bool,
        max_transfers: int,
        recursion_limit: int,
        database_url: str | None,
        use_memory: bool | None,
    ):
        """Store configuration for lazy initialization."""
        self._name = name
        self._instruction = instruction
        self._model = model
        self._tools = tools
        self._description = description
        self._channels = channels
        self._subagents = subagents
        self._output_schema = output_schema
        self._strict_mode = strict_mode
        self._max_transfers = max_transfers
        self._recursion_limit = recursion_limit
        self._database_url = database_url
        self._use_memory = use_memory

        self._agent: Optional[Agent] = None
        self._initializing = False

        # Expose attributes immediately for convenience and CLI compatibility
        from broadie.utils import slugify

        self.name = name
        self.id = slugify(name)  # Add id for CLI compatibility
        self.label = description or instruction  # Add label for registration
        self.model = model  # Add model for registration
        self.tools = tools
        self.subagents = subagents
        self.a2a_id: Optional[str] = None  # Will be set by CLI serve command

    async def _ensure_initialized(self):
        """Initialize the agent if not already initialized."""
        if self._agent is not None:
            return

        if self._initializing:
            # Avoid re-initialization if already in progress
            while self._initializing:
                await asyncio.sleep(0.01)
            return

        self._initializing = True
        try:
            logger.info(f"Lazy-initializing agent: {self._name}")

            # Build agent schema

            schema = AgentSchema(
                name=self._name,
                description=self._description or self._instruction,
                instruction=self._instruction,
                model=self._model,
                tools=self._tools,
                subagents=self._subagents,
                channels=self._channels,
                output_schema=self._output_schema,
                strict_mode=self._strict_mode,
                interrupt_before=[],
                interrupt_after=[],
                max_transfers=self._max_transfers,
                recursion_limit=self._recursion_limit,
            )

            # Create and initialize persistence
            persistence = PersistenceManager(database_url=self._database_url, use_memory=self._use_memory)
            await persistence.initialize()

            # Build graph
            if self._subagents:
                graph = await build_supervisor_graph(
                    main_agent_config=schema,
                    subagent_configs=self._subagents,
                    checkpointer=persistence.checkpointer,
                    store=persistence.store,
                )
            else:
                graph = await build_single_agent_graph(
                    config=schema,
                    checkpointer=persistence.checkpointer,
                    store=persistence.store,
                )

            # Create agent
            self._agent = Agent(config=schema, graph=graph, persistence_manager=persistence)
            logger.info(f"✅ Agent '{self._name}' initialized")

        finally:
            self._initializing = False

    def run(
        self, message: str, user_id: str | None = None, thread_id: str | None = None, message_id: str | None = None
    ):
        """Run the agent with a message.

        This method handles async internally, so you can use it like:
            result = agent.run("message")

        It works in both sync and async contexts.
        """
        # Check if we're in an async context
        try:
            asyncio.get_running_loop()
            # We're in async context - return coroutine
            return self._async_run(message, user_id, thread_id, message_id)
        except RuntimeError:
            # No event loop - run in sync mode
            return asyncio.run(self._async_run(message, user_id, thread_id, message_id))

    async def _async_run(
        self, message: str, user_id: str | None = None, thread_id: str | None = None, message_id: str | None = None
    ):
        """Internal async run method."""
        await self._ensure_initialized()
        return await self._agent.run(message, user_id=user_id, thread_id=thread_id, message_id=message_id)

    async def arun(
        self, message: str, user_id: str | None = None, thread_id: str | None = None, message_id: str | None = None
    ):
        """Execute agent with message and return final result.

        This is the async version of run() and is identical in behavior.

        Args:
            message: User message to process
            user_id: User identifier (default: "anonymous")
            thread_id: Thread identifier for conversation context
            message_id: Message identifier

        Returns:
            Final agent response (structured output or AIMessage)
        """
        await self._ensure_initialized()
        return await self._agent.arun(message, user_id=user_id, thread_id=thread_id, message_id=message_id)

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
            thread_id: Thread identifier for conversation context
            message_id: Message identifier
            stream_mode: Streaming mode - "values" (default), "updates", or "messages"

        Yields:
            Stream of execution events from the graph

        Example:
            ```python
            async for event in agent.stream("Hello"):
                print(event)
            ```
        """
        await self._ensure_initialized()
        async for event in self._agent.stream(message, user_id, thread_id, message_id, stream_mode):
            yield event

    async def astream(
        self,
        message: str,
        user_id: str | None = None,
        thread_id: str | None = None,
        message_id: str | None = None,
        stream_mode: str = "values",
    ):
        """Stream agent execution events (alias for stream()).

        Args:
            message: User message to process
            user_id: User identifier (default: "anonymous")
            thread_id: Thread identifier for conversation context
            message_id: Message identifier
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

    def get_identity(self) -> dict[str, Any]:
        """Return agent identity and metadata.

        This method works without initialization for server info endpoints.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.label,
            "model": self.model,
            "tools": [str(tool) if callable(tool) else str(tool) for tool in self.tools],
            "subagents": [{"name": sa.name, "description": sa.description} for sa in self.subagents],
            "channels": [{"type": ch.type, "config": ch.config} for ch in self._channels] if self._channels else [],
            "has_output_schema": self._output_schema is not None,
            "interrupt_before": [],
            "interrupt_after": [],
        }

    async def resume(self, thread_id: str, approval: bool = True, feedback: str | None = None):
        """Resume interrupted execution."""
        await self._ensure_initialized()
        return await self._agent.resume(thread_id, approval, feedback)

    async def close(self):
        """Close the agent and cleanup resources."""
        if self._agent:
            await self._agent.close()
            self._agent = None

    def __call__(self):
        """Make LazyAgent callable for CLI compatibility.

        CLI expects: agent = load_agent_from_path("file.py:agent")
        Then calls: agent() expecting a coroutine or Agent

        This returns self, which is awaitable via __await__
        """
        return self

    def __await__(self):
        """Make LazyAgent awaitable for CLI compatibility.

        The CLI does: agent = await agent()
        This makes LazyAgent work with that pattern.
        """

        async def _init():
            await self._ensure_initialized()
            return self  # Return LazyAgent, not internal Agent, to keep the simple API

        return _init().__await__()

    async def __aenter__(self):
        """Async context manager support."""
        await self._ensure_initialized()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager cleanup."""
        await self.close()
        return False

    def __repr__(self):
        status = "initialized" if self._agent else "not initialized"
        return f"<LazyAgent '{self._name}' ({status})>"


def create_sub_agent(
    name: str,
    prompt: str,
    description: str | None = None,
    tools: list[Any] | None = None,
    model: ModelSchema | None = None,
    output_schema: type[BaseModel] | None = None,
    strict_mode: bool = True,
    capabilities: list[str] | None = None,
    tags: list[str] | None = None,
) -> SubAgentSchema:
    """
    Create a subagent schema (not instantiated until parent agent is created).

    Args:
        name: Subagent name
        prompt: System prompt for the subagent
        description: Optional description (defaults to prompt)
        tools: List of tools available to the subagent
        model: Optional model configuration (defaults to parent agent's model)
        output_schema: Pydantic model for structured output
        strict_mode: Enable strict mode for output validation
        capabilities: List of capabilities this subagent provides
        tags: Tags for categorization

    Returns:
        SubAgentSchema configuration
    """
    logger.info(f"Creating subagent schema: {name}")

    return SubAgentSchema(
        name=name,
        prompt=prompt,
        description=description or prompt,
        tools=tools or [],
        model=model,
        output_schema=(output_schema.model_rebuild() if output_schema else BaseDefaultOutput.model_rebuild()),
        strict_mode=strict_mode,
        capabilities=capabilities or [],
        tags=tags or [],
    )


def create_agent(
    name: str,
    instruction: str,
    model: str | ModelSchema = "gemini-2.0-flash",
    provider: str | ModelProvider = ModelProvider.google,
    tools: list[Any] | None = None,
    description: str | None = None,
    channels: list[ChannelSchema | dict[str, Any]] | None = None,
    subagents: list[SubAgentSchema | dict[str, Any]] | None = None,
    output_schema: type[BaseModel] | None = None,
    strict_mode: bool = True,
    max_transfers: int | None = None,
    recursion_limit: int | None = None,
    database_url: str | None = None,
    use_memory: bool | None = None,
) -> LazyAgent:
    """
    Create an agent with lazy initialization for simple API.

    Simple usage pattern:
    ```python
    from broadie import create_agent, tool

    @tool
    def my_tool():
        return "result"

    # Create agent (returns immediately, no await needed)
    agent = create_agent(
        name="MyAgent",
        instruction="You are helpful",
        tools=[my_tool]
    )

    # Use agent (handles async internally)
    result = agent.run("Hello!")
    ```

    Args:
        name: Agent name
        instruction: System instruction for the agent
        model: Model name or ModelSchema
        provider: Model provider (google, openai, anthropic)
        tools: List of tools available to the agent
        description: Optional description
        channels: Output channels for results
        subagents: List of subagents for delegation
        output_schema: Pydantic model for structured output
        strict_mode: Enable strict mode for output validation
        max_transfers: Maximum number of subagent transfers (default from settings)
        recursion_limit: Maximum recursion depth (default from settings)
        database_url: Custom database URL (default from settings)
        use_memory: Force in-memory persistence (default based on environment)

    Returns:
        LazyAgent that initializes on first use
    """
    logger.info(f"Creating lazy agent: {name} with {len(subagents or [])} subagents")

    # Build model schema
    if isinstance(model, str):
        model = ModelSchema(provider=provider, name=model)
    if isinstance(provider, str):
        provider = ModelProvider(provider)

    # Build channels and subagents
    built_channels = _build_channels(channels)
    built_subagents = []
    if subagents:
        for sa in subagents:
            if isinstance(sa, SubAgentSchema):
                built_subagents.append(sa)
            elif isinstance(sa, dict):
                built_subagents.append(SubAgentSchema(**sa))
            else:
                raise ValueError(f"Invalid subagent type: {type(sa)}")

    # Apply defaults from config
    from broadie.config import settings

    final_max_transfers = max_transfers if max_transfers is not None else settings.SWARM_MAX_TRANSFERS
    final_recursion_limit = recursion_limit if recursion_limit is not None else settings.SWARM_RECURSION_LIMIT

    # Return lazy agent that initializes on first use
    return LazyAgent(
        name=name,
        instruction=instruction,
        model=model,
        tools=tools or [],
        description=description,
        channels=built_channels,
        subagents=built_subagents,
        output_schema=output_schema or BaseDefaultOutput,
        strict_mode=strict_mode,
        max_transfers=final_max_transfers,
        recursion_limit=final_recursion_limit,
        database_url=database_url,
        use_memory=use_memory,
    )
