"""
PGMQ (PostgreSQL Message Queue) ORM 适配器
使用 SQLAlchemy ORM 和 PostgreSQL 的 PGMQ 扩展实现队列功能
"""

import json
import asyncio
from dataclasses import dataclass, field
from typing import Any, TypeVar, override

from ..protocol.db import DB
from .base import BaseQueue, Item

T = TypeVar("T")


@dataclass
class Config:
    db: DB
    queue_name: str
    maxsize: int = field(default=0)


class PGMQueue(BaseQueue[Item[T]]):
    """PGMQ ORM 包装器，实现 Queue 协议"""

    def __init__(self, config: Config):
        self._db: DB = config.db
        self._queue_name: str = config.queue_name
        self._maxsize: int = config.maxsize
        self._initialized: bool = False

    async def _ensure_initialized(self):
        """确保队列已初始化"""
        if not self._initialized:
            await self._create_queue_if_not_exists()
            self._initialized = True

    async def _create_queue_if_not_exists(self):
        """创建PGMQ队列（如果不存在）"""
        # 使用 DB 协议的统一接口
        async with self._db.transaction() as conn:
            # 创建 PGMQ 队列
            await conn.sql(
                "SELECT pgmq.create(:queue_name)",
                {"queue_name": self._queue_name}
            )


    @override
    async def qsize(self) -> int:
        """返回队列中的项目数量"""
        await self._ensure_initialized()
        
        # 直接使用 PGMQ 函数获取队列大小
        result = await self._db.sql(
            "SELECT * FROM pgmq.metrics(:queue_name)",
            {"queue_name": self._queue_name}
        )
        
        if result.rows:
            # PGMQ metrics 返回的结构包含队列长度信息
            metrics = result.rows[0]
            return metrics.get('queue_length', 0)
        return 0

    @override
    async def maxsize(self) -> int:
        """返回队列的最大大小，0表示无限制"""
        return self._maxsize

    @override
    async def empty(self) -> bool:
        """如果队列为空返回True"""
        size = await self.qsize()
        return size == 0

    @override
    async def full(self) -> bool:
        """如果队列已满返回True"""
        if self._maxsize <= 0:
            return False
        size = await self.qsize()
        return size >= self._maxsize

    @override
    async def put(self, item: Any) -> None:
        """将项目放入队列，如果队列已满则等待"""
        await self._ensure_initialized()
        
        message_data = json.dumps(item)

        # 如果有最大大小限制，检查队列是否已满
        while self._maxsize > 0:
            size = await self.qsize()
            if size < self._maxsize:
                break
            # 等待一小段时间后重试
            await asyncio.sleep(0.01)

        # 使用 DB 协议的事务管理
        async with self._db.transaction() as conn:
            await conn.sql(
                "SELECT pgmq.send(:queue_name, CAST(:message AS jsonb))",
                {"queue_name": self._queue_name, "message": message_data}
            )

    @override
    async def get(self) -> Any:
        """从队列获取项目，如果队列为空则等待"""
        await self._ensure_initialized()
        
        while True:
            # 使用 PGMQ pop 函数，一次性读取并删除消息
            result = await self._db.sql(
                "SELECT * FROM pgmq.pop(:queue_name)",
                {"queue_name": self._queue_name}
            )
            
            if result.rows:
                row = result.rows[0]
                message_data = row.get('message')
                
                # 检查消息数据类型，如果已经是字典则直接返回，否则解析JSON
                if isinstance(message_data, (dict, list)):
                    return message_data
                elif isinstance(message_data, str):
                    return json.loads(message_data)
                else:
                    return message_data

            # 如果没有消息，等待一小段时间后重试
            await asyncio.sleep(0.1)

    @override
    def put_nowait(self, item: Any) -> None:
        """立即将项目放入队列，如果队列已满则抛出异常"""
        raise NotImplementedError("PGMQ ORM does not support synchronous put_nowait")

    @override
    def get_nowait(self) -> Any:
        """立即从队列获取项目，如果队列为空则抛出异常"""
        raise NotImplementedError("PGMQ ORM does not support synchronous get_nowait")

    @override
    async def task_done(self) -> None:
        """指示之前排队的任务已完成"""
        # PGMQ 通过删除消息来表示任务完成
        pass

    @override
    async def join(self) -> None:
        """阻塞直到队列中的所有项目都被获取并处理"""
        # 等待队列变空
        while not await self.empty():
            await asyncio.sleep(0.01)

    async def peek(self, limit: int = 1) -> list[Any]:
        """查看队列中的消息而不删除它们"""
        await self._ensure_initialized()
        
        # 使用 PGMQ read 函数查看消息但不删除
        result = await self._db.sql(
            "SELECT message FROM pgmq.read(:queue_name, 0, :limit)",
            {"queue_name": self._queue_name, "limit": limit}
        )
        
        messages = []
        for row in result.rows:
            message_data = row.get('message')
            # 检查消息数据类型，如果已经是字典/列表则直接使用，否则解析JSON
            if isinstance(message_data, (dict, list)):
                messages.append(message_data)
            elif isinstance(message_data, str):
                messages.append(json.loads(message_data))
            else:
                messages.append(message_data)
        
        return messages

    async def purge(self) -> int:
        """清空队列中的所有消息"""
        await self._ensure_initialized()
        
        # 使用 PGMQ 函数清空队列
        result = await self._db.sql(
            "SELECT pgmq.purge_queue(:queue_name)",
            {"queue_name": self._queue_name}
        )
        
        # 返回清除的消息数量
        if result.rows:
            return result.rows[0].get('purge_queue', 0)
        return 0

    async def archive_message(self, msg_id: int) -> bool:
        """将消息归档而不是删除"""
        await self._ensure_initialized()
        
        # 使用 PGMQ 函数归档消息
        result = await self._db.sql(
            "SELECT pgmq.archive(:queue_name, CAST(:msg_id AS bigint))",
            {"queue_name": self._queue_name, "msg_id": msg_id}
        )
        
        return len(result.rows) > 0

    async def get_queue_metrics(self) -> dict[str, Any]:
        """获取队列的统计信息"""
        await self._ensure_initialized()
        
        # 使用 PGMQ 内置的 metrics 函数
        result = await self._db.sql(
            "SELECT * FROM pgmq.metrics(:queue_name)",
            {"queue_name": self._queue_name}
        )
        
        if result.rows:
            metrics = result.rows[0]
            total_messages = metrics.get('queue_length', 0)
            
            return {
                "queue_name": self._queue_name,
                "total_messages": total_messages,
                "archived_messages": metrics.get('archived_messages', 0),
                "oldest_message_time": metrics.get('oldest_msg_age_sec'),
                "is_empty": total_messages == 0,
                "is_full": self._maxsize > 0 and total_messages >= self._maxsize,
            }
        
        return {
            "queue_name": self._queue_name,
            "total_messages": 0,
            "archived_messages": 0,
            "oldest_message_time": None,
            "is_empty": True,
            "is_full": False,
        }
