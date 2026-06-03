from src.database.clickhouse import clickhouse_client
from src.auth.utils import hash_password, check_password


class User:
    @staticmethod
    def create_table():
        query = """
        CREATE TABLE IF NOT EXISTS github_analytics.users (
            username String,
            password_hash String,
            role String DEFAULT 'user',
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY username
        """
        clickhouse_client.execute_query(query)

    @staticmethod
    def create(username: str, password: str, role: str = "user"):
        password_hash = hash_password(password)
        query = """
        INSERT INTO github_analytics.users (username, password_hash, role)
        VALUES (%(username)s, %(password_hash)s, %(role)s)
        """
        clickhouse_client.execute_query(
            query, {"username": username, "password_hash": password_hash, "role": role}
        )

    @staticmethod
    def get_by_username(username: str):
        query = """
        SELECT username, password_hash, role
        FROM github_analytics.users
        WHERE username = %(username)s
        """
        result = clickhouse_client.execute_query(query, {"username": username})
        if result:
            return {
                "username": result[0][0],
                "password_hash": result[0][1],
                "role": result[0][2],
            }
        return None

    @staticmethod
    def verify_password(user: dict, password: str) -> bool:
        return check_password(password, user["password_hash"])
