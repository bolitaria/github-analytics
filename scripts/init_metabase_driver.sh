#!/bin/bash
# scripts/init_metabase_driver.sh
set -e

DRIVER_URL="https://github.com/ClickHouse/clickhouse-jdbc/releases/download/v0.4.6/clickhouse-jdbc-0.4.6-shaded.jar"
DRIVER_DIR="./drivers"
DRIVER_FILE="${DRIVER_DIR}/clickhouse.metabase-driver.jar"

mkdir -p "$DRIVER_DIR"

if [ ! -f "$DRIVER_FILE" ]; then
    echo "Downloading ClickHouse JDBC driver for Metabase..."
    wget -q --show-progress "$DRIVER_URL" -O "$DRIVER_FILE"
    echo "Driver saved to $DRIVER_FILE"
else
    echo "Driver already exists: $DRIVER_FILE (skip download)"
fi