import asyncio
import logging
import os
import socket
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from .distributed import DistributedScheduler
from ...protocol.scheduler import TaskHandler


class DistributedWorker:
    """
    分布式调度器 Worker
    连接到分布式调度器，竞争获取和执行任务
    """

    def __init__(
        self,
        scheduler: DistributedScheduler,
        worker_id: str | None = None,
        max_concurrent_tasks: int = 10,
        poll_interval: float = 5.0,
        heartbeat_interval: float = 30.0,
        capabilities: list[str] | None = None,
    ):
        """
        初始化分布式 Worker

        :param scheduler: 分布式调度器实例
        :param worker_id: Worker ID，如果不指定则自动生成
        :param max_concurrent_tasks: 最大并发任务数
        :param poll_interval: 任务轮询间隔（秒）
        :param heartbeat_interval: 心跳间隔（秒）
        :param capabilities: Worker 能力列表（用于任务路由）
        """
        self.scheduler = scheduler
        self.worker_id = worker_id or self._generate_worker_id()
        self.max_concurrent_tasks = max_concurrent_tasks
        self.poll_interval = poll_interval
        self.heartbeat_interval = heartbeat_interval
        self.capabilities = capabilities or []

        self.hostname = socket.gethostname()
        self.pid = os.getpid()

        self.logger = logging.getLogger(f"{__name__}.{self.worker_id}")

        # 任务处理器注册表
        self.handlers: dict[str, TaskHandler] = {}

        # 运行状态
        self.running = False
        self.running_tasks: set[asyncio.Task] = set()
        self._heartbeat_task: asyncio.Task | None = None

    def _generate_worker_id(self) -> str:
        """生成 Worker ID"""
        hostname = socket.gethostname()
        pid = os.getpid()
        unique_id = str(uuid.uuid4())[:8]
        return f"{hostname}-{pid}-{unique_id}"

    def register_handler(self, callback_name: str, handler: TaskHandler) -> None:
        """注册任务处理器"""
        self.handlers[callback_name] = handler
        self.logger.info(f"Registered handler for callback: {callback_name}")

    def register_function(self, callback_name: str, func: Callable) -> None:
        """注册函数作为任务处理器"""

        async def handler(payload: Any) -> Any:
            if asyncio.iscoroutinefunction(func):
                return await func(payload)
            else:
                return func(payload)

        self.register_handler(callback_name, handler)

    async def start(self) -> None:
        """启动 Worker"""
        self.running = True
        self.logger.info(f"Starting distributed worker {self.worker_id}")

        try:
            # 注册 Worker
            await self.scheduler.register_worker(
                worker_id=self.worker_id,
                hostname=self.hostname,
                pid=self.pid,
                capabilities=self.capabilities,
                max_concurrent_tasks=self.max_concurrent_tasks,
            )

            # 启动心跳任务
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            # 主工作循环
            while self.running:
                try:
                    await self._process_tasks()
                    await self._cleanup_completed_tasks()
                    await asyncio.sleep(self.poll_interval)
                except Exception as e:
                    self.logger.error(f"Error in worker loop: {e}", exc_info=True)
                    await asyncio.sleep(self.poll_interval)

        except Exception as e:
            self.logger.error(f"Worker error: {e}", exc_info=True)
        finally:
            await self._shutdown()

    async def stop(self) -> None:
        """停止 Worker"""
        self.logger.info(f"Stopping distributed worker {self.worker_id}")
        self.running = False

    async def _shutdown(self) -> None:
        """清理资源"""
        # 停止心跳
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # 等待运行中的任务完成
        await self._wait_for_running_tasks()

        self.logger.info(f"Distributed worker {self.worker_id} stopped")

    async def _heartbeat_loop(self) -> None:
        """心跳循环"""
        while self.running:
            try:
                current_tasks = len(self.running_tasks)
                await self.scheduler.worker_heartbeat(
                    worker_id=self.worker_id, current_tasks=current_tasks
                )
                self.logger.debug(f"Heartbeat sent, current tasks: {current_tasks}")

                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}", exc_info=True)
                await asyncio.sleep(self.heartbeat_interval)

    async def _process_tasks(self) -> None:
        """处理任务"""
        try:
            # 检查可用任务槽位
            available_slots = self.max_concurrent_tasks - len(self.running_tasks)
            if available_slots <= 0:
                return

            # 尝试认领任务
            claimed_tasks = await self.scheduler.claim_tasks(
                worker_id=self.worker_id, limit=available_slots
            )

            if not claimed_tasks:
                return

            self.logger.info(f"Claimed {len(claimed_tasks)} tasks")

            # 为每个认领的任务创建执行协程
            for schedule in claimed_tasks:
                if not self.running:
                    break

                # 检查是否有对应的处理器
                callback = schedule["callback"]
                if callback not in self.handlers:
                    self.logger.error(f"No handler for callback: {callback}")
                    # 标记任务失败
                    await self.scheduler.mark_executed(
                        schedule,
                        success=False,
                        error_message=f"No handler registered for callback: {callback}",
                    )
                    continue

                # 创建任务执行协程
                task = asyncio.create_task(self._execute_schedule(schedule))
                self.running_tasks.add(task)

                # 任务完成时自动清理
                task.add_done_callback(self.running_tasks.discard)

        except Exception as e:
            self.logger.error(f"Error processing tasks: {e}", exc_info=True)

    async def _execute_schedule(self, schedule) -> None:
        """执行单个调度任务"""
        schedule_id = schedule["id"]
        callback = schedule["callback"]
        payload = schedule.get("payload")

        self.logger.info(f"Executing schedule {schedule_id}: {callback}")

        start_time = datetime.now(timezone.utc)
        success = True
        error_message = None

        try:
            handler = self.handlers[callback]

            # 执行任务
            result = await handler(**payload)
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            self.logger.info(
                f"Schedule {schedule_id} completed successfully in {execution_time:.2f}s"
            )

        except Exception as e:
            success = False
            error_message = str(e)
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            self.logger.error(
                f"Schedule {schedule_id} failed after {execution_time:.2f}s: {e}",
                exc_info=True,
            )

        # 标记任务已执行
        try:
            await self.scheduler.mark_executed(
                schedule, success=success, error_message=error_message
            )
        except Exception as e:
            self.logger.error(f"Failed to mark schedule {schedule_id} as executed: {e}")

    async def _cleanup_completed_tasks(self) -> None:
        """清理已完成的任务"""
        completed_tasks = [task for task in self.running_tasks if task.done()]
        for task in completed_tasks:
            self.running_tasks.discard(task)

            # 检查任务是否有异常
            if task.exception() is not None:
                self.logger.error(
                    f"Task completed with exception: {task.exception()}",
                    exc_info=task.exception(),
                )

    async def _wait_for_running_tasks(self) -> None:
        """等待所有运行中的任务完成"""
        if self.running_tasks:
            self.logger.info(
                f"Waiting for {len(self.running_tasks)} running tasks to complete"
            )
            await asyncio.gather(*self.running_tasks, return_exceptions=True)
