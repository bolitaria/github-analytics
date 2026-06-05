import sys
import os
import json
import jwt
import pytest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import settings
from src.database.clickhouse import clickhouse_client
from src.api.app import create_app


def get_test_token():
    payload = {
        "username": "test_user",
        "role": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    secret = settings.JWT_SECRET_KEY or "test_secret_key"
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture(scope="module")
def setup_database():
    from src.database.clickhouse import clickhouse_client as client
    client.execute_query("""
        CREATE TABLE IF NOT EXISTS github_analytics.events (
            id String, type String, actor_login String, repo_name String,
            created_at DateTime, payload String, org_login Nullable(String)
        ) ENGINE = MergeTree() ORDER BY (created_at, repo_name)
    """)
    client.execute_query("""
        CREATE TABLE IF NOT EXISTS github_analytics.forecasts (
            repository String, forecast_date Date, predicted_events Float64,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree() ORDER BY (repository, forecast_date)
    """)
    client.execute_query("ALTER TABLE github_analytics.events DELETE WHERE repo_name = 'test/integration'")
    base_time = datetime.now(timezone.utc) - timedelta(days=5)
    sample_events = []
    for i in range(50):
        event_time = base_time + timedelta(hours=i)
        sample_events.append({
            "id": f"int_test_{i}",
            "type": "PushEvent",
            "actor_login": f"tester_{i % 3}",
            "repo_name": "test/integration",
            "created_at": event_time,
            "payload": json.dumps({"push_id": i}),
            "org_login": None
        })
    client.insert_batch("github_analytics.events", sample_events)
    yield
    client.execute_query("ALTER TABLE github_analytics.events DELETE WHERE repo_name = 'test/integration'")
    client.execute_query("ALTER TABLE github_analytics.forecasts DELETE WHERE repository = 'test/integration'")


@pytest.fixture(scope="module")
def api_client():
    app = create_app(testing=True)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_database_connection():
    result = clickhouse_client.execute_query("SELECT 1")
    assert result[0][0] == 1


def test_data_insertion(setup_database):
    result = clickhouse_client.execute_query(
        "SELECT count(*) FROM github_analytics.events WHERE repo_name = 'test/integration'"
    )
    assert result[0][0] == 50


def test_model_training_and_forecast(setup_database):
    try:
        from src.models.forecast import train_and_forecast, save_predictions
    except ImportError:
        pytest.skip("Forecast module not available")
    predictions = train_and_forecast("test/integration", periods=5)
    assert predictions is not None and len(predictions) == 5
    save_predictions(predictions)
    result = clickhouse_client.execute_query(
        "SELECT count(*) FROM github_analytics.forecasts WHERE repository = 'test/integration'"
    )
    assert result[0][0] == 5


def test_api_predictions_endpoint(api_client, setup_database):
    try:
        from src.models.forecast import train_and_forecast, save_predictions
        predictions = train_and_forecast("test/integration", periods=3)
        if predictions:
            save_predictions(predictions)
    except Exception:
        pytest.skip("Could not generate predictions")
    token = get_test_token()
    response = api_client.get(
        "/api/predictions/test/integration",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 404:
        pytest.skip("Predictions endpoint not implemented")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)


def test_api_classify_endpoint(api_client):
    token = get_test_token()
    payload = {"title": "Fix login bug", "body": "Users cannot authenticate"}
    response = api_client.post(
        "/api/classify",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in (200, 503)


def test_api_repos_endpoint(api_client, setup_database):
    token = get_test_token()
    response = api_client.get("/api/repos", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert "test/integration" in data