"""
基于 Supabase SDK 的 Realtime 协议实现
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, TypeVar, override

from .base import BaseRealtime, BaseChannel

from supabase import AsyncClient
from realtime import AsyncRealtimeChannel


T = TypeVar("T", bound=dict[str, Any])


class SupabaseChannel(BaseChannel[T]):
    """Supabase 实时频道实现"""

    def __init__(
        self, realtime: "SupabaseRealtime[T]", name: str, opts: dict[str, Any]
    ):
        self.realtime: "SupabaseRealtime[T]" = realtime
        self.name: str = name
        self.opts: dict[str, Any] = opts
        self.subscribed: bool = False
        self._supabase_channel: AsyncRealtimeChannel | None = (
            None  # Supabase AsyncRealtimeChannel 类型
        )
        self._event_handlers: dict[str, list[Callable[[T], Any]]] = {}

    @override
    async def send(self, type: str, event: str, payload: dict[str, Any]) -> None:
        """发送消息到频道"""
        if type == "broadcast":
            # 直接广播消息
            await self._ensure_channel()
            await self._send_broadcast(event, payload)
        elif type == "db_changes":
            # 向数据库插入数据
            await self._send_db_change(event, payload)
        elif type == "presence":
            # 更新在线状态
            await self._ensure_channel()
            await self._send_presence(payload)
        else:
            raise ValueError(f"Unsupported message type: {type}")

    @override
    async def on(self, type: str, event: str, callback: Callable[[T], Any]) -> None:
        """监听频道事件"""
        # 添加本地事件处理器
        key = f"{type}:{event}"
        if key not in self._event_handlers:
            self._event_handlers[key] = []
        self._event_handlers[key].append(callback)

        # 如果已经订阅了频道，立即设置监听
        if self.subscribed:
            await self._setup_event_listener(type, event, callback)

    @override
    async def subscribe(self):
        """订阅频道"""
        if self.subscribed:
            return

        await self._ensure_channel()

        # 设置所有已注册的事件监听器
        for key, handlers in self._event_handlers.items():
            type_, event = key.split(":", 1)
            for handler in handlers:
                await self._setup_event_listener(type_, event, handler)

        # 订阅频道
        if self._supabase_channel:
            _ = await self._supabase_channel.subscribe()
        self.subscribed = True

    @override
    async def unsubscribe(self):
        """取消订阅频道"""
        if not self.subscribed:
            return

        if self._supabase_channel:
            _ = await self._supabase_channel.unsubscribe()

        self.subscribed = False

    @override
    async def close(self) -> None:
        """关闭频道"""
        await self.unsubscribe()
        self._event_handlers.clear()
        self._supabase_channel = None

    async def _ensure_channel(self):
        """确保 Supabase 频道已创建"""
        if self._supabase_channel is None:
            self._supabase_channel = self.realtime.config.client.channel(self.name)

    async def _setup_event_listener(self, type: str, event: str, callback: Callable):
        """设置事件监听器"""
        await self._ensure_channel()

        if type == "broadcast":
            # 订阅广播消息
            if self._supabase_channel:
                # _ = self._supabase_channel.on("broadcast", {"event": event}, self._wrap_callback(callback))
                _ =  self._supabase_channel.on_broadcast(
                    event, self._wrap_callback(callback)
                )
        elif type == "db_changes":
            # 订阅数据库变更
            if self._supabase_channel:
                await self._subscribe_db_changes(event, callback)
        elif type == "presence":
            # 订阅在线状态变更
            if self._supabase_channel:
                _ = self._supabase_channel.on_presence_sync(
                    self._wrap_callback(callback)
                )
                _ = self._supabase_channel.on_presence_join(
                    self._wrap_callback(callback)
                )
                _ = self._supabase_channel.on_presence_leave(
                    self._wrap_callback(callback)
                )
        else:
            raise ValueError(f"Unsupported subscription type: {type}")

    async def _send_broadcast(self, event: str, payload: dict[str, Any]):
        """发送广播消息"""
        try:
            if self._supabase_channel:
                _ = await self._supabase_channel.send_broadcast(event, payload)
        except Exception as e:
            raise RuntimeError(f"Failed to send broadcast: {e}")

    async def _send_db_change(self, event: str, payload: dict[str, Any]):
        """向数据库发送变更（插入数据）"""
        if not event.startswith("table:"):
            raise ValueError("Database change event must start with 'table:'")

        table_name = event.split(":", 1)[1]

        try:
            result = (
                await self.realtime.config.client.table(table_name)
                .insert(payload)
                .execute()
            )
            if not result.data:
                raise RuntimeError("Failed to insert data")
        except Exception as e:
            raise RuntimeError(f"Failed to send database change: {e}")

    async def _send_presence(self, payload: dict[str, Any]):
        """发送在线状态更新"""
        try:
            if self._supabase_channel:
                _ = await self._supabase_channel.track(payload)
        except Exception as e:
            raise RuntimeError(f"Failed to send presence: {e}")

    async def _subscribe_db_changes(self, event: str, callback: Callable):
        """订阅数据库变更"""
        if not event.startswith("table:"):
            raise ValueError("Database change event must start with 'table:'")

        parts = event.split(":")
        table_name = parts[1]

        # 支持不同类型的数据库事件
        events = ["INSERT", "UPDATE", "DELETE"]

        for db_event in events:
            if self._supabase_channel:
                _ =  self._supabase_channel.on_postgres_changes(
                    db_event,
                    self._wrap_db_callback(callback, db_event.lower()),
                    table=table_name,
                    schema="public",
                )

    def _wrap_callback(self, callback: Callable):
        """包装回调函数以适配 Supabase 的事件格式"""

        def wrapper(payload):
            try:
                # 将 Supabase 的 payload 格式转换为我们的标准格式
                if hasattr(payload, "payload"):
                    data = payload.payload
                else:
                    data = payload

                # 如果是异步回调，需要在事件循环中运行
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(data))
                else:
                    callback(data)
            except Exception as e:
                print(f"Callback error: {e}")

        return wrapper

    def _wrap_db_callback(self, callback: Callable, event_type: str):
        """包装数据库变更回调函数"""

        def wrapper(payload):
            try:
                # Supabase 数据库变更的 payload 格式
                data = {
                    "event_type": event_type,
                    "table": payload.get("table"),
                    "schema": payload.get("schema"),
                    "old": payload.get("old"),
                    "new": payload.get("new"),
                    "commit_timestamp": payload.get("commit_timestamp"),
                }

                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(data))
                else:
                    callback(data)
            except Exception as e:
                print(f"Database callback error: {e}")

        return wrapper


@dataclass
class Config:
    client: AsyncClient


class SupabaseRealtime(BaseRealtime[T]):
    """基于 Supabase 的 Realtime 实现

    注意：这个实现需要安装 supabase 客户端库
    pip install supabase
    """

    def __init__(self, config: Config):
        self.config: Config = config
        self._channels: dict[str, SupabaseChannel[T]] = {}

    # BaseRealtime 接口实现
    @override
    async def channel(self, name: str, opts: dict[str, Any]) -> BaseChannel[T]:
        """创建或获取频道"""
        if name not in self._channels:
            self._channels[name] = SupabaseChannel(self, name, opts)
        return self._channels[name]

    @override
    async def get_channels(self) -> list[BaseChannel[T]]:
        """获取所有频道"""
        return list(self._channels.values())

    @override
    async def remove_channel(self, channel: BaseChannel[T]) -> None:
        """移除指定频道"""
        if isinstance(channel, SupabaseChannel) and channel.name in self._channels:
            await channel.close()
            del self._channels[channel.name]

    @override
    async def remove_all_channels(self) -> None:
        """移除所有频道"""
        for channel in list(self._channels.values()):
            await channel.close()
        self._channels.clear()

    # 扩展方法
    async def get_presence_state(self, channel_name: str) -> dict[str, Any]:
        """获取频道的在线状态"""
        channel = self._channels.get(channel_name)
        if channel and channel._supabase_channel:
            try:
                return channel._supabase_channel.presence_state()
            except Exception as e:
                print(f"Failed to get presence state: {e}")
                return {}
        return {}

    async def get_channel_info(self, channel_name: str) -> dict[str, Any]:
        """获取频道信息"""
        channel = self._channels.get(channel_name)
        if channel:
            return {
                "channel_name": channel_name,
                "state": getattr(channel._supabase_channel, "state", "unknown")
                if channel._supabase_channel
                else "not_created",
                "subscribed": channel.subscribed,
            }

        return {
            "channel_name": channel_name,
            "state": "not_created",
            "subscribed": False,
        }
