#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.clickhouse import clickhouse_client as ClickHouseClient
from src.etl.github_etl import GitHubETL


def test_fetch_events_demo():
    """Prueba la generación de eventos de demostración cuando no hay token."""
    etl = GitHubETL()
    etl.headers = {}
    import src.config.settings as settings_module

    original_token = settings_module.settings.GITHUB_TOKEN
    settings_module.settings.GITHUB_TOKEN = ""
    try:
        events = etl.fetch_events("demo", "test_repo")
        assert isinstance(events, list)
        if events:
            assert "id" in events[0]
    finally:
        settings_module.settings.GITHUB_TOKEN = original_token


def test_transform_event():
    """Prueba la transformación de un evento crudo a GitHubEvent."""
    etl = GitHubETL()
    # Fecha en formato correcto: sin microsegundos y con Z
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    raw_event = {
        "id": "123",
        "type": "PushEvent",
        "actor": {"login": "testuser"},
        "repo": {"name": "test/repo"},
        "created_at": now_str,
        "payload": {"push_id": 456},
        "org": None,
    }
    event = etl.transform_event(raw_event)
    assert event.id == "123"
    assert event.type == "PushEvent"
    assert event.actor_login == "testuser"
    assert event.repo_name == "test/repo"
    assert "push_id" in event.payload


def test_load_events():
    """Prueba la carga de eventos en ClickHouse (requiere base de datos activa)."""
    etl = GitHubETL()
    from src.models.github_models import GitHubEvent

    test_event = GitHubEvent(
        id="load_test_1",
        type="TestEvent",
        actor_login="tester",
        repo_name="test/load",
        created_at=datetime.now(timezone.utc),
        payload={"test": True},
        org_login=None,
    )
    try:
        etl.load_events([test_event])
        result = ClickHouseClient.execute_query(
            "SELECT count() FROM github_analytics.events WHERE id = 'load_test_1'"
        )
        assert result[0][0] == 1
        ClickHouseClient.execute_query(
            "ALTER TABLE github_analytics.events DELETE WHERE id = 'load_test_1'"
        )
    except Exception as e:
        pytest.fail(f"Load events failed: {e}")


def test_run_etl_demo(monkeypatch):
    """Prueba la ejecución completa del ETL en modo demo sin token."""
    import src.config.settings as settings_module

    # Forzar token vacío para activar modo demo
    monkeypatch.setattr(settings_module.settings, "GITHUB_TOKEN", "")
    etl = GitHubETL()
    etl.headers = {}
    etl.run_etl("demo", "repo", days_back=1)
    result = ClickHouseClient.execute_query(
        "SELECT count() FROM github_analytics.events WHERE repo_name = 'demo/repo'"
    )
    assert result[0][0] > 0
    # Limpiar datos de prueba
    ClickHouseClient.execute_query(
        "ALTER TABLE github_analytics.events DELETE WHERE repo_name = 'demo/repo'"
    )
