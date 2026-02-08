"""Tests for flag evaluation logic — the core of the service."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _setup_flag_with_env(
    client: TestClient,
    admin_headers: dict[str, str],
    *,
    flag_key: str = "eval-flag",
    enabled: bool = True,
    rollout: float | None = None,
    allow: list[str] | None = None,
    deny: list[str] | None = None,
) -> tuple[str, str]:
    """Create a flag and environment, return (flag_id, env_id)."""
    flag_body: dict[str, object] = {"key": flag_key, "name": "Eval Flag", "enabled": enabled}
    if rollout is not None:
        flag_body["rollout_percentage"] = rollout
    if allow:
        flag_body["targeted_allow"] = allow
    if deny:
        flag_body["targeted_deny"] = deny
    flag_resp = client.post("/api/v1/flags", json=flag_body, headers=admin_headers)
    flag_id = flag_resp.json()["id"]
    env_resp = client.post(
        "/api/v1/environments",
        json={"key": "production", "name": "Production"},
        headers=admin_headers,
    )
    env_id = env_resp.json()["id"]
    return flag_id, env_id


class TestEvaluation:
    def test_disabled_flag(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        _setup_flag_with_env(client, admin_headers, enabled=False)
        resp = client.post(
            "/api/v1/evaluate",
            json={"flag_key": "eval-flag", "env_key": "production", "user_id": "user1"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is False
        assert data["reason"] == "disabled"

    def test_nonexistent_flag(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/evaluate",
            json={"flag_key": "nope", "env_key": "production", "user_id": "user1"},
            headers=admin_headers,
        )
        data = resp.json()
        assert data["enabled"] is False
        assert data["reason"] == "disabled"

    def test_targeted_deny(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        _setup_flag_with_env(client, admin_headers, deny=["blocked-user"])
        resp = client.post(
            "/api/v1/evaluate",
            json={"flag_key": "eval-flag", "env_key": "production", "user_id": "blocked-user"},
            headers=admin_headers,
        )
        data = resp.json()
        assert data["enabled"] is False
        assert data["reason"] == "targeted_deny"

    def test_targeted_allow(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        _setup_flag_with_env(client, admin_headers, allow=["vip-user"])
        resp = client.post(
            "/api/v1/evaluate",
            json={"flag_key": "eval-flag", "env_key": "production", "user_id": "vip-user"},
            headers=admin_headers,
        )
        data = resp.json()
        assert data["enabled"] is True
        assert data["reason"] == "targeted_allow"

    def test_targeted_deny_takes_precedence(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        _setup_flag_with_env(client, admin_headers, allow=["both"], deny=["both"])
        resp = client.post(
            "/api/v1/evaluate",
            json={"flag_key": "eval-flag", "env_key": "production", "user_id": "both"},
            headers=admin_headers,
        )
        data = resp.json()
        assert data["enabled"] is False
        assert data["reason"] == "targeted_deny"

    def test_rule_match(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        flag_id, env_id = _setup_flag_with_env(client, admin_headers)
        client.post(
            "/api/v1/rules",
            json={
                "flag_id": flag_id,
                "environment_id": env_id,
                "priority": 1,
                "conditions": [{"attribute": "country", "operator": "equals", "value": "US"}],
                "variant": "us-variant",
            },
            headers=admin_headers,
        )
        resp = client.post(
            "/api/v1/evaluate",
            json={
                "flag_key": "eval-flag",
                "env_key": "production",
                "user_id": "user1",
                "attributes": {"country": "US"},
            },
            headers=admin_headers,
        )
        data = resp.json()
        assert data["enabled"] is True
        assert data["reason"] == "rule_match"
        assert data["variant"] == "us-variant"
        assert data["rule_id"] is not None

    def test_rule_no_match_falls_through(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        flag_id, env_id = _setup_flag_with_env(client, admin_headers)
        client.post(
            "/api/v1/rules",
            json={
                "flag_id": flag_id,
                "environment_id": env_id,
                "priority": 1,
                "conditions": [{"attribute": "country", "operator": "equals", "value": "US"}],
                "variant": "us-variant",
            },
            headers=admin_headers,
        )
        resp = client.post(
            "/api/v1/evaluate",
            json={
                "flag_key": "eval-flag",
                "env_key": "production",
                "user_id": "user1",
                "attributes": {"country": "UK"},
            },
            headers=admin_headers,
        )
        data = resp.json()
        assert data["reason"] == "default"

    def test_rollout_deterministic(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        _setup_flag_with_env(client, admin_headers, rollout=50.0)
        results = []
        for i in range(20):
            resp = client.post(
                "/api/v1/evaluate",
                json={
                    "flag_key": "eval-flag",
                    "env_key": "production",
                    "user_id": f"user-{i}",
                },
                headers=admin_headers,
            )
            results.append(resp.json()["enabled"])
        # With 50% rollout and 20 users, expect some true and some false
        assert any(results)
        assert not all(results)
        # Verify determinism: same request => same result
        resp1 = client.post(
            "/api/v1/evaluate",
            json={"flag_key": "eval-flag", "env_key": "production", "user_id": "user-0"},
            headers=admin_headers,
        )
        resp2 = client.post(
            "/api/v1/evaluate",
            json={"flag_key": "eval-flag", "env_key": "production", "user_id": "user-0"},
            headers=admin_headers,
        )
        assert resp1.json()["enabled"] == resp2.json()["enabled"]
        # Rollout reason
        assert resp1.json()["reason"] == "rollout"

    def test_default_evaluation(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        _setup_flag_with_env(client, admin_headers)
        resp = client.post(
            "/api/v1/evaluate",
            json={"flag_key": "eval-flag", "env_key": "production", "user_id": "user1"},
            headers=admin_headers,
        )
        data = resp.json()
        assert data["reason"] == "default"
        assert data["eval_id"]
        assert data["timestamp"]

    def test_bulk_evaluation(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        _setup_flag_with_env(client, admin_headers)
        resp = client.post(
            "/api/v1/evaluate",
            json={
                "evaluations": [
                    {"flag_key": "eval-flag", "env_key": "production", "user_id": "u1"},
                    {"flag_key": "eval-flag", "env_key": "production", "user_id": "u2"},
                ]
            },
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert len(data["results"]) == 2

    def test_eval_response_fields(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        _setup_flag_with_env(client, admin_headers)
        resp = client.post(
            "/api/v1/evaluate",
            json={"flag_key": "eval-flag", "env_key": "production", "user_id": "user1"},
            headers=admin_headers,
        )
        data = resp.json()
        assert "flag_key" in data
        assert "env_key" in data
        assert "enabled" in data
        assert "variant" in data
        assert "reason" in data
        assert "eval_id" in data
        assert "timestamp" in data


class TestPredicates:
    """Test individual predicate operators via rule evaluation."""

    def _setup_with_rule(
        self, client: TestClient, admin_headers: dict[str, str],
        conditions: list[dict[str, object]], flag_key: str = "pred-flag",
    ) -> None:
        flag_resp = client.post(
            "/api/v1/flags",
            json={"key": flag_key, "name": "Pred Flag", "enabled": True},
            headers=admin_headers,
        )
        flag_id = flag_resp.json()["id"]
        env_resp = client.post(
            "/api/v1/environments",
            json={"key": "prod", "name": "Prod"},
            headers=admin_headers,
        )
        env_id = env_resp.json()["id"]
        client.post(
            "/api/v1/rules",
            json={
                "flag_id": flag_id,
                "environment_id": env_id,
                "priority": 1,
                "conditions": conditions,
                "variant": "matched",
            },
            headers=admin_headers,
        )

    def test_exists_operator(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        self._setup_with_rule(
            client, admin_headers,
            conditions=[{"attribute": "beta", "operator": "exists"}],
        )
        resp = client.post(
            "/api/v1/evaluate",
            json={
                "flag_key": "pred-flag", "env_key": "prod", "user_id": "u1",
                "attributes": {"beta": True},
            },
            headers=admin_headers,
        )
        assert resp.json()["reason"] == "rule_match"

    def test_not_equals_operator(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        self._setup_with_rule(
            client, admin_headers,
            conditions=[{"attribute": "plan", "operator": "not_equals", "value": "free"}],
            flag_key="ne-flag",
        )
        resp = client.post(
            "/api/v1/evaluate",
            json={
                "flag_key": "ne-flag", "env_key": "prod", "user_id": "u1",
                "attributes": {"plan": "pro"},
            },
            headers=admin_headers,
        )
        assert resp.json()["reason"] == "rule_match"

    def test_contains_operator(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        self._setup_with_rule(
            client, admin_headers,
            conditions=[{"attribute": "email", "operator": "contains", "value": "@example.com"}],
            flag_key="contains-flag",
        )
        resp = client.post(
            "/api/v1/evaluate",
            json={
                "flag_key": "contains-flag", "env_key": "prod", "user_id": "u1",
                "attributes": {"email": "user@example.com"},
            },
            headers=admin_headers,
        )
        assert resp.json()["reason"] == "rule_match"

    def test_in_list_operator(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        self._setup_with_rule(
            client, admin_headers,
            conditions=[{"attribute": "country", "operator": "in_list", "value": ["US", "CA", "UK"]}],
            flag_key="in-flag",
        )
        resp = client.post(
            "/api/v1/evaluate",
            json={
                "flag_key": "in-flag", "env_key": "prod", "user_id": "u1",
                "attributes": {"country": "CA"},
            },
            headers=admin_headers,
        )
        assert resp.json()["reason"] == "rule_match"

    def test_numeric_gt(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        self._setup_with_rule(
            client, admin_headers,
            conditions=[{"attribute": "age", "operator": "gt", "value": 18}],
            flag_key="gt-flag",
        )
        resp = client.post(
            "/api/v1/evaluate",
            json={
                "flag_key": "gt-flag", "env_key": "prod", "user_id": "u1",
                "attributes": {"age": 25},
            },
            headers=admin_headers,
        )
        assert resp.json()["reason"] == "rule_match"

    def test_numeric_lte(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        self._setup_with_rule(
            client, admin_headers,
            conditions=[{"attribute": "score", "operator": "lte", "value": 100}],
            flag_key="lte-flag",
        )
        resp = client.post(
            "/api/v1/evaluate",
            json={
                "flag_key": "lte-flag", "env_key": "prod", "user_id": "u1",
                "attributes": {"score": 50},
            },
            headers=admin_headers,
        )
        assert resp.json()["reason"] == "rule_match"
