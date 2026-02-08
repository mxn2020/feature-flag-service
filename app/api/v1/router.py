"""V1 API router — aggregates all v1 sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.environments import router as environments_router
from app.api.v1.evaluate import router as evaluate_router
from app.api.v1.flags import router as flags_router
from app.api.v1.health import router as health_router
from app.api.v1.rules import router as rules_router

router = APIRouter(prefix="/api/v1")
router.include_router(flags_router)
router.include_router(environments_router)
router.include_router(rules_router)
router.include_router(evaluate_router)
router.include_router(health_router)
