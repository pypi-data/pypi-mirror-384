from typing import Any

from sqlalchemy import text

from .db_connection_config import DBConnectionConfig
from .common_vars import SQLSource
from .dbclient import DBClient

from time import perf_counter, sleep


class AsyncDBClient(DBClient):
    """Asynchronous database client."""
    def __init__(self,
            db_conn: dict[str, Any] | DBConnectionConfig,
            future: bool = True,
            do_initialize: bool = True,
            *args,
            **kwargs,):
        super().__init__(db_conn, future, False, *args, **kwargs)

    def get_async_conn_str(self) -> str:
        """Generate async connection string based on dialect."""
        base_str = self.get_conn_str()
        dialect = self.db_conn.dialect.lower()

        if "postgresql" in dialect:
            return base_str.replace("://", "+asyncpg://")
        elif "mssql" in dialect:
            return base_str.replace("://", "+asyncodbc://")
        else:
            raise ValueError(f"Unsupported async dialect: {dialect}")

    async def create_conn(self) -> None:
        """Create a new database connection."""
        if not self.conn:
            self.conn = await self.engine.connect()
            self.logger.debug("Created new database connection")

    async def create_engine(self) -> None:
        """Create async SQLAlchemy engine with multi-database support."""
        from sqlalchemy.ext.asyncio import create_async_engine

        connect_str = self.get_async_conn_str()
        try:
            self.engine = create_async_engine(
                connect_str,
                future=self.future,
                pool_pre_ping=True,
                pool_recycle=3600,
                **self.kwargs,
            )
            self.logger.info(f"Created async engine for {self.db_conn.dialect}")
        except ImportError as e:
            self.logger.error(f"Missing driver for async {self.db_conn.dialect}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to create async engine: {str(e)}")
            raise

    async def get_data(
            self,
            sql: SQLSource,
            params: dict | None = None,
            encoding: str = "utf-8",
            print_script: bool = False,
            max_attempts: int = 5,
            **kwargs,
    ) -> list[dict]:
        """Async version of get_data."""
        if not self.conn:
            await self.create_engine()

        script = self._prepare_script(sql, encoding, **kwargs)

        if print_script:
            print(script)

        return await self._execute(script, params, max_attempts)

    async def _execute(self, script: str, params: dict, max_attempts: int) -> list[dict]:
        """Async version of _execute."""
        from sqlalchemy.ext.asyncio import AsyncConnection

        result = []
        start_time = perf_counter()

        async with AsyncConnection(self.engine) as conn:
            for attempt in range(1, max_attempts + 1):
                try:
                    self.logger.debug(f"Executing async query (attempt {attempt}/{max_attempts})")
                    res = await conn.execute(text(script), params or {})
                    result = [dict(row) for row in res.mappings()]
                    await conn.commit()
                    self.logger.debug(f"Async query executed in {perf_counter() - start_time:.2f}s")
                    break
                except Exception as ex:
                    self.logger.warning(
                        f"Async attempt {attempt} failed: {str(ex)}. Retrying..."
                    )
                    await conn.rollback()
                    if attempt == max_attempts:
                        raise
                    sleep(10)

        return result