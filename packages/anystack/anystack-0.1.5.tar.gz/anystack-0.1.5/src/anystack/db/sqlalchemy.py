from contextlib import asynccontextmanager
from typing import override
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncTransaction
from sqlalchemy.sql.expression import ClauseElement

from ..protocol.db import DBConnection, DBResult, SQLStatement
from .base import BaseDB, BaseDBConnection, BaseDBResult


@dataclass
class Config:
    engine: AsyncEngine


class SQLAlchemyConnection(BaseDBConnection):
    """
    SQLAlchemy 连接包装器，支持事务管理
    """

    def __init__(self, connection: AsyncConnection, transaction: AsyncTransaction | None = None):
        self._connection = connection
        self._transaction = transaction
        self._closed = False

    @override
    async def sql(
        self, sql: SQLStatement, params: dict[str, object] | None = None
    ) -> DBResult:
        """
        在此连接上执行 SQL 查询
        """
        if self._closed:
            raise RuntimeError("Connection is closed")

        params = params or {}

        if isinstance(sql, ClauseElement):
            result = await self._execute_clause_element(sql, params)
        else:
            result = await self._execute_raw_sql(sql, params)

        return result

    async def _execute_clause_element(
        self, clause: ClauseElement, params: dict[str, object]
    ) -> DBResult:
        """
        执行 SQLAlchemy ClauseElement
        """
        try:
            cursor_result = await self._connection.execute(clause, params)
        except Exception:
            # 如果直接执行失败，尝试编译为文本再执行
            compiled = clause.compile(compile_kwargs={"literal_binds": True})
            cursor_result = await self._connection.execute(text(str(compiled)), params)

        return await self._process_result(cursor_result)

    async def _execute_raw_sql(self, sql: str, params: dict[str, object]) -> DBResult:
        """
        执行原始 SQL 字符串
        """
        cursor_result = await self._connection.execute(text(sql), params)
        return await self._process_result(cursor_result)

    async def _process_result(self, cursor_result) -> DBResult:
        """
        处理查询结果
        """
        # 获取查询结果
        rows: list[dict[str, object]] = []
        try:
            if hasattr(cursor_result, "mappings"):
                rows = [dict(row) for row in cursor_result.mappings().fetchall()]
        except Exception:
            rows = []

        # 获取受影响的行数
        rows_affected = 0
        try:
            rows_affected = (
                cursor_result.rowcount if hasattr(cursor_result, "rowcount") else 0
            )
        except Exception:
            pass

        # 获取最后插入的行 ID
        last_insert_rowid = None
        try:
            if hasattr(cursor_result, "lastrowid"):
                last_insert_rowid = cursor_result.lastrowid
        except Exception:
            pass

        return BaseDBResult(
            rows=rows,
            rows_affected=rows_affected or 0,
            last_insert_rowid=last_insert_rowid,
        )

    @override
    async def commit(self) -> None:
        """
        提交当前事务
        """
        if self._closed:
            raise RuntimeError("Connection is closed")

        if self._transaction:
            await self._transaction.commit()
        else:
            await self._connection.commit()

    @override
    async def rollback(self) -> None:
        """
        回滚当前事务
        """
        if self._closed:
            raise RuntimeError("Connection is closed")

        if self._transaction:
            await self._transaction.rollback()
        else:
            await self._connection.rollback()

    @override
    async def close(self) -> None:
        """
        关闭连接
        """
        if not self._closed:
            if self._transaction:
                await self._transaction.close()
            await self._connection.close()
            self._closed = True


class SQLAlchemyDB(BaseDB):
    """
    SQLAlchemy 异步数据库实现，支持连接复用和事务管理
    """

    def __init__(self, config: Config):
        """
        初始化 SQLAlchemy 数据库连接

        :param engine: SQLAlchemy 异步引擎
        """
        self._engine: AsyncEngine = config.engine

    @override
    async def sql(
        self, sql: SQLStatement, params: dict[str, object] | None = None
    ) -> DBResult:
        """
        执行单个 SQL 查询（使用自动事务）

        :param sql: SQL 语句或 SQLAlchemy 表达式
        :param params: 查询参数
        :return: 查询结果
        """
        async with self.connection() as conn:
            result = await conn.sql(sql, params)
            await conn.commit()
            return result

    @override
    def connection(self) -> AbstractAsyncContextManager[DBConnection]:
        """
        获取可复用的连接上下文管理器
        """
        return self._connection_context()

    @override
    def transaction(self) -> AbstractAsyncContextManager[DBConnection]:
        """
        获取事务上下文管理器（自动提交/回滚）
        """
        return self._transaction_context()

    @asynccontextmanager
    async def _connection_context(self) -> AbstractAsyncContextManager[DBConnection]:
        """
        连接上下文管理器实现
        """
        async with self._engine.connect() as conn:
            sqlalchemy_conn = SQLAlchemyConnection(conn)
            try:
                yield sqlalchemy_conn
            finally:
                await sqlalchemy_conn.close()

    @asynccontextmanager
    async def _transaction_context(self) -> AbstractAsyncContextManager[DBConnection]:
        """
        事务上下文管理器实现（自动提交/回滚）
        """
        async with self._engine.begin() as conn:
            transaction = conn.get_transaction()
            sqlalchemy_conn = SQLAlchemyConnection(conn, transaction)
            try:
                yield sqlalchemy_conn
                # 如果没有异常，事务会自动提交
            except Exception:
                # 如果有异常，事务会自动回滚
                await sqlalchemy_conn.rollback()
                raise
            finally:
                # 不需要显式关闭，因为 begin() 会自动管理
                pass

    @override
    async def close(self) -> None:
        """
        关闭数据库引擎
        """
        await self._engine.dispose()
        print("SQLAlchemy engine disposed.")
