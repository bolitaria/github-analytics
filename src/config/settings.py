import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

    # Cambiar a puerto 9001 para protocolo nativo
    CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
    CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", 9001))  # 9001 para nativo
    CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
    CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
    CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "github_analytics")

    GITHUB_API_BASE_URL = "https://api.github.com"
    GITHUB_RATE_LIMIT_DELAY = 1

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tu-secreto-super-seguro")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 1440)
    )

    @property
    def has_github_token(self):
        return bool(self.GITHUB_TOKEN)


settings = Settings()
