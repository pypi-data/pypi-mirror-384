"""
SQLAlchemy Models for Broadie Persistence

Base models and tables for storing conversations, messages, and agent state.
Designed to work with any SQLAlchemy-supported database.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields for all tables."""

    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="Primary key UUID"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        comment="Record last update timestamp",
    )


class Thread(BaseModel):
    """
    Conversation threads (conversations).
    One user can have many threads, one thread has many messages.
    """

    __tablename__ = "threads"

    # External user identifier (no user table, provided by external system)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="External user identifier")

    # Thread metadata
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Optional thread title")

    # Thread status and configuration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="Whether thread is active")

    # Agent configuration for this thread
    agent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Associated agent identifier")

    # Additional metadata as JSON (renamed from metadata to avoid SQLAlchemy conflict)
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Additional thread metadata"
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="thread", cascade="all, delete-orphan", order_by="Message.created_at"
    )

    checkpoints: Mapped[list["Checkpoint"]] = relationship(
        "Checkpoint", back_populates="thread", cascade="all, delete-orphan", order_by="Checkpoint.created_at.desc()"
    )

    # Indexes for performance
    __table_args__ = (
        Index("ix_threads_user_id_created", "user_id", "created_at"),
        Index("ix_threads_agent_id", "agent_id"),
        Index("ix_threads_is_active", "is_active"),
    )


class Message(BaseModel):
    """
    Individual messages within threads.
    Stores both user messages and agent responses.
    """

    __tablename__ = "messages"

    # Foreign key to thread
    thread_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to parent thread",
    )

    # Message identification
    message_id: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()), comment="Unique message identifier"
    )

    # Message content and metadata
    role: Mapped[str] = mapped_column(String(50), nullable=False, comment="Message role: user, assistant, system, tool")

    content: Mapped[str] = mapped_column(Text, nullable=False, comment="Message content")

    # User identification (for user messages)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, comment="External user identifier for user messages"
    )

    # Agent identification (for assistant messages)
    agent_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Agent identifier for assistant messages"
    )

    # Run identification for tracing
    run_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, comment="Run identifier for agent execution tracing"
    )

    # Structured response data (for agent outputs)
    structured_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Structured response data from agents"
    )

    # Tool execution data
    tool_calls: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Tool calls made during message processing"
    )

    # Additional metadata (renamed from metadata to avoid SQLAlchemy conflict)
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Additional message metadata"
    )

    # Performance and analytics
    processing_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Processing time in milliseconds"
    )

    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Token count for this message")

    # Relationships
    thread: Mapped[Thread] = relationship("Thread", back_populates="messages")

    # Indexes for performance
    __table_args__ = (
        Index("ix_messages_thread_id_created", "thread_id", "created_at"),
        Index("ix_messages_role", "role"),
        Index("ix_messages_user_id", "user_id"),
        Index("ix_messages_agent_id", "agent_id"),
        Index("ix_messages_run_id", "run_id"),
        Index("ix_messages_message_id", "message_id"),
    )


class Checkpoint(BaseModel):
    """
    LangGraph state checkpoints for conversation state management.
    Stores agent state after LLM calls and tool executions.
    """

    __tablename__ = "checkpoints"

    # Foreign key to thread
    thread_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to parent thread",
    )

    # Checkpoint identification
    checkpoint_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique checkpoint identifier",
    )

    # Checkpoint metadata
    checkpoint_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Type of checkpoint: llm_call, tool_call, user_input, etc."
    )

    # State data
    state_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, comment="Serialized LangGraph state data")

    # Associated message (if applicable)
    message_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("messages.message_id"), nullable=True, comment="Associated message identifier"
    )

    # Agent and run identification
    agent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Agent identifier")

    run_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, comment="Run identifier for tracing")

    # Checkpoint sequence for ordering
    sequence_number: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Sequence number within thread"
    )

    # Additional metadata (renamed from metadata to avoid SQLAlchemy conflict)
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Additional checkpoint metadata"
    )

    # Relationships
    thread: Mapped[Thread] = relationship("Thread", back_populates="checkpoints")

    # Indexes for performance
    __table_args__ = (
        Index("ix_checkpoints_thread_id_sequence", "thread_id", "sequence_number"),
        Index("ix_checkpoints_type", "checkpoint_type"),
        Index("ix_checkpoints_message_id", "message_id"),
        Index("ix_checkpoints_run_id", "run_id"),
    )


class UserFact(BaseModel):
    """
    User profile facts for long-term memory.
    Replaces the current store-based user facts system.
    """

    __tablename__ = "user_facts"

    # User identification
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="External user identifier")

    # Fact identification
    fact_id: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()), comment="Unique fact identifier"
    )

    # Fact content
    fact_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, comment="Fact content and metadata")

    # Fact category/type
    fact_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="Type or category of fact")

    # Embedding for semantic search (stored as JSON array)
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        JSON, nullable=True, comment="Vector embedding for semantic search"
    )

    # Fact importance/weight
    importance_score: Mapped[Optional[float]] = mapped_column(
        nullable=True, comment="Importance score for fact ranking"
    )

    # Expiration (if applicable)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Optional expiration timestamp"
    )

    # Additional metadata (renamed from metadata to avoid SQLAlchemy conflict)
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Additional fact metadata"
    )

    # Indexes for performance
    __table_args__ = (
        Index("ix_user_facts_user_id_created", "user_id", "created_at"),
        Index("ix_user_facts_fact_type", "fact_type"),
        Index("ix_user_facts_importance", "importance_score"),
        Index("ix_user_facts_expires", "expires_at"),
    )
