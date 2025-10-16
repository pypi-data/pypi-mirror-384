"""
Database Client (dgdb) - A flexible SQLAlchemy-based database client

Features:
- Multiple database support (PostgreSQL, MySQL, Oracle, SQL Server)
- Connection pooling and management
- SQL template processing
- Automatic retry on connection failures
- Configuration validation
- Context manager support
- Sync and async interfaces
- Comprehensive logging

Example usage:
    >>> db_config = {
    ...     'dialect': 'postgresql',
    ...     'db_user': 'user',
    ...     'db_pass': 'password',
    ...     'db_host': 'localhost',
    ...     'db_port': 5432,
    ...     'db_name': 'mydb'
    ... }
    >>> client = DBClient(db_config)
    >>> data = client.get_data("SELECT * FROM users WHERE id = :id", params={'id': 1})
"""

import logging
import os
from contextlib import contextmanager
from string import Template
from time import perf_counter, sleep
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    Generator,
)

import sqlalchemy.exc
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import (
    DatabaseError,
    ResourceClosedError,
    ProgrammingError,
)
from sqlalchemy.engine.base import Connection as SQLAlchemyConnection

from .db_connection_config import DBConnectionConfig
from .common_vars import ConnectionFields, SQLSource


class DBClient:
    """Database client for managing connections and executing queries."""

    def __init__(
            self,
            db_conn: dict[str, Any] | DBConnectionConfig,
            future: bool = True,
            do_initialize: bool = True,
            *args,
            **kwargs,
    ):
        """Initialize the database client.

        Args:
            db_conn: Database connection parameters as dict or DBConnectionConfig
            future: Use SQLAlchemy 2.0 style APIs
            do_initialize: Initialize connection immediately
            *args: Additional arguments for create_engine
            **kwargs: Additional keyword arguments for create_engine
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.args = args
        self.kwargs = kwargs
        self.future = future

        # Validate and store connection config
        if isinstance(db_conn, dict):
            self.db_conn = DBConnectionConfig(**db_conn)
        else:
            self.db_conn = db_conn

        # Connection attributes
        self.engine: Optional[Engine] = None
        self.conn: Optional[SQLAlchemyConnection] = None
        self.metadata: Optional[MetaData] = None

        if do_initialize:
            self.create_engine()

    def get_conn_str(self) -> str:
        """Generate connection string from configuration."""
        if self.db_conn.dialect == "mssql+pytds":
            from sqlalchemy.dialects import registry

            registry.register("mssql.pytds", "sqlalchemy_pytds.dialect", "MSDialect_pytds")

        if self.db_conn.db_host and self.db_conn.db_port:
            if "oracle" in self.db_conn.dialect.lower() and ".orcl" in self.db_conn.db_name:
                return (
                    f"{self.db_conn.dialect}://{self.db_conn.db_user}:{self.db_conn.db_pass}@"
                    f"{self.db_conn.db_host}:{self.db_conn.db_port}/?service_name={self.db_conn.db_name}"
                )
            return (
                f"{self.db_conn.dialect}://{self.db_conn.db_user}:{self.db_conn.db_pass}@"
                f"{self.db_conn.db_host}:{self.db_conn.db_port}/{self.db_conn.db_name}"
            )
        return f"{self.db_conn.dialect}://{self.db_conn.db_user}:{self.db_conn.db_pass}@{self.db_conn.db_name}"

    def create_engine(self) -> None:
        """Create SQLAlchemy engine with connection pooling."""
        connect_str = self.get_conn_str()
        try:
            self.engine = create_engine(
                connect_str,
                future=self.future,
                pool_pre_ping=True,
                pool_recycle=3600,
                *self.args,
                **self.kwargs,
            )
            self.logger.info(f"Created engine for {self.db_conn.dialect}")
        except sqlalchemy.exc.ArgumentError as e:
            self.logger.error(f"Failed to create engine: {str(e)}")
            # Fallback for SQLAlchemy>=2.0.0
            self.engine = create_engine(connect_str, future=True, *self.args, **self.kwargs)

    def create_conn(self) -> None:
        """Create a new database connection."""
        if not self.conn:
            self.conn = self.engine.connect()
            self.logger.debug("Created new database connection")

    def create_raw_conn(self) -> None:
        """Create a raw DBAPI connection."""
        if not self.conn:
            self.conn = self.engine.raw_connection()
            self.logger.debug("Created raw DBAPI connection")

    def create_metadata(self) -> None:
        """Initialize SQLAlchemy metadata."""
        if not self.metadata:
            self.create_conn()
            self.metadata = MetaData()
            self.logger.debug("Initialized database metadata")

    def set_args(self, *args, **kwargs) -> None:
        """Update engine creation arguments."""
        self.args = args
        self.kwargs = kwargs
        self.logger.debug("Updated engine creation arguments")

    def set_conn(self) -> None:
        """Create connection for SQLAlchemy."""
        self.create_engine()
        self.create_conn()
        self.create_metadata()
        self.logger.info("Initialized SQLAlchemy connection")

    def set_raw_conn(self) -> None:
        """Create raw connection for SQLAlchemy."""
        self.engine = create_engine(self.get_conn_str(), *self.args, **self.kwargs)
        self.conn = self.engine.raw_connection()
        self.metadata = MetaData(bind=self.conn)
        self.logger.info("Initialized raw DBAPI connection")

    def get_conn(
            self, fields: Union[ConnectionFields, List[ConnectionFields]] = "conn"
    ) -> Union[Optional[Any], Tuple[Optional[Any], ...]]:
        """Get connection components.

        Args:
            fields: Single field name or list of fields to return

        Returns:
            Requested connection components
        """
        if isinstance(fields, str):
            return self.__dict__.get(fields)
        if isinstance(fields, list):
            return tuple([self.__dict__.get(x) for x in fields])
        raise ValueError("Fields must be string or list of strings")

    def close_conn(self) -> None:
        """Close connection and dispose engine."""
        if self.conn:
            self.conn.close()
            self.conn = None
        if self.engine:
            self.engine.dispose()
            self.engine = None
        self.logger.info("Closed connection and disposed engine")

    def check_connection_status(self) -> None:
        """Verify database connection is alive."""
        try:
            if "oracle" in self.db_conn.dialect.lower():
                d = self.get_data_row("select dummy from dual")
            else:
                d = self.get_data_row("select 'x' as dummy")

            if (v := d.get("dummy")) is None or v != "x":
                raise DatabaseError("Connection test failed")
        except Exception as e:
            self.logger.warning(f"Connection check failed: {str(e)}")
            self.close_conn()
            self.set_conn()

    @staticmethod
    def get_sql(filename: SQLSource, encoding: str = "utf-8") -> str:
        """Read SQL from file.

        Args:
            filename: Path to SQL file
            encoding: File encoding

        Returns:
            SQL content as string
        """
        with open(filename, "r", encoding=encoding) as file:
            return file.read()

    @contextmanager
    def session_scope(self) -> Generator[SQLAlchemyConnection, None, None]:
        """Provide transactional scope around series of operations.

        Example:
            with dgdb.session_scope() as session:
                session.execute(text("SELECT 1"))
        """
        session = self.engine.connect()
        try:
            yield session
            session.commit()
            self.logger.debug("Transaction committed")
        except Exception as e:
            session.rollback()
            self.logger.error(f"Transaction rolled back: {str(e)}")
            raise
        finally:
            session.close()
            self.logger.debug("Session closed")

    def get_data(
            self,
            sql: SQLSource,
            params: Optional[Dict] = None,
            encoding: str = "utf-8",
            print_script: bool = False,
            max_attempts: int = 5,
            **kwargs,
    ) -> List[Dict]:
        """Execute query and return results as list of dictionaries.

        Args:
            sql: SQL file path or query string
            params: Parameters for parameterized query
            encoding: File encoding if sql is a file path
            print_script: Print the executed SQL to console
            max_attempts: Maximum retry attempts on failure
            kwargs: Template substitution variables

        Returns:
            List of dictionaries representing query results
        """
        if not self.conn:
            self.create_conn()

        script = self._prepare_script(sql, encoding, **kwargs)

        if print_script:
            print(script)

        return self._execute(script, params, max_attempts)

    def get_data_row(
            self,
            sql: SQLSource,
            index: int = 0,
            params: Optional[Dict] = None,
            encoding: str = "utf-8",
            print_script: bool = False,
            max_attempts: int = 5,
            **kwargs,
    ) -> Optional[Dict]:
        """Get single row from query results.

        Args:
            sql: SQL file path or query string
            index: Row index to return
            params: Parameters for parameterized query
            encoding: File encoding if sql is a file path
            print_script: Print the executed SQL to console
            max_attempts: Maximum retry attempts on failure
            kwargs: Template substitution variables

        Returns:
            Dictionary representing the requested row or None if not found
        """
        result = self.get_data(sql, params, encoding, print_script, max_attempts, **kwargs)
        return result[index] if result and len(result) > index else None

    def run_script(
            self,
            sql: SQLSource,
            encoding: str = "utf-8",
            print_script: bool = False,
            max_attempts: int = 5,
            **kwargs,
    ) -> None:
        """Execute SQL script without returning results.

        Args:
            sql: SQL file path or query string
            encoding: File encoding if sql is a file path
            print_script: Print the executed SQL to console
            max_attempts: Maximum retry attempts on failure
            kwargs: Template substitution variables
        """
        self.get_data(sql, None, encoding, print_script, max_attempts, **kwargs)

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists in database.

        Args:
            table_name: Name of table to check

        Returns:
            True if table exists, False otherwise
        """
        self.create_metadata()
        return table_name in self.metadata.tables

    def get_table(self, table_name: str) -> Table:
        """Get SQLAlchemy Table object.

        Args:
            table_name: Name of table to retrieve

        Returns:
            SQLAlchemy Table object
        """
        self.create_metadata()
        return Table(table_name, self.metadata, autoload_with=self.engine)

    def commit(self, transaction=None) -> None:
        """Commit transaction."""
        if transaction:
            transaction.commit()
        elif self.conn:
            self.conn.commit()
        self.logger.debug("Transaction committed")

    def rollback(self, transaction=None) -> None:
        """Rollback transaction."""
        if transaction:
            transaction.rollback()
        elif self.conn:
            self.conn.rollback()
        self.logger.debug("Transaction rolled back")

    def begin_transaction(self):
        """Begin a new transaction."""
        self.logger.debug("Beginning new transaction")
        return self.engine.begin()

    def _prepare_script(self, sql: SQLSource, encoding: str, **kwargs) -> str:
        """Prepare SQL script from file or string with template substitution."""
        if os.path.exists(sql):
            script_t = Template(self.get_sql(sql, encoding))
        else:
            script_t = Template(str(sql))
        return script_t.safe_substitute(**kwargs)

    def _execute(self, script: str, params: Optional[Dict], max_attempts: int) -> List[Dict]:
        """Execute SQL script with retry logic."""
        result = []
        transaction = None
        start_time = perf_counter()

        for attempt in range(1, max_attempts + 1):
            try:
                if not self.future:
                    transaction = self.conn.begin()

                self.logger.debug(f"Executing query (attempt {attempt}/{max_attempts})")
                res = self.conn.execute(text(script), params or {})

                try:
                    result = [dict(row) for row in res.mappings()]
                except ResourceClosedError:
                    result = []

                self.commit(transaction)
                self.logger.debug(f"Query executed in {perf_counter() - start_time:.2f}s")
                break

            except ProgrammingError as ex:
                self.logger.error(f"SQL Error: {str(ex)}")
                self.rollback(transaction)
                raise
            except DatabaseError as ex:
                self.logger.warning(
                    f"Attempt {attempt} failed: {str(ex)}. Retrying..."
                )
                self.rollback(transaction)
                try:
                    self.close_conn()
                except Exception as ex:
                    self.logger.error(f"Error closing connection: {str(ex)}")
                sleep(10)
                self.set_conn()
                if attempt == max_attempts:
                    raise

        return result


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    config = {
        "dialect": "postgresql",
        "db_user": "user",
        "db_pass": "password",
        "db_host": "localhost",
        "db_port": 5432,
        "db_name": "testdb"
    }

    client = DBClient(config)

    try:
        # Using context manager
        with client.session_scope() as session:
            result = session.execute(text("SELECT 1 AS test"))
            print(result.scalar())

        # Regular query
        data = client.get_data("SELECT * FROM users WHERE id = :id", params={"id": 1})
        print(data)

    finally:
        client.close_conn()