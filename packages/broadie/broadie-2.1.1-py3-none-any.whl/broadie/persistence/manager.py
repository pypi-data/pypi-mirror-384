"""Persistence manager for checkpointer and store initialization."""

import logging
import os
import re
from pathlib import Path

from broadie.config import settings

logger = logging.getLogger(__name__)


class PersistenceManager:
    """Manages checkpointer (short-term) and store (long-term) for agents.

    Each agent should own its own PersistenceManager instance for proper
    lifecycle management and resource cleanup. This eliminates global state
    and makes testing easier.

    Usage:
        persistence = PersistenceManager(database_url="sqlite:///agent.db")
        await persistence.initialize()
        # Use persistence.checkpointer and persistence.store
        await persistence.close()  # Cleanup when done
    """

    def __init__(self, database_url: str = None, use_memory: bool = None):
        self.database_url = database_url or settings.DATABASE_URL

        # Validate DATABASE_URL format
        self._validate_database_url()

        # If use_memory is explicitly set, respect it; otherwise check environment
        if use_memory is not None:
            self.use_memory = use_memory
        else:
            self.use_memory = os.getenv("CI") == "true" or settings.ENV == "test"

        self._checkpointer = None
        self._store = None
        self._is_sqlite = self._detect_sqlite()
        self._connections = []  # Track connections for cleanup
        logger.info(
            f"PersistenceManager initialized: use_memory={self.use_memory}, is_sqlite={self._is_sqlite}, "
            f"url={self._mask_password(self.database_url)}"
        )

    def _validate_database_url(self) -> None:
        """Validate DATABASE_URL format and accessibility."""
        if not self.database_url:
            raise ValueError("DATABASE_URL is required but not configured")

        # Check for valid URL scheme
        valid_schemes = ["sqlite", "sqlite+aiosqlite", "postgresql", "postgresql+asyncpg"]
        url_lower = self.database_url.lower()

        if not any(url_lower.startswith(scheme + "://") for scheme in valid_schemes):
            raise ValueError(f"Invalid DATABASE_URL scheme. Must start with one of: {', '.join(valid_schemes)}")

        # Validate PostgreSQL URL format
        if url_lower.startswith("postgresql"):
            postgres_pattern = r"postgresql(?:\+asyncpg)?://[^:]+:[^@]+@[^:/]+:\d+/.+"
            if not re.match(postgres_pattern, self.database_url):
                logger.warning(
                    "PostgreSQL URL may be malformed. Expected format: postgresql://user:password@host:port/database"
                )

    def _mask_password(self, url: str) -> str:
        """Mask password in database URL for logging."""
        if "@" in url:
            pattern = r"://([^:]+):([^@]+)@"
            return re.sub(pattern, r"://\1:****@", url)
        return url

    def _detect_sqlite(self) -> bool:
        """Detect if database URL is SQLite."""
        return self.database_url.startswith("sqlite")

    def _extract_sqlite_path(self, database_url: str) -> str:
        """Extract SQLite file path from database URL."""
        original_url = database_url
        url = database_url

        # Remove SQLite prefixes
        if url.startswith("sqlite+aiosqlite://"):
            url = url[19:]  # len("sqlite+aiosqlite://") = 19
        elif url.startswith("sqlite://"):
            url = url[9:]  # len("sqlite://") = 9

        # After removing prefix:
        # "//path" -> absolute path (keep one slash: "/path")
        # "/path" -> relative or absolute depending on context
        # "path" -> relative path

        # If we have multiple leading slashes, it's typically meant to be relative
        # sqlite:///file.db should become ./file.db (relative in current dir)
        # sqlite:////file.db should become /file.db (absolute)

        if url.startswith("//"):
            # Two slashes after prefix = relative in current directory
            url = url[2:]
        elif url.startswith("/") and not url.startswith("//"):
            # Single slash - check if it looks like an absolute path or just a filename
            # If it's just a filename (no directory separators after first char), treat as relative
            if "/" not in url[1:]:
                # Just a filename like "/file.db" -> treat as relative
                url = url[1:]

        # Convert to Path object - resolve relative to current working directory
        path_obj = Path(url)

        # If it's a relative path, resolve it relative to current working directory first
        if not path_obj.is_absolute():
            path_obj = Path.cwd() / path_obj

        # Create parent directory if needed (now we have absolute path)
        if path_obj.parent and path_obj.parent != Path("/"):
            try:
                path_obj.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.error(f"Failed to create directory {path_obj.parent}: {e}")
                raise

        resolved_path = str(path_obj)
        logger.info(f"Extracted SQLite path: {original_url} -> {resolved_path}")

        return resolved_path

    async def get_checkpointer(self):
        """Get checkpointer for thread-level conversation history."""
        if self.use_memory:
            from langgraph.checkpoint.memory import MemorySaver

            logger.info("Using in-memory checkpointer")
            return MemorySaver()

        if self._is_sqlite:
            import aiosqlite
            from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

            db_path = self._extract_sqlite_path(self.database_url)
            logger.info(f"Using SQLite checkpointer: {db_path}")

            try:
                # Create connection and checkpointer
                conn = await aiosqlite.connect(db_path)
                self._connections.append(conn)
                checkpointer = AsyncSqliteSaver(conn)
                await checkpointer.setup()
                logger.info("SQLite checkpointer initialized successfully")
                return checkpointer
            except Exception as e:
                logger.error(f"Failed to initialize SQLite checkpointer: {e}")
                raise ConnectionError(f"Cannot connect to SQLite database at {db_path}: {e}")
        else:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            from psycopg import AsyncConnection

            logger.info(f"Using PostgreSQL checkpointer: {self._mask_password(self.database_url)}")

            try:
                # Create connection with autocommit to allow CREATE INDEX CONCURRENTLY
                conn = await AsyncConnection.connect(self.database_url)
                await conn.set_autocommit(True)
                self._connections.append(conn)

                checkpointer = AsyncPostgresSaver(conn)
                await checkpointer.setup()
                logger.info("PostgreSQL checkpointer initialized successfully")
                return checkpointer
            except Exception as e:
                logger.error(f"Failed to initialize PostgreSQL checkpointer: {e}")
                raise ConnectionError(f"Cannot connect to PostgreSQL database: {e}")

    async def get_store(self):
        """Get store for cross-thread long-term memory."""
        if self.use_memory:
            from langgraph.store.memory import InMemoryStore

            logger.info("Using in-memory store")
            return InMemoryStore()

        if self._is_sqlite:
            # SQLite doesn't have a store implementation yet, use in-memory for now
            from langgraph.store.memory import InMemoryStore

            logger.warning("SQLite store not available, using in-memory store")
            return InMemoryStore()
        else:
            from langgraph.store.postgres import AsyncPostgresStore
            from psycopg import AsyncConnection

            logger.info(f"Using PostgreSQL store: {self._mask_password(self.database_url)}")

            try:
                # Create connection with autocommit to allow CREATE INDEX CONCURRENTLY
                conn = await AsyncConnection.connect(self.database_url)
                await conn.set_autocommit(True)
                self._connections.append(conn)

                store = AsyncPostgresStore(conn)
                await store.setup()
                logger.info("PostgreSQL store initialized successfully")
                return store
            except Exception as e:
                logger.error(f"Failed to initialize PostgreSQL store: {e}")
                raise ConnectionError(f"Cannot connect to PostgreSQL database: {e}")

    async def initialize(self):
        """Initialize persistence resources asynchronously."""
        if not self._checkpointer:
            self._checkpointer = await self.get_checkpointer()
        if not self._store:
            self._store = await self.get_store()

    @property
    def checkpointer(self):
        if not self._checkpointer:
            raise RuntimeError(
                "PersistenceManager not initialized. Call 'await persistence_manager.initialize()' first."
            )
        return self._checkpointer

    @property
    def store(self):
        if not self._store:
            raise RuntimeError(
                "PersistenceManager not initialized. Call 'await persistence_manager.initialize()' first."
            )
        return self._store

    async def cleanup(self):
        """Cleanup persistence resources."""
        await self.close()

    async def close(self):
        """Close all persistence resources and connections."""
        # Close checkpointer if it has cleanup methods
        if self._checkpointer:
            try:
                if hasattr(self._checkpointer, "__aexit__"):
                    await self._checkpointer.__aexit__(None, None, None)
                elif hasattr(self._checkpointer, "close"):
                    await self._checkpointer.close()
            except Exception as e:
                logger.warning(f"Error closing checkpointer: {e}")
            finally:
                self._checkpointer = None

        # Close store if it has cleanup methods
        if self._store:
            try:
                if hasattr(self._store, "__aexit__"):
                    await self._store.__aexit__(None, None, None)
                elif hasattr(self._store, "close"):
                    await self._store.close()
            except Exception as e:
                logger.warning(f"Error closing store: {e}")
            finally:
                self._store = None

        # Close all tracked connections
        for conn in self._connections:
            try:
                await conn.close()
                logger.info("Closed database connection")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")

        self._connections.clear()
