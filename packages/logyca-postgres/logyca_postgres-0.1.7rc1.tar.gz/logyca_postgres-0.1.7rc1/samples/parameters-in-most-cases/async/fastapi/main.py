from fastapi import FastAPI, Depends, HTTPException
from logyca import parse_bool
from logyca_postgres import AsyncConnEngine, commit_rollback_async, check_connection_async
from sqlalchemy import text as text_to_sql
from sqlalchemy.ext.asyncio import AsyncSession
import os

DB_USER=os.getenv('DB_USER','postgres')
DB_PASS=os.getenv('DB_PASS','***')
DB_HOST=os.getenv('DB_HOST','localhost')
DB_PORT=os.getenv('DB_PORT',5432)
DB_NAME=os.getenv('DB_NAME','test')
DB_SSL_ENABLE=parse_bool(os.getenv('DB_SSL_ENABLE',False))

app = FastAPI()

conn_async_session=AsyncConnEngine(
    url_connection=AsyncConnEngine.build_url_connection(user=DB_USER,password=DB_PASS,host=DB_HOST,port=DB_PORT,database=DB_NAME,ssl_enable=DB_SSL_ENABLE),
    server_settings=AsyncConnEngine.server_settings(pool_size=5,max_overflow=1,pool_recycle=10800,application_name="MyApp - AsyncConnEngine")
    )

'''
The connection pool (pool_size) after the first query will remain open until the application is stopped.
'''

@app.get("/simulated_query_async/")
async def read_item(async_session:AsyncSession = Depends(conn_async_session)):
    try:
        status, date_time_or_exception_error = await check_connection_async(async_session)
        if(status):
            query = text_to_sql("SELECT now();")
            result = await async_session.execute(query)
            simulated_query = result.scalar_one_or_none()
            await commit_rollback_async(async_session)
            return {"date_time_or_exception_error": date_time_or_exception_error, "simulated_query": simulated_query}
        else:
            raise HTTPException(status_code=404, detail="async_session connect db error...")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"error: {e}")
