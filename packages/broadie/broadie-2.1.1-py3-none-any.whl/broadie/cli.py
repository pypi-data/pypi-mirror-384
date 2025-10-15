# broadie/cli.py
import asyncio
import importlib
import inspect
import pathlib
import secrets
import sys
import uuid
from contextlib import asynccontextmanager
from inspect import iscoroutine

import click
import uvicorn
from fastapi import FastAPI

from .a2a.register import register_agent_with_registry
from .a2a.routes import add_a2a_routes
from .config import settings
from .server import add_agent_routes, create_app


# ----------------------------
# Helpers
# ----------------------------
def ensure_env_file():
    """Check if .env file exists, create one with API_KEY if not."""
    env_path = pathlib.Path(".env")
    if not env_path.exists():
        api_key = secrets.token_urlsafe(48)

        # Create .env file with API_KEY
        with open(env_path, "w") as f:
            f.write(f"SAMPLE_API_KEY={api_key}\n")

        click.secho(
            "✅ Created .env file with API_KEY, you will use this when APIKeyHeader (apiKey) is needed "
            "example to call /invoke",
            fg="green",
        )
    else:
        click.secho(
            "🔍 Found existing .env file, you will use this when APIKeyHeader (apiKey) is needed "
            "example to call /invoke",
            fg="blue",
        )


def load_agent_from_path(path: str):
    """Load an agent from 'file.py:agent_name' or 'module:agent_name'."""
    try:
        module_path, agent_name = path.split(":")
    except ValueError:
        raise click.ClickException("❌ Invalid format. Use file.py:agent_name")

    p = pathlib.Path(module_path)
    if p.exists() and p.suffix == ".py":  # local .py file
        spec = importlib.util.spec_from_file_location(p.stem, str(p))
        module = importlib.util.module_from_spec(spec)
        sys.modules[p.stem] = module
        spec.loader.exec_module(module)  # type: ignore
    else:  # treat as dotted import
        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError:
            raise click.ClickException(f"❌ Could not import '{module_path}'")

    if not hasattr(module, agent_name):
        raise click.ClickException(f"❌ '{agent_name}' not found in '{module_path}'")

    return getattr(module, agent_name)


async def prepare_agent(agent):
    """Prepare agent by calling factory or handling coroutine, with proper initialization."""
    # Handle factory functions (callables that aren't coroutines)
    if callable(agent) and not iscoroutine(agent):
        agent = agent()  # Call the factory/LazyAgent

    # Handle coroutine objects (from async create_agent calls)
    if iscoroutine(agent):
        click.secho("⏳ Awaiting agent creation...", fg="yellow")
        agent = await agent

    # Perform additional initialization if needed (legacy support)
    if hasattr(agent, "init_checkpointer") and callable(agent.init_checkpointer):
        if inspect.iscoroutinefunction(agent.init_checkpointer):
            await agent.init_checkpointer()
        else:
            agent.init_checkpointer()
    if hasattr(agent, "init_store") and callable(agent.init_store):
        if inspect.iscoroutinefunction(agent.init_store):
            await agent.init_store()
        else:
            agent.init_store()

    return agent


# ----------------------------
# CLI
# ----------------------------
@click.group()
def main():
    """🔒 Broadie — Build and serve AI Agents with ease."""
    click.secho("🚀 Broadie CLI started", fg="green", bold=True)
    ensure_env_file()


@main.command("version")
def version():
    """Show version information."""
    from broadie import __version__

    click.echo(f"Broadie AI Framework v{__version__}")


@main.command("serve")
@click.argument("target", type=str)
@click.option("--host", default=settings.HOST, type=str)
@click.option("--port", default=settings.PORT, type=int)
@click.option("--workers", default=1, type=int, help="Number of worker processes")
def serve(target, host, port, workers):
    """Serve a single agent.

    TARGET must be:
    - file.py:agent_name
    - dotted.module:agent_name
    """
    agent_or_coroutine = load_agent_from_path(target)
    agent = asyncio.run(prepare_agent(agent_or_coroutine))
    agent.a2a_id = str(uuid.uuid4())
    asyncio.run(register_agent_with_registry(agent))

    @asynccontextmanager
    async def lifespan(fapp: FastAPI):
        click.secho(f"🔄 Initializing agent '{agent.id}'", fg="cyan")
        yield
        if hasattr(agent, "close"):
            await agent.close()
            click.secho(
                f"🧹 Cleaned up persistence for agent '{agent.id}'",
                fg="yellow",
            )

    app: FastAPI = create_app(lifespan=lifespan)
    add_agent_routes(app, agent)
    add_a2a_routes(app, agent)
    click.secho(
        f"📖 API Documentation available at http://{host}:{port}/docs",
        fg="blue",
        bold=True,
    )
    uvicorn.run(app, host=host, port=port, workers=workers, use_colors=True, log_level="warning")


@main.command("chat")
@click.argument("target", type=str)
def chat(target):
    """Run an agent in CLI chat mode.

    TARGET must be:
    - file.py:agent_name
    - dotted.module:agent_name
    """

    async def start():
        agent = load_agent_from_path(target)
        agent = await prepare_agent(agent)

        # Single thread_id for the entire CLI session, anonymous user
        session_thread_id = str(uuid.uuid4())
        user_id = "anonymous"

        click.secho(f"💬 Chatting with agent '{agent.id}' (Ctrl+C to quit)", fg="cyan")
        click.secho(
            f"🆔 User: {user_id} | Session Thread: {session_thread_id[:8]}...",
            fg="blue",
        )

        while True:
            try:
                user_msg = click.prompt("You")
                # Use consistent session identifiers
                resp = await agent.run(
                    message=user_msg,
                    user_id=user_id,
                    thread_id=session_thread_id,  # Same thread_id for entire session
                    message_id=str(uuid.uuid4()),
                )

                # Handle interrupt responses
                if isinstance(resp, dict) and resp.get("status") == "interrupted":
                    await handle_approval_flow(agent, resp, session_thread_id)
                else:
                    # Normal response
                    if hasattr(resp, "content"):
                        click.secho(f"{agent.id}> {resp.content}", fg="green")
                    else:
                        click.secho(f"{agent.id}> {resp}", fg="green")

            except KeyboardInterrupt:
                click.secho("\n👋 Exiting chat", fg="red")
                break

    asyncio.run(start())


async def handle_approval_flow(agent, interrupt_resp: dict, thread_id: str):
    """Handle interactive approval flow for interrupted executions."""
    interrupt_data = interrupt_resp.get("interrupt_data", {})

    # Display approval request
    click.secho("\n" + "=" * 60, fg="yellow")
    click.secho("⚠️  APPROVAL REQUIRED", fg="yellow", bold=True)
    click.secho("=" * 60, fg="yellow")

    tool_name = interrupt_data.get("tool", "unknown")
    message = interrupt_data.get("message", "Approval needed")
    risk_level = interrupt_data.get("risk_level", "medium")
    args = interrupt_data.get("args", {})

    click.secho(f"Tool: {tool_name}", fg="cyan")
    click.secho(f"Risk Level: {risk_level.upper()}", fg="red" if risk_level == "high" else "yellow")
    click.secho(f"Message: {message}", fg="white")

    if args:
        click.secho("\nArguments:", fg="cyan")
        for key, value in args.items():
            click.secho(f"  {key}: {value}", fg="white")

    click.secho("\n" + "=" * 60, fg="yellow")

    # Prompt for decision - just approve or reject
    while True:
        decision = (
            click.prompt(
                "\nDecision: [a]pprove / [r]eject",
                type=str,
                default="r",  # Default to reject for safety
            )
            .lower()
            .strip()
        )

        if decision in ["a", "approve", "yes", "y"]:
            click.secho("✅ Approving and resuming execution...", fg="green")
            resp = await agent.resume(thread_id=thread_id, approval=True)

            # Handle nested interrupts or final response
            if isinstance(resp, dict) and resp.get("status") == "interrupted":
                await handle_approval_flow(agent, resp, thread_id)
            else:
                if hasattr(resp, "content"):
                    click.secho(f"\n{agent.id}> {resp.content}", fg="green")
                else:
                    click.secho(f"\n{agent.id}> {resp}", fg="green")
            break

        elif decision in ["r", "reject", "no", "n"]:
            reason = click.prompt("Rejection reason (optional)", type=str, default="", show_default=False)
            click.secho("❌ Rejecting and stopping execution...", fg="red")
            resp = await agent.resume(thread_id=thread_id, approval=False, feedback=reason or "Rejected by user")
            if hasattr(resp, "content"):
                click.secho(f"\n{agent.id}> {resp.content}", fg="yellow")
            else:
                click.secho(f"\n{agent.id}> {resp}", fg="yellow")
            break

        else:
            click.secho("Invalid option. Please choose [a]pprove or [r]eject", fg="red")
