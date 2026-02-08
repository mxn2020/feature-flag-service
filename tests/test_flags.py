"""Tests for flag CRUD endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


class TestFlagCRUD:
    def test_create_flag(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/flags",
            json={"key": "my-flag", "name": "My Flag"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["key"] == "my-flag"
        assert data["name"] == "My Flag"
        assert data["enabled"] is False
        assert data["archived"] is False
        assert data["id"]

    def test_create_duplicate_flag(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        client.post("/api/v1/flags", json={"key": "dup", "name": "Dup"}, headers=admin_headers)
        resp = client.post(
            "/api/v1/flags", json={"key": "dup", "name": "Dup"}, headers=admin_headers
        )
        assert resp.status_code == 409

    def test_list_flags(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        client.post("/api/v1/flags", json={"key": "f1", "name": "F1"}, headers=admin_headers)
        client.post("/api/v1/flags", json={"key": "f2", "name": "F2"}, headers=admin_headers)
        resp = client.get("/api/v1/flags", headers=admin_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_flag(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        create_resp = client.post(
            "/api/v1/flags", json={"key": "g1", "name": "G1"}, headers=admin_headers
        )
        flag_id = create_resp.json()["id"]
        resp = client.get(f"/api/v1/flags/{flag_id}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["key"] == "g1"

    def test_get_flag_not_found(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        resp = client.get("/api/v1/flags/nonexistent", headers=admin_headers)
        assert resp.status_code == 404

    def test_update_flag(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        create_resp = client.post(
            "/api/v1/flags", json={"key": "u1", "name": "U1"}, headers=admin_headers
        )
        flag_id = create_resp.json()["id"]
        resp = client.patch(
            f"/api/v1/flags/{flag_id}",
            json={"name": "Updated", "enabled": True},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"
        assert resp.json()["enabled"] is True

    def test_delete_flag(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        create_resp = client.post(
            "/api/v1/flags", json={"key": "d1", "name": "D1"}, headers=admin_headers
        )
        flag_id = create_resp.json()["id"]
        resp = client.delete(f"/api/v1/flags/{flag_id}", headers=admin_headers)
        assert resp.status_code == 204
        resp = client.get(f"/api/v1/flags/{flag_id}", headers=admin_headers)
        assert resp.status_code == 404

    def test_flag_key_validation(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/flags",
            json={"key": "INVALID KEY!", "name": "Bad"},
            headers=admin_headers,
        )
        assert resp.status_code == 422
