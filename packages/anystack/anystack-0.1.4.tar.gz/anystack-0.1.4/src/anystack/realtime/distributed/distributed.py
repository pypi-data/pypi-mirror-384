import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, override, TypeVar
from urllib.parse import urljoin

import aiohttp

from ..base import BaseRealtime, BaseChannel
from .models import WebSocketMessage


T = TypeVar("T", bound=dict[str, Any])


class DistributedChannel(BaseChannel[T]):
    """分布式实时频道实现"""

    def __init__(self, realtime: 'DistributedRealtime[dict[str, Any]]', name: str, opts: dict[str, Any]):
        self.realtime: 'DistributedRealtime[dict[str, Any]]' = realtime
        self.name: str = name
        self.opts: dict[str, Any] = opts
        self.subscribed: bool = False
        self._event_handlers: dict[str, list[Callable[[T], Any]]] = {}
        self.logger: logging.Logger = logging.getLogger(f"{__name__}.{name}")

    @override
    async def send(self, type: str, event: str, payload: dict[str, Any]) -> None:
        """发送消息到频道"""
        if not self.realtime.connected:
            raise RuntimeError("Not connected")
        
        if not self.realtime.authenticated:
            raise RuntimeError("Not authenticated")
        
        await self.realtime.send_message(self.name, type, event, payload)

    @override
    async def on(self, type: str, event: str, callback: Callable[[T], Any]) -> None:
        """监听频道事件"""
        # 添加本地事件处理器
        key = f"{self.name}:{type}:{event}"
        if key not in self._event_handlers:
            self._event_handlers[key] = []
        self._event_handlers[key].append(callback)
        
        # 添加到 realtime 的全局处理器中
        self.realtime.add_event_handler(self.name, type, event, callback)
        
        # 如果已经订阅了频道，直接订阅这个事件
        if self.subscribed:
            await self.realtime.subscribe_to(self.name, type, event)

    @override
    async def subscribe(self):
        """订阅频道"""
        if self.subscribed:
            return
            
        # 确保连接已建立
        if not self.realtime.connected:
            await self.realtime.connect()
            
        # 订阅所有已注册的事件
        for key in self._event_handlers.keys():
            # key 格式: channel_name:type:event
            parts = key.split(":", 2)
            if len(parts) == 3:
                channel_name, type_, event = parts
                await self.realtime.subscribe_to(channel_name, type_, event)
            
        self.subscribed = True
        self.logger.info(f"Subscribed to channel {self.name}")

    @override
    async def unsubscribe(self):
        """取消订阅频道"""
        if not self.subscribed:
            return
            
        # 取消订阅所有事件
        for key in self._event_handlers.keys():
            # key 格式: channel_name:type:event
            parts = key.split(":", 2)
            if len(parts) == 3:
                channel_name, type_, event = parts
                await self.realtime.unsubscribe_from(channel_name, type_, event)
            
        self.subscribed = False
        self.logger.info(f"Unsubscribed from channel {self.name}")

    @override
    async def close(self) -> None:
        """关闭频道"""
        # 取消订阅
        await self.unsubscribe()
        
        # 清理事件处理器
        for key, handlers in self._event_handlers.items():
            # key 格式: channel_name:type:event
            parts = key.split(":", 2)
            if len(parts) == 3:
                channel_name, type_, event = parts
                for handler in handlers:
                    self.realtime.remove_event_handler(channel_name, type_, event, handler)
                
        self._event_handlers.clear()
        self.logger.info(f"Closed channel {self.name}")


@dataclass
class Config:
    server_url: str
    token: str | None
    websocket_path: str = field(default="/realtime")
    auto_reconnect: bool = field(default=True)
    reconnect_interval: float = field(default=5.0)


class DistributedRealtime(BaseRealtime[T]):
    """
    分布式实时客户端
    轻量级的 WebSocket 客户端，连接到中心化的 DistributedRealtimeService
    """

    def __init__(
        self,
        config: Config,
    ):
        """
        初始化分布式实时客户端

        Args:
            server_url: 服务器地址，例如 "http://localhost:8000"
            token: 认证令牌
            websocket_path: WebSocket 路径
            auto_reconnect: 是否自动重连
            reconnect_interval: 重连间隔（秒）
        """
        self.server_url: str = config.server_url.rstrip("/")
        self.token: str | None = config.token
        self.websocket_path: str = config.websocket_path
        self.auto_reconnect: bool = config.auto_reconnect
        self.reconnect_interval: float = config.reconnect_interval

        # 构建 WebSocket URL
        ws_url = config.server_url.replace("http://", "ws://").replace(
            "https://", "wss://"
        )
        self.websocket_url: str = urljoin(ws_url, config.websocket_path.lstrip("/"))

        self.logger: logging.Logger = logging.getLogger(__name__)

        # 连接状态
        self.connected: bool = False
        self.authenticated: bool = False
        self.user_id: str | None = None

        # WebSocket 连接
        self._session: aiohttp.ClientSession | None = None
        self._websocket: aiohttp.ClientWebSocketResponse | None = None

        # 事件回调
        self._event_handlers: dict[str, dict[str, list[Callable[[T], Any]]]] = {}

        # 订阅管理
        self._subscriptions: set[str] = set()

        # 频道管理
        self._channels: dict[str, DistributedChannel] = {}

        # 运行状态
        self.running: bool = False
        self._message_handler_task: asyncio.Task[None] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._reconnect_task: asyncio.Task[None] | None = None

    async def connect(self) -> None:
        """连接到服务器"""
        if self.connected:
            return

        self.running = True
        self.logger.info(f"Connecting to {self.websocket_url}")

        try:
            self._session = aiohttp.ClientSession()
            self._websocket = await self._session.ws_connect(self.websocket_url)
            self.connected = True

            # 启动消息处理任务
            self._message_handler_task = asyncio.create_task(self._message_handler())

            # 启动心跳任务
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            # 如果有认证令牌，自动认证
            if self.token:
                _ = await self.authenticate(self.token)

            self.logger.info("Connected successfully")

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            await self._cleanup_connection()

            if self.auto_reconnect and self.running:
                self._reconnect_task = asyncio.create_task(self._reconnect_loop())
            else:
                raise

    async def disconnect(self) -> None:
        """断开连接"""
        self.running = False
        self.logger.info("Disconnecting...")

        # 停止重连任务
        if self._reconnect_task:
            _ = self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        await self._cleanup_connection()
        self.logger.info("Disconnected")

    async def _cleanup_connection(self):
        """清理连接资源"""
        # 停止任务
        if self._message_handler_task:
            _ = self._message_handler_task.cancel()
            try:
                await self._message_handler_task
            except asyncio.CancelledError:
                pass

        if self._heartbeat_task:
            _ = self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # 关闭 WebSocket
        if self._websocket and not self._websocket.closed:
            _ = await self._websocket.close()

        # 关闭会话
        if self._session and not self._session.closed:
            await self._session.close()

        # 重置状态
        self.connected = False
        self.authenticated = False
        self.user_id = None
        self._websocket = None
        self._session = None

    async def _reconnect_loop(self):
        """重连循环"""
        while self.running and self.auto_reconnect:
            try:
                self.logger.info(
                    f"Reconnecting in {self.reconnect_interval} seconds..."
                )
                await asyncio.sleep(self.reconnect_interval)

                if not self.running:
                    break

                await self.connect()
                break  # 连接成功，退出重连循环

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Reconnection failed: {e}")

    async def authenticate(self, token: str) -> bool:
        """认证"""
        if not self.connected or not self._websocket:
            raise RuntimeError("Not connected")

        message = WebSocketMessage(action="auth", token=token)
        await self._websocket.send_str(message.to_json())

        # 等待认证结果（这里简化处理，实际应该等待服务器响应）
        await asyncio.sleep(0.1)
        return self.authenticated

    async def subscribe_to(self, channel_name: str, type_: str, event: str) -> None:
        """订阅频道"""
        if not self.connected or not self._websocket:
            raise RuntimeError("Not connected")

        if not self.authenticated:
            raise RuntimeError("Not authenticated")

        subscription_key = f"{channel_name}:{type_}:{event}"
        if subscription_key in self._subscriptions:
            return  # 已经订阅了

        message = WebSocketMessage(action="subscribe", channel_name=channel_name, type=type_, event=event)
        await self._websocket.send_str(message.to_json())

        self._subscriptions.add(subscription_key)
        self.logger.info(f"Subscribed to {channel_name}:{type_}:{event}")

    async def unsubscribe_from(self, channel_name: str, type_: str, event: str) -> None:
        """取消订阅频道"""
        if not self.connected or not self._websocket:
            return

        subscription_key = f"{channel_name}:{type_}:{event}"
        if subscription_key not in self._subscriptions:
            return  # 没有订阅

        message = WebSocketMessage(action="unsubscribe", channel_name=channel_name, type=type_, event=event)
        await self._websocket.send_str(message.to_json())

        self._subscriptions.discard(subscription_key)
        self.logger.info(f"Unsubscribed from {channel_name}:{type_}:{event}")

    async def send_message(self, channel_name: str, type_: str, event: str, payload: T) -> None:
        """发送消息"""
        if not self.connected or not self._websocket:
            raise RuntimeError("Not connected")

        if not self.authenticated:
            raise RuntimeError("Not authenticated")

        message = WebSocketMessage(
            action="send", channel_name=channel_name, type=type_, event=event, payload=payload
        )
        await self._websocket.send_str(message.to_json())

    def add_event_handler(
        self, channel_name: str, type_: str, event: str, handler: Callable[[T], Any]
    ) -> None:
        """添加事件处理器"""
        key = f"{channel_name}:{type_}"
        if key not in self._event_handlers:
            self._event_handlers[key] = {}

        if event not in self._event_handlers[key]:
            self._event_handlers[key][event] = []

        self._event_handlers[key][event].append(handler)

    def remove_event_handler(
        self, channel_name: str, type_: str, event: str, handler: Callable[[T], Any]
    ) -> None:
        """移除事件处理器"""
        key = f"{channel_name}:{type_}"
        if key in self._event_handlers and event in self._event_handlers[key]:
            try:
                self._event_handlers[key][event].remove(handler)
                if not self._event_handlers[key][event]:
                    del self._event_handlers[key][event]
                if not self._event_handlers[key]:
                    del self._event_handlers[key]
            except ValueError:
                pass

    async def _message_handler(self):
        """消息处理循环"""
        while self.running and self.connected and self._websocket:
            try:
                msg = await self._websocket.receive()

                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_message(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error: {self._websocket.exception()}")
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    self.logger.info("WebSocket closed by server")
                    break

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Message handler error: {e}")
                break

        # 连接断开，尝试重连
        self.connected = False
        if self.auto_reconnect and self.running:
            self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _handle_message(self, message_text: str):
        """处理收到的消息"""
        try:
            data = json.loads(message_text)
            action = data.get("action")

            if action == "auth":
                # 认证响应
                if data.get("status") == "success":
                    self.authenticated = True
                    self.user_id = data.get("user_id")
                    self.logger.info(f"Authenticated as user {self.user_id}")
                else:
                    self.logger.error("Authentication failed")

            elif action == "message":
                # 实时消息
                channel_name = data.get("channel_name")
                type_ = data.get("type")
                event = data.get("event")
                payload = data.get("payload", {})

                if channel_name and type_ and event:
                    await self._dispatch_event(channel_name, type_, event, payload)

            elif action == "pong":
                # 心跳响应
                pass

            else:
                self.logger.debug(f"Received message: {data}")

        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON message: {message_text}")
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")

    async def _dispatch_event(self, channel_name: str, type_: str, event: str, payload: T):
        """分发事件到处理器"""
        key = f"{channel_name}:{type_}"
        handlers = self._event_handlers.get(key, {}).get(event, [])

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(payload)
                else:
                    handler(payload)
            except Exception as e:
                self.logger.error(f"Error in event handler: {e}")

    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.running and self.connected and self._websocket:
            try:
                await asyncio.sleep(30)  # 30秒心跳间隔

                if not self.connected or not self._websocket:
                    break

                ping_message = WebSocketMessage(action="ping")
                await self._websocket.send_str(ping_message.to_json())

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")
                break

    # BaseRealtime 接口实现
    @override
    async def channel(self, name: str, opts: dict[str, Any]) -> BaseChannel[T]:
        """创建或获取频道"""
        if name not in self._channels:
            self._channels[name] = DistributedChannel(self, name, opts)
        return self._channels[name]

    @override
    async def get_channels(self) -> list[BaseChannel[T]]:
        """获取所有频道"""
        return list(self._channels.values())

    @override
    async def remove_channel(self, channel: BaseChannel[T]) -> None:
        """移除指定频道"""
        if isinstance(channel, DistributedChannel) and channel.name in self._channels:
            await channel.close()
            del self._channels[channel.name]

    @override
    async def remove_all_channels(self) -> None:
        """移除所有频道"""
        for channel in list(self._channels.values()):
            await channel.close()
        self._channels.clear()

    def get_stats(self) -> dict[str, Any]:
        """获取客户端统计信息"""
        return {
            "connected": self.connected,
            "authenticated": self.authenticated,
            "user_id": self.user_id,
            "subscriptions": len(self._subscriptions),
            "event_handlers": sum(
                len(events)
                for events in self._event_handlers.values()
                for events in events.values()
            ),
        }
