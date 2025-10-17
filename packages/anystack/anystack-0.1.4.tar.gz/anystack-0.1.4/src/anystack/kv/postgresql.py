import asyncio
import json
from collections.abc import AsyncIterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
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
    # 过期数据清理间隔（秒），None 表示不启动后台清理
    cleanup_interval: int | None = field(default=300)  # 默认5分钟


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
        self._cleanup_task: asyncio.Task[None] | None = None

        # 动态创建对应表名的模型
        self._model = create_kv_table(self._table_name)

    async def _ensure_initialized(self):
        """确保表已初始化"""
        if not self._initialized:
            # 自动创建表（如果启用）
            if self._config.auto_create_table:
                await self._create_table_if_not_exists()
            # 启动后台清理任务
            if self._config.cleanup_interval and self._cleanup_task is None:
                self._cleanup_task = asyncio.create_task(self._cleanup_expired_keys())
            self._initialized = True

    async def _create_table_if_not_exists(self):
        """创建KV存储表（如果不存在）"""
        # 使用 SQLAlchemy ORM 的 metadata.create_all() 来创建表
        # 这样可以自动适配不同的数据库方言
        from .models import Base
        from sqlalchemy import Index
        
        # 确保模型的表在元数据中
        if not hasattr(self._model, '__table__'):
            return
        
        # 获取底层的 SQLAlchemy 引擎
        async with self._db.transaction() as conn:
            # 获取 SQLAlchemy 连接
            raw_conn = conn._connection if hasattr(conn, '_connection') else conn
            
            # 使用 run_sync 在异步上下文中执行同步的 create_all
            def create_tables(sync_conn):
                # 只创建这个特定的表
                Base.metadata.create_all(
                    bind=sync_conn,
                    tables=[self._model.__table__],
                    checkfirst=True
                )
                
                # 为 expires_at 创建索引（如果数据库支持）
                try:
                    idx = Index(
                        f'idx_{self._table_name}_expires_at',
                        self._model.expires_at,
                        postgresql_where=self._model.expires_at.isnot(None)
                    )
                    if not idx.exists(sync_conn):
                        idx.create(sync_conn)
                except Exception:
                    # 某些数据库可能不支持部分索引，忽略错误
                    pass
            
            await raw_conn.run_sync(create_tables)
    
    async def _cleanup_expired_keys(self) -> None:
        """后台任务：定期清理过期的键"""
        if self._config.cleanup_interval is None:
            return
        
        while True:
            try:
                await asyncio.sleep(self._config.cleanup_interval)
                
                # 删除已过期的键
                async with self._db.transaction() as conn:
                    now = datetime.now(timezone.utc)
                    stmt = delete(self._model).where(
                        self._model.expires_at.isnot(None),
                        self._model.expires_at <= now
                    )
                    await conn.sql(stmt)
            except asyncio.CancelledError:
                break
            except Exception:
                # 忽略清理过程中的错误，继续下一轮
                pass


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

        # 使用 SQLAlchemy 的 select 语法，过滤未过期的数据
        now = datetime.now(timezone.utc)
        stmt = select(self._model.value).where(
            self._model.key == prefixed_key,
            (self._model.expires_at.is_(None)) | (self._model.expires_at > now)
        )
        result = await self._db.sql(stmt)
        
        if result.rows:
            return result.rows[0]["value"]
        return None

    @override
    async def set(self, key: str, value: T, ttl: int | None = None) -> None:
        """设置键值对

        Args:
            key: 键名
            value: 值，必须是JSON序列化兼容的类型
            ttl: 过期时间（秒），None 表示永不过期
        """
        await self._ensure_initialized()

        # 验证值是否可以JSON序列化
        try:
            json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Value must be JSON serializable: {e}")

        prefixed_key = self._get_prefixed_key(key)
        
        # 计算过期时间
        expires_at = None
        if ttl is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        # 使用 SQLAlchemy 的 insert 和 on_conflict_do_update 语法
        async with self._db.transaction() as conn:
            stmt = insert(self._model).values(
                key=prefixed_key, 
                value=value,
                expires_at=expires_at
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["key"],
                set_={
                    "value": stmt.excluded.value, 
                    "updated_at": func.now(),
                    "expires_at": stmt.excluded.expires_at
                },
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

        # 使用 SQLAlchemy 的 select 和 func.count 语法，过滤未过期的数据
        now = datetime.now(timezone.utc)
        stmt = select(func.count()).where(
            self._model.key == prefixed_key,
            (self._model.expires_at.is_(None)) | (self._model.expires_at > now)
        )
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
            now = datetime.now(timezone.utc)

            if self._key_prefix:
                # 使用 SQLAlchemy 的 like 查询匹配前缀，过滤未过期的数据
                pattern = f"{self._key_prefix}%"
                stmt = (
                    select(self._model.key)
                    .where(
                        self._model.key.like(pattern),
                        (self._model.expires_at.is_(None)) | (self._model.expires_at > now)
                    )
                    .order_by(self._model.key)
                )
                result = await self._db.sql(stmt)
                for row in result.rows:
                    yield self._remove_prefix(row["key"])
            else:
                # 使用 SQLAlchemy 查询所有键，过滤未过期的数据
                stmt = select(self._model.key).where(
                    (self._model.expires_at.is_(None)) | (self._model.expires_at > now)
                ).order_by(self._model.key)
                result = await self._db.sql(stmt)
                for row in result.rows:
                    yield row["key"]

        return _list()

    @override
    async def expire(self, key: str, seconds: int) -> None:
        """设置键的过期时间
        
        Args:
            key: 键名
            seconds: 过期时间（秒）
        """
        await self._ensure_initialized()
        prefixed_key = self._get_prefixed_key(key)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        
        async with self._db.transaction() as conn:
            stmt = (
                insert(self._model)
                .values(key=prefixed_key, expires_at=expires_at)
                .on_conflict_do_update(
                    index_elements=["key"],
                    set_={"expires_at": expires_at, "updated_at": func.now()}
                )
            )
            await conn.sql(stmt)
    
    @override
    async def ttl(self, key: str) -> int:
        """获取键的剩余生存时间
        
        Args:
            key: 键名
            
        Returns:
            剩余生存时间（秒），-1表示永不过期，-2表示键不存在
        """
        await self._ensure_initialized()
        prefixed_key = self._get_prefixed_key(key)
        
        stmt = select(self._model.expires_at).where(self._model.key == prefixed_key)
        result = await self._db.sql(stmt)
        
        if not result.rows:
            return -2  # 键不存在
        
        expires_at = result.rows[0]["expires_at"]
        if expires_at is None:
            return -1  # 永不过期
        
        now = datetime.now(timezone.utc)
        if expires_at <= now:
            return -2  # 已过期，视为不存在
        
        remaining = (expires_at - now).total_seconds()
        return int(remaining)
    
    @override
    async def close(self) -> None:
        """关闭连接，清理资源"""
        # 取消后台清理任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
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
