"""
数据库队列适配器
使用标准SQL操作实现的通用数据库队列，支持优先级和FIFO
"""

import json
import asyncio
from dataclasses import dataclass, field
from typing import Any, TypeVar, override, cast
from datetime import datetime

from ..protocol.db import DB
from .base import BaseQueue, Item

T = TypeVar("T")


@dataclass
class Config:
    """数据库队列配置"""
    db: DB
    table_name: str = field(default="queue_items")
    maxsize: int = field(default=0)
    auto_create_table: bool = field(default=True)


class DBQueue(BaseQueue[Item[T]]):
    """基于数据库的队列实现，使用标准SQL操作"""

    def __init__(self, config: Config):
        self._db: DB = config.db
        self._table_name: str = config.table_name
        self._maxsize: int = config.maxsize
        self._auto_create_table: bool = config.auto_create_table
        self._initialized: bool = False

    async def _ensure_initialized(self):
        """确保队列表已初始化"""
        if not self._initialized:
            if self._auto_create_table:
                await self._create_table_if_not_exists()
            self._initialized = True

    async def _create_table_if_not_exists(self):
        """创建队列表（如果不存在）"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self._table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            processing BOOLEAN NOT NULL DEFAULT FALSE
        )
        """
        
        # 创建索引以优化查询性能
        create_index_sql = f"""
        CREATE INDEX IF NOT EXISTS idx_{self._table_name}_priority_created 
        ON {self._table_name} (priority DESC, created_at ASC)
        """
        
        async with self._db.transaction() as conn:
            _ = await conn.sql(create_table_sql)
            _ = await conn.sql(create_index_sql)

    @override
    async def qsize(self) -> int:
        """返回队列中的项目数量"""
        await self._ensure_initialized()
        
        result = await self._db.sql(
            f"SELECT COUNT(*) as count FROM {self._table_name} WHERE processing = FALSE"
        )
        
        if result.rows:
            return result.rows[0]['count']
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
    async def put(self, item: Item[T]):
        """将项目放入队列，如果队列已满则等待"""
        await self._ensure_initialized()
        
        # 如果有最大大小限制，等待直到有空间
        while self._maxsize > 0:
            if not await self.full():
                break
            await asyncio.sleep(0.01)

        # 序列化数据
        data_json = json.dumps({
            'data': item.data,
            'priority': item.priority
        }, default=str)

        # 插入到数据库
        async with self._db.transaction() as conn:
            _ = await conn.sql(
                f"""
                INSERT INTO {self._table_name} (data, priority, created_at, processing)
                VALUES (:data, :priority, :created_at, FALSE)
                """,
                {
                    'data': data_json,
                    'priority': item.priority,
                    'created_at': datetime.now()
                }
            )

    @override
    async def get(self) -> Item[T]:
        """从队列获取项目，如果队列为空则等待"""
        await self._ensure_initialized()
        
        while True:
            # 使用事务确保原子性操作
            async with self._db.transaction() as conn:
                # 查找优先级最高（数值最大）且最早的项目
                result = await conn.sql(
                    f"""
                    SELECT id, data FROM {self._table_name} 
                    WHERE processing = FALSE 
                    ORDER BY priority DESC, created_at ASC 
                    LIMIT 1
                    """
                )
                
                if result.rows:
                    row = result.rows[0]
                    item_id = row['id']
                    
                    # 标记为正在处理
                    _ = await conn.sql(
                        f"UPDATE {self._table_name} SET processing = TRUE WHERE id = :id",
                        {'id': item_id}
                    )
                    
                    # 解析数据
                    data_dict = json.loads(cast(str, row['data']))
                    return Item(
                        data=data_dict['data'],
                        priority=data_dict['priority']
                    )
            
            # 如果没有项目，等待一小段时间后重试
            await asyncio.sleep(0.1)

    @override
    def put_nowait(self, item: Item[T]):
        """立即将项目放入队列，如果队列已满则抛出异常"""
        # 由于数据库操作是异步的，这里抛出异常
        raise NotImplementedError("数据库队列不支持同步的 put_nowait 操作")

    @override
    def get_nowait(self) -> Item[T]:
        """立即从队列获取项目，如果队列为空则抛出异常"""
        # 由于数据库操作是异步的，这里抛出异常
        raise NotImplementedError("数据库队列不支持同步的 get_nowait 操作")

    @override
    async def task_done(self):
        """指示之前排队的任务已完成"""
        await self._ensure_initialized()
        
        # 删除所有标记为正在处理的项目
        async with self._db.transaction() as conn:
            _ = await conn.sql(
                f"DELETE FROM {self._table_name} WHERE processing = TRUE"
            )

    @override
    async def join(self):
        """阻塞直到队列中的所有项目都被获取并处理"""
        # 等待队列变空且没有正在处理的项目
        while True:
            result = await self._db.sql(
                f"SELECT COUNT(*) as count FROM {self._table_name}"
            )
            
            if result.rows and result.rows[0]['count'] == 0:
                break
            
            await asyncio.sleep(0.01)

    async def peek(self, limit: int = 1) -> list[Item[T]]:
        """查看队列中的项目而不删除它们"""
        await self._ensure_initialized()
        
        result = await self._db.sql(
            f"""
            SELECT data FROM {self._table_name} 
            WHERE processing = FALSE 
            ORDER BY priority DESC, created_at ASC 
            LIMIT :limit
            """,
            {'limit': limit}
        )
        
        items: list[Item[T]] = []
        for row in result.rows:
            data_dict = json.loads(cast(str, row['data']))
            items.append(Item(
                data=cast(T, data_dict['data']),
                priority=cast(int, data_dict['priority'])
            ))
        
        return items

    async def purge(self) -> int:
        """清空队列中的所有项目"""
        await self._ensure_initialized()
        
        result = await self._db.sql(f"SELECT COUNT(*) as count FROM {self._table_name}")
        count = result.rows[0]['count'] if result.rows else 0
        
        async with self._db.transaction() as conn:
            _ = await conn.sql(f"DELETE FROM {self._table_name}")
        
        return count

    async def get_metrics(self) -> dict[str, Any]:
        """获取队列的统计信息"""
        await self._ensure_initialized()
        
        result = await self._db.sql(
            f"""
            SELECT 
                COUNT(*) as total_count,
                COUNT(CASE WHEN processing = FALSE THEN 1 END) as pending_count,
                COUNT(CASE WHEN processing = TRUE THEN 1 END) as processing_count,
                MIN(created_at) as oldest_item_time
            FROM {self._table_name}
            """
        )
        
        if result.rows:
            row = result.rows[0]
            return {
                "table_name": self._table_name,
                "total_items": row['total_count'],
                "pending_items": row['pending_count'],
                "processing_items": row['processing_count'],
                "oldest_item_time": row['oldest_item_time'],
                "is_empty": row['pending_count'] == 0,
                "is_full": self._maxsize > 0 and row['pending_count'] >= self._maxsize,
                "maxsize": self._maxsize
            }
        
        return {
            "table_name": self._table_name,
            "total_items": 0,
            "pending_items": 0,
            "processing_items": 0,
            "oldest_item_time": None,
            "is_empty": True,
            "is_full": False,
            "maxsize": self._maxsize
        }

    async def reset_processing_items(self):
        """重置所有正在处理的项目状态（用于错误恢复）"""
        await self._ensure_initialized()
        
        async with self._db.transaction() as conn:
            result = await conn.sql(
                f"UPDATE {self._table_name} SET processing = FALSE WHERE processing = TRUE"
            )
            return result.rows_affected
