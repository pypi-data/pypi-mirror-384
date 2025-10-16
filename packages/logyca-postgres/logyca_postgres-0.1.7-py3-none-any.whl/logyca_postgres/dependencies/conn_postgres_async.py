from logyca_postgres.utils.helpers.functions import html_escaping_special_characters
from logyca_postgres.utils.helpers.singleton import Singleton
from sqlalchemy import text as text_to_sql
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, DeclarativeMeta
from starlette.exceptions import HTTPException
from starlette.status import HTTP_409_CONFLICT
from typing import AsyncGenerator, Any


AsyncDeclarativeBaseORM: DeclarativeMeta = declarative_base()

class AsyncConnEngine(metaclass=Singleton):
    def __init__(self,url_connection:str,server_settings:dict[str, Any]|None,max_app_name_len:int=62):
        application_name = None
        connect_args = {}
        engine_kwargs = {}
        if server_settings is not None:
            if "application_name" in server_settings:
                application_name = server_settings.pop("application_name")[:max_app_name_len]
            if "connect_args" in server_settings:
                connect_args = server_settings["connect_args"]
            if application_name is not None: 
                connect_args.setdefault("server_settings", {})
                connect_args["server_settings"]["application_name"] = application_name
            if "engine_kwargs" in server_settings:
                engine_kwargs = server_settings["engine_kwargs"]
        self.url_connection=url_connection
        self.__engine = create_async_engine(
            url=url_connection,
            connect_args=connect_args,
            **engine_kwargs
        )
        self.__async_session_maker = async_sessionmaker(autoflush=False, bind=self.__engine, class_=AsyncSession) 

    async def __call__(self):
        '''Description

        Used by fastapi dependency injection
        '''
        async with self.__async_session_maker() as session:
            yield session

    async def get_async_session(self)->AsyncGenerator[AsyncSession, None]:
        '''Description

        Used by console scripts
        '''
        async with self.__async_session_maker() as session:
            yield session

    async def close_engine(self):
        await self.__engine.dispose()

    @classmethod
    def server_settings(self,
                        application_name:str|None=None,
                        max_overflow:int|None=None,
                        pool_pre_ping:bool|None=None,
                        pool_recycle:int|None=None,
                        pool_size:int|None=None,
                        pool_use_lifo:bool|None=None,
                        connect_args:dict[str, Any]|None=None,
                        engine_kwargs:dict[str, Any]|None=None,
                        ) -> dict[str, Any]|None:
        """Prepare configuration dictionaries for an asynchronous PostgreSQL engine.

        This method builds and merges connection and engine parameters used
        when creating an async SQLAlchemy engine via `create_async_engine`.

        Args:
            application_name (str | None): Optional name identifying the client application.
                This value is visible in PostgreSQL’s `pg_stat_activity` view.
                If not provided, it can be injected into `connect_args`.

            pool_size (int | None): Maximum number of connections to keep open
                simultaneously in the pool (default is 5).

            max_overflow (int | None): Maximum number of additional temporary
                connections created when demand exceeds `pool_size` (default is 10).

            pool_recycle (int | None): Time in seconds after which connections in
                the pool are automatically recycled. Helps prevent stale connections.

            pool_pre_ping (bool | None): If True, SQLAlchemy validates each connection
                before using it (recommended for long-lived services).
                If None, uses the default (False).

            pool_use_lifo (bool | None): If True, the pool uses a LIFO strategy,
                often reducing latency under high contention. Default is False.

            connect_args (dict[str, Any] | None):  
                Arguments passed **directly** to the database driver (e.g., psycopg or asyncpg).
                These control connection behavior at the DB-API level, not SQLAlchemy.

                Common keys include:
                    - `application_name`: Application name for `pg_stat_activity`
                    - `connect_timeout`: Timeout (seconds) for connection attempts
                    - `options`: Advanced libpq options string, e.g. `'-c search_path=my_schema'`
                    - SSL parameters:
                        - `sslmode`: "disable", "require", "verify-ca", "verify-full"
                        - `sslrootcert`, `sslcert`, `sslkey`, `sslpassword`
                    - Keepalive parameters:
                        - `keepalives`, `keepalives_idle`, `keepalives_interval`, `keepalives_count`
                    - Other driver-specific options like `target_session_attrs`

                Note:
                    If `application_name` is provided here, it takes precedence
                    over the top-level `application_name` parameter.

            engine_kwargs (dict[str, Any] | None):  
                Advanced parameters passed **as-is** to `create_async_engine()`
                (and ultimately to the underlying synchronous engine).

                Common keys include:
                    - `pool_size`, `max_overflow`, `pool_timeout`, `pool_recycle`
                    - `pool_pre_ping`, `pool_use_lifo`
                    - `isolation_level`: e.g. `"AUTOCOMMIT"`, `"READ COMMITTED"`
                    - `execution_options`: e.g. `{"stream_results": True}`
                    - `poolclass`: Custom pool class (`NullPool`, `StaticPool`, etc.)
                    - `echo`: If True, logs all SQL statements for debugging

                Note:
                    Changing `poolclass` may override or disable parameters such as
                    `pool_size` and `max_overflow`.

        Returns:
            dict[str, Any] | None:  
                A dictionary containing:
                    - `"engine_kwargs"`: Engine parameters ready to unpack into
                    `create_async_engine(**engine_kwargs)`.
                    - `"connect_args"`: Final connection arguments dictionary,
                    merged with `application_name` if applicable.

        Notes:
            - If none of the pool parameters are provided, defaults from SQLAlchemy apply.
            - Values defined in `engine_kwargs` can override base parameters if duplicated.
            - This function is typically used to standardize async PostgreSQL engine setup
            across multiple services or modules.
        """
        _engine_kwargs: dict[str, Any] = {}
        if max_overflow is not None: _engine_kwargs["max_overflow"] = max_overflow 
        if pool_pre_ping is not None: _engine_kwargs["pool_pre_ping"] = pool_pre_ping 
        if pool_recycle is not None: _engine_kwargs["pool_recycle"] = pool_recycle 
        if pool_size is not None: _engine_kwargs["pool_size"] = pool_size 
        if pool_use_lifo is not None: _engine_kwargs["pool_use_lifo"] = pool_use_lifo 
        
        _engine_kwargs["application_name"]   = application_name if application_name is not None else "logyca-azure-storage-blob"

        if connect_args is not None: _engine_kwargs["connect_args"] = connect_args
        if engine_kwargs is not None: _engine_kwargs["engine_kwargs"] = engine_kwargs

        if not _engine_kwargs:
            return None
        return _engine_kwargs
    
    @classmethod
    def build_url_connection(cls,user:str,password:str,host:str,port:int,database:str,ssl_enable:bool):
        """Descriptions

        Data for connection to the database
            Args:
                ssl_enable (str): whether ssl=require is needed or not
        """
        dialect="postgresql"
        driver="asyncpg"
        ssl_option = '?ssl=require' if ssl_enable else ''
        ps_escaping_special_characters=html_escaping_special_characters(password)
        return f"{dialect}+{driver}://{user}:{ps_escaping_special_characters}@{host}:{port}/{database}{ssl_option}"

async def check_connection_async(async_session: AsyncSession)->tuple[bool,str]:
    '''Description
    
    :return tuple[bool,str]: status, date_time_or_exception_error'''    
    try:
        query = text_to_sql(f"SELECT now();")
        result = await async_session.execute(query)
        date_time = result.scalar_one_or_none()
        if date_time is not None:
            return True, date_time
        else:
           return False, ''
    except Exception as e:
        return False, str(e)

async def commit_rollback_async(async_session: AsyncSession):
    try:
        await async_session.commit()
    except Exception as e:
        await async_session.rollback()
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail=f"{e}",
        )

