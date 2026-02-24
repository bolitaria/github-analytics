#!/usr/bin/env python3
import schedule
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.etl.github_etl import GitHubETL
from scripts.train_models import train_for_all_repos
from scripts.export_to_bigquery import export_table
from src.utils.logger import logger

def run_etl():
    logger.info("Ejecutando ETL programado...")
    etl = GitHubETL()
    repos = [('ClickHouse', 'ClickHouse'), ('nodejs', 'node'), ('microsoft', 'vscode')]
    for owner, repo in repos:
        try:
            etl.run_etl(owner, repo, days_back=1)
        except Exception as e:
            logger.error(f"Error en ETL de {owner}/{repo}: {e}")

def train_models():
    logger.info("Entrenando modelos programado...")
    train_for_all_repos()

def export_all():
    logger.info("Exportando a BigQuery programado...")
    for table in ['events', 'issues', 'forecasts', 'repo_activity']:
        export_table(table)

if __name__ == '__main__':
    # Programar tareas
    schedule.every().hour.do(run_etl)
    schedule.every().day.at("03:00").do(train_models)
    schedule.every().day.at("04:00").do(export_all)
    
    logger.info("Scheduler iniciado. Presiona Ctrl+C para detener.")
    while True:
        schedule.run_pending()
        time.sleep(60)