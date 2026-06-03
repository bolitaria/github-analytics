import os
import joblib
from datetime import datetime
from flask import Flask, request, jsonify
from src.auth.models import User
from src.auth.utils import create_token
from src.auth.decorators import token_required
from src.database.clickhouse import clickhouse_client
from src.utils.logger import logger
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer

# Cargar modelo de clasificación de issues (si existe)
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


def create_app():
    app = Flask(__name__)

    # ---------------------------
    # Endpoints de autenticación
    # ---------------------------
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
        return jsonify(
            {
                "token": token,
                "user": {"username": user["username"], "role": user["role"]},
            }
        )

    @app.route("/api/protected", methods=["GET"])
    @token_required
    def protected():
        return jsonify({"message": f"Hello {request.user['username']}"})

    # ---------------------------
    # Endpoints de datos
    # ---------------------------
    @app.route("/api/repos", methods=["GET"])
    @token_required
    def list_repos():
        try:
            result = clickhouse_client.execute_query(
                "SELECT DISTINCT repo_name FROM github_analytics.events ORDER BY repo_name"
            )
            repos = [row[0] for row in result]
            return jsonify(repos)
        except Exception as e:
            logger.error(f"Error listing repos: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/repos/<path:repo_name>/activity", methods=["GET"])
    @token_required
    def repo_activity(repo_name):
        try:
            query = """
                SELECT toDate(created_at) as date, count() as events
                FROM github_analytics.events
                WHERE repo_name = %(repo)s
                GROUP BY date
                ORDER BY date
            """
            result = clickhouse_client.execute_query(query, {"repo": repo_name})
            data = [{"date": row[0].isoformat(), "events": row[1]} for row in result]
            return jsonify(data)
        except Exception as e:
            logger.error(f"Error fetching activity for {repo_name}: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/predictions/<path:repo_name>", methods=["GET"])
    @token_required
    def get_predictions(repo_name):
        try:
            query = """
                SELECT forecast_date, predicted_events, lower_bound, upper_bound
                FROM github_analytics.forecasts
                WHERE repository = %(repo)s
                ORDER BY forecast_date
            """
            result = clickhouse_client.execute_query(query, {"repo": repo_name})
            data = [
                {
                    "date": row[0].isoformat(),
                    "predicted": row[1],
                    "lower": row[2],
                    "upper": row[3],
                }
                for row in result
            ]
            return jsonify(data)
        except Exception as e:
            logger.error(f"Error fetching predictions for {repo_name}: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/classify", methods=["POST"])
    @token_required
    def classify_issue():
        if model is None:
            return jsonify({"error": "Model not available"}), 503

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        title = data.get("title", "")
        body = data.get("body", "")
        text = title + " " + body

        try:
            pred = model.predict([text])[0]
            proba = model.predict_proba([text]).max()
            return jsonify({"label": pred, "confidence": float(proba)})
        except Exception as e:
            logger.error(f"Error during classification: {e}")
            return jsonify({"error": "Classification failed"}), 500

    # ---------------------------
    # Nuevo endpoint de resumen con sumy
    # ---------------------------
    def summarize_text(text, sentences_count=2):
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = TextRankSummarizer()
        summary = summarizer(parser.document, sentences_count)
        return " ".join(str(sentence) for sentence in summary)

    @app.route("/api/summarize", methods=["POST"])
    @token_required
    def summarize_endpoint():
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "Missing text"}), 400
        try:
            summary = summarize_text(data["text"])
            return jsonify({"summary": summary})
        except Exception as e:
            logger.error(f"Error in summarization: {e}")
            return jsonify({"error": "Summarization failed"}), 500

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify(
            {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
        )

    return app
