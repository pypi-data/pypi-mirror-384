"""Graph builder for creating LangGraph supervisor architectures.

This replaces the swarm pattern with a supervisor pattern that:
1. Properly aggregates subagent results
2. Handles approval propagation from subagents
3. Maintains subagents as individual entities
4. Coordinates execution through a supervisor
"""

import logging
import os
from typing import Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from typing_extensions import Annotated

from broadie.schemas import AgentSchema, BaseDefaultOutput, SubAgentSchema
from broadie.tracing import log_trace_event, safe_trace

logger = logging.getLogger(__name__)


class ExtendedAgentState(TypedDict):
    """Extended agent state that includes structured_response for output schemas."""

    messages: Annotated[list[BaseMessage], "add_messages"]
    structured_response: Any | None


def validate_model_credentials(model_config) -> None:
    """Validate that required credentials are available for the model provider."""
    provider = model_config.provider.value

    if provider == "google_vertexai":
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and not os.getenv("GOOGLE_CLOUD_PROJECT"):
            logger.warning(
                "Google Vertex AI credentials not found. "
                "Set GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_CLOUD_PROJECT environment variable"
            )

    elif provider == "google":
        if not os.getenv("GOOGLE_API_KEY"):
            logger.warning("Google API key not found. Set GOOGLE_API_KEY environment variable")

    elif provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable")

    elif provider == "anthropic":
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable")


def initialize_model(model_config):
    """Initialize LLM model instance based on provider."""
    validate_model_credentials(model_config)

    model_params = {
        "temperature": 0.2,
        "max_tokens": 8100,
    }

    provider = model_config.provider.value
    logger.info(f"Initializing model: {provider}/{model_config.name}")

    with safe_trace(
        name="initialize_model",
        run_type="llm",
        metadata={
            "provider": provider,
            "model_name": model_config.name,
            "temperature": model_params["temperature"],
            "max_tokens": model_params["max_tokens"],
        },
        tags=["model", "initialization", provider],
    ):
        try:
            if provider == "google_vertexai":
                from langchain_google_vertexai import ChatVertexAI

                return ChatVertexAI(model_name=model_config.name, **model_params)

            elif provider == "google":
                from langchain_google_genai import ChatGoogleGenerativeAI

                return ChatGoogleGenerativeAI(model=model_config.name, **model_params)

            elif provider == "openai":
                from langchain_openai import ChatOpenAI

                return ChatOpenAI(model=model_config.name, **model_params)

            elif provider == "anthropic":
                from langchain_anthropic import ChatAnthropic

                return ChatAnthropic(model=model_config.name, **model_params)

            raise ValueError(f"Unsupported model provider: {provider}")
        except Exception as e:
            logger.error(f"Failed to initialize model {provider}/{model_config.name}: {e}")
            log_trace_event("model_initialization_failed", provider=provider, error=str(e))
            raise


def collect_interrupt_tools(tools: list[Any]) -> tuple[list[str], list[str]]:
    """Collect tool names that require approval (interrupt_before and interrupt_after).

    Args:
        tools: List of tool functions

    Returns:
        Tuple of (interrupt_before, interrupt_after) tool name lists
    """
    interrupt_before = []
    interrupt_after = []

    for tool in tools:
        # Check if tool has approval_required metadata
        if hasattr(tool, "__broadie_approval_required__") and tool.__broadie_approval_required__:
            tool_name = getattr(tool, "name", tool.__name__)
            # Add to interrupt_before for approval workflow
            interrupt_before.append(tool_name)
            logger.debug(f"Tool '{tool_name}' requires approval - adding to interrupt_before")

    return interrupt_before, interrupt_after


async def build_supervisor_graph(
    main_agent_config: AgentSchema,
    subagent_configs: list[SubAgentSchema],
    checkpointer: Any,
    store: Any,
) -> CompiledStateGraph:
    """Build supervisor graph with subagents.

    The supervisor pattern:
    1. Main agent (supervisor) coordinates and has its own tools
    2. Subagents are created as individual agents (Pregel objects)
    3. Supervisor delegates to subagents via handoff tools
    4. Subagent results flow back to supervisor
    5. Supervisor aggregates and returns final response
    6. Approvals from subagent tools bubble up to supervisor level

    Args:
        main_agent_config: Configuration for main/supervisor agent
        subagent_configs: List of subagent configurations
        checkpointer: Checkpointer for persistence
        store: Store for memory/context

    Returns:
        Compiled StateGraph with supervisor and subagents
    """
    logger.info(f"Building supervisor graph for agent: {main_agent_config.name} with {len(subagent_configs)} subagents")

    with safe_trace(
        name=f"build_supervisor_{main_agent_config.name}",
        run_type="chain",
        metadata={
            "main_agent": main_agent_config.name,
            "subagent_count": len(subagent_configs),
            "subagent_names": [sa.name for sa in subagent_configs],
            "has_checkpointer": checkpointer is not None,
            "has_store": store is not None,
        },
        tags=["supervisor", "build", main_agent_config.name],
    ):
        log_trace_event("supervisor_build_started", agent=main_agent_config.name)

        # Initialize model for main agent
        main_model = initialize_model(main_agent_config.model)

        # Build subagent nodes
        subagent_nodes = []
        if subagent_configs:
            logger.info(f"Building {len(subagent_configs)} subagent(s)...")

            for config in subagent_configs:
                logger.info(f"  Building subagent: {config.name}")

                # Initialize model for subagent (or use main agent's model)
                sub_model = initialize_model(config.model or main_agent_config.model)

                # Collect interrupt tools for approval handling
                interrupt_before, interrupt_after = collect_interrupt_tools(config.tools)

                # Create subagent as a react agent
                subagent = create_react_agent(
                    model=sub_model,
                    tools=list(config.tools),
                    prompt=config.prompt,
                    response_format=config.output_schema if config.output_schema else BaseDefaultOutput,
                    checkpointer=checkpointer,
                    store=store,
                    name=config.name,
                )

                subagent_nodes.append(subagent)
                logger.info(f"    ✅ Subagent '{config.name}' created with {len(config.tools)} tool(s)")

        # Add memory tools to supervisor's tools (not subagents to avoid duplication)
        from broadie.tools.memory import build_memory_tools_langgraph

        supervisor_tools = list(main_agent_config.tools)
        if store:
            memory_tools = build_memory_tools_langgraph(store)
            supervisor_tools.extend(memory_tools)
            logger.info(f"Added {len(memory_tools)} memory tool(s) to supervisor")

        # Collect interrupt tools from supervisor's own tools
        supervisor_interrupt_before, supervisor_interrupt_after = collect_interrupt_tools(main_agent_config.tools)

        # Import create_supervisor from langgraph_supervisor (separate package)
        try:
            from langgraph_supervisor import create_supervisor

            logger.info("Creating supervisor with LangGraph's create_supervisor...")

            # Build supervisor prompt
            supervisor_prompt = main_agent_config.instruction

            # Add subagent descriptions to help supervisor delegate
            if subagent_configs:
                supervisor_prompt += "\n\nYou can delegate to these specialized agents:\n"
                for sa in subagent_configs:
                    capabilities = ", ".join(sa.capabilities) if sa.capabilities else sa.description
                    supervisor_prompt += f"- {sa.name}: {capabilities}\n"

            # Create supervisor workflow
            workflow = create_supervisor(
                agents=subagent_nodes,  # Subagents created with create_react_agent
                model=main_model,
                tools=supervisor_tools if supervisor_tools else None,
                prompt=supervisor_prompt,
                response_format=(
                    main_agent_config.output_schema if main_agent_config.output_schema else BaseDefaultOutput
                ),
                add_handoff_messages=True,  # Always True - adds AI/Tool message pairs for handoffs
                add_handoff_back_messages=True,  # Always True - tracks return to supervisor
                handoff_tool_prefix="transfer_to",  # Use transfer_to_AgentName pattern
                supervisor_name=main_agent_config.name,
                include_agent_name="inline",  # Better compatibility across LLM providers
                output_mode="full_history",  # Return full message history (not just last message)
            )

            logger.info("Compiling supervisor graph...")

            # Compile the supervisor workflow
            graph = workflow.compile(
                checkpointer=checkpointer,
                store=store,
                interrupt_before=supervisor_interrupt_before if supervisor_interrupt_before else None,
                interrupt_after=supervisor_interrupt_after if supervisor_interrupt_after else None,
            )

            logger.info("✅ Supervisor graph compiled successfully")
            log_trace_event("supervisor_build_completed", agent=main_agent_config.name)

            return graph

        except ImportError as e:
            logger.error(
                "Failed to import create_supervisor from langgraph_supervisor. "
                "Make sure you have the package installed: pip install langgraph-supervisor"
            )
            raise ImportError("create_supervisor not found. Please install: pip install langgraph-supervisor") from e
        except Exception as e:
            logger.error(f"Failed to compile supervisor graph: {e}")
            log_trace_event("supervisor_build_failed", agent=main_agent_config.name, error=str(e))
            raise ValueError(f"Supervisor graph compilation failed: {e}") from e


async def build_single_agent_graph(
    config: AgentSchema,
    checkpointer: Any,
    store: Any,
) -> CompiledStateGraph:
    """Build graph for single agent without subagents.

    Args:
        config: Agent configuration
        checkpointer: Checkpointer for persistence
        store: Store for memory/context

    Returns:
        Compiled StateGraph for single agent
    """
    logger.info(f"Building single agent graph: {config.name}")

    with safe_trace(
        name=f"build_single_agent_{config.name}",
        run_type="chain",
        metadata={
            "agent_name": config.name,
            "tool_count": len(config.tools),
            "has_output_schema": config.output_schema is not None,
            "has_checkpointer": checkpointer is not None,
            "has_store": store is not None,
        },
        tags=["agent", "build", config.name],
    ):
        log_trace_event("single_agent_build_started", agent=config.name)

        # Initialize model
        model = initialize_model(config.model)

        # Add memory tools
        from broadie.tools.memory import build_memory_tools_langgraph

        tools = list(config.tools)
        if store:
            memory_tools = build_memory_tools_langgraph(store)
            tools.extend(memory_tools)
            logger.info(f"Added {len(memory_tools)} memory tool(s)")

        # Collect interrupt tools for approval handling
        interrupt_before, interrupt_after = collect_interrupt_tools(config.tools)

        # Create single react agent
        agent = create_react_agent(
            model=model,
            tools=tools,
            prompt=config.instruction,
            response_format=config.output_schema if config.output_schema else None,
            checkpointer=checkpointer,
            store=store,
            name=config.name,
        )

        logger.info("✅ Single agent graph created successfully")
        log_trace_event("single_agent_build_completed", agent=config.name)

        return agent
