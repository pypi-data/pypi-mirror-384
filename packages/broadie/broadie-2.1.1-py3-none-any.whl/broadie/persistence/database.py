"""
Database session management for Broadie persistence.

Provides database connection management and session handling
for any SQLAlchemy-supported database.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from broadie.config import settings

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Universal database manager that works with any SQLAlchemy-supported database.
    Handles both sync and async operations with proper connection pooling.
    """

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.DATABASE_URL
        self.async_engine: Optional[AsyncEngine] = None
        self.async_session_factory: Optional[async_sessionmaker] = None
        self._initialized = False

    def _get_async_url(self, url: str) -> str:
        """Convert database URL to async version if needed."""
        if not url:
            # Default to SQLite in-memory for testing
            return "sqlite+aiosqlite:///:memory:"

        # Handle different database types
        if url.startswith("sqlite://"):
            return url.replace("sqlite://", "sqlite+aiosqlite://")
        elif url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://")
        elif url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://")
        elif url.startswith("mysql://"):
            return url.replace("mysql://", "mysql+aiomysql://")
        elif url.startswith("oracle://"):
            return url.replace("oracle://", "oracle+cx_oracle_async://")
        else:
            # Assume it's already an async URL
            return url

    def _configure_sqlite_engine(self, engine: AsyncEngine) -> None:
        """Configure SQLite-specific settings."""

        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            # Enable foreign key constraints
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            # Optimize for performance
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()

    async def initialize(self) -> None:
        """Initialize the database connection and create tables if needed."""
        if self._initialized:
            return

        try:
            async_url = self._get_async_url(self.database_url)
            logger.info(f"Initializing database with URL: {async_url.split('@')[0]}@...")

            # For file-based SQLite, ensure the directory exists
            if "sqlite" in async_url and "memory" not in async_url:
                from pathlib import Path

                # Extract the file path from the URL
                db_path = async_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
                if db_path and db_path != ":memory:":
                    # Create parent directory if it doesn't exist
                    db_file = Path(db_path)
                    db_file.parent.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Ensured database directory exists: {db_file.parent}")

            # Configure engine based on database type
            if "sqlite" in async_url:
                # SQLite configuration
                self.async_engine = create_async_engine(
                    async_url,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 30,
                    },
                    echo=settings.DATABASE_ECHO,
                    future=True,
                )
                self._configure_sqlite_engine(self.async_engine)

            else:
                # PostgreSQL, MySQL, etc.
                self.async_engine = create_async_engine(
                    async_url,
                    pool_size=settings.DATABASE_POOL_SIZE or 10,
                    max_overflow=settings.DATABASE_MAX_OVERFLOW or 20,
                    pool_timeout=30,
                    pool_recycle=3600,
                    echo=settings.DATABASE_ECHO,
                    future=True,
                )

            # Create session factory
            self.async_session_factory = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            # Create tables
            await self.create_tables()

            self._initialized = True
            logger.info("Database initialization completed successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def create_tables(self) -> None:
        """Create all tables if they don't exist."""
        if not self.async_engine:
            raise RuntimeError("Database not initialized")

        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created/verified")

    async def drop_tables(self) -> None:
        """Drop all tables (useful for testing)."""
        if not self.async_engine:
            raise RuntimeError("Database not initialized")

        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.info("Database tables dropped")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session with proper error handling."""
        if not self._initialized:
            await self.initialize()

        if not self.async_session_factory:
            raise RuntimeError("Database not properly initialized")

        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """Close database connections."""
        if self.async_engine:
            await self.async_engine.dispose()
            logger.info("Database connections closed")

    async def health_check(self) -> bool:
        """Check database connection health."""
        try:
            async with self.get_session() as session:
                await session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get or create the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Convenience function to get a database session."""
    db_manager = get_database_manager()
    async with db_manager.get_session() as session:
        yield session


async def initialize_database() -> None:
    """Initialize the global database manager."""
    db_manager = get_database_manager()
    await db_manager.initialize()


async def close_database() -> None:
    """Close the global database manager."""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None
