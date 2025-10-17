import asyncio
import logging

from .distributed import DistributedScheduler


class SchedulerService:
    """
    调度服务
    独立运行的调度器服务，负责管理调度任务和清理工作
    """

    def __init__(
        self,
        scheduler: DistributedScheduler,
        cleanup_interval: float = 300.0,  # 5分钟
    ):
        """
        初始化调度服务

        :param scheduler: 分布式调度器实例
        :param cleanup_interval: 清理间隔（秒）
        """
        self.scheduler = scheduler
        self.cleanup_interval = cleanup_interval
        self.logger = logging.getLogger(__name__)

        self.running = False
        self._cleanup_task: asyncio.Task | None = None

    async def start(self) -> None:
        """启动调度服务"""
        self.running = True
        self.logger.info("Starting scheduler service")

        try:
            # 确保数据库模式存在
            await self.scheduler.ensure_schema()

            # 启动清理任务
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            # 服务主循环（可以添加其他管理任务）
            while self.running:
                await asyncio.sleep(1.0)

        except Exception as e:
            self.logger.error(f"Scheduler service error: {e}", exc_info=True)
        finally:
            await self._shutdown()

    async def stop(self) -> None:
        """停止调度服务"""
        self.logger.info("Stopping scheduler service")
        self.running = False

    async def _shutdown(self) -> None:
        """清理资源"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Scheduler service stopped")

    async def _cleanup_loop(self) -> None:
        """清理循环"""
        while self.running:
            try:
                # 清理死掉的 worker
                dead_workers = await self.scheduler.cleanup_dead_workers()
                if dead_workers > 0:
                    self.logger.info(f"Cleaned up {dead_workers} dead workers")

                # 清理过期的任务锁定
                expired_locks = await self.scheduler.cleanup_expired_locks()
                if expired_locks > 0:
                    self.logger.info(f"Cleaned up {expired_locks} expired locks")

                await asyncio.sleep(self.cleanup_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}", exc_info=True)
                await asyncio.sleep(self.cleanup_interval)
