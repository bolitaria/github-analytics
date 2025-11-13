#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.getcwd())

from src.database.clickhouse import clickhouse_client

try:
    result = clickhouse_client.execute_query('SHOW DATABASES')
    print('✅ Conexión exitosa a ClickHouse')
    print('Bases de datos disponibles:', result)
except Exception as e:
    print(f'❌ Error de conexión: {e}')