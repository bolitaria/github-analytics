#!/usr/bin/env python3
"""
Predict labels for issues that don't have a prediction yet.
"""
import sys
import os
import joblib
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.clickhouse import clickhouse_client
from src.utils.logger import logger

def load_model():
    model_path = 'models/issue_classifier.pkl'
    if not os.path.exists(model_path):
        logger.error("Model not found. Train first with train_issue_classifier.py")
        return None
    return joblib.load(model_path)

def get_issues_without_prediction():
    query = """
    SELECT id, title, body
    FROM github_analytics.issues
    WHERE id NOT IN (SELECT issue_id FROM github_analytics.issue_predictions)
    """
    result = clickhouse_client.execute_query(query)
    return result

def save_predictions(predictions):
    if not predictions:
        return
    query = """
    INSERT INTO github_analytics.issue_predictions (issue_id, predicted_label, confidence, prediction_date)
    VALUES
    """
    values = [(p['id'], p['label'], p['confidence'], datetime.now().date()) for p in predictions]
    clickhouse_client.client.execute(query, values)
    logger.info(f"Saved {len(predictions)} predictions.")

def main():
    model = load_model()
    if not model:
        return
    issues = get_issues_without_prediction()
    if not issues:
        logger.info("No issues to predict.")
        return
    predictions = []
    for issue in issues:
        issue_id, title, body = issue
        text = f"{title} {body if body else ''}"
        pred = model.predict([text])[0]
        proba = model.predict_proba([text]).max()
        predictions.append({
            'id': issue_id,
            'label': pred,
            'confidence': proba
        })
        if len(predictions) % 100 == 0:
            save_predictions(predictions)
            predictions = []
    if predictions:
        save_predictions(predictions)

if __name__ == '__main__':
    main()