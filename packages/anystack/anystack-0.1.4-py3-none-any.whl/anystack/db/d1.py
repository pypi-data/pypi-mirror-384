import re
from contextlib import asynccontextmanager
from typing import Any, override
from dataclasses import dataclass, field
from contextlib import AbstractAsyncContextManager

import httpx
from sqlalchemy.dialects import sqlite
from sqlalchemy.sql.expression import ClauseElement

from ..protocol.db import DBConnection, DBResult, SQLStatement
from .base import BaseDB, BaseDBConnection, BaseDBResult


@dataclass(slots=True)
class Config:
    account_id: str
    database_id: str
    api_token: str
    client: httpx.AsyncClient | None = field(default=None)


class D1Connection(BaseDBConnection):
    """
    D1 连接包装器，支持批量操作和事务模拟
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        api_url: str,
        headers: dict[str, str],
        dialect: sqlite.dialect,
    ):
        self._client = client
        self._api_url = api_url
        self._headers = headers
        self._dialect = dialect
        self._closed = False
        # D1 不支持真正的事务，我们用批量操作模拟
        self._batch_statements: list[dict[str, Any]] = []
        self._in_transaction = False

    @override
    async def sql(
        self, sql: SQLStatement, params: dict[str, Any] | None = None
    ) -> DBResult:
        """
        在此连接上执行 SQL 查询
        """
        if self._closed:
            raise RuntimeError("Connection is closed")

        params = params or {}

        # 编译 SQL 和参数
        sql_str, param_list = self._compile_statement(sql, params)

        # 如果在事务中，添加到批量操作列表
        if self._in_transaction:
            self._batch_statements.append({"sql": sql_str, "params": param_list})
            # 返回一个占位符结果，真正的结果在 commit 时获得
            return BaseDBResult(rows=[], rows_affected=0, last_insert_rowid=None)
        else:
            # 立即执行单个语句
            return await self._execute_single(sql_str, param_list)

    def _compile_statement(
        self, sql: SQLStatement, params: dict[str, Any]
    ) -> tuple[str, list[Any]]:
        """
        编译 SQL 语句和参数为 D1 格式
        """
        if isinstance(sql, ClauseElement):
            # 编译 SQLAlchemy 表达式为 SQLite 方言
            # 使用 literal_binds=True 直接生成完整的 SQL，避免参数处理复杂性
            try:
                compiled = sql.compile(
                    dialect=self._dialect, compile_kwargs={"literal_binds": True}
                )
                sql_str = str(compiled)
                param_list = []  # literal_binds 模式下没有参数

                # 如果用户额外提供了参数，忽略它们并给出警告
                if params:
                    print(
                        "警告：SQLAlchemy 表达式使用 literal_binds 模式，忽略额外提供的参数"
                    )

            except Exception as e:
                # 如果 literal_binds 失败，回退到参数化模式
                print(f"literal_binds 编译失败，回退到参数化模式: {e}")
                compiled = sql.compile(dialect=self._dialect)
                sql_str = str(compiled)

                # 简化的参数处理
                param_list = []
                if hasattr(compiled, "construct_params"):
                    try:
                        construct_params = compiled.construct_params()
                        if construct_params:
                            # 使用命名参数重新编译以获得参数顺序
                            named_compiled = sql.compile(
                                dialect=sqlite.dialect(paramstyle="named")
                            )
                            named_sql = str(named_compiled)
                            param_keys = re.findall(r":(\w+)", named_sql)
                            param_list = [
                                construct_params.get(key) for key in param_keys
                            ]
                    except Exception:
                        # 最后的回退方案
                        if compiled.params:
                            param_list = list(compiled.params.values())

                # 合并用户提供的额外参数
                if params:
                    if isinstance(params, dict):
                        param_list.extend(params.values())
                    else:
                        param_list.extend(params)

        else:
            # 处理原始 SQL 字符串
            sql_str = sql
            param_list = []

            # 检查是否有命名参数 (:param)
            param_keys = re.findall(r":(\w+)", sql_str)
            if param_keys:
                if not params:
                    raise ValueError(
                        "Raw SQL with named parameters requires a params dict."
                    )
                # 按顺序构建参数列表
                param_list = [params.get(key) for key in param_keys]
                # 将命名占位符替换为 '?'
                sql_str = re.sub(r":\w+", "?", sql_str)
            elif params:
                # 如果 SQL 中没有命名参数，但提供了参数字典
                # 假设参数是按顺序提供的值
                if isinstance(params, dict):
                    # 如果是字典，提取值作为位置参数
                    param_list = list(params.values())
                else:
                    # 如果是列表，直接使用
                    param_list = params

        return sql_str, param_list

    async def _execute_single(self, sql: str, params: list[Any]) -> DBResult:
        """
        执行单个 SQL 语句
        """
        # D1 API 期望的格式
        payload = {"sql": sql}

        # 只有当有参数时才添加 params 字段
        if params:
            payload["params"] = params

        # 添加正确的 Content-Type 头
        headers = {**self._headers, "Content-Type": "application/json"}

        response = await self._client.post(self._api_url, headers=headers, json=payload)

        # 打印详细错误信息以便调试
        if response.status_code >= 400:
            error_text = (
                await response.aread() if hasattr(response, "aread") else response.text
            )
            print(f"D1 API Error - Status: {response.status_code}")
            print(f"Request payload: {payload}")
            print(f"Response: {error_text}")

        response.raise_for_status()

        return self._parse_response(response.json())

    async def _execute_batch(self, statements: list[dict[str, Any]]) -> list[DBResult]:
        """
        执行批量 SQL 语句
        """
        if not statements:
            return []

        # D1 批量 API 格式 - 清理空参数
        clean_statements = []
        for stmt in statements:
            clean_stmt = {"sql": stmt["sql"]}
            if stmt.get("params"):
                clean_stmt["params"] = stmt["params"]
            clean_statements.append(clean_stmt)

        payload = {"statements": clean_statements}

        # 添加正确的 Content-Type 头
        headers = {**self._headers, "Content-Type": "application/json"}

        response = await self._client.post(self._api_url, headers=headers, json=payload)

        # 打印详细错误信息以便调试
        if response.status_code >= 400:
            error_text = (
                await response.aread() if hasattr(response, "aread") else response.text
            )
            print(f"D1 Batch API Error - Status: {response.status_code}")
            print(f"Request payload: {payload}")
            print(f"Response: {error_text}")

        response.raise_for_status()

        data = response.json()
        if not data.get("success"):
            raise Exception(f"D1 API Error: {data.get('errors')}")

        # 解析批量结果
        results = []
        for result_part in data["result"]:
            if not result_part.get("success"):
                raise Exception(f"D1 Query Error: {result_part.get('error')}")
            results.append(self._parse_single_result(result_part))

        return results

    def _parse_response(self, data: dict[str, Any]) -> DBResult:
        """
        解析 D1 API 响应
        """
        if not data.get("success"):
            raise Exception(f"D1 API Error: {data.get('errors')}")

        # D1 的结果嵌套在 result 数组的第一个元素中
        result_part = data["result"][0]
        return self._parse_single_result(result_part)

    def _parse_single_result(self, result_part: dict[str, Any]) -> DBResult:
        """
        解析单个查询结果
        """
        if not result_part.get("success"):
            raise Exception(f"D1 Query Error: {result_part.get('error')}")

        meta = result_part.get("meta", {})

        return BaseDBResult(
            rows=result_part.get("results", []),
            rows_affected=meta.get("rows_written", 0),
            last_insert_rowid=meta.get("last_row_id", None),
        )

    @override
    async def commit(self) -> None:
        """
        提交事务（执行批量操作）
        """
        if self._closed:
            raise RuntimeError("Connection is closed")

        if self._in_transaction and self._batch_statements:
            # 执行批量操作
            await self._execute_batch(self._batch_statements)
            self._batch_statements.clear()

        self._in_transaction = False

    @override
    async def rollback(self) -> None:
        """
        回滚事务（清除批量操作）
        """
        if self._closed:
            raise RuntimeError("Connection is closed")

        # D1 不支持真正的回滚，我们只能清除待执行的语句
        self._batch_statements.clear()
        self._in_transaction = False

    def begin_transaction(self) -> None:
        """
        开始事务（启用批量模式）
        """
        self._in_transaction = True
        self._batch_statements.clear()

    @override
    async def close(self) -> None:
        """
        关闭连接
        """
        if not self._closed:
            # 如果有未提交的事务，自动回滚
            if self._in_transaction:
                await self.rollback()
            self._closed = True


class D1DB(BaseDB):
    """
    Cloudflare D1 数据库实现，通过 HTTP API 交互
    """

    def __init__(
        self,
        *,
        config: Config,
    ):
        """
        初始化 D1 数据库连接

        :param account_id: Cloudflare 账户 ID
        :param database_id: D1 数据库 ID
        :param api_token: Cloudflare API Token
        :param client: 可选的自定义 httpx 客户端
        """
        if not all([config.account_id, config.database_id, config.api_token]):
            raise ValueError("account_id, database_id, and api_token are required.")

        self._api_url = f"https://api.cloudflare.com/client/v4/accounts/{config.account_id}/d1/database/{config.database_id}/query"
        self._headers = {"Authorization": f"Bearer {config.api_token}"}
        self._client = config.client or httpx.AsyncClient()
        self._own_client = config.client is None  # 记录是否需要关闭客户端

        # D1 使用 SQLite 方言，参数样式为 'qmark' (?)
        self._dialect = sqlite.dialect(paramstyle="qmark")

    @override
    async def sql(
        self, sql: SQLStatement, params: dict[str, Any] | None = None
    ) -> DBResult:
        """
        执行单个 SQL 查询
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
        获取事务上下文管理器（批量操作模式）
        """
        return self._transaction_context()

    @asynccontextmanager
    async def _connection_context(self):
        """
        连接上下文管理器实现
        """
        d1_conn = D1Connection(
            self._client, self._api_url, self._headers, self._dialect
        )
        try:
            yield d1_conn
        finally:
            await d1_conn.close()

    @asynccontextmanager
    async def _transaction_context(self):
        """
        事务上下文管理器实现（批量操作模式）
        """
        d1_conn = D1Connection(
            self._client, self._api_url, self._headers, self._dialect
        )
        d1_conn.begin_transaction()

        try:
            yield d1_conn
            # 如果没有异常，自动提交
            await d1_conn.commit()
        except Exception:
            # 如果有异常，自动回滚
            await d1_conn.rollback()
            raise
        finally:
            await d1_conn.close()

    @override
    async def close(self) -> None:
        """
        关闭数据库连接
        """
        if self._own_client:
            await self._client.aclose()
        print("D1 client session closed.")
