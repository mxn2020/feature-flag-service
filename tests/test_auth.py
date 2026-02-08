"""Tests for authentication middleware."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


class TestAuth:
    def test_admin_endpoint_no_key(self, client: TestClient) -> None:
        resp = client.get("/api/v1/flags")
        assert resp.status_code == 401

    def test_admin_endpoint_wrong_key(self, client: TestClient) -> None:
        resp = client.get("/api/v1/flags", headers={"X-API-Key": "wrong"})
        assert resp.status_code == 401

    def test_admin_endpoint_read_key(
        self, client: TestClient, read_headers: dict[str, str]
    ) -> None:
        resp = client.get("/api/v1/flags", headers=read_headers)
        assert resp.status_code == 401

    def test_admin_endpoint_admin_key(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        resp = client.get("/api/v1/flags", headers=admin_headers)
        assert resp.status_code == 200

    def test_evaluate_with_read_key(self, client: TestClient, read_headers: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/evaluate",
            json={"flag_key": "test", "env_key": "dev", "user_id": "u1"},
            headers=read_headers,
        )
        assert resp.status_code == 200

    def test_evaluate_with_admin_key(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        resp = client.post(
            "/api/v1/evaluate",
            json={"flag_key": "test", "env_key": "dev", "user_id": "u1"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
