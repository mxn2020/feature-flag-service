"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.core.database import get_engine
from app.models.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create database tables on startup if they don't exist."""
    Base.metadata.create_all(bind=get_engine())
    yield


def create_app(*, run_startup: bool = True) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Feature Flag Service",
        description="A minimal but serious feature flag platform",
        version="0.1.0",
        lifespan=lifespan if run_startup else None,
    )
    app.include_router(v1_router)
    return app


app = create_app()

