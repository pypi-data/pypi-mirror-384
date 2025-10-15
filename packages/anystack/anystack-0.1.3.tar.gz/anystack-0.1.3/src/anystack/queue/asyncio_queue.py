"""
AsyncIO Queue 适配器
"""

import asyncio
from typing import override, TypeVar, Protocol
from dataclasses import dataclass, field

from .base import BaseQueue, Item

T = TypeVar("T")


@dataclass
class Config:
    maxsize: int = field(default=0)


class AsyncioQueue(BaseQueue[Item[T]]):
    """AsyncIO Priority Queue"""

    def __init__(self, config: Config):
        self._queue = asyncio.PriorityQueue(maxsize=config.maxsize)

    @override
    async def qsize(self) -> int:
        """返回队列中的项目数量"""
        return self._queue.qsize()

    @override
    async def maxsize(self) -> int:
        """返回队列的最大大小，0表示无限制"""
        return self._queue.maxsize

    @override
    async def empty(self) -> bool:
        """如果队列为空返回True"""
        return self._queue.empty()

    @override
    async def full(self) -> bool:
        """如果队列已满返回True"""
        return self._queue.full()

    @override
    async def put(self, item: Item[T]):
        """将项目放入队列，如果队列已满则等待"""
        await self._queue.put(item)

    @override
    async def get(self) -> Item[T]:
        """从队列获取项目，如果队列已空则等待"""
        return await self._queue.get()

    @override
    def put_nowait(self, item: Item[T]):
        """立即将项目放入队列，如果队列已满则抛出异常"""
        self._queue.put_nowait(item)

    @override
    def get_nowait(self) -> Item[T]:
        """立即从队列获取项目，如果队列已空则抛出异常"""
        return self._queue.get_nowait()

    @override
    async def task_done(self):
        """指示之前排队的任务已完成"""
        self._queue.task_done()

    @override
    async def join(self):
        """阻塞直到队列中的所有项目都被获取并处理"""
        await self._queue.join()
