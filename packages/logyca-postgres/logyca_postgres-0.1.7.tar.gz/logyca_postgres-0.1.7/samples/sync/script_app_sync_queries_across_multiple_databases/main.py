from app.internal.config import settings
from logyca_postgres import SyncConnEngine, commit_rollback_sync, check_connection_sync
from sqlalchemy import text as text_to_sql
from sqlalchemy.orm.session import Session

"""
########################################################################
Global state

- conn_sync_session: SyncConnEngine
  Creates the primary SQLAlchemy Engine (via create_engine) along with its
  connection pool. An Engine’s database URL (bind) is fixed at creation time;
  reusing this Engine will always connect to the same database. To target a
  different database, create a new Engine and dispose the old one.
"""

conn_sync_session=SyncConnEngine(
    url_connection=SyncConnEngine.build_url_connection(user=settings.DB_USER,password=settings.DB_PASS,host=settings.DB_HOST,port=settings.DB_PORT,database=settings.DB_NAME,ssl_enable=settings.DB_SSL),
    server_settings=SyncConnEngine.server_settings(pool_size=5,max_overflow=1,pool_recycle=10800,application_name="MyApp - SyncConnEngine")
)

SEPARATOR    = "======================================"
SUBSEPARATOR = "---------------------"

queries = [
    {
        "database": "postgres",
        "sql": [
            "Create database tmp_test_01;",
            "Create database tmp_test_02;"
        ]
    },
    {
        "database": "tmp_test_01",
        "sql": [
            "SELECT current_database();",
            """
            CREATE TABLE IF NOT EXISTS data_sample_a (
            id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            day           date,
            num           int8 NOT NULL,
            price         float8,
            description   text
            );
            """,
            """
            INSERT INTO data_sample_a (day, num, price, description)
            VALUES ('2025-10-11', 1011, 12.50, 'Product K - sample item');
            """
        ]
    },
    {
        "database": "tmp_test_02",
        "sql": [
            "SELECT current_database();",
            """
            CREATE TABLE IF NOT EXISTS data_sample_b(
            id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            day           date,
            num           int8 NOT NULL,
            price         float8,
            description   text
            );
            """,
            """
            INSERT INTO data_sample_b (day, num, price, description)
            VALUES ('2025-10-30', 1030, 12.50, 'Product AE - sample item');
            """
        ]
    }
]

'''
########################################################################
Functions
'''

def run_on_multiple_databases(database_overwrite:str, queries:list[str]):

    """
    Execute a list of SQL statements against a specific database by creating
    a short-lived Engine bound to `database_overwrite`.

    Notes:
    - Each Engine owns its own connection pool.
    - An Engine’s URL/bind cannot be changed after it is created.
      To use another database, instantiate a new Engine and dispose the old one.
    """
    class SyncConnEngineTmp(SyncConnEngine):
        pass
    """
    Local/temporary Engine

    - conn_sync_session_tmp: SyncConnEngineTMP
      Creates a fresh Engine bound to `database_overwrite`. This Engine has
      its own pool; its URL is immutable after creation. Use a new Engine for
      each target database and close/dispose it when done.
    """
    connect_args = {"connect_timeout":10}
    engine_kwargs = {"isolation_level":"AUTOCOMMIT"}
    conn_sync_session_tmp=SyncConnEngineTmp(
        url_connection=SyncConnEngineTmp.build_url_connection(user=settings.DB_USER,password=settings.DB_PASS,host=settings.DB_HOST,port=settings.DB_PORT,database=database_overwrite,ssl_enable=settings.DB_SSL),
        server_settings=SyncConnEngineTmp.server_settings(pool_size=5,max_overflow=1,pool_recycle=10800,application_name="MyApp - SyncConnEngine",
                                                          connect_args=connect_args,
                                                          engine_kwargs=engine_kwargs
                                                          )
                )
    for sync_session_tmp in conn_sync_session_tmp.get_sync_session():
        for query in queries:
            try:
                query = text_to_sql(query)
                result = sync_session_tmp.execute(query)
                print(f"{SUBSEPARATOR}")
                print(f"Database: {database_overwrite}")
                try:
                    data = result.scalar()
                    print(f"- Query: {query}")
                    print(f"Query result: {data}")
                except:
                    try:
                        commit_rollback_sync(sync_session_tmp)
                        print(f"DML or change in records: {query}")
                    except:
                        pass
            except Exception as e:
                print(str(e))
    conn_sync_session_tmp.close_engine()

def methods(sync_session: Session):
    status, date_time_or_exception_error = check_connection_sync(sync_session)
    if(status):
        query = text_to_sql("SELECT now(), current_database();")
        result = sync_session.execute(query)
        simulated_query = result.fetchone()
        print(f"\n{SEPARATOR}\nQuery OK at {simulated_query[0]}, current_database={simulated_query[1]}")
        for qs in queries:
            database_overwrite = qs.get("database",None)
            run_on_multiple_databases(database_overwrite, qs.get("sql",[]))
    else:
        print(f"sync_session connect db error: {date_time_or_exception_error}")

'''
########################################################################
Main
'''
def main():
    print("\n\n")
    for sync_session in conn_sync_session.get_sync_session():
        methods(sync_session)
    conn_sync_session.close_engine()


main()
