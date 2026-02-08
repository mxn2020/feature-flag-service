"""Tests for environment CRUD endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestEnvironmentCRUD:
    def test_create_environment(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/environments",
            json={"key": "production", "name": "Production"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["key"] == "production"
        assert data["name"] == "Production"

    def test_create_duplicate_environment(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        client.post(
            "/api/v1/environments",
            json={"key": "staging", "name": "Staging"},
            headers=admin_headers,
        )
        resp = client.post(
            "/api/v1/environments",
            json={"key": "staging", "name": "Staging 2"},
            headers=admin_headers,
        )
        assert resp.status_code == 409

    def test_list_environments(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        client.post(
            "/api/v1/environments",
            json={"key": "dev", "name": "Development"},
            headers=admin_headers,
        )
        resp = client.get("/api/v1/environments", headers=admin_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
