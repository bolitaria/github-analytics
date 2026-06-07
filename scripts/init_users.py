#!/usr/bin/env python3
"""
Initialize default users in ClickHouse: create admin user if not exists.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.auth.utils import hash_password
from src.database.clickhouse import clickhouse_client
from src.utils.logger import logger


def init_users():
    """Create admin user if it does not exist."""
    # Ensure users table exists (in case init_clickhouse.py hasn't been run)
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

    # Check if admin already exists
    result = clickhouse_client.execute_query(
        "SELECT count() FROM github_analytics.users WHERE username = 'admin'"
    )
    if result[0][0] == 0:
        password_hash = hash_password("admin123")
        clickhouse_client.execute_query(
            "INSERT INTO github_analytics.users (username, password_hash, role) VALUES ('admin', %(hash)s, 'admin')",
            {"hash": password_hash}
        )
        logger.info("✅ Admin user created (username: admin, password: admin123)")
    else:
        logger.info("ℹ️ Admin user already exists")


if __name__ == "__main__":
    init_users()