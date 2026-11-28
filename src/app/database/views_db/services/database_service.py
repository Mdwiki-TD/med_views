"""
Database service for initialization and session management.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from ..db import BaseModel, init_db
from ..models import (
    LanguageCount,
    PipelineMetadata,
    Statistic,
    Title,
    ViewAllAgents,
    ViewUsersAgents,
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Service for database initialization and session management.

    Handles engine creation, table initialization, and provides session
    context managers for database operations.
    """

    _instance = None
    _session_factory = None

    def __init__(self, database_path: Path) -> None:
        """
        Initialize the database service.

        Parameters:
            database_path: Path to the SQLite database file.
        """
        self.database_path = database_path
        self._engine = None

    @classmethod
    def get_instance(cls, database_path: Path | None = None) -> DatabaseService:
        """
        Get or create a singleton instance of DatabaseService.

        Parameters:
            database_path: Path to the SQLite database file. Required on first call.

        Returns:
            DatabaseService: Singleton instance.
        """
        if cls._instance is None:
            if database_path is None:
                raise ValueError("database_path is required on first call to get_instance()")
            cls._instance = cls(database_path)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None
        cls._session_factory = None

    def initialize(self) -> sessionmaker[Session]:
        """
        Initialize the database engine and create tables.

        Returns:
            sessionmaker: Session factory for creating database sessions.
        """
        if self._session_factory is not None:
            logger.debug("Database already initialized")
            return self._session_factory

        logger.info(f"Initializing database at {self.database_path}")

        # Create parent directory if needed
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize SQLAlchemy engine
        database_url = f"sqlite:///{self.database_path}"
        self._session_factory = init_db(
            database_url,
            connect_args={"check_same_thread": False},
            echo=False,
        )

        # Set SQLite pragmas for performance
        self._set_sqlite_pragmas()

        # Create all tables
        self._create_tables()

        logger.info("Database initialized successfully")
        return self._session_factory

    def _set_sqlite_pragmas(self) -> None:
        """Set SQLite pragmas for optimal performance."""
        from ..db import engine

        if engine is None:
            raise RuntimeError("Database engine not initialized")

        with engine.connect() as conn:
            # Enable WAL mode for better concurrent read/write performance
            conn.execute(text("PRAGMA journal_mode=WAL"))
            # Use NORMAL synchronous mode for better write performance
            conn.execute(text("PRAGMA synchronous=NORMAL"))
            # Increase cache size (in pages)
            conn.execute(text("PRAGMA cache_size=10000"))
            # Enable foreign key enforcement
            conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.commit()

        logger.debug("SQLite pragmas configured")

    def _create_tables(self) -> None:
        """Create all database tables."""
        from ..db import engine

        if engine is None:
            raise RuntimeError("Database engine not initialized")

        # Create all tables defined in models
        BaseModel.metadata.create_all(engine)

        logger.debug("Database tables created")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Provide a transactional session context manager.

        Usage:
            with db_service.get_session() as session:
                session.add(record)
                # Auto-commits on successful exit, rolls back on exception
        """
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("Session rolled back due to an error")
            raise
        finally:
            session.close()

    def get_session_factory(self) -> sessionmaker[Session]:
        """
        Get the session factory.

        Returns:
            sessionmaker: Session factory for creating database sessions.
        """
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._session_factory

    def drop_all_tables(self) -> None:
        """
        Drop all database tables (useful for testing).

        WARNING: This will delete all data in the database.
        """
        from ..db import engine

        if engine is None:
            raise RuntimeError("Database engine not initialized")

        BaseModel.metadata.drop_all(engine)
        logger.warning("All database tables dropped")


__all__ = [
    "DatabaseService",
]
