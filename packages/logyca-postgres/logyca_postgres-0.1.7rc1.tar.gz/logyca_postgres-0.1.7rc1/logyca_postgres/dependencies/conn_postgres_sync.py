from logyca_postgres.utils.helpers.functions import html_escaping_special_characters
from logyca_postgres.utils.helpers.singleton import Singleton
from sqlalchemy import create_engine, text as text_to_sql
from sqlalchemy.orm import declarative_base, DeclarativeMeta, sessionmaker
from sqlalchemy.orm.session import Session
from starlette.exceptions import HTTPException
from starlette.status import HTTP_409_CONFLICT
from typing import Any

SyncDeclarativeBaseORM: DeclarativeMeta = declarative_base()

class SyncConnEngine(metaclass=Singleton):
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
                connect_args["application_name"] = application_name
            if "engine_kwargs" in server_settings:
                engine_kwargs = server_settings["engine_kwargs"]
        self.url_connection=url_connection
        self.__engine = create_engine(
            url=url_connection,
            connect_args=connect_args,
            **engine_kwargs
        )
        self.__sync_session_maker=sessionmaker(bind=self.__engine,autoflush=False)

    def __call__(self):
        '''Description

        Used by fastapi dependency injection
        '''
        sync_session=self.__sync_session_maker()
        try:
            yield sync_session
        finally:
            sync_session.close()

    def get_sync_session(self):
        '''Description

        Used by console scripts
        '''
        sync_session=self.__sync_session_maker()
        try:
            yield sync_session
        finally:
            sync_session.close()

    def close_engine(self):
        self.__engine.dispose()

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
        """Descriptions

        Args:
            pool_size (int | None): Postgres server or engine configuration parameter given in seconds.
                             Is the maximum number of connections that an application can keep open simultaneously
            max_overflow (int | None): Postgres server or engine configuration parameter given in seconds.
                             Determines the maximum number of additional connections that can be temporarily created when demand exceeds the maximum connection pool size.
            pool_recycle (int | None): Postgres server or engine configuration parameter given in seconds.
                             Specifies the time after which connections in the pool are automatically recycled to avoid connection stagnation or blocking issues.
            application_name (str): Postgres server or engine configuration parameter given in text.
                             Seconds: Description that can be seen when listing the connected user sessions in the database.
            pool_pre_ping (bool | None):
                                If True, SQLAlchemy validates the connection before using it, killing zombie connections.
                                Recommended for long-lived services. If None, use the default (False).
            pool_use_lifo (bool | None):
                            If True, use LIFO in the pool (usually reduces latency under high contention).
                            If None, use the default (False).
            connect_args (dict[str, Any] | None):
                            Args passed **directly** to the DB-API (psycopg2/libpq).
                            Common Keys:
                            - `application_name`, `connect_timeout`, `options`
                            - SSL: `sslmode`, `sslrootcert`, `sslcert`, `sslkey`, `sslpassword`
                            - Keepalives: `keepalives`, `keepalives_idle`, `keepalives_interval`, `keepalives_count`
                            - `target_session_attrs`, etc.
                            If you already provide `application_name` here, it is respected (it takes precedence over the parent parameter).
            engine_kwargs (dict[str, Any] | None):
                            Advanced parameters that are passed **as is** to `create_engine`.
                            Some useful ones:
                            - `pool_timeout` (float): Max time waiting for a connection from the pool (default 30s).
                            - `isolation_level` (str | None): e.g. "AUTOCOMMIT", "READ COMMITTED".
                            - `poolclass`: Alternative pool class (`NullPool`, `StaticPool`, etc.).
                            NOTE: If you change the pool, `pool_size/max_overflow/...` may not apply.
                            - `execution_options`: Default options dict (e.g., `{"stream_results": True}`).
                            - `future` (bool): Enables "future" behavior.
                            - `echo` (bool): SQL log to stdout (debug).
                            - Any other KW supported by `sqlalchemy.create_engine`.

            Returns:
            dict: A dictionary containing:
            - "engine_kwargs": Kwargs ready to be expanded in `create_engine(**engine_kwargs)`
            (including `pool_size`, `max_overflow`, `pool_recycle`, `pool_pre_ping`,
            `pool_use_lifo`, `isolation_level`, `pool_timeout`, etc.),
            - "connect_args": Final dict for `connect_args` (merging `application_name` if applicable).

            Notes:
            - If you **do not** pass any of the pool parameters, `create_engine` uses its defaults.
            - `application_name` is injected into `connect_args` only if it is not already in `connect_args`.
            - Values ​​in `engine_kwargs` can overwrite core values ​​if you repeat the key.

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
        driver="psycopg2"
        ssl_option = '?sslmode=require' if ssl_enable else ''
        ps_escaping_special_characters=html_escaping_special_characters(password)
        return f"{dialect}+{driver}://{user}:{ps_escaping_special_characters}@{host}:{port}/{database}{ssl_option}"

def check_connection_sync(sync_session: Session)->tuple[bool,str]:
    '''Description
    
    :return tuple[bool,str]: status, date_time_or_exception_error'''    
    try:
        query = text_to_sql(f"SELECT now();")
        result = sync_session.execute(query)
        date_time = result.fetchone()[0]
        if date_time is not None:            
            return True, date_time
        else:
           return False, ''
    except Exception as e:
        return False, str(e)

def commit_rollback_sync(sync_session: Session):
    '''
    In SQLAlchemy, all CRUD methods are transactions to the database that must be completed with commit or rollback.
    When the session manager is reviewed in the postgres engine, transactions without commit are reported as rollback, generating a false failure report.
    '''
    try:
        sync_session.commit()
    except Exception as e:
        sync_session.rollback()
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail=f"{e}",
        )

