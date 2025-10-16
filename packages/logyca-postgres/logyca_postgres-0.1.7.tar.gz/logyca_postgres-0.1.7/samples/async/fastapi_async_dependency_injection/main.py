from app.internal.config import settings
from fastapi import FastAPI, Depends, HTTPException
from logyca_postgres import AsyncConnEngine, commit_rollback_async, check_connection_async
from sqlalchemy import text as text_to_sql
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

conn_async_session=AsyncConnEngine(
    url_connection=AsyncConnEngine.build_url_connection(user=settings.DB_USER,password=settings.DB_PASS,host=settings.DB_HOST,port=settings.DB_PORT,database=settings.DB_NAME,ssl_enable=settings.DB_SSL),
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
            query = text_to_sql("SELECT current_database();")
            result = await async_session.execute(query)
            simulated_query = result.scalar_one_or_none()
            await commit_rollback_async(async_session)
            return {"Query OK at": date_time_or_exception_error, "current_database": simulated_query}
        else:
            raise HTTPException(status_code=404, detail="async_session connect db error...")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"error: {e}")
