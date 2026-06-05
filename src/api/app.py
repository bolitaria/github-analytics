import os
import joblib
from datetime import datetime
from flask import Flask, request, jsonify
from src.auth.models import User
from src.auth.utils import create_token
from src.auth.decorators import token_required
from src.database.clickhouse import clickhouse_client
from src.utils.logger import logger

# Load classification model if exists
model = None
model_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "issue_classifier.pkl"
)
if os.path.exists(model_path):
    try:
        model = joblib.load(model_path)
        logger.info("Modelo de clasificación cargado")
    except Exception as e:
        logger.error(f"Error cargando modelo: {e}")
else:
    logger.warning(
        "Modelo no encontrado. Entrena primero con train_issue_classifier.py"
    )


def create_app(testing=False):
    app = Flask(__name__)
    if testing:
        app.config["TESTING"] = True

    # Only create tables if not in testing mode
    if not app.config.get("TESTING", False):
        User.create_table()

    # ------------------------------------------------------------------
    # Public endpoints
    # ------------------------------------------------------------------
    @app.route("/api/health", methods=["GET"])
    def health():
        return (
            jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}),
            200,
        )

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        username = data.get("username")
        password = data.get("password")
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400

        user = User.get_by_username(username)
        if not user or not User.verify_password(user, password):
            return jsonify({"error": "Invalid credentials"}), 401

        token = create_token(user["username"], user["role"])
        return (
            jsonify(
                {
                    "token": token,
                    "user": {"username": user["username"], "role": user["role"]},
                }
            ),
            200,
        )

    # ------------------------------------------------------------------
    # Protected endpoints (require JWT)
    # ------------------------------------------------------------------
    @app.route("/api/repos", methods=["GET"])
    @token_required
    def list_repos(current_user):
        query = """
            SELECT DISTINCT repo_name
            FROM github_analytics.events
            ORDER BY repo_name
        """
        try:
            result = clickhouse_client.execute_query(query)
            repos = [row[0] for row in result]
            return jsonify(repos), 200
        except Exception as e:
            logger.error(f"Error listing repos: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/repos/<owner>/<repo>/activity", methods=["GET"])
    @token_required
    def repo_activity(current_user, owner, repo):
        repo_name = f"{owner}/{repo}"
        query = """
            SELECT toDate(created_at) as date,
                   count(*) as events,
                   uniq(actor_login) as contributors
            FROM github_analytics.events
            WHERE repo_name = %(repo_name)s
            GROUP BY date
            ORDER BY date DESC
            LIMIT 30
        """
        try:
            result = clickhouse_client.execute_query(query, {"repo_name": repo_name})
            data = [
                {"date": str(row[0]), "events": row[1], "contributors": row[2]}
                for row in result
            ]
            return jsonify(data), 200
        except Exception as e:
            logger.error(f"Error fetching activity for {repo_name}: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/predictions/<owner>/<repo>", methods=["GET"])
    @token_required
    def get_predictions(current_user, owner, repo):
        repo_name = f"{owner}/{repo}"
        query = """
            SELECT forecast_date, predicted_events
            FROM github_analytics.forecasts
            WHERE repository = %(repo_name)s
            ORDER BY forecast_date
        """
        try:
            result = clickhouse_client.execute_query(query, {"repo_name": repo_name})
            data = [
                {"forecast_date": str(row[0]), "predicted": row[1]} for row in result
            ]
            return jsonify(data), 200
        except Exception as e:
            logger.error(f"Error fetching predictions for {repo_name}: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/classify", methods=["POST"])
    @token_required
    def classify_issue(current_user):
        data = request.get_json()
        if not data or "title" not in data:
            return jsonify({"error": "Title required"}), 400

        title = data["title"]
        body = data.get("body", "")
        text = f"{title}. {body}"

        if model is None:
            return jsonify({"error": "Model not trained yet"}), 503

        try:
            prediction = model.predict([text])[0]
            confidence = 0.85
            return jsonify({"label": prediction, "confidence": confidence}), 200
        except Exception as e:
            logger.error(f"Error during classification: {e}")
            return jsonify({"error": "Classification failed"}), 500

    @app.route("/api/metrics/event-types", methods=["GET"])
    @token_required
    def event_type_metrics(current_user):
        query = """
            SELECT type, count(*) as count
            FROM github_analytics.events
            GROUP BY type
            ORDER BY count DESC
        """
        try:
            result = clickhouse_client.execute_query(query)
            data = [{"event_type": row[0], "count": row[1]} for row in result]
            return jsonify(data), 200
        except Exception as e:
            logger.error(f"Error fetching event type metrics: {e}")
            return jsonify({"error": "Internal server error"}), 500

    return app
