import asyncio
import json
from collections.abc import AsyncIterable
from dataclasses import dataclass, field
from typing import Any, override, TypeVar

from .base import BaseKV


T = TypeVar("T")


@dataclass
class Config:
    """内存KV配置"""

    initial_data: dict[str, Any] = field(default_factory=dict)


class MemoryKV(BaseKV[T]):
    """内存KV存储实现

    使用Python字典作为后端存储，支持JSON序列化的数据类型。
    适用于开发、测试环境或需要高性能临时存储的场景。
    """

    def __init__(self, config: Config):
        """初始化内存KV存储

        Args:
            config: 配置对象，可包含初始数据
        """
        self._store: dict[str, T] = config.initial_data.copy()
        self._lock = asyncio.Lock()

    @override
    async def get(self, key: str) -> T | None:
        """获取指定键的值

        Args:
            key: 键名

        Returns:
            键对应的值，如果键不存在则返回None
        """
        async with self._lock:
            return self._store.get(key)

    @override
    async def set(self, key: str, value: T) -> None:
        """设置键值对

        Args:
            key: 键名
            value: 值
        """

        async with self._lock:
            self._store[key] = value

    @override
    async def delete(self, key: str) -> None:
        """删除指定键

        Args:
            key: 要删除的键名
        """
        async with self._lock:
            self._store.pop(key, None)

    @override
    async def exists(self, key: str) -> bool:
        """检查键是否存在

        Args:
            key: 键名

        Returns:
            如果键存在返回True，否则返回False
        """
        async with self._lock:
            return key in self._store

    @override
    async def list(self) -> AsyncIterable[str]:
        """列出所有键

        Yields:
            存储中的所有键名
        """
        async def _list():
            async with self._lock:
                for key in self._store.keys():
                    yield key
        return _list()

    @override
    async def close(self) -> None:
        """关闭连接，清理资源

        对于内存存储，这里主要是清空数据
        """
        async with self._lock:
            self._store.clear()
