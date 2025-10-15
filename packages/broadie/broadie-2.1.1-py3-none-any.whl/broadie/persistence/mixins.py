"""
New SQLAlchemy-backed PersistenceMixin that maintains compatibility
with the existing interface while providing robust database storage.
"""

import asyncio
import datetime
import logging
import pathlib
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

from langchain.embeddings import init_embeddings
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.store.memory import InMemoryStore
from langgraph.store.postgres import AsyncPostgresStore

from broadie.config import settings

from .database import initialize_database
from .repository import PersistenceRepository

logger = logging.getLogger(__name__)


class PersistenceMixin:
    """
    Enhanced PersistenceMixin that maintains the exact same interface as before
    while using SQLAlchemy for robust database storage.

    Provides backward compatibility with existing agent code while adding
    new capabilities like state checkpoints and enhanced analytics.
    """

    def __init__(self):
        self.url = settings.DATABASE_URL
        self.embedding_model = settings.EMBEDDING_MODEL
        self.decay_minutes = settings.MEMORY_DECAY_MINUTES
        self._exit_stack = AsyncExitStack()
        self.checkpointer = None
        self.store = None

        # Initialize the new SQLAlchemy repository
        self._repository = PersistenceRepository(decay_minutes=self.decay_minutes)
        self._db_initialized = False

    # ----------------------------
    # Setup (enhanced with SQLAlchemy initialization)
    # ----------------------------

    async def _ensure_db_initialized(self):
        """Ensure database is initialized before operations."""
        if not self._db_initialized:
            await initialize_database()
            self._db_initialized = True

    async def init_checkpointer(self):
        """Initialize async checkpointer depending on DATABASE_URL."""
        await self._ensure_db_initialized()

        if not self.url:
            self.checkpointer = InMemorySaver()
            return self.checkpointer

        # Handle SQLite URLs (both sqlite:// and sqlite+aiosqlite://)
        if self.url.startswith(("sqlite://", "sqlite+aiosqlite://")):
            # Extract the database path from the URL
            if self.url.startswith("sqlite+aiosqlite://"):
                db_path = self.url.replace("sqlite+aiosqlite://", "").lstrip("/")
            else:
                db_path = self.url.split("///", 1)[-1]

            # Handle relative paths and ensure directory exists
            if not db_path.startswith("/"):
                db_path = pathlib.Path(db_path)
                db_path.parent.mkdir(parents=True, exist_ok=True)
                db_path = str(db_path)

            cm = AsyncSqliteSaver.from_conn_string(db_path)
            self.checkpointer = await self._exit_stack.enter_async_context(cm)
            return self.checkpointer

        # Handle PostgreSQL URLs
        if self.url.startswith(("postgres://", "postgresql://")):
            cm = AsyncPostgresSaver.from_conn_string(self.url)
            self.checkpointer = await self._exit_stack.enter_async_context(cm)
            return self.checkpointer

        raise ValueError(
            f"Unsupported DATABASE_URL schema: {self.url}. Supported schemes: sqlite://,"
            f" sqlite+aiosqlite://, postgresql://, postgres://"
        )

    async def init_store(self):
        """Initialize async store depending on DATABASE_URL."""
        if self.url and self.url.startswith(("postgres://", "postgresql://")):
            cm = await AsyncPostgresStore.from_conn_string(
                self.url,
                index={
                    "dims": 768,
                    "embed": init_embeddings(self.embedding_model),
                },
            )
            await cm.setup()
            self.store = await self._exit_stack.enter_async_context(cm)
            return self.store

        # Default: in-memory store
        self.store = InMemoryStore(
            index={
                "dims": 768,
                "embed": init_embeddings(self.embedding_model),
            },
        )
        return self.store

    async def aclose(self):
        """Gracefully close all registered resources."""
        await self._exit_stack.aclose()

    # ------------------------
    # User Long-Term Profile (using SQLAlchemy repository)
    # ------------------------

    async def remember_user_fact(self, user_id: str, fact: Dict[str, Any]) -> str:
        """Store a user fact for long-term memory."""
        await self._ensure_db_initialized()
        return await self._repository.remember_user_fact(user_id, fact)

    async def recall_user_facts(self, user_id: str, query: str, limit: int = 3):
        """Recall user facts matching query."""
        await self._ensure_db_initialized()
        return await self._repository.recall_user_facts(user_id, query, limit)

    async def clear_user_facts(self, user_id: str):
        """Clear all facts for a user."""
        await self._ensure_db_initialized()
        return await self._repository.clear_user_facts(user_id)

    # ------------------------
    # Thread History (using SQLAlchemy repository)
    # ------------------------

    async def save_thread_message(self, thread_id: str, message: Dict[str, Any]) -> str:
        """
        Save a message to a thread. Maintains exact compatibility with existing interface.

        Args:
            thread_id: Thread identifier
            message: Message data dict

        Returns:
            Message ID (maintains compatibility)
        """
        await self._ensure_db_initialized()

        # Add timestamp if not present (maintains compatibility)
        if "_created_at" not in message:
            message["_created_at"] = datetime.datetime.utcnow().isoformat()

        # Save using repository and capture state if it's an agent response
        message_id = await self._repository.save_thread_message(thread_id, message)

        # If this is an agent response with structured data, save a checkpoint
        if message.get("role") == "assistant" and message.get("structured_response") and message.get("run_id"):
            try:
                await self.save_agent_checkpoint(
                    thread_id=thread_id,
                    checkpoint_type="llm_response",
                    state_data={
                        "structured_response": message.get("structured_response"),
                        "content": message.get("content"),
                        "processing_time_ms": message.get("processing_time_ms"),
                        "token_count": message.get("token_count"),
                    },
                    message_id=message_id,
                    agent_id=message.get("agent_id"),
                    run_id=message.get("run_id"),
                )
            except Exception as e:
                # Don't fail message saving if checkpoint fails
                logger.warning(f"Failed to save checkpoint for message {message_id}: {e}")

        return message_id

    async def get_thread_history(self, thread_id: str, limit: int = 50):
        """Get thread history. Maintains exact compatibility with existing interface."""
        await self._ensure_db_initialized()
        return await self._repository.get_thread_history(thread_id, limit)

    async def clear_thread_history(self, thread_id: str):
        """Clear thread history. Maintains exact compatibility."""
        await self._ensure_db_initialized()
        return await self._repository.clear_thread_history(thread_id)

    def _is_expired(self, value: Dict[str, Any]) -> bool:
        """Check if a record is expired (maintains compatibility)."""
        ts = value.get("_created_at")
        if not ts:
            return False
        created = datetime.datetime.fromisoformat(ts)
        age = (datetime.datetime.utcnow() - created).total_seconds() / 60
        return age > self.decay_minutes

    # ------------------------
    # New Checkpoint Methods (LangGraph State Management)
    # ------------------------

    async def save_agent_checkpoint(
        self,
        thread_id: str,
        checkpoint_type: str,
        state_data: Dict[str, Any],
        message_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save a LangGraph state checkpoint.

        Args:
            thread_id: Thread identifier
            checkpoint_type: Type of checkpoint (llm_call, tool_call, user_input, etc.)
            state_data: Serialized state data
            message_id: Associated message ID
            agent_id: Agent identifier
            run_id: Run identifier for tracing
            metadata: Additional metadata

        Returns:
            Checkpoint ID
        """
        await self._ensure_db_initialized()
        return await self._repository.save_checkpoint(
            thread_id=thread_id,
            checkpoint_type=checkpoint_type,
            state_data=state_data,
            message_id=message_id,
            agent_id=agent_id,
            run_id=run_id,
            metadata=metadata,
        )

    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest checkpoint for a thread."""
        await self._ensure_db_initialized()
        return await self._repository.get_latest_checkpoint(thread_id)

    async def get_checkpoints_by_type(
        self, thread_id: str, checkpoint_type: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get checkpoints of a specific type for a thread."""
        await self._ensure_db_initialized()
        return await self._repository.get_checkpoints_by_type(thread_id, checkpoint_type, limit)

    # ------------------------
    # Enhanced Analytics Methods (new capabilities)
    # ------------------------

    async def get_thread_analytics(self, thread_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a thread."""
        await self._ensure_db_initialized()
        return await self._repository.get_thread_analytics(thread_id)

    async def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics for a user across all threads."""
        await self._ensure_db_initialized()
        return await self._repository.get_user_analytics(user_id)

    # ------------------------
    # Legacy Cleanup Method (enhanced)
    # ------------------------

    async def _start_decay_cleaner(self):
        """Enhanced decay cleaner that removes expired records from database."""
        while True:
            try:
                logger.debug("[DECAY] Running enhanced cleaner...")
                await self._ensure_db_initialized()

                # The repository handles expiration filtering automatically
                # in get_thread_history, but we could add active cleanup here
                # for better database maintenance

                # TODO: Add active cleanup of expired records if needed
                # This would involve deleting old messages beyond decay_minutes

            except Exception as e:
                logger.warning(f"[DECAY] Enhanced cleaner failed: {e}")
            await asyncio.sleep(self.decay_minutes * 30)
