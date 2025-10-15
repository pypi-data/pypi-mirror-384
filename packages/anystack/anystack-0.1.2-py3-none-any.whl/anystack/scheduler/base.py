"""
调度器基类定义
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Callable
from collections.abc import Sequence

from ..protocol.scheduler import Schedule, ScheduleQuery, TaskHandler


class BaseScheduler(ABC):
    """调度器基类，定义调度器的标准接口"""

    @abstractmethod
    async def ensure_schema(self) -> None:
        """确保后端存储结构存在"""
        ...

    @abstractmethod
    async def schedule(
        self,
        when: datetime | timedelta | str,
        callback: str,
        payload: Any | None = None,
        *,
        schedule_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Schedule:
        """创建新的调度任务并返回其描述"""
        ...

    @abstractmethod
    async def get(self, schedule_id: str) -> Schedule | None:
        """根据 ID 获取调度任务"""
        ...

    @abstractmethod
    async def list(self, query: ScheduleQuery | None = None) -> Sequence[Schedule]:
        """根据条件列出调度任务"""
        ...

    @abstractmethod
    async def cancel(self, schedule_id: str) -> bool:
        """取消调度任务，如果存在返回 True"""
        ...

    @abstractmethod
    async def due(
        self, *, now: datetime | None = None, limit: int | None = None
    ) -> Sequence[Schedule]:
        """返回在指定时间或之前应该运行的调度任务"""
        ...

    @abstractmethod
    async def mark_executed(
        self,
        schedule: Schedule,
        *,
        next_run: datetime | None = None,
    ) -> None:
        """标记调度任务已执行，并更新存储"""
        ...


class BaseWorker(ABC):
    """调度器工作者基类，定义调度器工作者的标准接口"""

    @abstractmethod
    async def start(self) -> None:
        """启动工作者"""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """停止工作者"""
        ...

    @abstractmethod
    def register_handler(self, callback_name: str, handler: TaskHandler) -> None:
        """注册任务处理器"""
        ...

    @abstractmethod
    def register_function(self, callback_name: str, func: Callable) -> None:
        """注册函数作为任务处理器"""
        ...