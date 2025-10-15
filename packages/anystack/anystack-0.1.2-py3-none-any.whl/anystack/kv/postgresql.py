import json
from collections.abc import AsyncIterable
from dataclasses import dataclass, field
from typing import Any, override, TypeVar

from sqlalchemy import select, delete, func, text
from sqlalchemy.dialects.postgresql import insert

from ..protocol.db import DB
from .base import BaseKV
from .models import create_kv_table


T = TypeVar("T", bound=dict[str, Any])


@dataclass
class Config:
    """PostgreSQL ORM KV配置"""

    # 数据库实例
    db: DB
    # 表名配置
    table_name: str = field(default="kv_store")
    # 键前缀，避免命名冲突
    key_prefix: str = field(default="")
    # 是否自动创建表
    auto_create_table: bool = field(default=True)


class PostgreSQLKV(BaseKV[T]):
    """PostgreSQL ORM KV存储实现

    使用SQLAlchemy ORM作为后端存储，支持JSON序列化的数据类型。
    适用于生产环境，支持事务、持久化和高可用性。
    """

    def __init__(self, config: Config):
        """初始化PostgreSQL ORM KV存储

        Args:
            config: PostgreSQL配置对象
        """
        self._config: Config = config
        self._db: DB = config.db
        self._key_prefix: str = config.key_prefix
        self._table_name: str = config.table_name
        self._initialized: bool = False

        # 动态创建对应表名的模型
        self._model = create_kv_table(self._table_name)

    async def _ensure_initialized(self):
        """确保表已初始化"""
        if not self._initialized:
            # 自动创建表（如果启用）
            if self._config.auto_create_table:
                await self._create_table_if_not_exists()
            self._initialized = True

    async def _create_table_if_not_exists(self):
        """创建KV存储表（如果不存在）"""
        # 使用 DB 协议的统一接口执行 DDL
        async with self._db.transaction() as conn:
            # 使用 SQLAlchemy 的 text() 构造器创建 DDL 语句
            create_table_sql = text(f"""
                CREATE TABLE IF NOT EXISTS {self._table_name} (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            await conn.sql(create_table_sql)


    def _get_prefixed_key(self, key: str) -> str:
        """获取带前缀的键名"""
        return f"{self._key_prefix}{key}" if self._key_prefix else key

    def _remove_prefix(self, prefixed_key: str) -> str:
        """移除键名前缀"""
        if self._key_prefix and prefixed_key.startswith(self._key_prefix):
            return prefixed_key[len(self._key_prefix) :]
        return prefixed_key

    @override
    async def get(self, key: str) -> T | None:
        """获取指定键的值

        Args:
            key: 键名

        Returns:
            键对应的值，如果键不存在则返回None
        """
        await self._ensure_initialized()
        prefixed_key = self._get_prefixed_key(key)

        # 使用 SQLAlchemy 的 select 语法
        stmt = select(self._model.value).where(self._model.key == prefixed_key)
        result = await self._db.sql(stmt)
        
        if result.rows:
            return result.rows[0]["value"]
        return None

    @override
    async def set(self, key: str, value: T) -> None:
        """设置键值对

        Args:
            key: 键名
            value: 值，必须是JSON序列化兼容的类型
        """
        await self._ensure_initialized()

        # 验证值是否可以JSON序列化
        try:
            json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Value must be JSON serializable: {e}")

        prefixed_key = self._get_prefixed_key(key)

        # 使用 SQLAlchemy 的 insert 和 on_conflict_do_update 语法
        async with self._db.transaction() as conn:
            stmt = insert(self._model).values(key=prefixed_key, value=value)
            stmt = stmt.on_conflict_do_update(
                index_elements=["key"],
                set_={"value": stmt.excluded.value, "updated_at": func.now()},
            )
            await conn.sql(stmt)

    @override
    async def delete(self, key: str) -> None:
        """删除指定键

        Args:
            key: 要删除的键名
        """
        await self._ensure_initialized()
        prefixed_key = self._get_prefixed_key(key)

        # 使用 SQLAlchemy 的 delete 语法
        async with self._db.transaction() as conn:
            stmt = delete(self._model).where(self._model.key == prefixed_key)
            await conn.sql(stmt)

    @override
    async def exists(self, key: str) -> bool:
        """检查键是否存在

        Args:
            key: 键名

        Returns:
            如果键存在返回True，否则返回False
        """
        await self._ensure_initialized()
        prefixed_key = self._get_prefixed_key(key)

        # 使用 SQLAlchemy 的 select 和 func.count 语法
        stmt = select(func.count()).where(self._model.key == prefixed_key)
        result = await self._db.sql(stmt)
        
        if result.rows:
            # func.count() 的结果通常是第一个列
            count_value = list(result.rows[0].values())[0]
            return count_value > 0
        return False

    @override
    async def list(self) -> AsyncIterable[str]:
        """列出所有键

        Yields:
            存储中的所有键名（不包含前缀）
        """

        async def _list():
            await self._ensure_initialized()

            if self._key_prefix:
                # 使用 SQLAlchemy 的 like 查询匹配前缀
                pattern = f"{self._key_prefix}%"
                stmt = (
                    select(self._model.key)
                    .where(self._model.key.like(pattern))
                    .order_by(self._model.key)
                )
                result = await self._db.sql(stmt)
                for row in result.rows:
                    yield self._remove_prefix(row["key"])
            else:
                # 使用 SQLAlchemy 查询所有键
                stmt = select(self._model.key).order_by(self._model.key)
                result = await self._db.sql(stmt)
                for row in result.rows:
                    yield row["key"]

        return _list()

    @override
    async def close(self) -> None:
        """关闭连接，清理资源"""
        # 数据库连接由外部管理，这里不需要关闭
        # 只需要重置初始化状态
        self._initialized = False

    async def ping(self) -> bool:
        """测试PostgreSQL连接

        Returns:
            如果连接正常返回True，否则返回False
        """
        try:
            # 使用 SQLAlchemy 的 text() 执行简单的测试查询
            stmt = text("SELECT 1")
            result = await self._db.sql(stmt)
            return len(result.rows) > 0
        except Exception:
            return False

    async def clear(self) -> None:
        """清空所有数据"""
        await self._ensure_initialized()

        # 使用 SQLAlchemy 的 delete 语法
        async with self._db.transaction() as conn:
            if self._key_prefix:
                # 只删除带前缀的键
                pattern = f"{self._key_prefix}%"
                stmt = delete(self._model).where(self._model.key.like(pattern))
            else:
                # 删除所有数据
                stmt = delete(self._model)

            await conn.sql(stmt)

    async def count(self) -> int:
        """获取存储的键值对数量

        Returns:
            键值对数量
        """
        await self._ensure_initialized()

        # 使用 SQLAlchemy 的 select 和 func.count 语法
        if self._key_prefix:
            # 只计算带前缀的键
            pattern = f"{self._key_prefix}%"
            stmt = select(func.count()).where(self._model.key.like(pattern))
        else:
            # 计算所有键
            stmt = select(func.count()).select_from(self._model)

        result = await self._db.sql(stmt)
        if result.rows:
            count_value = list(result.rows[0].values())[0]
            return count_value or 0
        return 0

    async def get_metadata(self, key: str) -> dict[str, Any] | None:
        """获取键的元数据（创建时间、更新时间等）

        Args:
            key: 键名

        Returns:
            包含元数据的字典，如果键不存在则返回None
        """
        await self._ensure_initialized()
        prefixed_key = self._get_prefixed_key(key)

        # 使用 SQLAlchemy 的 select 语法
        stmt = select(self._model.created_at, self._model.updated_at).where(
            self._model.key == prefixed_key
        )

        result = await self._db.sql(stmt)

        if result.rows:
            row = result.rows[0]
            return {
                "created_at": row["created_at"], 
                "updated_at": row["updated_at"]
            }

        return None
