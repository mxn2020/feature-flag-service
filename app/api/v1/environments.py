"""Environment management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.models import Environment
from app.schemas.schemas import EnvironmentCreate, EnvironmentResponse

router = APIRouter(prefix="/environments", tags=["environments"])


@router.post("", response_model=EnvironmentResponse, status_code=status.HTTP_201_CREATED)
def create_environment(
    body: EnvironmentCreate,
    db: Session = Depends(get_db),
    _key: str = Depends(require_admin),
) -> EnvironmentResponse:
    existing = db.execute(
        select(Environment).where(Environment.key == body.key)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Environment key already exists"
        )
    env = Environment(key=body.key, name=body.name, description=body.description)
    db.add(env)
    db.commit()
    db.refresh(env)
    return EnvironmentResponse.model_validate(env)


@router.get("", response_model=list[EnvironmentResponse])
def list_environments(
    db: Session = Depends(get_db),
    _key: str = Depends(require_admin),
) -> list[EnvironmentResponse]:
    envs = db.execute(select(Environment).order_by(Environment.created_at.desc())).scalars().all()
    return [EnvironmentResponse.model_validate(e) for e in envs]
