#!/usr/bin/env python3
"""
Automated training script for models.
Trains forecast model and issue classifier, then saves predictions.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.forecast import train_and_forecast, save_predictions
from src.models.issue_classifier import train_classifier
from src.database.clickhouse import clickhouse_client
from src.utils.logger import logger

def train_forecast_models():
    """Train forecast models for all repositories."""
    result = clickhouse_client.execute_query("SELECT DISTINCT repo_name FROM github_analytics.events")
    repos = [row[0] for row in result]
    for repo in repos:
        predictions = train_and_forecast(repo)
        if predictions:
            save_predictions(predictions)

def train_issue_model():
    """Train issue classifier and save model."""
    train_classifier()  # This function should save the model to disk

def main():
    logger.info("Starting automatic training...")
    train_forecast_models()
    train_issue_model()
    logger.info("Training completed.")

if __name__ == '__main__':
    main()