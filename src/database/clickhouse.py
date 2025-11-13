from clickhouse_driver import Client
from src.config.settings import settings
from src.utils.logger import logger

class ClickHouseClient:
    def __init__(self):
        self.client = Client(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            user=settings.CLICKHOUSE_USER,
            password=settings.CLICKHOUSE_PASSWORD,
            database=settings.CLICKHOUSE_DATABASE
        )
        logger.info("ClickHouse client initialized with native protocol")

    def execute_query(self, query: str, params=None):
        try:
            return self.client.execute(query, params)
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

    def insert_batch(self, table: str, data: list):
        if not data:
            return
        
        columns = list(data[0].keys())
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES"
        
        # Preparar valores - NO convertir datetime a string
        values = []
        for item in data:
            row_values = []
            for col in columns:
                value = item[col]
                # ClickHouse driver maneja automáticamente los objetos datetime
                row_values.append(value)
            values.append(tuple(row_values))
        
        try:
            self.client.execute(query, values)
        except Exception as e:
            logger.error(f"Error in batch insert: {e}")
            raise

clickhouse_client = ClickHouseClient()