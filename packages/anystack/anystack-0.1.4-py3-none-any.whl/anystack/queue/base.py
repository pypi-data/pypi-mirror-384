"""
队列适配器基类
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Protocol
from dataclasses import dataclass, field

D = TypeVar("D")
T = TypeVar("T")


@dataclass(slots=True)
class Item[D]:
    data: D
    priority: int = field(default=0)


class BaseQueue[T](ABC):
    """队列适配器基类"""

    @abstractmethod
    async def qsize(self) -> int:
        """返回队列中的项目数量"""
        ...

    @abstractmethod
    async def maxsize(self) -> int:
        """返回队列的最大大小，0表示无限制"""
        ...

    @abstractmethod
    async def empty(self) -> bool:
        """如果队列为空返回True"""
        ...

    @abstractmethod
    async def full(self) -> bool:
        """如果队列已满返回True"""
        ...

    @abstractmethod
    async def put(self, item: T):
        """将项目放入队列，如果队列已满则等待"""
        ...

    @abstractmethod
    async def get(self) -> T:
        """从队列获取项目，如果队列为空则等待"""
        ...

    @abstractmethod
    def put_nowait(self, item: T):
        """立即将项目放入队列，如果队列已满则抛出异常"""
        ...

    @abstractmethod
    def get_nowait(self) -> T:
        """立即从队列获取项目，如果队列为空则抛出异常"""
        ...

    @abstractmethod
    async def task_done(self):
        """指示之前排队的任务已完成"""
        ...

    @abstractmethod
    async def join(self):
        """阻塞直到队列中的所有项目都被获取并处理"""
        ...
