#!/usr/bin/env python3
"""
Script para entrenar modelos y generar predicciones periódicamente.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.forecast import train_and_forecast, save_predictions
from src.database.clickhouse import clickhouse_client
from src.utils.logger import logger

def train_for_all_repos():
    """Entrena modelos para todos los repositorios en la base de datos."""
    # Obtener lista de repositorios únicos
    result = clickhouse_client.execute_query(
        "SELECT DISTINCT repository FROM github_analytics.repo_activity"
    )
    repos = [row[0] for row in result]
    
    for repo in repos:
        predictions = train_and_forecast(repo)
        if predictions:
            save_predictions(predictions)
    
    logger.info("Entrenamiento completado para todos los repositorios")

if __name__ == "__main__":
    train_for_all_repos()