from enum import StrEnum

class Environment:

    class PostgreSQL(StrEnum):
        HOST = "ENGINE_POSTGRES_CONN_HOST"
        DB_NAME = "ENGINE_POSTGRES_CONN_DB"
        PASSWORD = "ENGINE_POSTGRES_CONN_PASSWORD"
        PORT = "ENGINE_POSTGRES_CONN_PORT"
        USER = "ENGINE_POSTGRES_CONN_USER"
        SSL = "ENGINE_POSTGRES_CONN_SSL"