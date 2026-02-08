"""Database engine and session setup using SQLAlchemy 2.0."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.engine import Engine

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _enable_sqlite_fk(dbapi_conn: object, _connection_record: object) -> None:
    """Enable foreign key enforcement for SQLite connections."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_engine() -> Engine:
    """Return cached engine singleton."""
    global _engine  # noqa: PLW0603
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        if settings.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(
            settings.database_url,
            connect_args=connect_args,
            echo=False,
        )
        if settings.database_url.startswith("sqlite"):
            event.listen(_engine, "connect", _enable_sqlite_fk)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return cached session factory singleton."""
    global _session_factory  # noqa: PLW0603
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def reset_engine() -> None:
    """Dispose engine and reset singletons (used in tests)."""
    global _engine, _session_factory  # noqa: PLW0603
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
