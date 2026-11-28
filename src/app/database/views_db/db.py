"""
Database initialization using pure SQLAlchemy.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, ClassVar

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)


class BaseModel(DeclarativeBase):
    """Base model providing a generic to_json() for all records."""

    # Column names that must never be serialized. Override in subclasses.
    __json_exclude__: ClassVar[frozenset[str]] = frozenset()

    def to_json(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for column in self.__table__.columns:  # type: ignore
            if column.name in self.__json_exclude__:
                continue
            value = getattr(self, column.name)  # type: ignore
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            data[column.name] = value  # type: ignore
        return data

    @classmethod
    def load(cls, **kwargs: Any):
        args = {key: value for key, value in kwargs.items() if hasattr(cls, key)}
        return cls(**args)


# Alias for compatibility with existing model imports.
Model = BaseModel

# Global engine and session factory initialized via init_db().
engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def init_db(database_url: str, **engine_kwargs: Any) -> sessionmaker[Session]:
    """Initialize the SQLAlchemy engine and session factory."""
    global engine, SessionLocal

    # Dispose old engine to release connections before replacing it
    if engine is not None:
        engine.dispose()

    # expire_on_commit=False preserves behavior where objects remain accessible
    # after commit without triggering new queries.
    engine = create_engine(database_url, **engine_kwargs)
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    return SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    if SessionLocal is None:
        raise RuntimeError("Database is not initialized. Call init_db() first.")

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Session rolled back due to an error.")
        raise
    finally:
        session.close()


__all__ = [
    "Model",
    "BaseModel",
    "engine",
    "SessionLocal",
    "init_db",
    "get_session",
]
