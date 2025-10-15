from abc import ABC, abstractmethod
from typing import Any
from contextlib import AbstractAsyncContextManager


from pydantic import BaseModel

from ..protocol.db import DBConnection, DBResult, SQLStatement


class BaseDBResult(BaseModel):
    rows: list[dict[str, Any]]
    rows_affected: int
    last_insert_rowid: int | str | None


class BaseDBConnection(ABC):
    @abstractmethod
    async def sql(
        self, sql: SQLStatement, params: dict[str, Any] | None = None
    ) -> DBResult: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...


class BaseDB(ABC):
    @abstractmethod
    async def sql(
        self, sql: SQLStatement, params: dict[str, Any] | None = None
    ) -> DBResult: ...

    @abstractmethod
    def connection(self) -> AbstractAsyncContextManager[DBConnection]: ...

    @abstractmethod
    def transaction(self) -> AbstractAsyncContextManager[DBConnection]: ...

    @abstractmethod
    async def close(self) -> None: ...
