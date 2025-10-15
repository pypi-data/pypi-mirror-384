"""
Repository layer for Broadie persistence.

Provides the same interface as the current PersistenceMixin while using
SQLAlchemy for robust database storage. Maintains backward compatibility.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, NamedTuple, Optional

from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .database import get_db_session
from .models import Checkpoint, Message, Thread, UserFact

logger = logging.getLogger(__name__)


class ThreadHistoryItem(NamedTuple):
    """Structure to match current PersistenceMixin return format."""

    key: str
    value: Dict[str, Any]


class PersistenceRepository:
    """
    Repository that maintains the current PersistenceMixin interface
    while using SQLAlchemy for storage.
    """

    def __init__(self, decay_minutes: int = 1440):  # 24 hours default
        self.decay_minutes = decay_minutes

    # ------------------------
    # Thread History Methods (maintains compatibility)
    # ------------------------

    async def save_thread_message(self, thread_id: str, message: Dict[str, Any]) -> str:
        """
        Save a message to a thread. Maintains compatibility with current interface.

        Args:
            thread_id: Thread identifier
            message: Message data dict with role, content, user_id, etc.

        Returns:
            Message ID
        """
        async with get_db_session() as session:
            # Ensure thread exists
            await self._ensure_thread_exists(session, thread_id, message.get("user_id"))

            # Create message record
            message_record = Message(
                thread_id=thread_id,
                message_id=message.get("message_id", str(uuid.uuid4())),
                role=message.get("role", "user"),
                content=message.get("content", ""),
                user_id=message.get("user_id"),
                agent_id=message.get("agent_id"),
                run_id=message.get("run_id"),
                structured_response=message.get("structured_response"),
                tool_calls=message.get("tool_calls"),
                processing_time_ms=message.get("processing_time_ms"),
                token_count=message.get("token_count"),
                extra_data=message.get("metadata", {}),  # Map metadata to extra_data
            )

            session.add(message_record)
            await session.commit()

            logger.debug(f"Saved message {message_record.message_id} to thread {thread_id}")
            return message_record.message_id

    async def get_thread_history(self, thread_id: str, limit: int = 50) -> List[ThreadHistoryItem]:
        """
        Get thread history in the same format as current PersistenceMixin.

        Args:
            thread_id: Thread identifier
            limit: Maximum number of messages to return

        Returns:
            List of ThreadHistoryItem matching current interface
        """
        async with get_db_session() as session:
            # Get messages ordered by creation time
            stmt = select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at).limit(limit)

            result = await session.execute(stmt)
            messages = result.scalars().all()

            # Convert to format expected by current code
            history_items = []
            for msg in messages:
                # Filter out expired messages based on decay_minutes
                if self._is_expired(msg.created_at):
                    continue

                # Format to match current interface
                value = {
                    "role": msg.role,
                    "content": msg.content,
                    "message_id": msg.message_id,
                    "user_id": msg.user_id,
                    "agent_id": msg.agent_id,
                    "run_id": msg.run_id,
                    "structured_response": msg.structured_response,
                    "tool_calls": msg.tool_calls,
                    "processing_time_ms": msg.processing_time_ms,
                    "token_count": msg.token_count,
                    "_created_at": msg.created_at.isoformat(),
                    **(msg.extra_data or {}),  # Use extra_data instead of metadata
                }

                history_items.append(ThreadHistoryItem(key=msg.message_id, value=value))

            return history_items

    async def clear_thread_history(self, thread_id: str) -> int:
        """
        Clear all messages from a thread.

        Args:
            thread_id: Thread identifier

        Returns:
            Number of messages deleted
        """
        async with get_db_session() as session:
            stmt = delete(Message).where(Message.thread_id == thread_id)
            result = await session.execute(stmt)
            await session.commit()

            deleted_count = result.rowcount
            logger.info(f"Cleared {deleted_count} messages from thread {thread_id}")
            return deleted_count

    # ------------------------
    # User Profile Methods (maintains compatibility)
    # ------------------------

    async def remember_user_fact(self, user_id: str, fact: Dict[str, Any]) -> str:
        """
        Store a user fact for long-term memory.

        Args:
            user_id: User identifier
            fact: Fact data

        Returns:
            Fact ID
        """
        async with get_db_session() as session:
            fact_record = UserFact(
                user_id=user_id,
                fact_id=str(uuid.uuid4()),
                fact_data=fact,
                fact_type=fact.get("type"),
                importance_score=fact.get("importance", 1.0),
                extra_data=fact.get("metadata", {}),  # Map metadata to extra_data
            )

            session.add(fact_record)
            await session.commit()

            logger.debug(f"Remembered fact {fact_record.fact_id} for user {user_id}")
            return fact_record.fact_id

    async def recall_user_facts(self, user_id: str, query: str, limit: int = 3) -> List[ThreadHistoryItem]:
        """
        Recall user facts (basic text search for now).

        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum results

        Returns:
            List of matching facts in ThreadHistoryItem format
        """
        async with get_db_session() as session:
            # Basic text search - can be enhanced with vector search later
            stmt = (
                select(UserFact)
                .where(UserFact.user_id == user_id, func.json_extract(UserFact.fact_data, "$").like(f"%{query}%"))
                .order_by(desc(UserFact.importance_score), desc(UserFact.created_at))
                .limit(limit)
            )

            result = await session.execute(stmt)
            facts = result.scalars().all()

            # Convert to ThreadHistoryItem format for compatibility
            fact_items = []
            for fact in facts:
                fact_items.append(ThreadHistoryItem(key=fact.fact_id, value=fact.fact_data))

            return fact_items

    async def clear_user_facts(self, user_id: str) -> int:
        """
        Clear all facts for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of facts deleted
        """
        async with get_db_session() as session:
            stmt = delete(UserFact).where(UserFact.user_id == user_id)
            result = await session.execute(stmt)
            await session.commit()

            deleted_count = result.rowcount
            logger.info(f"Cleared {deleted_count} facts for user {user_id}")
            return deleted_count

    # ------------------------
    # Checkpoint Methods (new functionality for LangGraph state)
    # ------------------------

    async def save_checkpoint(
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
            checkpoint_type: Type of checkpoint (llm_call, tool_call, etc.)
            state_data: Serialized state data
            message_id: Associated message ID
            agent_id: Agent identifier
            run_id: Run identifier
            metadata: Additional metadata

        Returns:
            Checkpoint ID
        """
        async with get_db_session() as session:
            # Get next sequence number for this thread
            seq_stmt = select(func.coalesce(func.max(Checkpoint.sequence_number), 0) + 1).where(
                Checkpoint.thread_id == thread_id
            )
            seq_result = await session.execute(seq_stmt)
            sequence_number = seq_result.scalar()

            checkpoint = Checkpoint(
                thread_id=thread_id,
                checkpoint_id=str(uuid.uuid4()),
                checkpoint_type=checkpoint_type,
                state_data=state_data,
                message_id=message_id,
                agent_id=agent_id,
                run_id=run_id,
                sequence_number=sequence_number,
                extra_data=metadata or {},  # Map metadata to extra_data
            )

            session.add(checkpoint)
            await session.commit()

            logger.debug(f"Saved checkpoint {checkpoint.checkpoint_id} for thread {thread_id}")
            return checkpoint.checkpoint_id

    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest checkpoint for a thread.

        Args:
            thread_id: Thread identifier

        Returns:
            Latest checkpoint data or None
        """
        async with get_db_session() as session:
            stmt = (
                select(Checkpoint)
                .where(Checkpoint.thread_id == thread_id)
                .order_by(desc(Checkpoint.sequence_number))
                .limit(1)
            )

            result = await session.execute(stmt)
            checkpoint = result.scalar_one_or_none()

            if checkpoint:
                return {
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "checkpoint_type": checkpoint.checkpoint_type,
                    "state_data": checkpoint.state_data,
                    "sequence_number": checkpoint.sequence_number,
                    "created_at": checkpoint.created_at.isoformat(),
                    "metadata": checkpoint.extra_data,  # Map extra_data back to metadata for compatibility
                }

            return None

    async def get_checkpoints_by_type(
        self, thread_id: str, checkpoint_type: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get checkpoints of a specific type for a thread.

        Args:
            thread_id: Thread identifier
            checkpoint_type: Type of checkpoint to retrieve
            limit: Maximum results

        Returns:
            List of checkpoint data
        """
        async with get_db_session() as session:
            stmt = (
                select(Checkpoint)
                .where(Checkpoint.thread_id == thread_id, Checkpoint.checkpoint_type == checkpoint_type)
                .order_by(desc(Checkpoint.sequence_number))
                .limit(limit)
            )

            result = await session.execute(stmt)
            checkpoints = result.scalars().all()

            return [
                {
                    "checkpoint_id": cp.checkpoint_id,
                    "checkpoint_type": cp.checkpoint_type,
                    "state_data": cp.state_data,
                    "sequence_number": cp.sequence_number,
                    "created_at": cp.created_at.isoformat(),
                    "message_id": cp.message_id,
                    "run_id": cp.run_id,
                    "metadata": cp.extra_data,  # Map extra_data back to metadata for compatibility
                }
                for cp in checkpoints
            ]

    # ------------------------
    # Enhanced Analytics Methods (new capabilities)
    # ------------------------

    async def get_thread_analytics(self, thread_id: str) -> Dict[str, Any]:
        """
        Get analytics for a specific thread.

        Args:
            thread_id: Thread identifier

        Returns:
            Thread analytics data
        """
        async with get_db_session() as session:
            # Get thread with related data
            stmt = (
                select(Thread)
                .options(selectinload(Thread.messages), selectinload(Thread.checkpoints))
                .where(Thread.id == thread_id)
            )

            result = await session.execute(stmt)
            thread = result.scalar_one_or_none()

            if not thread:
                return {}

            # Calculate analytics
            messages = thread.messages
            user_messages = [m for m in messages if m.role == "user"]
            assistant_messages = [m for m in messages if m.role == "assistant"]

            total_tokens = sum(m.token_count or 0 for m in messages)
            avg_processing_time = sum(m.processing_time_ms or 0 for m in assistant_messages)
            if assistant_messages:
                avg_processing_time /= len(assistant_messages)

            return {
                "thread_id": thread_id,
                "user_id": thread.user_id,
                "created_at": thread.created_at.isoformat(),
                "is_active": thread.is_active,
                "total_messages": len(messages),
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "total_tokens": total_tokens,
                "avg_processing_time_ms": avg_processing_time,
                "total_checkpoints": len(thread.checkpoints),
                "agent_id": thread.agent_id,
            }

    async def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """
        Get analytics for a specific user across all threads.

        Args:
            user_id: User identifier

        Returns:
            User analytics data
        """
        async with get_db_session() as session:
            # Get threads count
            threads_stmt = select(func.count(Thread.id)).where(Thread.user_id == user_id)
            threads_result = await session.execute(threads_stmt)
            thread_count = threads_result.scalar()

            # Get messages count
            messages_stmt = select(func.count(Message.id)).where(Message.user_id == user_id)
            messages_result = await session.execute(messages_stmt)
            message_count = messages_result.scalar()

            # Get user facts count
            facts_stmt = select(func.count(UserFact.id)).where(UserFact.user_id == user_id)
            facts_result = await session.execute(facts_stmt)
            facts_count = facts_result.scalar()

            return {
                "user_id": user_id,
                "total_threads": thread_count,
                "total_messages": message_count,
                "total_facts": facts_count,
            }

    # ------------------------
    # Helper Methods
    # ------------------------

    async def _ensure_thread_exists(
        self, session: AsyncSession, thread_id: str, user_id: Optional[str] = None
    ) -> Thread:
        """Ensure a thread exists, create if it doesn't."""
        stmt = select(Thread).where(Thread.id == thread_id)
        result = await session.execute(stmt)
        thread = result.scalar_one_or_none()

        if not thread:
            thread = Thread(id=thread_id, user_id=user_id or "anonymous", is_active=True)
            session.add(thread)
            await session.flush()  # Flush to get the ID

        return thread

    def _is_expired(self, created_at: datetime) -> bool:
        """Check if a record is expired based on decay_minutes."""
        if not created_at:
            return False

        # Ensure created_at is timezone-aware
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age_minutes = (now - created_at).total_seconds() / 60
        return age_minutes > self.decay_minutes
