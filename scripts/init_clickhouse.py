#!/usr/bin/env python3
"""
ClickHouse initialization script
"""
import time
import logging
from clickhouse_driver import Client  # Use the native driver

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_analytics')

def wait_for_clickhouse(max_retries=30, retry_interval=2):
    """Wait for ClickHouse to be fully ready"""
    logger.info("Waiting for ClickHouse to be ready...")
    
    for i in range(max_retries):
        try:
            # Try to connect using the native client (port 9001 on host)
            client = Client(host='localhost', port=9001, user='default', password='')
            # Execute a simple query to verify
            client.execute('SELECT 1')
            logger.info("✅ ClickHouse is ready and responding")
            return True
        except Exception as e:
            if i < max_retries - 1:
                logger.warning(f"Attempt {i+1}/{max_retries}: ClickHouse not ready - {str(e)[:100]}...")
                time.sleep(retry_interval)
            else:
                logger.error(f"❌ ClickHouse could not be initialized after {max_retries} attempts")
                return False
    return False

def init_clickhouse():
    """Initialize the ClickHouse database"""
    try:
        # Wait for ClickHouse to be ready
        if not wait_for_clickhouse():
            raise Exception("ClickHouse is not available")
        
        # Create client for operations
        clickhouse_client = Client(host='localhost', port=9001, user='default', password='')
        
        logger.info("Initializing database...")
        
        # Create database
        clickhouse_client.execute('CREATE DATABASE IF NOT EXISTS github_analytics')
        logger.info("✅ Database created/exists")
        
        # Create tables
        tables = [
            """
            CREATE TABLE IF NOT EXISTS github_analytics.repo_activity (
                timestamp DateTime,
                repository String,
                event_type String,
                user_login String,
                commits UInt32,
                additions UInt32,
                deletions UInt32,
                issues_opened UInt32,
                issues_closed UInt32,
                pull_requests_opened UInt32,
                pull_requests_merged UInt32
            ) ENGINE = MergeTree()
            ORDER BY (timestamp, repository)
            """,
            """
            CREATE TABLE IF NOT EXISTS github_analytics.daily_summary (
                date Date,
                repository String,
                total_commits UInt32,
                total_additions UInt32,
                total_deletions UInt32,
                total_issues UInt32,
                total_pull_requests UInt32,
                unique_contributors UInt32
            ) ENGINE = MergeTree()
            ORDER BY (date, repository)
            """,
            """
            CREATE TABLE IF NOT EXISTS github_analytics.forecasts (
                repository String,
                forecast_date Date,
                predicted_events UInt32,
                lower_bound UInt32,
                upper_bound UInt32,
                model_type String,
                training_date Date
            ) ENGINE = MergeTree()
            ORDER BY (repository, forecast_date)
            """,
            """
            CREATE TABLE IF NOT EXISTS github_analytics.issues (
                id UInt64,
                number UInt32,
                title String,
                body String,
                labels Array(String),
                state String,
                created_at DateTime,
                closed_at Nullable(DateTime),
                user_login String,
                repo_name String
            ) ENGINE = MergeTree()
            ORDER BY (repo_name, created_at)
            """,
            """
            CREATE TABLE IF NOT EXISTS github_analytics.issue_predictions (
                issue_id UInt64,
                predicted_label String,
                confidence Float32,
                prediction_date Date
            ) ENGINE = MergeTree()
            ORDER BY (issue_id)
            """
        ]
        
        for table_sql in tables:
            clickhouse_client.execute(table_sql)
        
        logger.info("✅ Tables created/exist")
        logger.info("✅ ClickHouse initialization completed")
        
    except Exception as e:
        logger.error(f"❌ Error initializing ClickHouse: {e}")
        raise

if __name__ == "__main__":
    init_clickhouse()