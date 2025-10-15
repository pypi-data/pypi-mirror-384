import json
from collections.abc import AsyncIterable
from dataclasses import dataclass, field
from typing import Any, override, TypeVar

import redis.asyncio as redis
from redis.asyncio import Redis

from .base import BaseKV


T = TypeVar("T", bound=dict[str, Any])


@dataclass
class Config:
    """Redis KV配置"""

    # Redis URL 格式: redis://username:password@host:port/db
    url: str | None = field(default_factory=lambda: f"redis://localhost:6379/0")
    decode_responses: bool = field(default=True)
    socket_timeout: float = field(default=5.0)
    socket_connect_timeout: float = field(default=5.0)
    retry_on_timeout: bool = field(default=True)
    health_check_interval: int = field(default=30)
    max_connections: int = field(default=10)
    # 键前缀，避免命名冲突
    key_prefix: str = field(default="")


class RedisKV(BaseKV[T]):
    """Redis KV存储实现

    使用Redis作为后端存储，支持JSON序列化的数据类型。
    适用于生产环境，支持持久化、集群和高可用性。
    """

    def __init__(self, config: Config):
        """初始化Redis KV存储

        Args:
            config: Redis配置对象

        Raises:
            ImportError: 如果没有安装redis包
        """

        self._config: Config = config
        self._client: Redis | None = None
        self._key_prefix: str = config.key_prefix

    async def _ensure_client(self):
        """确保Redis客户端已初始化"""
        if self._client is None:
            self._client = redis.from_url(
                self._config.url,
                decode_responses=self._config.decode_responses,
                socket_timeout=self._config.socket_timeout,
                socket_connect_timeout=self._config.socket_connect_timeout,
                retry_on_timeout=self._config.retry_on_timeout,
                health_check_interval=self._config.health_check_interval,
                max_connections=self._config.max_connections,
            )

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
        await self._ensure_client()

        if self._client is None:
            raise RuntimeError("Redis client not available")

        prefixed_key = self._get_prefixed_key(key)
        value = await self._client.get(prefixed_key)

        if value is None:
            return None

        return json.loads(value)

    @override
    async def set(self, key: str, value: T) -> None:
        """设置键值对

        Args:
            key: 键名
            value: 值，必须是JSON序列化兼容的类型
        """
        await self._ensure_client()

        if self._client is None:
            raise RuntimeError("Redis client not available")

        # 将值序列化为JSON
        try:
            serialized_value = json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Value must be JSON serializable: {e}")

        prefixed_key = self._get_prefixed_key(key)
        await self._client.set(prefixed_key, serialized_value)

    @override
    async def delete(self, key: str) -> None:
        """删除指定键

        Args:
            key: 要删除的键名
        """
        await self._ensure_client()

        if self._client is None:
            raise RuntimeError("Redis client not available")

        prefixed_key = self._get_prefixed_key(key)
        await self._client.delete(prefixed_key)

    @override
    async def exists(self, key: str) -> bool:
        """检查键是否存在

        Args:
            key: 键名

        Returns:
            如果键存在返回True，否则返回False
        """
        await self._ensure_client()

        if self._client is None:
            raise RuntimeError("Redis client not available")

        prefixed_key = self._get_prefixed_key(key)
        result = await self._client.exists(prefixed_key)
        return bool(result)

    @override
    async def list(self) -> AsyncIterable[str]:
        """列出所有键

        Yields:
            存储中的所有键名（不包含前缀）
        """
        async def _list():
            await self._ensure_client()

            if self._client is None:
                raise RuntimeError("Redis client not available")

            pattern = f"{self._key_prefix}*" if self._key_prefix else "*"

            async for key in self._client.scan_iter(match=pattern):
                yield self._remove_prefix(key)
        return _list()

    @override
    async def close(self) -> None:
        """关闭连接，清理资源"""
        if self._client:
            await self._client.close()
            self._client = None

    async def ping(self) -> bool:
        """测试Redis连接

        Returns:
            如果连接正常返回True，否则返回False
        """
        try:
            await self._ensure_client()
            if self._client is None:
                return False
            await self._client.ping()
            return True
        except Exception:
            return False

    async def expire(self, key: str, seconds: int) -> None:
        """设置键的过期时间

        Args:
            key: 键名
            seconds: 过期时间（秒）
        """
        await self._ensure_client()

        if self._client is None:
            raise RuntimeError("Redis client not available")

        prefixed_key = self._get_prefixed_key(key)
        await self._client.expire(prefixed_key, seconds)

    async def ttl(self, key: str) -> int:
        """获取键的剩余生存时间

        Args:
            key: 键名

        Returns:
            剩余生存时间（秒），-1表示永不过期，-2表示键不存在
        """
        await self._ensure_client()

        if self._client is None:
            raise RuntimeError("Redis client not available")

        prefixed_key = self._get_prefixed_key(key)
        return await self._client.ttl(prefixed_key)
