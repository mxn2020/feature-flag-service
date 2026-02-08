"""Flag management endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.models import Flag
from app.schemas.schemas import FlagCreate, FlagResponse, FlagUpdate

router = APIRouter(prefix="/flags", tags=["flags"])


def _flag_to_response(flag: Flag) -> FlagResponse:
    return FlagResponse(
        id=flag.id,
        key=flag.key,
        name=flag.name,
        description=flag.description,
        enabled=flag.enabled,
        archived=flag.archived,
        default_variant=flag.default_variant,
        rollout_percentage=flag.rollout_percentage,
        targeted_allow=json.loads(flag.targeted_allow),
        targeted_deny=json.loads(flag.targeted_deny),
        created_at=flag.created_at,
        updated_at=flag.updated_at,
    )


@router.post("", response_model=FlagResponse, status_code=status.HTTP_201_CREATED)
def create_flag(
    body: FlagCreate,
    db: Session = Depends(get_db),
    _key: str = Depends(require_admin),
) -> FlagResponse:
    existing = db.execute(select(Flag).where(Flag.key == body.key)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Flag key already exists")
    flag = Flag(
        key=body.key,
        name=body.name,
        description=body.description,
        enabled=body.enabled,
        default_variant=body.default_variant,
        rollout_percentage=body.rollout_percentage,
        targeted_allow=json.dumps(body.targeted_allow),
        targeted_deny=json.dumps(body.targeted_deny),
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return _flag_to_response(flag)


@router.get("", response_model=list[FlagResponse])
def list_flags(
    db: Session = Depends(get_db),
    _key: str = Depends(require_admin),
) -> list[FlagResponse]:
    flags = db.execute(select(Flag).order_by(Flag.created_at.desc())).scalars().all()
    return [_flag_to_response(f) for f in flags]


@router.get("/{flag_id}", response_model=FlagResponse)
def get_flag(
    flag_id: str,
    db: Session = Depends(get_db),
    _key: str = Depends(require_admin),
) -> FlagResponse:
    flag = db.execute(select(Flag).where(Flag.id == flag_id)).scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flag not found")
    return _flag_to_response(flag)


@router.patch("/{flag_id}", response_model=FlagResponse)
def update_flag(
    flag_id: str,
    body: FlagUpdate,
    db: Session = Depends(get_db),
    _key: str = Depends(require_admin),
) -> FlagResponse:
    flag = db.execute(select(Flag).where(Flag.id == flag_id)).scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flag not found")
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ("targeted_allow", "targeted_deny"):
            setattr(flag, field, json.dumps(value))
        else:
            setattr(flag, field, value)
    db.commit()
    db.refresh(flag)
    return _flag_to_response(flag)


@router.delete("/{flag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flag(
    flag_id: str,
    db: Session = Depends(get_db),
    _key: str = Depends(require_admin),
) -> None:
    flag = db.execute(select(Flag).where(Flag.id == flag_id)).scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flag not found")
    db.delete(flag)
    db.commit()
