import asyncio
import json
from collections.abc import AsyncIterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, override, TypeVar

from .base import BaseKV


T = TypeVar("T")


@dataclass
class Config:
    """内存KV配置"""

    initial_data: dict[str, Any] = field(default_factory=dict)
    # 过期数据清理间隔（秒），None 表示不启动后台清理
    cleanup_interval: int | None = field(default=60)  # 默认1分钟


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
        self._expires: dict[str, datetime] = {}  # 存储过期时间
        self._lock = asyncio.Lock()
        self._config = config
        self._cleanup_task: asyncio.Task[None] | None = None
        self._initialized = False

    async def _ensure_initialized(self):
        """确保已初始化"""
        if not self._initialized:
            # 启动后台清理任务
            if self._config.cleanup_interval and self._cleanup_task is None:
                self._cleanup_task = asyncio.create_task(self._cleanup_expired_keys())
            self._initialized = True
    
    async def _cleanup_expired_keys(self) -> None:
        """后台任务：定期清理过期的键"""
        if self._config.cleanup_interval is None:
            return
        
        while True:
            try:
                await asyncio.sleep(self._config.cleanup_interval)
                
                async with self._lock:
                    now = datetime.now(timezone.utc)
                    expired_keys = [
                        key for key, expires_at in self._expires.items()
                        if expires_at <= now
                    ]
                    for key in expired_keys:
                        self._store.pop(key, None)
                        self._expires.pop(key, None)
            except asyncio.CancelledError:
                break
            except Exception:
                # 忽略清理过程中的错误，继续下一轮
                pass
    
    def _is_expired(self, key: str) -> bool:
        """检查键是否已过期"""
        if key not in self._expires:
            return False
        now = datetime.now(timezone.utc)
        return self._expires[key] <= now

    @override
    async def get(self, key: str) -> T | None:
        """获取指定键的值

        Args:
            key: 键名

        Returns:
            键对应的值，如果键不存在则返回None
        """
        await self._ensure_initialized()
        async with self._lock:
            # 检查是否过期
            if self._is_expired(key):
                self._store.pop(key, None)
                self._expires.pop(key, None)
                return None
            return self._store.get(key)

    @override
    async def set(self, key: str, value: T, ttl: int | None = None) -> None:
        """设置键值对

        Args:
            key: 键名
            value: 值
            ttl: 过期时间（秒），None 表示永不过期
        """
        await self._ensure_initialized()
        async with self._lock:
            self._store[key] = value
            if ttl is not None:
                self._expires[key] = datetime.now(timezone.utc) + timedelta(seconds=ttl)
            else:
                # 移除过期时间（如果之前设置过）
                self._expires.pop(key, None)

    @override
    async def delete(self, key: str) -> None:
        """删除指定键

        Args:
            key: 要删除的键名
        """
        async with self._lock:
            self._store.pop(key, None)
            self._expires.pop(key, None)

    @override
    async def exists(self, key: str) -> bool:
        """检查键是否存在

        Args:
            key: 键名

        Returns:
            如果键存在返回True，否则返回False
        """
        async with self._lock:
            if key not in self._store:
                return False
            # 检查是否过期
            if self._is_expired(key):
                self._store.pop(key, None)
                self._expires.pop(key, None)
                return False
            return True

    @override
    async def list(self) -> AsyncIterable[str]:
        """列出所有键

        Yields:
            存储中的所有键名
        """
        async def _list():
            async with self._lock:
                # 清理过期的键并返回有效的键
                now = datetime.now(timezone.utc)
                expired_keys = []
                for key in list(self._store.keys()):
                    if self._is_expired(key):
                        expired_keys.append(key)
                    else:
                        yield key
                # 清理过期的键
                for key in expired_keys:
                    self._store.pop(key, None)
                    self._expires.pop(key, None)
        return _list()
    
    @override
    async def expire(self, key: str, seconds: int) -> None:
        """设置键的过期时间
        
        Args:
            key: 键名
            seconds: 过期时间（秒）
        """
        async with self._lock:
            if key in self._store:
                self._expires[key] = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    
    @override
    async def ttl(self, key: str) -> int:
        """获取键的剩余生存时间
        
        Args:
            key: 键名
            
        Returns:
            剩余生存时间（秒），-1表示永不过期，-2表示键不存在
        """
        async with self._lock:
            if key not in self._store:
                return -2  # 键不存在
            
            if key not in self._expires:
                return -1  # 永不过期
            
            expires_at = self._expires[key]
            now = datetime.now(timezone.utc)
            
            if expires_at <= now:
                # 已过期，清理并返回 -2
                self._store.pop(key, None)
                self._expires.pop(key, None)
                return -2
            
            remaining = (expires_at - now).total_seconds()
            return int(remaining)

    @override
    async def close(self) -> None:
        """关闭连接，清理资源

        对于内存存储，这里主要是清空数据
        """
        # 取消后台清理任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        async with self._lock:
            self._store.clear()
            self._expires.clear()
        
        self._initialized = False
