#!/usr/bin/env python3
"""
Initialize ClickHouse database: create database, tables, and materialized views.
"""
import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.clickhouse import clickhouse_client
from src.utils.logger import logger


def init_clickhouse():
    """Initialize ClickHouse: create database, tables, and views."""
    # Wait for ClickHouse to be ready
    logger.info("Waiting for ClickHouse to be ready...")
    time.sleep(5)

    try:
        # Create database
        clickhouse_client.execute_query('CREATE DATABASE IF NOT EXISTS github_analytics')
        logger.info("✅ Database created/exists")

        # Create events table
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
        logger.info("✅ Table events created")

        # Create daily summary table
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
        logger.info("✅ Table daily_summary created")

        # Create forecasts table
        clickhouse_client.execute_query('''
            CREATE TABLE IF NOT EXISTS github_analytics.forecasts
            (
                repository String,
                forecast_date Date,
                predicted_events Float64,
                created_at DateTime DEFAULT now()
            ) ENGINE = MergeTree()
            ORDER BY (repository, forecast_date)
        ''')
        logger.info("✅ Table forecasts created")

        # Create users table
        clickhouse_client.execute_query('''
            CREATE TABLE IF NOT EXISTS github_analytics.users
            (
                username String,
                password_hash String,
                role String DEFAULT 'user',
                created_at DateTime DEFAULT now()
            ) ENGINE = MergeTree()
            ORDER BY username
        ''')
        logger.info("✅ Table users created")

        # Create materialized view for daily aggregation
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
        logger.info("✅ Materialized view created")

        print("🎉 ClickHouse initialized successfully!")

    except Exception as e:
        logger.error(f"Error initializing ClickHouse: {e}")
        raise


if __name__ == '__main__':
    init_clickhouse()