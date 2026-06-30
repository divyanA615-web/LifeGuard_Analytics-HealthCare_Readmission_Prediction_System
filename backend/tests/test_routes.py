"""Route smoke tests."""

from __future__ import annotations

import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app  # noqa


client = TestClient(app)


def test_health() -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "ok"


def test_predict_requires_auth() -> None:
    response = client.post("/v1/predict", json={})
    assert response.status_code == 401
