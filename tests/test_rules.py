"""Tests for rule endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create_flag_and_env(client: TestClient, admin_headers: dict[str, str]) -> tuple[str, str]:
    """Helper: create a flag and environment, return (flag_id, env_id)."""
    flag_resp = client.post(
        "/api/v1/flags",
        json={"key": "rule-flag", "name": "Rule Flag", "enabled": True},
        headers=admin_headers,
    )
    flag_id = flag_resp.json()["id"]
    env_resp = client.post(
        "/api/v1/environments",
        json={"key": "dev", "name": "Development"},
        headers=admin_headers,
    )
    env_id = env_resp.json()["id"]
    return flag_id, env_id


class TestRuleCRUD:
    def test_create_rule(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        flag_id, env_id = _create_flag_and_env(client, admin_headers)
        resp = client.post(
            "/api/v1/rules",
            json={
                "flag_id": flag_id,
                "environment_id": env_id,
                "priority": 1,
                "conditions": [
                    {"attribute": "country", "operator": "equals", "value": "US"}
                ],
                "variant": "on",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["priority"] == 1
        assert len(data["conditions"]) == 1

    def test_list_rules(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        flag_id, env_id = _create_flag_and_env(client, admin_headers)
        client.post(
            "/api/v1/rules",
            json={
                "flag_id": flag_id,
                "environment_id": env_id,
                "priority": 1,
                "conditions": [],
            },
            headers=admin_headers,
        )
        resp = client.get(f"/api/v1/rules?flag_id={flag_id}&env=dev", headers=admin_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_create_rule_invalid_flag(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/rules",
            json={
                "flag_id": "nonexistent",
                "environment_id": "nonexistent",
                "priority": 0,
                "conditions": [],
            },
            headers=admin_headers,
        )
        assert resp.status_code == 404
