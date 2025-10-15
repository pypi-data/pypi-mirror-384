"""LangSmith tracing utility for Broadie agents.

This module provides a safe wrapper around LangSmith tracing that:
- Checks settings.LANGSMITH_TRACING before tracing
- Never fails the application if tracing fails
- Captures important metadata (user_id, thread_id, agent names, tool names)
- Provides context managers for easy integration
"""

import logging
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

_langsmith = None
_tracing_enabled = None


def _get_langsmith():
    """Lazy import langsmith."""
    global _langsmith
    if _langsmith is None:
        try:
            import langsmith as ls

            _langsmith = ls
        except ImportError:
            logger.debug("langsmith not installed, tracing disabled")
            _langsmith = False
    return _langsmith if _langsmith is not False else None


def _is_tracing_enabled() -> bool:
    """Check if tracing is enabled via settings."""
    global _tracing_enabled

    if _tracing_enabled is None:
        try:
            from broadie.config import settings

            _tracing_enabled = getattr(settings, "LANGSMITH_TRACING", False)

            if _tracing_enabled:
                logger.info("LangSmith tracing enabled")
            else:
                logger.debug("LangSmith tracing disabled (LANGSMITH_TRACING not set)")
        except Exception as e:
            logger.debug(f"Could not check tracing settings: {e}")
            _tracing_enabled = False

    return _tracing_enabled


@contextmanager
def safe_trace(
    name: str,
    run_type: str = "chain",
    metadata: Optional[dict] = None,
    tags: Optional[list[str]] = None,
):
    """
    Safe context manager for LangSmith tracing.

    Never fails the application if tracing fails.
    Only traces if settings.LANGSMITH_TRACING is enabled.

    Args:
        name: Name of the traced operation
        run_type: Type of run (chain, tool, llm, retriever, etc.)
        metadata: Additional metadata to capture
        tags: Tags for filtering traces

    Example:
        with safe_trace("agent_run", run_type="chain",
                       metadata={"user_id": "123", "agent": "main"},
                       tags=["agent", "run"]):
            result = await agent.execute()
    """
    trace_ctx = None

    if not _is_tracing_enabled():
        yield
        return

    ls = _get_langsmith()
    if ls is None:
        yield
        return

    try:
        trace_metadata = metadata or {}
        trace_tags = tags or []

        trace_ctx = ls.trace(name=name, run_type=run_type, metadata=trace_metadata, tags=trace_tags)
        trace_ctx.__enter__()
    except Exception as e:
        logger.debug(f"Failed to start trace '{name}': {e}")
        trace_ctx = None

    try:
        yield
    finally:
        if trace_ctx:
            try:
                trace_ctx.__exit__(None, None, None)
            except Exception as e:
                logger.debug(f"Failed to close trace '{name}': {e}")


def add_trace_metadata(metadata: dict):
    """
    Add metadata to the current trace context.

    Safe operation - never fails if tracing is disabled.
    """
    if not _is_tracing_enabled():
        return

    ls = _get_langsmith()
    if ls is None:
        return

    try:
        from langsmith import get_current_run_tree

        run = get_current_run_tree()
        if run:
            for key, value in metadata.items():
                run.metadata[key] = value
    except Exception as e:
        logger.debug(f"Could not add trace metadata: {e}")


def log_trace_event(event: str, **kwargs):
    """
    Log an event in the current trace.

    Safe operation - never fails if tracing is disabled.
    """
    if not _is_tracing_enabled():
        return

    ls = _get_langsmith()
    if ls is None:
        return

    try:
        from langsmith import get_current_run_tree

        run = get_current_run_tree()
        if run:
            events = run.metadata.get("events", [])
            events.append({"event": event, **kwargs})
            run.metadata["events"] = events
    except Exception as e:
        logger.debug(f"Could not log trace event: {e}")
