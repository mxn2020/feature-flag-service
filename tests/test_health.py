"""Tests for health endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealth:
    def test_liveness(self, client: TestClient) -> None:
        resp = client.get("/api/v1/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_readiness(self, client: TestClient) -> None:
        resp = client.get("/api/v1/readyz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
