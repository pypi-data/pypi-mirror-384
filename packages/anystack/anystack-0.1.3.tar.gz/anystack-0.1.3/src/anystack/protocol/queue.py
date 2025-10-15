from typing import Protocol, TypeVar


T = TypeVar('T')


class Queue(Protocol[T]):

    async def qsize(self) -> int:
        """返回队列中的项目数量"""
        ...
    
    async def maxsize(self) -> int:
        """返回队列的最大大小，0表示无限制"""
        ...
    
    async def empty(self) -> bool:
        """如果队列为空返回True"""
        ...
    
    async def full(self) -> bool:
        """如果队列已满返回True"""
        ...
    
    async def put(self, item: T):
        """将项目放入队列，如果队列已满则等待"""
        ...
    
    async def get(self) -> T:
        """从队列获取项目，如果队列为空则等待"""
        ...
    
    def put_nowait(self, item: T):
        """立即将项目放入队列，如果队列已满则抛出异常"""
        ...
    
    def get_nowait(self) -> T:
        """立即从队列获取项目，如果队列为空则抛出异常"""
        ...
    
    async def task_done(self):
        """指示之前排队的任务已完成"""
        ...
    
    async def join(self):
        """阻塞直到队列中的所有项目都被获取并处理"""
        ...


