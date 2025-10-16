from app.internal.config import settings
from fastapi import FastAPI, Depends, HTTPException
from logyca import parse_bool
from logyca_postgres import SyncConnEngine, commit_rollback_sync, check_connection_sync
from sqlalchemy import text as text_to_sql
from sqlalchemy.orm.session import Session
import os

app = FastAPI()

conn_sync_session=SyncConnEngine(
    url_connection=SyncConnEngine.build_url_connection(user=settings.DB_USER,password=settings.DB_PASS,host=settings.DB_HOST,port=settings.DB_PORT,database=settings.DB_NAME,ssl_enable=settings.DB_SSL),
    server_settings=SyncConnEngine.server_settings(pool_size=5,max_overflow=1,pool_recycle=10800,application_name="MyApp - SyncConnEngine")
    )

'''
The connection pool (pool_size) after the first query will remain open until the application is stopped.
'''

@app.get("/simulated_query_sync/")
def read_item(sync_session:Session = Depends(conn_sync_session)):
    try:
        status, date_time_or_exception_error = check_connection_sync(sync_session)
        if(status):
            query = text_to_sql("SELECT current_database();")
            result = sync_session.execute(query)
            simulated_query = result.fetchone()[0]
            commit_rollback_sync(sync_session)
            return {"Query OK at": date_time_or_exception_error, "current_database": simulated_query}
        else:
            raise HTTPException(status_code=404, detail="sync_session connect db error...")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"error: {e}")