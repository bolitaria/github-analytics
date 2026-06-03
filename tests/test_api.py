#!/usr/bin/env python3
"""
Tests para la API Flask
"""
import pytest
import json
from unittest.mock import Mock, patch
from src.api.app import create_app


class TestAPI:
    """Tests para los endpoints de la API"""

    @pytest.fixture
    def app(self):
        """Fixture de la aplicación Flask"""
        app = create_app()
        app.config["TESTING"] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Fixture del cliente de testing"""
        return app.test_client()

    @pytest.fixture
    def mock_clickhouse(self):
        """Mock de ClickHouse client"""
        with patch("src.api.app.clickhouse_client") as mock:
            mock.execute_query.return_value = [("repo1", 100, 10), ("repo2", 200, 20)]
            yield mock

    def test_health_endpoint(self, client):
        """Test del endpoint de health"""
        response = client.get("/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"

    def test_repositories_endpoint(self, client, mock_clickhouse):
        """Test del endpoint de repositorios"""
        response = client.get("/api/repos")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
        assert data[0]["name"] == "repo1"

    def test_repository_activity_endpoint(self, client, mock_clickhouse):
        """Test del endpoint de actividad de repositorio"""
        response = client.get("/api/repos/repo1/activity")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "events" in data
        assert "contributors" in data

    def test_metrics_endpoint(self, client, mock_clickhouse):
        """Test del endpoint de métricas"""
        mock_clickhouse.execute_query.return_value = [
            ("PushEvent", 50),
            ("WatchEvent", 30),
        ]

        response = client.get("/api/metrics/event-types")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
        assert data[0]["event_type"] == "PushEvent"


class TestAuthentication:
    """Tests para autenticación"""

    @pytest.fixture
    def auth_client(self):
        """Cliente con autenticación"""
        app = create_app()
        app.config["TESTING"] = True
        return app.test_client()

    def test_login_success(self, auth_client):
        """Test de login exitoso"""
        login_data = {"username": "admin", "password": "admin123"}

        response = auth_client.post(
            "/api/auth/login",
            data=json.dumps(login_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "token" in data
        assert data["user"]["username"] == "admin"

    def test_login_invalid_credentials(self, auth_client):
        """Test de login con credenciales inválidas"""
        login_data = {"username": "admin", "password": "wrongpassword"}

        response = auth_client.post(
            "/api/auth/login",
            data=json.dumps(login_data),
            content_type="application/json",
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data
