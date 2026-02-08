"""Rule management endpoints."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.models import Environment, Flag, Rule
from app.schemas.schemas import Predicate, RuleCreate, RuleResponse

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

router = APIRouter(prefix="/rules", tags=["rules"])


def _rule_to_response(rule: Rule) -> RuleResponse:
    return RuleResponse(
        id=rule.id,
        flag_id=rule.flag_id,
        environment_id=rule.environment_id,
        priority=rule.priority,
        conditions=[Predicate(**c) for c in json.loads(rule.conditions)],
        enabled=rule.enabled,
        variant=rule.variant,
        created_at=rule.created_at,
    )


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(
    body: RuleCreate,
    db: Session = Depends(get_db),
    _key: str = Depends(require_admin),
) -> RuleResponse:
    # Resolve flag: accept flag_id or flag_key
    flag_id = body.flag_id
    if flag_id:
        flag = db.execute(select(Flag).where(Flag.id == flag_id)).scalar_one_or_none()
    elif body.flag_key:
        flag = db.execute(select(Flag).where(Flag.key == body.flag_key)).scalar_one_or_none()
        if flag:
            flag_id = flag.id
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Provide either flag_id or flag_key (not both required)",
        )
    if not flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flag not found")

    # Resolve environment: accept environment_id or env_key
    env_id = body.environment_id
    if env_id:
        env = db.execute(select(Environment).where(Environment.id == env_id)).scalar_one_or_none()
    elif body.env_key:
        env = db.execute(
            select(Environment).where(Environment.key == body.env_key)
        ).scalar_one_or_none()
        if env:
            env_id = env.id
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Provide either environment_id or env_key (not both required)",
        )
    if not env:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Environment not found")

    rule = Rule(
        flag_id=flag_id,
        environment_id=env_id,
        priority=body.priority,
        conditions=json.dumps([c.model_dump() for c in body.conditions]),
        enabled=body.enabled,
        variant=body.variant,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return _rule_to_response(rule)


@router.get("", response_model=list[RuleResponse])
def list_rules(
    flag_id: str | None = Query(None),
    env: str | None = Query(None),
    db: Session = Depends(get_db),
    _key: str = Depends(require_admin),
) -> list[RuleResponse]:
    stmt = select(Rule)
    if flag_id:
        stmt = stmt.where(Rule.flag_id == flag_id)
    if env:
        env_obj = db.execute(select(Environment).where(Environment.key == env)).scalar_one_or_none()
        if env_obj:
            stmt = stmt.where(Rule.environment_id == env_obj.id)
        else:
            return []
    stmt = stmt.order_by(Rule.priority.asc())
    rules = db.execute(stmt).scalars().all()
    return [_rule_to_response(r) for r in rules]
