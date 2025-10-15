"""Custom tool decorator with integrated approval workflows."""

import functools
import inspect
import logging
from typing import Callable, Optional, Union

from langchain_core.tools import tool as langchain_tool
from pydantic import BaseModel

from broadie.tracing import add_trace_metadata, log_trace_event, safe_trace

logger = logging.getLogger(__name__)


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    return_direct: bool = False,
    args_schema: Optional[type[BaseModel]] = None,
    infer_schema: bool = True,
    response_format: str = "content",
    parse_docstring: bool = False,
    error_on_invalid_docstring: bool = True,
    # Approval workflow parameters
    approval_required: bool = False,
    approval_message: Optional[str] = None,
    approval_data: Optional[Union[dict, Callable]] = None,
    risk_level: str = "medium",
):
    """
    Decorator that creates a LangChain tool with optional approval workflows.

    This is a single decorator that handles both tool registration and approval logic.

    LangChain Tool Parameters:
        name: Optional name of the tool. If not provided, uses function name.
        description: Tool description. If not provided, uses function docstring.
        return_direct: Whether to return directly from the tool. Defaults to False.
        args_schema: Optional Pydantic model for argument validation.
        infer_schema: Whether to infer schema from function signature. Defaults to True.
        response_format: Tool response format ("content" or "content_and_artifact").
        parse_docstring: Whether to parse Google-style docstrings. Defaults to False.
        error_on_invalid_docstring: Whether to raise on invalid docstrings. Defaults to True.

    Approval Workflow Parameters:
        approval_required: Whether this tool requires human approval before execution.
        approval_message: Template message with {arg_name} placeholders.
                         Example: "Delete file {filename}? This cannot be undone!"
        approval_data: Additional data (dict or callable) to include in approval request.
        risk_level: Risk level (low, medium, high, critical). Defaults to "medium".

    Example without approval:
        @tool(parse_docstring=True)
        def read_file(filename: str) -> dict:
            '''Read a file.

            Args:
                filename: Name of the file to read
            '''
            with open(filename) as f:
                return {"content": f.read()}

    Example with approval:
        @tool(
            parse_docstring=True,
            approval_required=True,
            approval_message="⚠️ Delete file {filename}? This cannot be undone!",
            risk_level="high"
        )
        def delete_file(filename: str) -> dict:
            '''Delete a file - requires approval.'''
            os.remove(filename)
            return {"status": "deleted", "filename": filename}
    """

    def decorator(func: Callable) -> Callable:
        # If approval is required, wrap the function with approval logic
        if approval_required:
            func = _wrap_with_approval(func, message=approval_message, data=approval_data, risk_level=risk_level)

        # Create LangChain tool
        return langchain_tool(
            name,
            description=description,
            return_direct=return_direct,
            args_schema=args_schema,
            infer_schema=infer_schema,
            response_format=response_format,
            parse_docstring=parse_docstring,
            error_on_invalid_docstring=error_on_invalid_docstring,
        )(func)

    return decorator


def _wrap_with_approval(
    func: Callable,
    message: Optional[str] = None,
    data: Optional[Union[dict, Callable]] = None,
    risk_level: str = "medium",
) -> Callable:
    """Internal function to wrap a function with approval logic."""
    func_name = func.__name__

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)

        # Format approval message with function arguments
        approval_message = message or f"Approve execution of {func_name}?"
        try:
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            approval_message = approval_message.format(**bound_args.arguments)
        except Exception as e:
            logger.debug(f"Could not format approval message: {e}")

        # Build approval payload
        approval_payload = {
            "type": "approval_request",
            "tool": func_name,
            "message": approval_message,
            "risk_level": risk_level,
            "args": kwargs or dict(zip(sig.parameters.keys(), args)),
        }

        # Add custom data if provided
        if data:
            if callable(data):
                try:
                    custom_data = data(*args, **kwargs)
                    if isinstance(custom_data, dict):
                        approval_payload.update(custom_data)
                except Exception as e:
                    logger.warning(f"Failed to generate approval data: {e}")
            elif isinstance(data, dict):
                approval_payload.update(data)

        logger.warning(f"⚠️  [APPROVAL REQUIRED] {func_name}")
        logger.warning(f"   Message: {approval_message}")
        logger.warning(f"   Risk Level: {risk_level}")

        # Use safe_trace for approval request
        with safe_trace(
            name=f"tool_approval_{func_name}",
            run_type="tool",
            metadata={
                "tool_name": func_name,
                "requires_approval": True,
                "risk_level": risk_level,
                "approval_message": approval_message,
                "args": approval_payload["args"],
            },
            tags=["tool", "approval", func_name, risk_level],
        ):
            log_trace_event("approval_requested", tool=func_name, risk_level=risk_level)

            # Trigger LangGraph interrupt
            try:
                from langgraph.types import interrupt

                logger.info("🌐 [INTERRUPT] Triggering approval interrupt...")
                approval_response = interrupt(approval_payload)

                # Check approval decision
                if approval_response and approval_response.get("approved") is False:
                    rejection_reason = approval_response.get("reason", "Operation rejected by user")
                    logger.error(f"❌ [REJECTED] {func_name} - Reason: {rejection_reason}")

                    log_trace_event("approval_rejected", tool=func_name, reason=rejection_reason)
                    add_trace_metadata({"approved": False, "rejection_reason": rejection_reason})

                    return {
                        "status": "rejected",
                        "tool": func_name,
                        "reason": rejection_reason,
                        "message": f"Operation rejected: {rejection_reason}",
                    }

                # Approved - log and continue
                if approval_response and approval_response.get("approved") is True:
                    logger.info(f"✅ [APPROVED] {func_name}")
                    if approval_response.get("comment"):
                        logger.info(f"💬 Comment: {approval_response.get('comment')}")

                    log_trace_event("approval_granted", tool=func_name)
                    add_trace_metadata({"approved": True})

            except (ImportError, RuntimeError) as e:
                logger.error(f"❌ [APPROVAL ERROR] Not in LangGraph context: {e}")
                log_trace_event("approval_error", tool=func_name, error=str(e))
                raise RuntimeError(
                    f"Function '{func_name}' requires approval but is not running in LangGraph context. "
                    f"Ensure it's called within an agent's graph execution."
                )

            # Execute the wrapped function with tracing
            logger.info(f"🚀 [EXECUTING] {func_name}")

            with safe_trace(
                name=f"tool_execute_{func_name}",
                run_type="tool",
                metadata={
                    "tool_name": func_name,
                    "approved": True,
                    "args": approval_payload["args"],
                },
                tags=["tool", "execute", func_name],
            ):
                try:
                    result = func(*args, **kwargs)
                    logger.info(f"✅ [SUCCESS] {func_name}")
                    log_trace_event("tool_execution_success", tool=func_name)
                    return result
                except Exception as e:
                    logger.error(f"❌ [ERROR] {func_name} failed: {e}", exc_info=True)
                    log_trace_event("tool_execution_failed", tool=func_name, error=str(e), error_type=type(e).__name__)
                    add_trace_metadata({"error": str(e), "error_type": type(e).__name__})
                    raise

    return wrapper
