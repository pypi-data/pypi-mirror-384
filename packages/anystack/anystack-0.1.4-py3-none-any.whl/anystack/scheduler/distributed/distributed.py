"""
分布式调度器实现
支持多个 worker 实例并发处理任务
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Any, override

from ...protocol.db import DB
from ...protocol.scheduler import Schedule, ScheduleQuery
from ..base import BaseScheduler


@dataclass
class Config:
    """分布式调度器配置"""
    db: DB
    table_prefix: str = "distributed_"
    worker_heartbeat_interval: int = 30  # worker 心跳间隔（秒）
    worker_timeout: int = 120  # worker 超时时间（秒）
    task_lock_timeout: int = 300  # 任务锁定超时时间（秒）


class DistributedScheduler(BaseScheduler):
    """
    分布式调度器实现
    支持多个 worker 实例，使用数据库实现任务分发和锁定
    """

    def __init__(self, config: Config):
        self.db = config.db
        self.table_prefix = config.table_prefix
        self.schedules_table = f"{config.table_prefix}schedules"
        self.workers_table = f"{config.table_prefix}workers"
        self.task_locks_table = f"{config.table_prefix}task_locks"
        
        self.worker_heartbeat_interval = config.worker_heartbeat_interval
        self.worker_timeout = config.worker_timeout
        self.task_lock_timeout = config.task_lock_timeout
        
        self.logger = logging.getLogger(__name__)

    @override
    async def ensure_schema(self) -> None:
        """确保数据库表结构存在"""
        # 调度任务表
        create_schedules_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.schedules_table} (
            id TEXT PRIMARY KEY,
            callback TEXT NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('scheduled', 'delayed', 'cron')),
            scheduled_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            payload TEXT,
            delay_seconds INTEGER,
            cron TEXT,
            metadata TEXT,
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'cancelled')),
            next_run TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            last_error TEXT
        )
        """

        # Worker 注册表
        create_workers_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.workers_table} (
            id TEXT PRIMARY KEY,
            hostname TEXT NOT NULL,
            pid INTEGER NOT NULL,
            capabilities TEXT,  -- JSON 格式的能力列表
            max_concurrent_tasks INTEGER DEFAULT 10,
            current_tasks INTEGER DEFAULT 0,
            last_heartbeat TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'dead')),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        # 任务锁定表
        create_task_locks_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.task_locks_table} (
            schedule_id TEXT PRIMARY KEY,
            worker_id TEXT NOT NULL,
            locked_at TIMESTAMP NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'locked' CHECK (status IN ('locked', 'executing', 'completed')),
            FOREIGN KEY (schedule_id) REFERENCES {self.schedules_table}(id),
            FOREIGN KEY (worker_id) REFERENCES {self.workers_table}(id)
        )
        """

        # 创建索引
        create_indexes_sql = [
            # 调度任务索引
            f"CREATE INDEX IF NOT EXISTS idx_{self.schedules_table}_next_run ON {self.schedules_table} (next_run)",
            f"CREATE INDEX IF NOT EXISTS idx_{self.schedules_table}_status ON {self.schedules_table} (status)",
            f"CREATE INDEX IF NOT EXISTS idx_{self.schedules_table}_type ON {self.schedules_table} (type)",
            
            # Worker 索引
            f"CREATE INDEX IF NOT EXISTS idx_{self.workers_table}_status ON {self.workers_table} (status)",
            f"CREATE INDEX IF NOT EXISTS idx_{self.workers_table}_heartbeat ON {self.workers_table} (last_heartbeat)",
            
            # 任务锁定索引
            f"CREATE INDEX IF NOT EXISTS idx_{self.task_locks_table}_worker ON {self.task_locks_table} (worker_id)",
            f"CREATE INDEX IF NOT EXISTS idx_{self.task_locks_table}_expires ON {self.task_locks_table} (expires_at)",
        ]

        async with self.db.transaction() as conn:
            await conn.sql(create_schedules_table_sql)
            await conn.sql(create_workers_table_sql)
            await conn.sql(create_task_locks_table_sql)
            
            for index_sql in create_indexes_sql:
                await conn.sql(index_sql)

    @override
    async def schedule(
        self,
        when: datetime | timedelta | str,
        callback: str,
        payload: Any | None = None,
        *,
        schedule_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> Schedule:
        """创建新的调度任务"""
        if schedule_id is None:
            schedule_id = str(uuid.uuid4())

        # 解析调度时间和类型
        schedule_info = self._parse_schedule_plan(when)

        # 准备数据
        now = datetime.now(timezone.utc)
        schedule_data = {
            "id": schedule_id,
            "callback": callback,
            "type": schedule_info["type"],
            "scheduled_at": schedule_info["scheduled_at"].isoformat(),
            "created_at": now.isoformat(),
            "payload": json.dumps(payload) if payload is not None else None,
            "delay_seconds": schedule_info.get("delay_seconds"),
            "cron": schedule_info.get("cron"),
            "metadata": json.dumps(metadata) if metadata is not None else None,
            "status": "pending",
            "next_run": schedule_info["scheduled_at"].isoformat(),
            "max_retries": max_retries,
        }

        # 插入数据库
        insert_sql = f"""
        INSERT INTO {self.schedules_table} 
        (id, callback, type, scheduled_at, created_at, payload, delay_seconds, cron, metadata, status, next_run, max_retries)
        VALUES (:id, :callback, :type, :scheduled_at, :created_at, :payload, :delay_seconds, :cron, :metadata, :status, :next_run, :max_retries)
        """

        async with self.db.transaction() as conn:
            await conn.sql(insert_sql, schedule_data)

        return self._row_to_schedule({
            **schedule_data,
            "retry_count": 0,
        })

    @override
    async def get(self, schedule_id: str) -> Schedule | None:
        """根据 ID 获取调度任务"""
        select_sql = f"""
        SELECT * FROM {self.schedules_table} 
        WHERE id = :id AND status != 'cancelled'
        """

        result = await self.db.sql(select_sql, {"id": schedule_id})

        if not result.rows:
            return None

        return self._row_to_schedule(result.rows[0])

    @override
    async def list(self, query: ScheduleQuery | None = None) -> Sequence[Schedule]:
        """根据条件列出调度任务"""
        conditions = ["status != 'cancelled'"]
        params: dict[str, Any] = {}

        if query:
            if "id" in query:
                conditions.append("id = :id")
                params["id"] = query["id"]

            if "type" in query:
                conditions.append("type = :type")
                params["type"] = query["type"]

            if "starts_after" in query:
                conditions.append("scheduled_at >= :starts_after")
                params["starts_after"] = query["starts_after"].isoformat()

            if "ends_before" in query:
                conditions.append("scheduled_at <= :ends_before")
                params["ends_before"] = query["ends_before"].isoformat()

        where_clause = " AND ".join(conditions)
        select_sql = f"""
        SELECT * FROM {self.schedules_table} 
        WHERE {where_clause}
        ORDER BY scheduled_at ASC
        """

        result = await self.db.sql(select_sql, params)
        return [self._row_to_schedule(row) for row in result.rows]

    @override
    async def cancel(self, schedule_id: str) -> bool:
        """取消调度任务"""
        async with self.db.transaction() as conn:
            # 释放任务锁定
            await conn.sql(
                f"DELETE FROM {self.task_locks_table} WHERE schedule_id = :id",
                {"id": schedule_id}
            )
            
            # 标记任务为已取消
            result = await conn.sql(
                f"""
                UPDATE {self.schedules_table} 
                SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                WHERE id = :id AND status = 'pending'
                """,
                {"id": schedule_id}
            )
            
        return result.rows_affected > 0

    @override
    async def due(
        self, *, now: datetime | None = None, limit: int | None = None
    ) -> Sequence[Schedule]:
        """获取到期的调度任务（未被锁定的）"""
        if now is None:
            now = datetime.now(timezone.utc)

        params = {"now": now.isoformat()}
        limit_clause = f"LIMIT {limit}" if limit is not None else ""

        select_sql = f"""
        SELECT s.* FROM {self.schedules_table} s
        LEFT JOIN {self.task_locks_table} l ON s.id = l.schedule_id 
            AND l.expires_at > :now 
            AND l.status IN ('locked', 'executing')
        WHERE s.status = 'pending' 
        AND (s.next_run IS NULL OR s.next_run <= :now)
        AND l.schedule_id IS NULL  -- 未被锁定的任务
        ORDER BY s.scheduled_at ASC
        {limit_clause}
        """

        result = await self.db.sql(select_sql, params)
        return [self._row_to_schedule(row) for row in result.rows]

    async def claim_tasks(
        self, 
        worker_id: str, 
        limit: int = 10,
        now: datetime | None = None
    ) -> Sequence[Schedule]:
        """
        Worker 尝试认领任务
        使用数据库锁定机制确保任务不会被多个 worker 同时执行
        """
        if now is None:
            now = datetime.now(timezone.utc)
        
        expires_at = now + timedelta(seconds=self.task_lock_timeout)
        
        claimed_tasks = []
        
        async with self.db.transaction() as conn:
            # 获取可用任务
            available_tasks = await self.due(now=now, limit=limit)
            
            for schedule in available_tasks:
                if len(claimed_tasks) >= limit:
                    break
                    
                schedule_id = schedule["id"]
                
                try:
                    # 尝试锁定任务
                    await conn.sql(
                        f"""
                        INSERT INTO {self.task_locks_table} 
                        (schedule_id, worker_id, locked_at, expires_at, status)
                        VALUES (:schedule_id, :worker_id, :locked_at, :expires_at, 'locked')
                        """,
                        {
                            "schedule_id": schedule_id,
                            "worker_id": worker_id,
                            "locked_at": now.isoformat(),
                            "expires_at": expires_at.isoformat(),
                        }
                    )
                    
                    claimed_tasks.append(schedule)
                    self.logger.info(f"Worker {worker_id} claimed task {schedule_id}")
                    
                except Exception as e:
                    # 任务已被其他 worker 锁定，跳过
                    self.logger.debug(f"Failed to claim task {schedule_id}: {e}")
                    continue
        
        return claimed_tasks

    @override
    async def mark_executed(
        self,
        schedule: Schedule,
        *,
        next_run: datetime | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> None:
        """标记任务已执行"""
        schedule_id = schedule["id"]
        schedule_type = schedule["type"]
        
        async with self.db.transaction() as conn:
            if success:
                # 成功执行
                if schedule_type == "cron" and next_run is None:
                    # 自动计算 cron 的下次执行时间
                    next_run = self._calculate_next_cron_run(schedule)
                
                if next_run is not None:
                    # 更新下次运行时间
                    await conn.sql(
                        f"""
                        UPDATE {self.schedules_table} 
                        SET next_run = :next_run, retry_count = 0, last_error = NULL, updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                        """,
                        {
                            "id": schedule_id,
                            "next_run": next_run.isoformat(),
                        }
                    )
                else:
                    # 标记为已完成
                    await conn.sql(
                        f"""
                        UPDATE {self.schedules_table} 
                        SET status = 'completed', next_run = NULL, updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                        """,
                        {"id": schedule_id}
                    )
            else:
                # 执行失败，检查重试
                retry_count = schedule.get("retry_count", 0) + 1
                max_retries = schedule.get("max_retries", 3)
                
                if retry_count < max_retries:
                    # 重试：延迟一段时间后重新调度
                    retry_delay = min(60 * (2 ** retry_count), 3600)  # 指数退避，最大1小时
                    next_retry = datetime.now(timezone.utc) + timedelta(seconds=retry_delay)
                    
                    await conn.sql(
                        f"""
                        UPDATE {self.schedules_table} 
                        SET next_run = :next_run, retry_count = :retry_count, last_error = :error, updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                        """,
                        {
                            "id": schedule_id,
                            "next_run": next_retry.isoformat(),
                            "retry_count": retry_count,
                            "error": error_message,
                        }
                    )
                    self.logger.warning(f"Task {schedule_id} failed, scheduling retry {retry_count}/{max_retries}")
                else:
                    # 超过最大重试次数，标记为失败
                    await conn.sql(
                        f"""
                        UPDATE {self.schedules_table} 
                        SET status = 'completed', next_run = NULL, retry_count = :retry_count, last_error = :error, updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                        """,
                        {
                            "id": schedule_id,
                            "retry_count": retry_count,
                            "error": error_message,
                        }
                    )
                    self.logger.error(f"Task {schedule_id} failed after {max_retries} retries")
            
            # 释放任务锁定
            await conn.sql(
                f"DELETE FROM {self.task_locks_table} WHERE schedule_id = :id",
                {"id": schedule_id}
            )

    async def register_worker(
        self,
        worker_id: str,
        hostname: str,
        pid: int,
        capabilities: list[str] | None = None,
        max_concurrent_tasks: int = 10,
    ) -> None:
        """注册 worker"""
        now = datetime.now(timezone.utc)
        
        worker_data = {
            "id": worker_id,
            "hostname": hostname,
            "pid": pid,
            "capabilities": json.dumps(capabilities or []),
            "max_concurrent_tasks": max_concurrent_tasks,
            "last_heartbeat": now.isoformat(),
            "status": "active",
            "created_at": now.isoformat(),
        }
        
        # 使用 UPSERT 语法（如果支持）或先删除再插入
        async with self.db.transaction() as conn:
            await conn.sql(
                f"DELETE FROM {self.workers_table} WHERE id = :id",
                {"id": worker_id}
            )
            
            await conn.sql(
                f"""
                INSERT INTO {self.workers_table} 
                (id, hostname, pid, capabilities, max_concurrent_tasks, last_heartbeat, status, created_at)
                VALUES (:id, :hostname, :pid, :capabilities, :max_concurrent_tasks, :last_heartbeat, :status, :created_at)
                """,
                worker_data
            )
        
        self.logger.info(f"Registered worker {worker_id} on {hostname}:{pid}")

    async def worker_heartbeat(self, worker_id: str, current_tasks: int = 0) -> None:
        """Worker 心跳更新"""
        await self.db.sql(
            f"""
            UPDATE {self.workers_table} 
            SET last_heartbeat = CURRENT_TIMESTAMP, current_tasks = :current_tasks, status = 'active'
            WHERE id = :id
            """,
            {"id": worker_id, "current_tasks": current_tasks}
        )

    async def cleanup_dead_workers(self) -> int:
        """清理死掉的 worker 和它们的任务锁定"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=self.worker_timeout)
        
        async with self.db.transaction() as conn:
            # 查找死掉的 worker
            dead_workers_result = await conn.sql(
                f"""
                SELECT id FROM {self.workers_table}
                WHERE last_heartbeat < :cutoff_time AND status = 'active'
                """,
                {"cutoff_time": cutoff_time.isoformat()}
            )
            
            dead_worker_count = len(dead_workers_result.rows)
            
            if dead_worker_count > 0:
                dead_worker_ids = [row["id"] for row in dead_workers_result.rows]
                
                # 标记 worker 为死亡状态
                await conn.sql(
                    f"""
                    UPDATE {self.workers_table} 
                    SET status = 'dead' 
                    WHERE last_heartbeat < :cutoff_time AND status = 'active'
                    """,
                    {"cutoff_time": cutoff_time.isoformat()}
                )
                
                # 释放它们的任务锁定
                for worker_id in dead_worker_ids:
                    await conn.sql(
                        f"DELETE FROM {self.task_locks_table} WHERE worker_id = :worker_id",
                        {"worker_id": worker_id}
                    )
                
                self.logger.warning(f"Cleaned up {dead_worker_count} dead workers and their task locks")
        
        return dead_worker_count

    async def cleanup_expired_locks(self) -> int:
        """清理过期的任务锁定"""
        now = datetime.now(timezone.utc)
        
        result = await self.db.sql(
            f"DELETE FROM {self.task_locks_table} WHERE expires_at < :now",
            {"now": now.isoformat()}
        )
        
        if result.rows_affected > 0:
            self.logger.info(f"Cleaned up {result.rows_affected} expired task locks")
        
        return result.rows_affected

    def _parse_schedule_plan(self, when: datetime | timedelta | str) -> dict[str, Any]:
        """解析调度计划"""
        if isinstance(when, datetime):
            return {
                "type": "scheduled",
                "scheduled_at": when,
            }
        elif isinstance(when, timedelta):
            scheduled_at = datetime.now(timezone.utc) + when
            return {
                "type": "delayed",
                "scheduled_at": scheduled_at,
                "delay_seconds": int(when.total_seconds()),
            }
        elif isinstance(when, str):
            # 假设是 cron 表达式
            try:
                from croniter import croniter
                cron = croniter(when, datetime.now(timezone.utc))
                next_run = cron.get_next(datetime)
                return {
                    "type": "cron",
                    "scheduled_at": next_run,
                    "cron": when,
                }
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {when}") from e
        else:
            raise ValueError(f"Unsupported schedule plan type: {type(when)}")

    def _calculate_next_cron_run(self, schedule: Schedule) -> datetime | None:
        """计算 cron 任务的下次运行时间"""
        cron_expr = schedule.get("cron")
        if not cron_expr:
            return None
        
        try:
            from croniter import croniter
            cron = croniter(cron_expr, datetime.now(timezone.utc))
            return cron.get_next(datetime)
        except Exception:
            return None

    def _row_to_schedule(self, row: dict[str, Any]) -> Schedule:
        """将数据库行转换为 Schedule 对象"""
        schedule: Schedule = {
            "id": row["id"],
            "callback": row["callback"],
            "type": row["type"],
            "scheduled_at": self._parse_datetime(row["scheduled_at"]),
            "created_at": self._parse_datetime(row["created_at"]),
        }

        # 可选字段
        if row.get("payload"):
            schedule["payload"] = json.loads(row["payload"])

        if row.get("delay_seconds") is not None:
            schedule["delay_seconds"] = row["delay_seconds"]

        if row.get("cron"):
            schedule["cron"] = row["cron"]

        if row.get("metadata"):
            schedule["metadata"] = json.loads(row["metadata"])
        
        # 分布式相关字段
        if "retry_count" in row:
            schedule["retry_count"] = row["retry_count"]
        
        if "max_retries" in row:
            schedule["max_retries"] = row["max_retries"]
        
        if row.get("last_error"):
            schedule["last_error"] = row["last_error"]

        return schedule

    def _parse_datetime(self, dt_str: str) -> datetime:
        """解析日期时间字符串"""
        if isinstance(dt_str, datetime):
            return dt_str

        try:
            # ISO 格式
            if "T" in dt_str:
                return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            else:
                # 假设是 YYYY-MM-DD HH:MM:SS 格式
                return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                return datetime.fromisoformat(dt_str)
            except ValueError:
                raise ValueError(f"Unable to parse datetime: {dt_str}")
