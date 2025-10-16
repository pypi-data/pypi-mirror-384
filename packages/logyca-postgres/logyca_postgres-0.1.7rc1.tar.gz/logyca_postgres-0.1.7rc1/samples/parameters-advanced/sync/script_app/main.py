from logyca import parse_bool
from logyca_postgres import SyncConnEngine, commit_rollback_sync, check_connection_sync
from sqlalchemy import text as text_to_sql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.orm.session import Session
import os
from enum import Enum

class ConnectionPool(Enum):
    DEFAULT = QueuePool
    NULL_POOL = NullPool
    QUEUE_POOL = QueuePool

DB_USER=os.getenv('DB_USER','postgres')
DB_PASS=os.getenv('DB_PASS','***')
DB_HOST=os.getenv('DB_HOST','localhost')
DB_PORT=os.getenv('DB_PORT',5432)
DB_NAME=os.getenv('DB_NAME','test')
DB_SSL_ENABLE=parse_bool(os.getenv('DB_SSL_ENABLE',False))

class SyncConnEngineAdvancedParameters(SyncConnEngine):
    def __init__(self, url_connection: str, server_settings: dict, connection_pool:ConnectionPool = ConnectionPool.DEFAULT):
        super().__init__(url_connection, server_settings)

        kwargs = {
            "url": url_connection,
            "echo":False,
            "future":True,
            "connect_args":{
                "application_name": server_settings["application_name"],
            },
        }

        match connection_pool.name:
            case ConnectionPool.NULL_POOL.name:
                    kwargs["poolclass"]=NullPool
            case ConnectionPool.DEFAULT.name | ConnectionPool.QUEUE_POOL.name:
                    kwargs["poolclass"]=QueuePool
                    kwargs["pool_size"]=server_settings["pool_size"]
                    kwargs["max_overflow"]=server_settings["max_overflow"]
                    kwargs["pool_recycle"]=server_settings["pool_recycle"]
            case _ :
                    raise ValueError(f"Pool type not supported: {connection_pool}")

        new_engine = create_engine(**kwargs)

        self._SyncConnEngine__engine.dispose()
        self._SyncConnEngine__engine = new_engine

        self._SyncConnEngine__sync_session_maker = sessionmaker(
            bind=self._SyncConnEngine__engine,
            autoflush=False
        )

conn_sync_session=SyncConnEngineAdvancedParameters(
    url_connection=SyncConnEngine.build_url_connection(user=DB_USER,password=DB_PASS,host=DB_HOST,port=DB_PORT,database=DB_NAME,ssl_enable=DB_SSL_ENABLE),
    server_settings=SyncConnEngine.server_settings(pool_size=5,max_overflow=1,pool_recycle=10800,application_name="MyApp - SyncConnEngine"),
    connection_pool=ConnectionPool.DEFAULT
    )

'''
The connection pool (pool_size) after the first query will remain open until the application is stopped or the engine is terminated: close_engine().
'''

def methods(sync_session: Session):
    status, date_time_or_exception_error = check_connection_sync(sync_session)
    print("\n\n")
    if(status):
        query = text_to_sql("SELECT now();")
        result = sync_session.execute(query)
        simulated_query = result.fetchone()[0]
        commit_rollback_sync(sync_session)
        print(f"date_time_or_exception_error={date_time_or_exception_error},simulated_query={simulated_query}")
    else:
        print(f"sync_session connect db error...{date_time_or_exception_error}")

def main():
    for sync_session in conn_sync_session.get_sync_session():
        methods(sync_session)
    conn_sync_session.close_engine()            


if __name__ == "__main__":
    main()
