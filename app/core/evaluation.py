"""Deterministic flag evaluation engine.

Rule processing order:
1. If flag is archived/disabled => enabled=false reason=disabled
2. If user_id in targeted deny list => enabled=false reason=targeted_deny
3. If user_id in targeted allow list => enabled=true reason=targeted_allow
4. Evaluate rules in ascending priority:
   - If rule matches attributes => apply rule outcome and stop
5. If rollout percentage configured:
   - Deterministic hash of (flag_key, env_key, user_id) => bucket [0..9999]
   - enabled if bucket < rollout_percentage * 100
6. Otherwise return default value
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.models.models import Environment, Flag, FlagEnvironment, Rule
from app.schemas.schemas import EvalRequest, EvalResponse, Predicate

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _deterministic_bucket(flag_key: str, env_key: str, user_id: str) -> int:
    """Return an integer in [0, 9999] derived from a deterministic hash."""
    raw = f"{flag_key}:{env_key}:{user_id}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 10000


def _match_predicate(
    predicate: Predicate,
    attributes: dict[str, str | int | float | bool | list[str]],
) -> bool:
    """Evaluate a single predicate against the user's attributes."""
    attr_val = attributes.get(predicate.attribute)

    if predicate.operator == "exists":
        return predicate.attribute in attributes

    if attr_val is None:
        return False

    op = predicate.operator
    val = predicate.value

    if op == "equals":
        return _coerce_eq(attr_val, val)

    if op == "not_equals":
        return not _coerce_eq(attr_val, val)

    if op == "contains":
        return isinstance(attr_val, str) and isinstance(val, str) and val in attr_val

    if op == "in_list":
        if isinstance(val, list):
            return any(_coerce_eq(attr_val, v) for v in val)
        return False

    if op in ("gt", "gte", "lt", "lte"):
        return _numeric_compare(attr_val, val, op)

    return False


def _coerce_eq(a: object, b: object) -> bool:
    """Compare with coercion for string/number/bool."""
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    try:
        return float(a) == float(b)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return str(a) == str(b)


def _numeric_compare(a: object, b: object, op: str) -> bool:
    """Numeric comparison operators."""
    try:
        fa, fb = float(a), float(b)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    if op == "gt":
        return fa > fb
    if op == "gte":
        return fa >= fb
    if op == "lt":
        return fa < fb
    if op == "lte":
        return fa <= fb
    return False


def _match_all_conditions(
    conditions: list[Predicate],
    attributes: dict[str, str | int | float | bool | list[str]],
) -> bool:
    """All conditions must match (AND logic)."""
    return all(_match_predicate(c, attributes) for c in conditions)


def evaluate_flag(req: EvalRequest, db: Session) -> EvalResponse:
    """Evaluate a single flag for a user and return the result."""
    now = datetime.now(UTC)
    eval_id = str(uuid.uuid4())

    # Look up the flag
    flag = db.execute(select(Flag).where(Flag.key == req.flag_key)).scalar_one_or_none()
    if flag is None:
        return EvalResponse(
            flag_key=req.flag_key,
            env_key=req.env_key,
            enabled=False,
            variant="off",
            reason="disabled",
            eval_id=eval_id,
            timestamp=now,
        )

    # Step 1: archived or globally disabled
    if flag.archived or not flag.enabled:
        return EvalResponse(
            flag_key=req.flag_key,
            env_key=req.env_key,
            enabled=False,
            variant="off",
            reason="disabled",
            eval_id=eval_id,
            timestamp=now,
        )

    # Look up environment
    env = db.execute(select(Environment).where(Environment.key == req.env_key)).scalar_one_or_none()

    # Determine per-env config (fall back to flag-level)
    targeted_deny: list[str] = json.loads(flag.targeted_deny)
    targeted_allow: list[str] = json.loads(flag.targeted_allow)
    rollout_percentage = flag.rollout_percentage
    default_variant = flag.default_variant
    env_enabled: bool = flag.enabled

    if env is not None:
        flag_env = db.execute(
            select(FlagEnvironment).where(
                FlagEnvironment.flag_id == flag.id,
                FlagEnvironment.environment_id == env.id,
            )
        ).scalar_one_or_none()
        if flag_env is not None:
            env_enabled = flag_env.enabled
            targeted_deny = json.loads(flag_env.targeted_deny)
            targeted_allow = json.loads(flag_env.targeted_allow)
            if flag_env.rollout_percentage is not None:
                rollout_percentage = flag_env.rollout_percentage
            default_variant = flag_env.default_variant

            # If env-level is disabled, return disabled
            if not env_enabled:
                return EvalResponse(
                    flag_key=req.flag_key,
                    env_key=req.env_key,
                    enabled=False,
                    variant="off",
                    reason="disabled",
                    eval_id=eval_id,
                    timestamp=now,
                )

    # Step 2: targeted deny
    if req.user_id in targeted_deny:
        return EvalResponse(
            flag_key=req.flag_key,
            env_key=req.env_key,
            enabled=False,
            variant="off",
            reason="targeted_deny",
            eval_id=eval_id,
            timestamp=now,
        )

    # Step 3: targeted allow
    if req.user_id in targeted_allow:
        return EvalResponse(
            flag_key=req.flag_key,
            env_key=req.env_key,
            enabled=True,
            variant=default_variant if default_variant != "off" else "on",
            reason="targeted_allow",
            eval_id=eval_id,
            timestamp=now,
        )

    # Step 4: rule evaluation
    if env is not None:
        rules = (
            db.execute(
                select(Rule)
                .where(
                    Rule.flag_id == flag.id,
                    Rule.environment_id == env.id,
                    Rule.enabled == True,  # noqa: E712
                )
                .order_by(Rule.priority.asc())
            )
            .scalars()
            .all()
        )
        # Include user_id in the attributes for rule matching
        eval_attrs = {**req.attributes, "user_id": req.user_id}
        for rule in rules:
            conditions = [Predicate(**c) for c in json.loads(rule.conditions)]
            if _match_all_conditions(conditions, eval_attrs):
                return EvalResponse(
                    flag_key=req.flag_key,
                    env_key=req.env_key,
                    enabled=True,
                    variant=rule.variant,
                    reason="rule_match",
                    rule_id=rule.id,
                    eval_id=eval_id,
                    timestamp=now,
                )

    # Step 5: rollout percentage
    if rollout_percentage is not None:
        bucket = _deterministic_bucket(req.flag_key, req.env_key, req.user_id)
        threshold = int(rollout_percentage * 100)
        if bucket < threshold:
            return EvalResponse(
                flag_key=req.flag_key,
                env_key=req.env_key,
                enabled=True,
                variant=default_variant if default_variant != "off" else "on",
                reason="rollout",
                eval_id=eval_id,
                timestamp=now,
            )
        return EvalResponse(
            flag_key=req.flag_key,
            env_key=req.env_key,
            enabled=False,
            variant="off",
            reason="rollout",
            eval_id=eval_id,
            timestamp=now,
        )

    # Step 6: default
    is_enabled = default_variant != "off"
    return EvalResponse(
        flag_key=req.flag_key,
        env_key=req.env_key,
        enabled=is_enabled,
        variant=default_variant,
        reason="default",
        eval_id=eval_id,
        timestamp=now,
    )
