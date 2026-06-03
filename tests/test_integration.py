#!/usr/bin/env python3
"""
Tests de integración que verifican el flujo completo:
- Inserción de datos de prueba en ClickHouse
- Entrenamiento de modelo
- Consulta a la API
"""
import pytest
import sys
import os
import json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.clickhouse import clickhouse_client
from src.models.forecast import train_and_forecast, save_predictions
from src.api.app import app


@pytest.fixture
def test_client():
    """Cliente de prueba para la API Flask"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def setup_test_data():
    """Inserta datos de prueba en la base de datos antes de cada test"""
    # Limpiar tablas de prueba (opcional, pero cuidado)
    # clickhouse_client.execute_query("TRUNCATE TABLE github_analytics.events")
    # clickhouse_client.execute_query("TRUNCATE TABLE github_analytics.forecasts")

    # Insertar algunos eventos de prueba
    test_events = []
    base_time = datetime.utcnow() - timedelta(days=10)
    for i in range(100):
        event_time = base_time + timedelta(hours=i)
        test_events.append(
            {
                "id": f"test_{i}",
                "type": "PushEvent",
                "actor_login": f"user_{i % 5}",
                "repo_name": "test/repo",
                "created_at": event_time,
                "payload": "{}",
                "org_login": None,
            }
        )

    # Usar inserción por lotes (necesitas implementar un método en clickhouse_client)
    # Por simplicidad, insertamos uno a uno
    for event in test_events:
        clickhouse_client.client.execute(
            "INSERT INTO github_analytics.events VALUES",
            [
                (
                    event["id"],
                    event["type"],
                    event["actor_login"],
                    event["repo_name"],
                    event["created_at"],
                    event["payload"],
                    event["org_login"],
                )
            ],
        )

    yield

    # Limpiar (opcional)
    # clickhouse_client.execute_query("DELETE FROM github_analytics.events WHERE id LIKE 'test_%'")


def test_model_training():
    """Prueba que el entrenamiento de modelo funcione con datos de prueba"""
    predictions = train_and_forecast("test/repo", periods=5)
    assert predictions is not None
    assert len(predictions) == 5
    # Guardar predicciones
    save_predictions(predictions)

    # Verificar que se guardaron
    result = clickhouse_client.execute_query(
        "SELECT count() FROM github_analytics.forecasts WHERE repository = 'test/repo'"
    )
    assert result[0][0] == 5


def test_api_predictions(test_client):
    """Prueba el endpoint de predicciones de la API"""
    # Primero aseguramos que hay predicciones
    test_model_training()

    # Llamar al endpoint
    response = test_client.get("/api/repos/test/repo/predictions")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 5
    assert "date" in data[0]
    assert "predicted" in data[0]


def test_api_classify(test_client):
    """Prueba el endpoint de clasificación de issues"""
    # Necesitamos token de autenticación (para pruebas, podemos usar un token fijo o saltar auth)
    # En un test real, podrías mockear la autenticación o crear un token de prueba.
    # Aquí asumimos que la autenticación está desactivada en modo test.
    payload = {"title": "Fix typo in README", "body": "Just a small correction"}
    response = test_client.post("/api/classify", json=payload)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "label" in data
    assert "confidence" in data
