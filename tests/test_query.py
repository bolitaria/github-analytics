#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.clickhouse import clickhouse_client

def main():
    df = clickhouse_client.query_dataframe("SELECT * FROM github_analytics.events LIMIT 5")
    print(df)
    print(f"Filas: {len(df)}")

if __name__ == "__main__":
    main()