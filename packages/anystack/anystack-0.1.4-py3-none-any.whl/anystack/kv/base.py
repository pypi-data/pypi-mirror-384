from abc import ABC, abstractmethod
from collections.abc import AsyncIterable
from typing import TypeVar

T = TypeVar("T")


class BaseKV[T](ABC):
    """KV存储的基础抽象类"""
    
    @abstractmethod
    async def get(self, key: str) -> T | None:
        """获取指定键的值"""
        ...

    @abstractmethod
    async def set(self, key: str, value: T, ttl: int | None = None) -> None:
        """设置键值对
        
        Args:
            key: 键名
            value: 值
            ttl: 过期时间（秒），None 表示永不过期
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """删除指定键"""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        ...

    @abstractmethod
    async def list(self) -> AsyncIterable[str]:
        """列出所有键"""
        ...
    
    @abstractmethod
    async def expire(self, key: str, seconds: int) -> None:
        """设置键的过期时间
        
        Args:
            key: 键名
            seconds: 过期时间（秒）
        """
        ...
    
    @abstractmethod
    async def ttl(self, key: str) -> int:
        """获取键的剩余生存时间
        
        Args:
            key: 键名
            
        Returns:
            剩余生存时间（秒），-1表示永不过期，-2表示键不存在
        """
        ...
    
    @abstractmethod
    async def close(self) -> None:
        """关闭连接，清理资源"""
        ...
