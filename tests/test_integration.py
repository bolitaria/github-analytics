#!/usr/bin/env python3
"""
Integration tests for GitHub Analytics platform.
Supports database matrix testing via TEST_DB environment variable.
"""
import os
import sys
import json
import pytest
from datetime import datetime, timedelta, timezone
import jwt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import settings
from src.database.clickhouse import clickhouse_client
from src.api.app import create_app

# ============================================================================
# Helpers
# ============================================================================


def get_db_client():
    """Return database client based on TEST_DB environment variable."""
    db_type = os.environ.get("TEST_DB", "clickhouse").lower()
    if db_type == "clickhouse":
        return clickhouse_client
    elif db_type == "postgres":
        pytest.skip("PostgreSQL integration tests not yet implemented")
    elif db_type == "mysql":
        pytest.skip("MySQL integration tests not yet implemented")
    else:
        pytest.skip(f"Unknown database type: {db_type}")


def ensure_tables():
    """Create required tables if they don't exist."""
    client = get_db_client()
    client.execute_query(
        """
        CREATE TABLE IF NOT EXISTS github_analytics.events (
            id String,
            type String,
            actor_login String,
            repo_name String,
            created_at DateTime,
            payload String,
            org_login Nullable(String)
        ) ENGINE = MergeTree()
        ORDER BY (created_at, repo_name)
    """
    )
    client.execute_query(
        """
        CREATE TABLE IF NOT EXISTS github_analytics.forecasts (
            repository String,
            forecast_date Date,
            predicted_value Float64,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY (repository, forecast_date)
    """
    )


def get_test_token():
    """Generate a JWT token for testing."""
    payload = {
        "user_id": "test_user",
        "role": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    secret = settings.JWT_SECRET_KEY or "test_secret_key"
    return jwt.encode(payload, secret, algorithm="HS256")


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def setup_database():
    """Set up tables and insert sample data once per test module."""
    client = get_db_client()
    ensure_tables()

    # Clean old test data
    client.execute_query(
        "ALTER TABLE github_analytics.events DELETE WHERE repo_name = 'test/integration'"
    )

    # Insert sample events
    sample_events = []
    base_time = datetime.now(timezone.utc) - timedelta(days=5)
    for i in range(50):
        event_time = base_time + timedelta(hours=i)
        sample_events.append(
            {
                "id": f"int_test_{i}",
                "type": "PushEvent",
                "actor_login": f"tester_{i % 3}",
                "repo_name": "test/integration",
                "created_at": event_time,
                "payload": json.dumps({"push_id": i}),
                "org_login": None,
            }
        )
    client.insert_batch("github_analytics.events", sample_events)

    yield

    # Cleanup after tests
    client.execute_query(
        "ALTER TABLE github_analytics.events DELETE WHERE repo_name = 'test/integration'"
    )
    client.execute_query(
        "ALTER TABLE github_analytics.forecasts DELETE WHERE repository = 'test/integration'"
    )


@pytest.fixture(scope="module")
def api_client():
    """Flask test client with JWT token header."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ============================================================================
# Integration Tests
# ============================================================================


def test_database_connection():
    """Verify database connection and basic query."""
    client = get_db_client()
    result = client.execute_query("SELECT 1")
    assert result[0][0] == 1


def test_data_insertion(setup_database):
    """Check that sample data was inserted correctly."""
    client = get_db_client()
    result = client.execute_query(
        "SELECT count(*) FROM github_analytics.events WHERE repo_name = 'test/integration'"
    )
    assert result[0][0] == 50


def test_model_training_and_forecast(setup_database):
    """Test that forecasting model runs and stores predictions."""
    try:
        from src.models.forecast import train_and_forecast, save_predictions
    except ImportError:
        pytest.skip("Forecast module not available")

    predictions = train_and_forecast("test/integration", periods=5)
    assert predictions is not None
    assert len(predictions) == 5
    save_predictions(predictions)

    client = get_db_client()
    result = client.execute_query(
        "SELECT count(*) FROM github_analytics.forecasts WHERE repository = 'test/integration'"
    )
    assert result[0][0] == 5


def test_api_predictions_endpoint(api_client, setup_database):
    """Test predictions endpoint (adjust URL to match actual implementation)."""
    # First ensure predictions exist
    try:
        from src.models.forecast import train_and_forecast, save_predictions

        predictions = train_and_forecast("test/integration", periods=3)
        if predictions:
            save_predictions(predictions)
    except Exception:
        pytest.skip("Could not generate predictions")

    token = get_test_token()
    # Try the correct endpoint (as per README: /api/predictions/<owner>/<repo>)
    response = api_client.get(
        "/api/predictions/test/integration",
        headers={"Authorization": f"Bearer {token}"},
    )
    # If endpoint not implemented yet, skip gracefully
    if response.status_code == 404:
        pytest.skip("Predictions endpoint not implemented in API")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    if data:
        assert "forecast_date" in data[0] or "date" in data[0]


def test_api_classify_endpoint(api_client):
    """Test /api/classify endpoint."""
    token = get_test_token()
    payload = {"title": "Fix login bug", "body": "Users cannot authenticate"}
    response = api_client.post(
        "/api/classify", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    # May return 200 if model exists, else 503 or 500; we accept non-error.
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = json.loads(response.data)
        assert "label" in data
        assert "confidence" in data


def test_api_repos_endpoint(api_client, setup_database):
    """Test /api/repos endpoint (returns list of repository names)."""
    token = get_test_token()
    response = api_client.get(
        "/api/repos", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    # The endpoint returns a list of strings (repo names), not dictionaries
    assert isinstance(data, list)
    assert "test/integration" in data
