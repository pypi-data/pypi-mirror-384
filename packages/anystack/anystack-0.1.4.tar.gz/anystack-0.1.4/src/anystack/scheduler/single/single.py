from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Any, override
from dataclasses import dataclass, field

from croniter import croniter

from ...protocol.db import DB
from ...protocol.scheduler import (
    Schedule,
    SchedulePlan,
    ScheduleQuery,
    ScheduleType,
)
from ..base import BaseScheduler


def _get_db_dialect(db: DB) -> str:
    """检测数据库类型"""
    # 尝试通过 _engine 属性检测
    if hasattr(db, "_engine"):
        engine = db._engine
        if hasattr(engine, "dialect"):
            dialect_name = engine.dialect.name
            return dialect_name
    return "postgresql"  # 默认为 PostgreSQL


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return _ensure_aware(value)
    if isinstance(value, str):
        cleaned = value.replace("Z", "+00:00") if value.endswith("Z") else value
        return _ensure_aware(datetime.fromisoformat(cleaned))
    raise TypeError(f"Unsupported datetime value: {value!r}")


def _maybe_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


@dataclass
class Config:
    db: DB
    table_name: str = field(default="single_scheduler")
    dialect: str | None = field(default=None)  # 数据库方言：postgresql, sqlite 等


class SupabaseScheduler(BaseScheduler):
    """Scheduler that persists tasks in Supabase."""

    def __init__(self, config: Config) -> None:
        self._db = config.db
        self._table = config.table_name
        self._dialect = config.dialect or _get_db_dialect(config.db)

    @override
    async def ensure_schema(self) -> None:
        if self._dialect == "sqlite":
            # SQLite 语法
            await self._db.sql(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table} (
                    id TEXT PRIMARY KEY,
                    callback TEXT NOT NULL,
                    type TEXT NOT NULL CHECK (type IN ('scheduled', 'delayed', 'cron')),
                    scheduled_at TIMESTAMP NOT NULL,
                    delay_seconds INTEGER,
                    cron TEXT,
                    payload TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        else:
            # PostgreSQL 语法
            await self._db.sql(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table} (
                    id TEXT PRIMARY KEY,
                    callback TEXT NOT NULL,
                    type TEXT NOT NULL CHECK (type IN ('scheduled', 'delayed', 'cron')),
                    scheduled_at TIMESTAMPTZ NOT NULL,
                    delay_seconds INTEGER,
                    cron TEXT,
                    payload JSONB,
                    metadata JSONB,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        await self._db.sql(
            f"""
            CREATE INDEX IF NOT EXISTS {self._table}_scheduled_at_idx
            ON {self._table} (scheduled_at)
            """
        )

    @override
    async def schedule(
        self,
        when: SchedulePlan,
        callback: str,
        payload: Any | None = None,
        *,
        schedule_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Schedule:
        now = _utc_now()
        if isinstance(when, datetime):
            scheduled_at = _ensure_aware(when)
            schedule_type: ScheduleType = "scheduled"
            delay_seconds: int | None = None
            cron_expr: str | None = None
        elif isinstance(when, timedelta):
            delay_seconds = int(when.total_seconds())
            if delay_seconds < 0:
                raise ValueError("delay cannot be negative")
            scheduled_at = now + timedelta(seconds=delay_seconds)
            schedule_type = "delayed"
            cron_expr = None
        elif isinstance(when, str):
            schedule_type = "cron"
            cron_expr = when
            try:
                cron_iter = croniter(cron_expr, now)
                scheduled_at = datetime.fromtimestamp(cron_iter.get_next(), tz=timezone.utc)
            except (ValueError, KeyError) as exc:
                raise ValueError("Invalid cron expression") from exc
            delay_seconds = None
        else:
            raise TypeError("Unsupported schedule plan")

        schedule_id = schedule_id or uuid.uuid4().hex
        created_at = now
        updated_at = now

        params = {
            "id": schedule_id,
            "callback": callback,
            "type": schedule_type,
            "scheduled_at": scheduled_at if self._dialect == "postgresql" else scheduled_at.isoformat(),
            "delay_seconds": delay_seconds,
            "cron": cron_expr,
            "payload": json.dumps(payload) if payload is not None else None,
            "metadata": json.dumps(metadata) if metadata is not None else None,
            "created_at": created_at if self._dialect == "postgresql" else created_at.isoformat(),
            "updated_at": updated_at if self._dialect == "postgresql" else updated_at.isoformat(),
        }

        if self._dialect == "sqlite":
            sql = f"""
            INSERT INTO {self._table} (
                id, callback, type, scheduled_at, delay_seconds, cron, payload, metadata, created_at, updated_at
            ) VALUES (
                :id, :callback, :type, :scheduled_at, :delay_seconds, :cron,
                :payload, :metadata, :created_at, :updated_at
            )
            RETURNING *
            """
        else:
            sql = f"""
            INSERT INTO {self._table} (
                id, callback, type, scheduled_at, delay_seconds, cron, payload, metadata, created_at, updated_at
            ) VALUES (
                :id, :callback, :type, :scheduled_at, :delay_seconds, :cron,
                CAST(:payload AS jsonb), CAST(:metadata AS jsonb), :created_at, :updated_at
            )
            RETURNING *
            """
        result = await self._db.sql(sql, params)
        row = result.rows[0] if result.rows else None
        if not row:
            raise RuntimeError("Failed to persist schedule")
        return self._row_to_schedule(row)

    @override
    async def get(self, schedule_id: str) -> Schedule | None:
        sql = f"SELECT * FROM {self._table} WHERE id = :id LIMIT 1"
        result = await self._db.sql(sql, {"id": schedule_id})
        if not result.rows:
            return None
        return self._row_to_schedule(result.rows[0])

    @override
    async def list(self, query: ScheduleQuery | None = None) -> Sequence[Schedule]:
        clauses = []
        params: dict[str, Any] = {}
        if query:
            if schedule_id := query.get("id"):
                clauses.append("id = :id")
                params["id"] = schedule_id
            if schedule_type := query.get("type"):
                clauses.append("type = :type")
                params["type"] = schedule_type
            if starts_after := query.get("starts_after"):
                clauses.append("scheduled_at >= :starts_after")
                dt = _ensure_aware(starts_after)
                params["starts_after"] = dt if self._dialect == "postgresql" else dt.isoformat()
            if ends_before := query.get("ends_before"):
                clauses.append("scheduled_at <= :ends_before")
                dt = _ensure_aware(ends_before)
                params["ends_before"] = dt if self._dialect == "postgresql" else dt.isoformat()
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM {self._table} {where} ORDER BY scheduled_at ASC"
        result = await self._db.sql(sql, params)
        return [self._row_to_schedule(row) for row in result.rows]

    @override
    async def cancel(self, schedule_id: str) -> bool:
        sql = f"DELETE FROM {self._table} WHERE id = :id RETURNING id"
        result = await self._db.sql(sql, {"id": schedule_id})
        return bool(result.rows)

    @override
    async def due(
        self,
        *,
        now: datetime | None = None,
        limit: int | None = None,
    ) -> Sequence[Schedule]:
        current = _ensure_aware(now) if now else _utc_now()
        params: dict[str, Any] = {
            "now": current if self._dialect == "postgresql" else current.isoformat()
        }
        limit_clause = ""
        if limit is not None:
            limit_int = int(limit)
            if limit_int <= 0:
                return []
            limit_clause = f" LIMIT {limit_int}"
        sql = (
            f"SELECT * FROM {self._table} "
            "WHERE scheduled_at <= :now "
            "ORDER BY scheduled_at ASC"
            f"{limit_clause}"
        )
        result = await self._db.sql(sql, params)
        return [self._row_to_schedule(row) for row in result.rows]

    @override
    async def mark_executed(
        self,
        schedule: Schedule,
        *,
        next_run: datetime | None = None,
    ) -> None:
        schedule_type = schedule["type"]
        schedule_id = schedule["id"]
        if schedule_type == "cron":
            cron_expr = schedule.get("cron")
            if not cron_expr:
                raise ValueError("Cron schedule missing cron expression")
            if next_run:
                next_run_dt = _ensure_aware(next_run)
            else:
                cron_iter = croniter(
                    cron_expr, _ensure_aware(schedule["scheduled_at"])
                )
                next_run_dt = datetime.fromtimestamp(cron_iter.get_next(), tz=timezone.utc)
            updated_at = _utc_now()
            params = {
                "id": schedule_id,
                "scheduled_at": next_run_dt if self._dialect == "postgresql" else next_run_dt.isoformat(),
                "updated_at": updated_at if self._dialect == "postgresql" else updated_at.isoformat(),
            }
            sql = (
                f"UPDATE {self._table} "
                "SET scheduled_at = :scheduled_at, updated_at = :updated_at "
                "WHERE id = :id"
            )
            await self._db.sql(sql, params)
        else:
            await self._db.sql(
                f"DELETE FROM {self._table} WHERE id = :id",
                {"id": schedule_id},
            )

    def  _row_to_schedule(self, row: dict[str, Any]) -> Schedule:
        scheduled_at = _parse_datetime(row["scheduled_at"])
        created_at = _parse_datetime(row["created_at"])
        schedule: Schedule = {
            "id": row["id"],
            "callback": row["callback"],
            "type": row["type"],
            "scheduled_at": scheduled_at,
            "created_at": created_at,
        }
        if row.get("payload") is not None:
            schedule["payload"] = _maybe_json(row["payload"])
        if row.get("delay_seconds") is not None:
            schedule["delay_seconds"] = int(row["delay_seconds"])
        if row.get("cron") is not None:
            schedule["cron"] = row["cron"]
        if row.get("metadata") is not None:
            schedule["metadata"] = _maybe_json(row["metadata"])
        return schedule
