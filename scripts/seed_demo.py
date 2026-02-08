#!/usr/bin/env python3
"""Seed the feature-flag-service with demo data.

Idempotent: running twice will not create duplicates.

Usage:
    python scripts/seed_demo.py              # defaults to http://localhost:8000
    BASE_URL=http://host:9000 python scripts/seed_demo.py
"""

from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
ADMIN_KEY = os.environ.get("ADMIN_API_KEY", "change-me-admin-key")
READ_KEY = os.environ.get("READ_API_KEY", "change-me-read-key")
API = f"{BASE_URL}/api/v1"


def _req(method: str, path: str, body: dict[str, object] | None = None) -> dict[str, object]:
    """Fire an HTTP request and return the parsed JSON response."""
    url = f"{API}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {
        "X-API-Key": ADMIN_KEY,
        "Content-Type": "application/json",
    }
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())  # type: ignore[no-any-return]
    except HTTPError as exc:
        resp_body = exc.read().decode()
        print(f"  {method} {url} -> {exc.code}: {resp_body}")
        raise


# ── helpers ────────────────────────────────────────────────────────


def get_or_create_environment(key: str, name: str) -> str:
    """Return environment id, creating if needed."""
    envs: list[dict[str, object]] = _req("GET", "/environments")  # type: ignore[assignment]
    for env in envs:
        if env["key"] == key:
            print(f"  Environment '{key}' already exists (id={env['id']})")
            return str(env["id"])
    result = _req("POST", "/environments", {"key": key, "name": name})
    print(f"  Created environment '{key}' (id={result['id']})")
    return str(result["id"])


def get_or_create_flag(
    key: str,
    name: str,
    *,
    enabled: bool = True,
    rollout_percentage: float | None = None,
    targeted_allow: list[str] | None = None,
    targeted_deny: list[str] | None = None,
) -> str:
    """Return flag id, creating if needed."""
    flags: list[dict[str, object]] = _req("GET", "/flags")  # type: ignore[assignment]
    for flag in flags:
        if flag["key"] == key:
            print(f"  Flag '{key}' already exists (id={flag['id']})")
            return str(flag["id"])
    body: dict[str, object] = {"key": key, "name": name, "enabled": enabled}
    if rollout_percentage is not None:
        body["rollout_percentage"] = rollout_percentage
    if targeted_allow:
        body["targeted_allow"] = targeted_allow
    if targeted_deny:
        body["targeted_deny"] = targeted_deny
    result = _req("POST", "/flags", body)
    print(f"  Created flag '{key}' (id={result['id']})")
    return str(result["id"])


def ensure_rule(
    flag_id: str,
    env_id: str,
    priority: int,
    conditions: list[dict[str, object]],
    variant: str = "on",
) -> None:
    """Create a rule if one at this priority does not already exist."""
    rules: list[dict[str, object]] = _req(  # type: ignore[assignment]
        "GET", f"/rules?flag_id={flag_id}"
    )
    for rule in rules:
        if rule["environment_id"] == env_id and rule["priority"] == priority:
            print(f"  Rule priority={priority} already exists (id={rule['id']})")
            return
    _req(
        "POST",
        "/rules",
        {
            "flag_id": flag_id,
            "environment_id": env_id,
            "priority": priority,
            "conditions": conditions,
            "variant": variant,
        },
    )
    print(f"  Created rule priority={priority} variant={variant}")


# ── main ───────────────────────────────────────────────────────────


def main() -> None:
    print(f"Seeding demo data against {API} ...")

    # 1. Environment
    env_id = get_or_create_environment("dev", "Development")

    # 2. Flag
    flag_id = get_or_create_flag(
        "new_checkout",
        "New Checkout",
        enabled=True,
        rollout_percentage=50,
        targeted_allow=["user_allow1"],
        targeted_deny=["user_deny1"],
    )

    # 3. Rule a: country == "EG" => enabled, variant "egypt-ui" (priority 0 — wins)
    ensure_rule(
        flag_id,
        env_id,
        priority=0,
        conditions=[{"attribute": "country", "operator": "equals", "value": "EG"}],
        variant="egypt-ui",
    )

    # 4. Rule b: higher priority number (1) — would otherwise match but loses to rule a
    ensure_rule(
        flag_id,
        env_id,
        priority=1,
        conditions=[{"attribute": "country", "operator": "exists"}],
        variant="generic-geo",
    )

    print("\nDone! Try these curl commands:\n")
    print(f'  READ_KEY="{READ_KEY}"')
    print(f"  # Health check")
    print(f"  curl -s {BASE_URL}/api/v1/healthz | python3 -m json.tool")
    print(f"  # Evaluate deny-list user")
    print(
        f"  curl -s -X POST {BASE_URL}/api/v1/evaluate "
        f'-H "X-API-Key: $READ_KEY" -H "Content-Type: application/json" '
        f"-d '{{\"flag_key\":\"new_checkout\",\"env_key\":\"dev\",\"user_id\":\"user_deny1\"}}'"
    )
    print(f"  # Evaluate allow-list user")
    print(
        f"  curl -s -X POST {BASE_URL}/api/v1/evaluate "
        f'-H "X-API-Key: $READ_KEY" -H "Content-Type: application/json" '
        f"-d '{{\"flag_key\":\"new_checkout\",\"env_key\":\"dev\",\"user_id\":\"user_allow1\"}}'"
    )


if __name__ == "__main__":
    try:
        main()
    except (HTTPError, URLError) as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        print("Is the server running?", file=sys.stderr)
        sys.exit(1)
