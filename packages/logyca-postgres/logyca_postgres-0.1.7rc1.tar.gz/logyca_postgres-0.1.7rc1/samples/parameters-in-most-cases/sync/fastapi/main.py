from fastapi import FastAPI, Depends, HTTPException
from logyca import parse_bool
from logyca_postgres import SyncConnEngine, commit_rollback_sync, check_connection_sync
from sqlalchemy import text as text_to_sql
from sqlalchemy.orm.session import Session
import os

DB_USER=os.getenv('DB_USER','postgres')
DB_PASS=os.getenv('DB_PASS','***')
DB_HOST=os.getenv('DB_HOST','localhost')
DB_PORT=os.getenv('DB_PORT',5432)
DB_NAME=os.getenv('DB_NAME','test')
DB_SSL_ENABLE=parse_bool(os.getenv('DB_SSL_ENABLE',False))

app = FastAPI()

conn_sync_session=SyncConnEngine(
    url_connection=SyncConnEngine.build_url_connection(user=DB_USER,password=DB_PASS,host=DB_HOST,port=DB_PORT,database=DB_NAME,ssl_enable=DB_SSL_ENABLE),
    server_settings=SyncConnEngine.server_settings(pool_size=5,max_overflow=1,pool_recycle=10800,application_name="MyApp - AsyncConnEngine")
    )

'''
The connection pool (pool_size) after the first query will remain open until the application is stopped.
'''

@app.get("/simulated_query_sync/")
def read_item(sync_session:Session = Depends(conn_sync_session)):
    try:
        status, date_time_or_exception_error = check_connection_sync(sync_session)
        if(status):
            query = text_to_sql("SELECT now();")
            result = sync_session.execute(query)
            simulated_query = result.fetchone()[0]
            commit_rollback_sync(sync_session)
            return {"date_time_or_exception_error": date_time_or_exception_error, "simulated_query": simulated_query}
        else:
            raise HTTPException(status_code=404, detail="async_session connect db error...")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"error: {e}")