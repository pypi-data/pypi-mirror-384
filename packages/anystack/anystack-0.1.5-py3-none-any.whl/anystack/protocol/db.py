from typing import Any, Protocol, TypeAlias
from contextlib import AbstractAsyncContextManager

from sqlalchemy.sql.expression import ClauseElement

Row = dict[str, Any]
SQLStatement: TypeAlias = str | ClauseElement


class DBResult(Protocol):
    """
    Represents the result of a database query.
    """

    rows: list[Row]
    rows_affected: int
    # Not all drivers support this, so it's optional.
    # It can be int or str (e.g., UUID).
    last_insert_rowid: int | str | None


class DBConnection(Protocol):
    """
    A protocol for a database connection that can be reused.
    """

    async def sql(
        self, sql: SQLStatement, params: dict[str, Any] | None = None
    ) -> DBResult:
        """
        Execute a SQL query on this connection.

        :param sql: The SQL query to execute, can be a raw string or
                    an SQLAlchemy ClauseElement.
        :param params: A dictionary of parameters to bind to the query.
        :return: A DBResult object.
        """
        ...

    async def commit(self) -> None:
        """
        Commit the current transaction.
        """
        ...

    async def rollback(self) -> None:
        """
        Rollback the current transaction.
        """
        ...

    async def close(self) -> None:
        """
        Close this connection.
        """
        ...


class DB(Protocol):
    """
    A protocol for a database connection.
    """

    async def sql(
        self, sql: SQLStatement, params: dict[str, Any] | None = None
    ) -> DBResult:
        """
        Execute a SQL query.

        :param sql: The SQL query to execute, can be a raw string or
                    an SQLAlchemy ClauseElement.
        :param params: A dictionary of parameters to bind to the query.
        :return: A DBResult object.
        """
        ...

    def connection(self) -> AbstractAsyncContextManager[DBConnection]:
        """
        Get a reusable connection context manager.
        
        Usage:
            async with db.connection() as conn:
                result1 = await conn.sql("SELECT ...")
                result2 = await conn.sql("INSERT ...")
                await conn.commit()
        """
        ...

    def transaction(self) -> AbstractAsyncContextManager[DBConnection]:
        """
        Get a transaction context manager that auto-commits on success
        and auto-rollbacks on exception.
        
        Usage:
            async with db.transaction() as conn:
                await conn.sql("INSERT ...")
                await conn.sql("UPDATE ...")
                # Auto-commit on success, auto-rollback on exception
        """
        ...

    async def close(self) -> None:
        """
        Close the database connection.
        """
        ...
