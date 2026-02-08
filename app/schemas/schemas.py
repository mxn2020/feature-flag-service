"""Pydantic v2 schemas for request/response validation."""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, Field

# ── Flags ──────────────────────────────────────────────────────────


class FlagCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9_\-]+$")
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    enabled: bool = False
    default_variant: str = "off"
    rollout_percentage: float | None = Field(None, ge=0, le=100)
    targeted_allow: list[str] = Field(default_factory=list)
    targeted_deny: list[str] = Field(default_factory=list)


class FlagUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    enabled: bool | None = None
    archived: bool | None = None
    default_variant: str | None = None
    rollout_percentage: float | None = Field(None, ge=0, le=100)
    targeted_allow: list[str] | None = None
    targeted_deny: list[str] | None = None


class FlagResponse(BaseModel):
    id: str
    key: str
    name: str
    description: str
    enabled: bool
    archived: bool
    default_variant: str
    rollout_percentage: float | None
    targeted_allow: list[str]
    targeted_deny: list[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


# ── Environments ───────────────────────────────────────────────────


class EnvironmentCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9_\-]+$")
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""


class EnvironmentResponse(BaseModel):
    id: str
    key: str
    name: str
    description: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# ── Rules ──────────────────────────────────────────────────────────


class Predicate(BaseModel):
    attribute: str = Field(..., min_length=1)
    operator: str = Field(
        ...,
        pattern=r"^(exists|equals|not_equals|contains|in_list|gt|gte|lt|lte)$",
    )
    value: str | int | float | bool | list[str | int | float] | None = None


class RuleCreate(BaseModel):
    flag_id: str | None = None
    flag_key: str | None = None
    environment_id: str | None = None
    env_key: str | None = None
    priority: int = Field(0, ge=0)
    conditions: list[Predicate] = Field(default_factory=list)
    enabled: bool = True
    variant: str = "on"


class RuleResponse(BaseModel):
    id: str
    flag_id: str
    environment_id: str
    priority: int
    conditions: list[Predicate]
    enabled: bool
    variant: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# ── Evaluation ─────────────────────────────────────────────────────


class EvalRequest(BaseModel):
    flag_key: str
    env_key: str = "production"
    user_id: str
    attributes: dict[str, str | int | float | bool | list[str]] = Field(default_factory=dict)


class BulkEvalRequest(BaseModel):
    evaluations: list[EvalRequest]


class EvalResponse(BaseModel):
    flag_key: str
    env_key: str
    enabled: bool
    variant: str | None = None
    reason: str
    rule_id: str | None = None
    eval_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )


class BulkEvalResponse(BaseModel):
    results: list[EvalResponse]


# ── Health ─────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
