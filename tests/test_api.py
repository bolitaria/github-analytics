import sys
import os
import pytest
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.app import create_app
from src.auth.utils import create_token


@pytest.fixture
def client():
    app = create_app(testing=True)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers():
    token = create_token("testuser", "admin")
    return {"Authorization": f"Bearer {token}"}


class TestAPI:
    def test_health_endpoint(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get("status") == "healthy"

    def test_repositories_endpoint(self, client, auth_headers):
        response = client.get("/api/repos", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_repository_activity_endpoint(self, client, auth_headers):
        response = client.get("/api/repos/test/repo/activity", headers=auth_headers)
        assert response.status_code in (200, 404)

    def test_metrics_endpoint(self, client, auth_headers):
        response = client.get("/api/metrics/event-types", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        if data:
            assert "event_type" in data[0]
            assert "count" in data[0]


class TestAuthentication:
    def test_login_success(self, client):
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "token" in data
        assert data["user"]["username"] == "admin"

    def test_login_invalid_credentials(self, client):
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert response.status_code == 401
