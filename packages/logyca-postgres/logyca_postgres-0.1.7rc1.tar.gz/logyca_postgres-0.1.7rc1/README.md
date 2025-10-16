<p align="center">
  <a href="https://logyca.com/"><img src="https://logyca.com/sites/default/files/logyca.png" alt="Logyca"></a>
</p>
<p align="center">
    <em>LOGYCA public libraries</em>
</p>

<p align="center">
<a href="https://pypi.org/project/logyca" target="_blank">
    <img src="https://img.shields.io/pypi/v/logyca?color=orange&label=PyPI%20Package" alt="Package version">
</a>
<a href="(https://www.python.org" target="_blank">
    <img src="https://img.shields.io/badge/Python-%5B%3E%3D3.8%2C%3C%3D3.11%5D-orange" alt="Python">
</a>
</p>


---

# About us

* <a href="http://logyca.com" target="_blank">LOGYCA Company</a>
* <a href="https://www.youtube.com/channel/UCzcJtxfScoAtwFbxaLNnEtA" target="_blank">LOGYCA Youtube Channel</a>
* <a href="https://www.linkedin.com/company/logyca" target="_blank"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="Linkedin"></a>
* <a href="https://twitter.com/LOGYCA_Org" target="_blank"><img src="https://img.shields.io/badge/Twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white" alt="Twitter"></a>
* <a href="https://www.facebook.com/OrganizacionLOGYCA/" target="_blank"><img src="https://img.shields.io/badge/Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white" alt="Facebook"></a>

---

# LOGYCA public libraries: Standard methods to connect to postgres

* **Traversal libraries**: Standard methods to connect to postgres with dependency injection using yield to be used by microservices such as API(s), Workers or scripts.

[Source code](https://github.com/logyca/python-libraries/tree/main/logyca-postgres)
| [Package (PyPI)](https://pypi.org/project/logyca-postgres/)
| [Samples](https://github.com/logyca/python-libraries/tree/main/logyca-postgres/samples)

---

# "pip install" dependency check
The user must select the required libraries and versions for the project that uses this library, which validates that they are pre-installed in order to be installed.

To install the libraries of the logyca postgres package verifying the SQLAlchemy prerequisite without validating connection drivers to postgres, use the following command:

```Python
# Check SQLAlchemy dependency that is installed
pip install logyca_postgres
```

To install the logyca postgres package libraries and validate the postgres asynchronous or synchronous connection driver, use the following command:

```Python
# Check asyncpg driver dependency that is installed
pip install logyca_postgres[async]
# Check psycopg2 driver dependency that is installed
pip install logyca_postgres[sync-psycopg2]
# Check psycopg2-binary driver dependency that is installed
pip install logyca_postgres[sync-psycopg2-binary]
# Check asyncpg+psycopg2-binary driver dependency that is installed
pip install logyca_postgres[async-sync-psycopg2]
```
---

# Semantic Versioning

logyca < MAJOR >.< MINOR >.< PATCH >

* **MAJOR**: version when you make incompatible API changes
* **MINOR**: version when you add functionality in a backwards compatible manner
* **PATCH**: version when you make backwards compatible bug fixes

## Definitions for releasing versions
* https://peps.python.org/pep-0440/

    - X.YaN (Alpha release): Identify and fix early-stage bugs. Not suitable for production use.
    - X.YbN (Beta release): Stabilize and refine features. Address reported bugs. Prepare for official release.
    - X.YrcN (Release candidate): Final version before official release. Assumes all major features are complete and stable. Recommended for testing in non-critical environments.
    - X.Y (Final release/Stable/Production): Completed, stable version ready for use in production. Full release for public use.

---
# Make multiple connections to different motors

## When configuring the connection for dependency injection to another engine, a new object must be created that includes the singleton pattern.

The same thing must be done for each engine.

The library uses a singleton pattern "class SyncConnEngine(metaclass=Singleton):", where the class is allowed to be instantiated only once. You can create another connection to another engine but you must create an inherited class in order to create a new configuration instance.

Example:
```python
class SyncConnEngineX(SyncConnEngine):
    def __init__(self, url_connection,server_settings):
        super().__init__(url_connection,server_settings)
sync_session_x=SyncConnEngineX(
    url_connection=SyncConnEngineX.build_url_connection(user=settings.DB_USER_X,password=settings.DB_PASS_X,host=settings.DB_HOST_X,port=settings.DB_PORT_X,database=settings.DB_NAME_X,ssl_enable=SyncConnEngineX.DB_SSL_X),
    server_settings=SyncConnEngineX.server_settings(pool_size=5,max_overflow=1,pool_recycle=10800,application_name=f"{App.Settings.NAME} - SyncConnEngineX")
    )
```

## Asynchronous mode
FastAPI
```python
from fastapi import FastAPI, Depends, HTTPException
from logyca_postgres import AsyncConnEngine, commit_rollback_async, check_connection_async
from sqlalchemy import text as text_to_sql
from sqlalchemy.ext.asyncio import AsyncSession
import os

DB_USER=os.getenv('DB_USER','postgres')
DB_PASS=os.getenv('DB_PASS','xxx')
DB_HOST=os.getenv('DB_HOST','localhost')
DB_PORT=os.getenv('DB_PORT',5432)
DB_NAME=os.getenv('DB_NAME','test')
ssl_enable_like_local_docker_container=False

app = FastAPI()

conn_async_session=AsyncConnEngine(
    url_connection=AsyncConnEngine.build_url_connection(user=DB_USER,password=DB_PASS,host=DB_HOST,port=DB_PORT,database=DB_NAME,ssl_enable=ssl_enable_like_local_docker_container),
    server_settings=AsyncConnEngine.server_settings(pool_size=5,max_overflow=1,pool_recycle=10800,application_name="MyApp - AsyncConnEngine")
    )

'''
The connection pool (pool_size) after the first query will remain open until the application is stopped.
'''

@app.get("/simulated_query_async/")
async def read_item(async_session:AsyncSession = Depends(conn_async_session)):
    try:
        status, date_time_check_conn = await check_connection_async(async_session)
        if(status):
            query = text_to_sql("SELECT now();")
            result = await async_session.execute(query)
            simulated_query = result.scalar_one_or_none()
            await commit_rollback_async(async_session)
            return {"date_time_check_conn": date_time_check_conn, "simulated_query": simulated_query}
        else:
            raise HTTPException(status_code=404, detail="async_session connect db error...")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"error: {e}")
```
Worker or script
```python
from logyca_postgres import AsyncConnEngine, commit_rollback_async, check_connection_async
from sqlalchemy import text as text_to_sql
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import os

DB_USER=os.getenv('DB_USER','postgres')
DB_PASS=os.getenv('DB_PASS','xxx')
DB_HOST=os.getenv('DB_HOST','localhost')
DB_PORT=os.getenv('DB_PORT',5432)
DB_NAME=os.getenv('DB_NAME','test')
ssl_enable_like_local_docker_container=False

conn_async_session=AsyncConnEngine(
    url_connection=AsyncConnEngine.build_url_connection(user=DB_USER,password=DB_PASS,host=DB_HOST,port=DB_PORT,database=DB_NAME,ssl_enable=ssl_enable_like_local_docker_container),
    server_settings=AsyncConnEngine.server_settings(pool_size=5,max_overflow=1,pool_recycle=10800,application_name="MyApp - AsyncConnEngine")
            )

'''
The connection pool (pool_size) after the first query will remain open until the application is stopped or the engine is terminated: close_engine().
'''

async def methods(async_session:AsyncSession):
    status, date_time_check_conn = await check_connection_async(async_session)
    if(status):
        query = text_to_sql("SELECT now();")
        result = await async_session.execute(query)
        simulated_query = result.scalar_one_or_none()
        await commit_rollback_async(async_session)
        print(f"date_time_check_conn={date_time_check_conn},simulated_query={simulated_query}")
    else:
        print("async_session connect db error...")
async def main():
    async for async_session in conn_async_session.get_async_session():
        await methods(async_session)
    await conn_async_session.close_engine()

if __name__ == "__main__":
    asyncio.run(main())
```

## synchronous mode
FastAPI
```python
from fastapi import FastAPI, Depends, HTTPException
from logyca_postgres import SyncConnEngine, commit_rollback_sync, check_connection_sync
from sqlalchemy.orm.session import Session
import os
from sqlalchemy import text as text_to_sql

DB_USER=os.getenv('DB_USER','postgres')
DB_PASS=os.getenv('DB_PASS','xxx')
DB_HOST=os.getenv('DB_HOST','localhost')
DB_PORT=os.getenv('DB_PORT',5432)
DB_NAME=os.getenv('DB_NAME','test')
ssl_enable_like_local_docker_container=False

app = FastAPI()

conn_sync_session=SyncConnEngine(
    url_connection=SyncConnEngine.build_url_connection(user=DB_USER,password=DB_PASS,host=DB_HOST,port=DB_PORT,database=DB_NAME,ssl_enable=ssl_enable_like_local_docker_container),
    server_settings=SyncConnEngine.server_settings(pool_size=5,max_overflow=1,pool_recycle=10800,application_name="MyApp - AsyncConnEngine")
    )

'''
The connection pool (pool_size) after the first query will remain open until the application is stopped.
'''

@app.get("/simulated_query_sync/")
def read_item(sync_session:Session = Depends(conn_sync_session)):
    try:
        status, date_time_check_conn = check_connection_sync(sync_session)
        if(status):
            query = text_to_sql("SELECT now();")
            result = sync_session.execute(query)
            simulated_query = result.fetchone()[0]
            commit_rollback_sync(sync_session)
            return {"date_time_check_conn": date_time_check_conn, "simulated_query": simulated_query}
        else:
            raise HTTPException(status_code=404, detail="async_session connect db error...")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"error: {e}")
```
Worker or script
```python
from logyca_postgres import SyncConnEngine, commit_rollback_sync, check_connection_sync
from sqlalchemy import text as text_to_sql
from sqlalchemy.orm.session import Session
import os

DB_USER=os.getenv('DB_USER','postgres')
DB_PASS=os.getenv('DB_PASS','***')
DB_HOST=os.getenv('DB_HOST','localhost')
DB_PORT=os.getenv('DB_PORT',5432)
DB_NAME=os.getenv('DB_NAME','test')
ssl_enable_like_local_docker_container=False

conn_sync_session=SyncConnEngine(
    url_connection=SyncConnEngine.build_url_connection(user=DB_USER,password=DB_PASS,host=DB_HOST,port=DB_PORT,database=DB_NAME,ssl_enable=ssl_enable_like_local_docker_container),
    server_settings=SyncConnEngine.server_settings(pool_size=5,max_overflow=1,pool_recycle=10800,application_name="MyApp - SyncConnEngine")
            )

'''
The connection pool (pool_size) after the first query will remain open until the application is stopped or the engine is terminated: close_engine().
'''

def methods(sync_session: Session):
    status, date_time_check_conn = check_connection_sync(sync_session)
    if(status):
        query = text_to_sql("SELECT now();")
        result = sync_session.execute(query)
        simulated_query = result.fetchone()[0]
        commit_rollback_sync(sync_session)
        print(f"date_time_check_conn={date_time_check_conn},simulated_query={simulated_query}")
    else:
        print("sync_session connect db error...")
def main():
    for sync_session in conn_sync_session.get_sync_session():
        methods(sync_session)
    conn_sync_session.close_engine()            


if __name__ == "__main__":
    main()
```

---

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Types of changes

- Added for new features.
- Changed for changes in existing functionality.
- Deprecated for soon-to-be removed features.
- Removed for now removed features.
- Fixed for any bug fixes.
- Security in case of vulnerabilities.

## [0.0.1rc1] - 2024-04-22
### Added
- First tests using pypi.org in develop environment.
- New functionality of asynchronous and synchronous connections to postgresql databases.
- Functionalities can be used in fastapi or workers like Azure Functions.
- Examples of use are added to the documentation of the functions in docstring
- In the samples folder of this library, there are complete working examples of using the code.

## [0.1.0] - 2024-05-21
### Added
- Completion of testing and launch into production.

## [0.1.2] - 2024-05-23
### Added
- Documentation integrated with github

## [0.1.3] - 2024-05-30
### Fixed
- Static messages are removed, since they do not cover errors globally.

## [0.1.4] - 2024-07-03
### Fixed
- Postgresql sync connection, fix ssl mode name

## [0.1.5] - 2024-07-05
### Fixed
- Readme upgrade

## [0.1.6] - 2025-01-15
### Fixed
- Fix check_connection_sync, check_connection_async error message

## [0.1.7] - 2025-10-16
### Changed
- The dictionaries connect_args:dic[str,Any], engine_kwargs:dic[str,Any] are added when configuring server_settings for the engine to ensure that all existing parameters are accepted.
- Requirements for fastapi examples are updated.
- The script_app examples are refactored to connect to multiple databases and execute either queries or DML commands.

