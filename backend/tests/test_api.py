from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_setup_status():
    client = TestClient(app)

    response = client.get("/api/setup/status")

    assert response.status_code == 200
    assert "checks" in response.json()
