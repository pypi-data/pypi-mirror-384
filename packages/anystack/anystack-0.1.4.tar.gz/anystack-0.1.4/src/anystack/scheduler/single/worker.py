"""
调度器工作者实现
负责执行到期的调度任务
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, override

from ...protocol.scheduler import TaskHandler
from ..base import BaseWorker

class SchedulerWorker(BaseWorker):
    """
    调度器工作者
    轮询调度器获取到期任务并执行
    """

    def __init__(
        self,
        scheduler,  # Scheduler 协议实例
        poll_interval: float = 1.0,
        max_concurrent_tasks: int = 10,
        worker_id: str | None = None,
    ):
        """
        初始化工作者

        :param scheduler: 调度器实例
        :param poll_interval: 轮询间隔（秒）
        :param max_concurrent_tasks: 最大并发任务数
        :param worker_id: 工作者 ID
        """
        self.scheduler = scheduler
        self.poll_interval = poll_interval
        self.max_concurrent_tasks = max_concurrent_tasks
        self.worker_id = worker_id or f"worker-{id(self)}"
        
        self.logger = logging.getLogger(f"{__name__}.{self.worker_id}")
        
        # 任务处理器注册表
        self.handlers: dict[str, TaskHandler] = {}
        
        # 运行状态
        self.running = False
        self.running_tasks: set[asyncio.Task] = set()

    @override
    def register_handler(self, callback_name: str, handler: TaskHandler) -> None:
        """注册任务处理器"""
        self.handlers[callback_name] = handler
        self.logger.info(f"Registered handler for callback: {callback_name}")

    @override
    def register_function(self, callback_name: str, func: Callable) -> None:
        """注册函数作为任务处理器"""
        async def handler(payload: Any) -> Any:
            if asyncio.iscoroutinefunction(func):
                return await func(payload)
            else:
                return func(payload)
        
        self.register_handler(callback_name, handler)

    async def start(self) -> None:
        """启动工作者"""
        self.running = True
        self.logger.info(f"Starting scheduler worker {self.worker_id}")
        
        try:
            while self.running:
                await self._process_due_tasks()
                await self._cleanup_completed_tasks()
                await asyncio.sleep(self.poll_interval)
        except Exception as e:
            self.logger.error(f"Worker error: {e}", exc_info=True)
        finally:
            await self._wait_for_running_tasks()
            self.logger.info(f"Scheduler worker {self.worker_id} stopped")

    async def stop(self) -> None:
        """停止工作者"""
        self.logger.info(f"Stopping scheduler worker {self.worker_id}")
        self.running = False

    async def _process_due_tasks(self) -> None:
        """处理到期的任务"""
        try:
            # 检查并发任务数限制
            available_slots = self.max_concurrent_tasks - len(self.running_tasks)
            if available_slots <= 0:
                return

            # 获取到期的任务
            due_schedules = await self.scheduler.due(limit=available_slots)
            
            for schedule in due_schedules:
                if not self.running:
                    break
                
                # 创建任务执行协程
                task = asyncio.create_task(self._execute_schedule(schedule))
                self.running_tasks.add(task)
                
                # 任务完成时自动清理
                task.add_done_callback(self.running_tasks.discard)
                
        except Exception as e:
            self.logger.error(f"Error processing due tasks: {e}", exc_info=True)

    async def _execute_schedule(self, schedule) -> None:
        """执行单个调度任务"""
        schedule_id = schedule["id"]
        callback = schedule["callback"]
        payload = schedule.get("payload")
        
        self.logger.info(f"Executing schedule {schedule_id}: {callback}")
        
        try:
            # 检查处理器是否存在
            if callback not in self.handlers:
                raise ValueError(f"No handler registered for callback: {callback}")
            
            handler = self.handlers[callback]
            
            # 执行任务
            start_time = datetime.now(timezone.utc)
            result = await handler(**payload)
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            self.logger.info(
                f"Schedule {schedule_id} completed successfully in {execution_time:.2f}s"
            )
            
            # 计算下次运行时间（对于 cron 任务）
            next_run = None
            if schedule["type"] == "cron":
                # 让调度器自己计算下次运行时间
                pass
            
            # 标记任务已执行
            await self.scheduler.mark_executed(schedule, next_run=next_run)
            
        except Exception as e:
            self.logger.error(
                f"Schedule {schedule_id} failed: {e}", 
                exc_info=True
            )
            
            # 对于失败的任务，也要标记为已执行（避免重复执行）
            # 在实际应用中，可能需要更复杂的重试逻辑
            await self.scheduler.mark_executed(schedule)

    async def _cleanup_completed_tasks(self) -> None:
        """清理已完成的任务"""
        # 移除已完成的任务
        completed_tasks = [task for task in self.running_tasks if task.done()]
        for task in completed_tasks:
            self.running_tasks.discard(task)
            
            # 检查任务是否有异常
            if task.exception() is not None:
                self.logger.error(
                    f"Task completed with exception: {task.exception()}", 
                    exc_info=task.exception()
                )

    async def _wait_for_running_tasks(self) -> None:
        """等待所有运行中的任务完成"""
        if self.running_tasks:
            self.logger.info(f"Waiting for {len(self.running_tasks)} running tasks to complete")
            await asyncio.gather(*self.running_tasks, return_exceptions=True)


