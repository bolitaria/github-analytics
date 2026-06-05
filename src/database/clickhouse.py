import pandas as pd
from clickhouse_driver import Client
from src.config.settings import settings
from src.utils.logger import logger


class ClickHouseClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
        return cls._instance

    @property
    def client(self):
        if self._client is None:
            try:
                self._client = Client(
                    host=settings.CLICKHOUSE_HOST,
                    port=settings.CLICKHOUSE_PORT,  # Usa la variable de entorno (9001)
                    user=settings.CLICKHOUSE_USER,
                    password=settings.CLICKHOUSE_PASSWORD,
                    database=settings.CLICKHOUSE_DATABASE,
                )
                logger.info("ClickHouse client initialized with native protocol")
            except Exception as e:
                logger.error(f"Failed to connect to ClickHouse: {e}")
                raise
        return self._client

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
        values = [tuple(item[col] for col in columns) for item in data]
        try:
            self.client.execute(query, values)
        except Exception as e:
            logger.error(f"Error in batch insert: {e}")
            raise

    def query_dataframe(self, query: str, params=None):
        try:
            rows, columns = self.client.execute(query, params, with_column_types=True)
            if not rows:
                return pd.DataFrame()
            df = pd.DataFrame(rows, columns=[col[0] for col in columns])
            return df
        except Exception as e:
            logger.error(f"Error in query_dataframe: {e}")
            return pd.DataFrame()


clickhouse_client = ClickHouseClient()
