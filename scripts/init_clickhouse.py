#!/usr/bin/env python3

import sys
import os
import time

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.clickhouse import clickhouse_client
from src.utils.logger import logger

def init_clickhouse():
    """Inicializar la base de datos de ClickHouse"""
    
    # Esperar a que ClickHouse esté listo
    logger.info("Esperando que ClickHouse esté listo...")
    time.sleep(10)
    
    try:
        # Crear base de datos
        clickhouse_client.execute_query('CREATE DATABASE IF NOT EXISTS github_analytics')
        logger.info("✅ Base de datos creada/existe")
        
        # Crear tabla de eventos
        clickhouse_client.execute_query('''
            CREATE TABLE IF NOT EXISTS github_analytics.events
            (
                id String,
                type String,
                actor_login String,
                repo_name String,
                created_at DateTime,
                payload String,
                org_login Nullable(String),
                _inserted_at DateTime DEFAULT now()
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(created_at)
            ORDER BY (created_at, repo_name, type)
        ''')
        logger.info("✅ Tabla events creada")
        
        # Crear tabla de resumen diario
        clickhouse_client.execute_query('''
            CREATE TABLE IF NOT EXISTS github_analytics.daily_summary
            (
                date Date,
                repo_name String,
                event_type String,
                event_count UInt32,
                unique_users UInt32
            ) ENGINE = SummingMergeTree()
            PARTITION BY toYYYYMM(date)
            ORDER BY (date, repo_name, event_type)
        ''')
        logger.info("✅ Tabla daily_summary creada")
        
        # Crear vista materializada
        clickhouse_client.execute_query('''
            CREATE MATERIALIZED VIEW IF NOT EXISTS github_analytics.events_daily_mv
            TO github_analytics.daily_summary AS
            SELECT
                toDate(created_at) as date,
                repo_name,
                type as event_type,
                count(*) as event_count,
                uniq(actor_login) as unique_users
            FROM github_analytics.events
            GROUP BY date, repo_name, event_type
        ''')
        logger.info("✅ Vista materializada creada")
        
        print("🎉 ClickHouse inicializado exitosamente!")
        
    except Exception as e:
        logger.error(f"Error inicializando ClickHouse: {e}")
        raise

if __name__ == '__main__':
    init_clickhouse()