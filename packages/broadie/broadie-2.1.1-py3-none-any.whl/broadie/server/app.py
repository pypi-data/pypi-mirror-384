import time
from datetime import datetime, timezone
from threading import Lock
from typing import Optional

from fastapi import Depends, FastAPI, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from broadie.config import settings
from broadie.server.credentials import check_credentials

limiter = Limiter(key_func=get_remote_address)


# Approval tracking system for multi-user/multi-thread scenarios
class ApprovalRecord(BaseModel):
    """Record of an approval request with full metadata."""

    thread_id: str
    user_id: str
    checkpoint_id: Optional[str] = None
    tool: str
    message: str
    risk_level: str
    args: dict
    request_time: str  # ISO format
    status: str  # "pending", "approved", "rejected"
    decision_time: Optional[str] = None  # ISO format
    decided_by: Optional[str] = None


class ApprovalTracker:
    """Thread-safe in-memory tracker for approval requests."""

    def __init__(self):
        self._approvals: dict[str, ApprovalRecord] = {}
        self._lock = Lock()

    def add_approval(
        self, thread_id: str, user_id: str, interrupt_data: dict, checkpoint_id: Optional[str] = None
    ) -> ApprovalRecord:
        """Store a new pending approval."""
        with self._lock:
            record = ApprovalRecord(
                thread_id=thread_id,
                user_id=user_id,
                checkpoint_id=checkpoint_id,
                tool=interrupt_data.get("tool", "unknown"),
                message=interrupt_data.get("message", "Approval required"),
                risk_level=interrupt_data.get("risk_level", "medium"),
                args=interrupt_data.get("args", {}),
                request_time=datetime.now(timezone.utc).isoformat(),
                status="pending",
            )
            self._approvals[thread_id] = record
            return record

    def update_decision(self, thread_id: str, approved: bool, decided_by: Optional[str] = None):
        """Update approval decision."""
        with self._lock:
            if thread_id in self._approvals:
                self._approvals[thread_id].status = "approved" if approved else "rejected"
                self._approvals[thread_id].decision_time = datetime.now(timezone.utc).isoformat()
                self._approvals[thread_id].decided_by = decided_by or "system"

    def get_approvals(
        self, user_id: Optional[str] = None, thread_id: Optional[str] = None, status: Optional[str] = None
    ) -> list[ApprovalRecord]:
        """Get approvals with optional filters."""
        with self._lock:
            results = list(self._approvals.values())

            if user_id:
                results = [r for r in results if r.user_id == user_id]
            if thread_id:
                results = [r for r in results if r.thread_id == thread_id]
            if status:
                results = [r for r in results if r.status == status]

            return results

    def get_approval(self, thread_id: str) -> Optional[ApprovalRecord]:
        """Get a specific approval by thread_id."""
        with self._lock:
            return self._approvals.get(thread_id)


# Global approval tracker instance
approval_tracker = ApprovalTracker()


def create_app(**kwargs) -> FastAPI:
    app = FastAPI(**kwargs)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Use values from BROADIE_ config
    allow_origins = settings.CORS_ORIGINS or ["*"] if settings.DEBUG else settings.CORS_ORIGINS

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    return app


def get_app_with_agent(agent, lifespan=None) -> FastAPI:
    """Create a FastAPI app with agent routes configured.

    This function returns the FastAPI app object, allowing users to:
    - Add custom routes
    - Add custom middleware
    - Extend the API with additional endpoints
    - Modify app configuration

    Args:
        agent: Agent instance to serve
        lifespan: Optional async context manager for app lifecycle

    Returns:
        FastAPI app with agent routes configured

    Example:
        ```python
        from broadie import create_agent
        from broadie.server import get_app_with_agent

        agent = create_agent(name="my_agent", instruction="Be helpful")
        app = get_app_with_agent(agent)

        # Add custom routes
        @app.get("/custom/health")
        async def custom_health():
            return {"status": "custom endpoint working"}

        # Run with uvicorn
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
        ```
    """
    from broadie.a2a.routes import add_a2a_routes

    app = create_app(lifespan=lifespan)
    add_agent_routes(app, agent)
    add_a2a_routes(app, agent)

    return app


class ChatRequest(BaseModel):
    """Request model for chat invocation."""

    message: str
    user_id: Optional[str] = None
    thread_id: Optional[str] = None
    message_id: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Simple approval/rejection request - just needs thread_id."""

    thread_id: str
    reason: Optional[str] = None  # Optional reason for rejection


def add_agent_routes(app: FastAPI, agent):
    path = f"/agent/{agent.id}"

    @app.get("/")
    async def root():
        return {"message": "Welcome to the AI Agent API"}

    @app.get("/health")
    @limiter.limit("30/minute")
    async def global_health(request: Request, response: Response):
        """Global health check endpoint for readiness probes."""
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "auth": {
                "enabled": bool(settings.API_KEYS),
                "keys_configured": len(settings.API_KEYS),
            },
        }

    @app.get(f"{path}/info", dependencies=[Depends(check_credentials)])
    @limiter.limit("10/minute")
    async def info(request: Request, response: Response):
        return agent.get_identity()

    @app.post(f"{path}/invoke", dependencies=[Depends(check_credentials)])
    @limiter.limit("30/minute")
    async def invoke(req: ChatRequest, request: Request, response: Response):
        """
        Invoke the agent with a message.

        Always returns thread_id for tracking conversations and approvals.

        If approval is required, response includes interrupt_data and pending approval record.
        """
        # Generate thread_id if not provided
        if not req.thread_id:
            import uuid

            req.thread_id = str(uuid.uuid4())

        # Run agent
        resp = await agent.run(req.message, req.user_id, req.thread_id, req.message_id)

        # Check if response is an interrupt requiring approval
        if isinstance(resp, dict) and resp.get("status") == "interrupted":
            # Get checkpoint_id from LangGraph state
            checkpoint_id = None
            try:
                config = {"configurable": {"thread_id": req.thread_id}}
                state = await agent.graph.aget_state(config)
                if state and hasattr(state, "config") and state.config:
                    checkpoint_id = state.config.get("configurable", {}).get("checkpoint_id")
            except Exception as e:
                print(f"Could not get checkpoint_id: {e}")

            # Store approval record
            approval_record = approval_tracker.add_approval(
                thread_id=req.thread_id,
                user_id=req.user_id or "anonymous",
                interrupt_data=resp.get("interrupt_data", {}),
                checkpoint_id=checkpoint_id,
            )

            return {
                "agent": agent.id,
                "thread_id": req.thread_id,  # Always return thread_id
                "user_id": req.user_id or "anonymous",
                "status": "interrupted",
                "interrupt_data": resp.get("interrupt_data", {}),
                "approval_record": approval_record.model_dump(),
                "message": "Agent is waiting for approval to proceed.",
                "next_actions": {
                    "approve": f"POST /agent/{agent.id}/approve",
                    "reject": f"POST /agent/{agent.id}/reject",
                    "list_approvals": f"GET /agent/{agent.id}/approvals",
                },
            }

        # Normal response - always include thread_id
        return {
            "agent": agent.id,
            "thread_id": req.thread_id,
            "user_id": req.user_id or "anonymous",
            "status": "completed",
            "response": resp,
        }

    @app.get(f"{path}/approvals", dependencies=[Depends(check_credentials)])
    @limiter.limit("20/minute")
    async def list_approvals(
        request: Request,
        response: Response,
        user_id: Optional[str] = Query(None, description="Filter by user_id"),
        thread_id: Optional[str] = Query(None, description="Filter by thread_id"),
        status: Optional[str] = Query(None, description="Filter by status (pending/approved/rejected)"),
    ):
        """
        List approval requests with optional filters.

        Query parameters:
        - user_id: Filter approvals for specific user
        - thread_id: Get approval for specific thread
        - status: Filter by status (pending/approved/rejected)

        Returns list of approval records with metadata.
        """
        approvals = approval_tracker.get_approvals(user_id=user_id, thread_id=thread_id, status=status)

        return {"agent": agent.id, "count": len(approvals), "approvals": [a.model_dump() for a in approvals]}

    @app.post(f"{path}/approve", dependencies=[Depends(check_credentials)])
    @limiter.limit("30/minute")
    async def approve(req: ApprovalRequest, request: Request, response: Response):
        """
        Approve a pending operation and resume execution.

        Requires thread_id of the interrupted execution.
        Records approval decision with timestamp for audit trail.
        """
        # Check if approval exists
        approval_record = approval_tracker.get_approval(req.thread_id)
        if not approval_record:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "No pending approval found",
                    "thread_id": req.thread_id,
                    "hint": f"Use GET /agent/{agent.id}/approvals to list pending approvals",
                },
            )

        if approval_record.status != "pending":
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Approval already processed",
                    "thread_id": req.thread_id,
                    "status": approval_record.status,
                    "decision_time": approval_record.decision_time,
                },
            )

        # Update approval record
        approval_tracker.update_decision(req.thread_id, approved=True)

        # Resume execution
        resp = await agent.resume(thread_id=req.thread_id, approval=True, feedback="Approved")

        return {
            "agent": agent.id,
            "thread_id": req.thread_id,
            "status": "approved",
            "decision_time": datetime.now(timezone.utc).isoformat(),
            "response": resp,
        }

    @app.post(f"{path}/reject", dependencies=[Depends(check_credentials)])
    @limiter.limit("30/minute")
    async def reject(req: ApprovalRequest, request: Request, response: Response):
        """
        Reject a pending operation and stop execution.

        Requires thread_id of the interrupted execution.
        Optional reason for rejection.
        Records rejection decision with timestamp for audit trail.
        """
        # Check if approval exists
        approval_record = approval_tracker.get_approval(req.thread_id)
        if not approval_record:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "No pending approval found",
                    "thread_id": req.thread_id,
                    "hint": f"Use GET /agent/{agent.id}/approvals to list pending approvals",
                },
            )

        if approval_record.status != "pending":
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Approval already processed",
                    "thread_id": req.thread_id,
                    "status": approval_record.status,
                    "decision_time": approval_record.decision_time,
                },
            )

        # Update approval record
        approval_tracker.update_decision(req.thread_id, approved=False)

        # Resume execution with rejection
        resp = await agent.resume(thread_id=req.thread_id, approval=False, feedback=req.reason or "Rejected by user")

        return {
            "agent": agent.id,
            "thread_id": req.thread_id,
            "status": "rejected",
            "reason": req.reason or "Rejected by user",
            "decision_time": datetime.now(timezone.utc).isoformat(),
            "response": resp,
        }

    @app.get(f"{path}/health")
    @limiter.limit("60/minute")
    async def health(request: Request, response: Response):
        return {"status": "ok", "agent": agent.id}


def add_middlewares(app: FastAPI):
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        try:
            response = await call_next(request)
        except Exception as exc:
            duration = round(time.time() - start_time, 3)
            print(f"❌ {request.method} {request.url} failed after {duration}s: {exc}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "error": str(exc)},
            )
        duration = round(time.time() - start_time, 3)
        print(f"✅ {request.method} {request.url} completed in {duration}s")
        return response

    @app.middleware("http")
    async def restrict_hosts(request: Request, call_next):
        allow_hosts = settings.ALLOWED_HOSTS or ["localhost", "0.0.0.0"]
        host = request.headers.get("host", "").split(":")[0]
        if host not in allow_hosts and not settings.DEBUG:
            return JSONResponse(status_code=403, content={"detail": "Host not allowed"})
        return await call_next(request)
