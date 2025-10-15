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
    async def set(self, key: str, value: T) -> None:
        """设置键值对"""
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
    async def close(self) -> None:
        """关闭连接，清理资源"""
        ...
