"""Scheduler protocols inspired by Cloudflare agents."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any, Callable, Literal, Protocol, TypedDict, runtime_checkable

ScheduleType = Literal["scheduled", "delayed", "cron"]

SchedulePlan = datetime | timedelta | str
"""Represents how a schedule should be planned.

- ``datetime`` schedules for an absolute moment
- ``timedelta`` schedules relative to now
- ``str`` is treated as a cron expression
"""


class ScheduleBase(TypedDict):
    id: str
    callback: str
    type: ScheduleType
    scheduled_at: datetime
    created_at: datetime


class Schedule(ScheduleBase, total=False):
    payload: Any
    delay_seconds: int
    cron: str
    metadata: dict[str, Any]


class ScheduleQuery(TypedDict, total=False):
    id: str
    type: ScheduleType
    starts_after: datetime
    ends_before: datetime


class TaskHandler(Protocol):

    async def __call__(self, payload: Any) -> Any:
        ...


@runtime_checkable
class Scheduler(Protocol):
    """Abstract scheduler contract bridging storage and execution."""

    async def ensure_schema(self) -> None:
        """Ensure backing storage exists."""

    async def schedule(
        self,
        when: datetime | timedelta | str,
        callback: str,
        payload: Any | None = None,
        *,
        schedule_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Schedule:
        """Persist a new schedule and return its description."""
        ...

    async def get(self, schedule_id: str) -> Schedule | None:
        """Fetch a schedule by id."""
        ...

    async def list(self, query: ScheduleQuery | None = None) -> Sequence[Schedule]:
        """Return schedules matching optional criteria."""
        ...

    async def cancel(self, schedule_id: str) -> bool:
        """Remove schedule by id, returning ``True`` if it existed."""
        ...

    async def due(
        self, *, now: datetime | None = None, limit: int | None = None
    ) -> Sequence[Schedule]:
        """Return schedules that should run at or before ``now``."""
        ...

    async def mark_executed(
        self,
        schedule: Schedule,
        *,
        next_run: datetime | None = None,
    ) -> None:
        """Update storage after a schedule has run."""
        ...


@runtime_checkable
class Worker(Protocol):
    """Abstract worker contract for executing schedules."""

    async def start(self) -> None:
        """Start the worker."""
        ...

    async def stop(self) -> None:
        """Stop the worker."""
        ...

    async def register_handler(self, callback_name: str, handler: TaskHandler) -> None:
        """Register a handler for a callback."""
        ...

    async def register_function(self, callback_name: str, func: Callable) -> None:
        """Register a function as a handler for a callback."""
        ...
