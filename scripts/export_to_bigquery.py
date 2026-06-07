#!/usr/bin/env python3
import sys
import os
import pandas as pd
from google.cloud import bigquery
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.clickhouse import clickhouse_client
from src.utils.logger import logger

def export_table(table_name, dataset_id='github_analytics'):
    logger.info(f"Exportando {table_name} a BigQuery...")
    # Leer toda la tabla de ClickHouse
    df = clickhouse_client.query_dataframe(f"SELECT * FROM github_analytics.{table_name}")
    if df.empty:
        logger.warning(f"Tabla {table_name} vacía")
        return
    
    # Subir a BigQuery
    client = bigquery.Client()
    dataset_ref = client.dataset(dataset_id)
    try:
        client.get_dataset(dataset_ref)
    except Exception:
        client.create_dataset(dataset_ref)
    
    table_id = f"{dataset_id}.{table_name}"
    df.to_gbq(table_id, project_id=client.project, if_exists='replace')
    logger.info(f"Exportada {table_name} con {len(df)} filas")

if __name__ == '__main__':
    tables = ['events', 'issues', 'forecasts', 'repo_activity']
    for table in tables:
        export_table(table)