import pytest
from src.etl.github_etl import GitHubETL
from src.models.github_models import GitHubEvent


def test_transform_event():
    etl = GitHubETL()
    sample_event = {
        "id": "123",
        "type": "PushEvent",
        "actor": {"login": "testuser"},
        "repo": {"name": "test/repo"},
        "created_at": "2023-01-01T00:00:00Z",
        "payload": {"push_id": 123},
        "org": None,
    }

    transformed = etl.transform_event(sample_event)
    assert transformed.id == "123"
    assert transformed.actor_login == "testuser"
    assert transformed.repo_name == "test/repo"


#!/usr/bin/env python3
"""
Tests para el pipeline ETL
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.etl.github_etl import GitHubETL
from src.database.clickhouse_client import ClickHouseClient
from src.config.settings import settings


class TestGitHubETL:
    """Tests para la clase GitHubETL"""

    @pytest.fixture
    def mock_clickhouse(self):
        """Mock de ClickHouse client"""
        mock = Mock(spec=ClickHouseClient)
        mock.execute_query.return_value = []
        mock.insert_data.return_value = True
        return mock

    @pytest.fixture
    def etl_instance(self, mock_clickhouse):
        """Instancia de GitHubETL para testing"""
        return GitHubETL(mock_clickhouse, "test-token")

    def test_initialization(self, etl_instance, mock_clickhouse):
        """Test de inicialización"""
        assert etl_instance.clickhouse_client == mock_clickhouse
        assert etl_instance.github_token == settings.GITHUB_TOKEN
        assert etl_instance.base_url == "https://api.github.com"

    @patch("src.etl.github_etl.requests.get")
    def test_fetch_repository_events_success(self, mock_get, etl_instance):
        """Test de fetch exitoso de eventos"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "1",
                "type": "PushEvent",
                "actor": {"login": "user1"},
                "repo": {"name": "owner/repo1"},
                "created_at": "2023-01-01T00:00:00Z",
            }
        ]
        mock_get.return_value = mock_response

        events = etl_instance.fetch_repository_events("owner/repo1")

        assert len(events) == 1
        assert events[0]["type"] == "PushEvent"
        mock_get.assert_called_once()

    @patch("src.etl.github_etl.requests.get")
    def test_fetch_repository_events_rate_limit(self, mock_get, etl_instance):
        """Test de manejo de rate limit"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.headers = {"X-RateLimit-Remaining": "0"}
        mock_get.return_value = mock_response

        events = etl_instance.fetch_repository_events("owner/repo1")

        assert events == []
        mock_get.assert_called_once()

    def test_transform_event_data(self, etl_instance):
        """Test de transformación de datos"""
        raw_event = {
            "id": "123",
            "type": "PushEvent",
            "actor": {"login": "testuser"},
            "repo": {"name": "owner/repo"},
            "created_at": "2023-01-01T00:00:00Z",
            "payload": {"size": 1},
        }

        transformed = etl_instance.transform_event_data(raw_event)

        assert transformed["event_id"] == "123"
        assert transformed["event_type"] == "PushEvent"
        assert transformed["actor_login"] == "testuser"
        assert transformed["repo_name"] == "owner/repo"
        assert "created_at" in transformed

    def test_process_repository_demo_mode(self, etl_instance, mock_clickhouse):
        """Test de procesamiento en modo demo"""
        etl_instance.github_token = None  # Demo mode

        result = etl_instance.process_repository("owner/repo")

        assert result is True
        # Verificar que se llamó a insert_data con datos demo
        assert mock_clickhouse.insert_data.called


class TestClickHouseClient:
    """Tests para ClickHouse client"""

    @pytest.fixture
    def clickhouse_client(self):
        """Instancia de ClickHouse client para testing"""
        return ClickHouseClient()

    def test_connection_parameters(self, clickhouse_client):
        """Test de parámetros de conexión"""
        assert clickhouse_client.host == "clickhouse"
        assert clickhouse_client.port == 9001
        assert clickhouse_client.database == "github_events"

    @patch("src.database.clickhouse_client.clickhouse_connect")
    def test_connection_success(self, mock_connect, clickhouse_client):
        """Test de conexión exitosa"""
        mock_client = Mock()
        mock_connect.return_value = mock_client

        client = clickhouse_client._get_connection()

        assert client == mock_client
        mock_connect.assert_called_once()

    @patch("src.database.clickhouse_client.clickhouse_connect")
    def test_execute_query_success(self, mock_connect, clickhouse_client):
        """Test de ejecución de query exitosa"""
        mock_client = Mock()
        mock_client.query.return_value = [("result1",), ("result2",)]
        mock_connect.return_value = mock_client

        results = clickhouse_client.execute_query("SELECT * FROM table")

        assert len(results) == 2
        mock_client.query.assert_called_once()
