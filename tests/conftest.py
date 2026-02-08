"""Shared pytest fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings, reset_settings
from app.core.database import get_db, reset_engine
from app.main import create_app
from app.models.models import Base

if TYPE_CHECKING:
    from collections.abc import Generator

ADMIN_KEY = "test-admin-key"
READ_KEY = "test-read-key"


def _test_settings() -> Settings:
    return Settings(
        admin_api_key=ADMIN_KEY,
        read_api_key=READ_KEY,
        database_url="sqlite:///:memory:",
    )


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Create an in-memory database session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _connection_record):  # type: ignore[no-untyped-def]
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI test client with overridden dependencies."""
    app = create_app(run_startup=False)

    def _override_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_settings] = _test_settings

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    reset_settings()
    reset_engine()


@pytest.fixture()
def admin_headers() -> dict[str, str]:
    return {"X-API-Key": ADMIN_KEY}


@pytest.fixture()
def read_headers() -> dict[str, str]:
    return {"X-API-Key": READ_KEY}
