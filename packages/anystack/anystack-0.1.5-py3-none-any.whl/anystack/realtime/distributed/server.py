"""
分布式实时系统架构
DistributedRealtimeService 是中心化的实时服务，提供 WebSocket 端点
DistributedRealtimeClient 是轻量级客户端，连接到中心化服务
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

from ...protocol.db import DB
from ...protocol.gateway import Gateway, WebSocket as ProtocolWebSocket
from ...gateway.base import PathRoute
from ...kv.base import BaseKV
from ...kv import create as create_kv, Config as KVConfig
from ...queue import create as create_queue, Config as QueueConfig
from ...queue.base import BaseQueue, Item as MessageItem
from .models import RealtimeMessage, WebSocketMessage, ConnectionInfo
from ..base import BaseRealtime


T = TypeVar("T")


@dataclass
class Config:
    """分布式实时系统配置"""

    db: DB
    gateway: Gateway
    kv_store: BaseKV[str] = field(default_factory=lambda: create_kv(KVConfig(type="memory", config={})))
    message_queue: BaseQueue[MessageItem[str]] = field(default_factory=lambda: create_queue(QueueConfig(type="asyncio", config={})))
    table_prefix: str = field(default="realtime_")
    connection_timeout: int = field(default=300)
    heartbeat_interval: int = field(default=30)
    message_ttl: int = field(default=3600)
    service_id: str | None = field(default=None)
    auth_handler: Callable[[str], dict[str, Any] | None] | None = field(default=None)
    channel_auth_handler: Callable[[str, str | None], bool] | None = field(default=None)  # (channel_name, user_id) -> bool
    websocket_path: str = field(default="/realtime")


class DistributedRealtimeService:
    """
    分布式实时服务 - 中心化的实时服务
    提供 WebSocket 端点，负责管理连接状态、消息路由和集群协调
    """

    def __init__(
        self,
        config: Config,
    ):
        self.db = config.db
        self.kv_store = config.kv_store
        self.message_queue = config.message_queue
        self.table_prefix = config.table_prefix
        self.connection_timeout = config.connection_timeout
        self.heartbeat_interval = config.heartbeat_interval
        self.message_ttl = config.message_ttl

        self.gateway = config.gateway
        self.auth_handler = config.auth_handler or self._default_auth_handler
        self.channel_auth_handler = config.channel_auth_handler or self._default_channel_auth_handler
        self.websocket_path = config.websocket_path

        self.service_id = config.service_id or f"realtime-{uuid.uuid4().hex[:8]}"
        self.logger = logging.getLogger(f"{__name__}.{self.service_id}")

        # WebSocket 连接管理
        self.connections: dict[str, ProtocolWebSocket] = {}
        self.connection_info: dict[str, ConnectionInfo] = {}

        # 数据库表名
        self.connections_table = f"{self.table_prefix}connections"
        self.subscriptions_table = f"{self.table_prefix}subscriptions"
        self.channels_table = f"{self.table_prefix}channels"
        self.services_table = f"{self.table_prefix}services"

        # 运行状态
        self.running = False
        self._cleanup_task: asyncio.Task[None] | None = None
        self._message_router_task: asyncio.Task[None] | None = None
        self._route_listener_task: asyncio.Task[None] | None = None

        # 设置 WebSocket 路由
        self._setup_websocket_routes()

    def _setup_websocket_routes(self):
        """设置 WebSocket 路由"""
        websocket_route = PathRoute(
            path=self.websocket_path,
            endpoint=self._websocket_handler,
            methods=None,  # WebSocket 不需要 methods
            middlewares=[],
        )
        self.gateway.add_websocket_route(websocket_route)

    async def ensure_schema(self) -> None:
        """确保数据库表结构存在"""
        # 连接表
        create_connections_table = f"""
        CREATE TABLE IF NOT EXISTS {self.connections_table} (
            connection_id TEXT PRIMARY KEY,
            service_id TEXT NOT NULL,
            user_id TEXT,
            authenticated BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
        """

        # 频道表
        create_channels_table = f"""
        CREATE TABLE IF NOT EXISTS {self.channels_table} (
            channel_name TEXT PRIMARY KEY,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
        """

        # 订阅表
        create_subscriptions_table = f"""
        CREATE TABLE IF NOT EXISTS {self.subscriptions_table} (
            id TEXT PRIMARY KEY,
            connection_id TEXT NOT NULL,
            service_id TEXT NOT NULL,
            channel_name TEXT NOT NULL,
            type TEXT NOT NULL,
            event TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (connection_id) REFERENCES {self.connections_table}(connection_id) ON DELETE CASCADE,
            FOREIGN KEY (channel_name) REFERENCES {self.channels_table}(channel_name) ON DELETE CASCADE
        )
        """

        # 服务实例表
        create_services_table = f"""
        CREATE TABLE IF NOT EXISTS {self.services_table} (
            service_id TEXT PRIMARY KEY,
            hostname TEXT NOT NULL,
            pid INTEGER NOT NULL,
            last_heartbeat TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """

        # 创建索引
        create_indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_{self.connections_table}_service ON {self.connections_table} (service_id)",
            f"CREATE INDEX IF NOT EXISTS idx_{self.connections_table}_user ON {self.connections_table} (user_id)",
            f"CREATE INDEX IF NOT EXISTS idx_{self.connections_table}_last_seen ON {self.connections_table} (last_seen)",
            f"CREATE INDEX IF NOT EXISTS idx_{self.subscriptions_table}_connection ON {self.subscriptions_table} (connection_id)",
            f"CREATE INDEX IF NOT EXISTS idx_{self.subscriptions_table}_channel ON {self.subscriptions_table} (channel_name, type, event)",
            f"CREATE INDEX IF NOT EXISTS idx_{self.subscriptions_table}_service ON {self.subscriptions_table} (service_id)",
            f"CREATE INDEX IF NOT EXISTS idx_{self.channels_table}_name ON {self.channels_table} (channel_name)",
            f"CREATE INDEX IF NOT EXISTS idx_{self.services_table}_heartbeat ON {self.services_table} (last_heartbeat)",
        ]

        async with self.db.transaction() as conn:
            _ = await conn.sql(create_connections_table)
            _ = await conn.sql(create_channels_table)
            _ = await conn.sql(create_subscriptions_table)
            _ = await conn.sql(create_services_table)

            for index_sql in create_indexes:
                _ = await conn.sql(index_sql)

    async def start(self) -> None:
        """启动分布式实时服务"""
        self.running = True
        self.logger.info(f"Starting distributed realtime service {self.service_id}")

        await self.ensure_schema()

        # 注册服务实例
        await self._register_service()

        # 启动后台任务
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._message_router_task = asyncio.create_task(self._message_router())
        self._route_listener_task = asyncio.create_task(self._route_listener())

        self.logger.info(f"Distributed realtime service {self.service_id} started")

    async def stop(self) -> None:
        """停止分布式实时服务"""
        self.running = False
        self.logger.info(f"Stopping distributed realtime service {self.service_id}")

        # 停止后台任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self._message_router_task:
            self._message_router_task.cancel()
            try:
                await self._message_router_task
            except asyncio.CancelledError:
                pass

        if self._route_listener_task:
            self._route_listener_task.cancel()
            try:
                await self._route_listener_task
            except asyncio.CancelledError:
                pass

        # 标记服务为非活跃状态
        _ = await self.db.sql(
            f"UPDATE {self.services_table} SET status = 'inactive' WHERE service_id = :service_id",
            {"service_id": self.service_id},
        )

        self.logger.info(f"Distributed realtime service {self.service_id} stopped")

    async def _safe_send_json(
        self, websocket: ProtocolWebSocket, data: dict[str, Any]
    ) -> bool:
        """安全发送JSON数据，检查连接状态"""
        try:
            if websocket.state == "connected":
                await websocket.send_json(data)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to send JSON data: {e}")
            return False

    async def _websocket_handler(self, websocket: ProtocolWebSocket) -> None:
        """WebSocket 连接处理器"""
        connection_id = str(uuid.uuid4())

        await websocket.accept()
        self.connections[connection_id] = websocket
        self.connection_info[connection_id] = ConnectionInfo(
            connection_id=connection_id
        )

        # 在分布式服务中注册连接
        await self.register_connection(connection_id)

        try:
            await self._handle_websocket_connection(websocket, connection_id)
        except Exception as e:
            self.logger.error(f"WebSocket error for connection {connection_id}: {e}")
        finally:
            await self._cleanup_connection(connection_id)

    async def _handle_websocket_connection(
        self, websocket: ProtocolWebSocket, connection_id: str
    ):
        """处理 WebSocket 连接的消息"""
        conn_info = self.connection_info[connection_id]

        # 启动心跳任务
        heartbeat_task = asyncio.create_task(self._connection_heartbeat(connection_id))

        try:
            while websocket.state == "connected" and self.running:
                try:
                    message_text = await websocket.receive_text()
                    ws_message = WebSocketMessage.from_json(message_text)

                    if ws_message.action == "auth":
                        await self._handle_auth(websocket, conn_info, ws_message)

                    elif ws_message.action == "subscribe":
                        if not conn_info.authenticated:
                            _ = await self._safe_send_json(
                                websocket, {"error": "Not authenticated"}
                            )
                            continue
                        await self._handle_subscribe(websocket, conn_info, ws_message)

                    elif ws_message.action == "unsubscribe":
                        await self._handle_unsubscribe(websocket, conn_info, ws_message)

                    elif ws_message.action == "send":
                        if not conn_info.authenticated:
                            _ = await self._safe_send_json(
                                websocket, {"error": "Not authenticated"}
                            )
                            continue
                        await self._handle_send(websocket, ws_message)

                    elif ws_message.action == "ping":
                        _ = await self._safe_send_json(websocket, {"action": "pong"})

                    else:
                        _ = await self._safe_send_json(
                            websocket, {"error": f"Unknown action: {ws_message.action}"}
                        )

                except json.JSONDecodeError:
                    _ = await self._safe_send_json(
                        websocket, {"error": "Invalid JSON format"}
                    )
                except Exception as e:
                    _ = await self._safe_send_json(
                        websocket, {"error": f"Message processing error: {str(e)}"}
                    )

        except Exception as e:
            self.logger.error(f"WebSocket connection error: {e}")
            # 确保连接正常关闭
            try:
                if websocket.state == "connected":
                    await websocket.close(code=1011, reason="Server Error")
            except Exception:
                pass  # 忽略关闭时的错误
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

    async def _connection_heartbeat(self, connection_id: str):
        """连接心跳任务"""
        while self.running:
            try:
                await self.update_connection_heartbeat(connection_id)
                await asyncio.sleep(30)  # 30秒心跳间隔
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat error for {connection_id}: {e}")
                await asyncio.sleep(30)

    async def _handle_auth(
        self,
        websocket: ProtocolWebSocket,
        conn_info: ConnectionInfo,
        ws_message: WebSocketMessage,
    ):
        """处理认证请求"""
        if not ws_message.token:
            _ = await self._safe_send_json(websocket, {"error": "Token required"})
            return

        try:
            user_info = self.auth_handler(ws_message.token)
            if user_info:
                conn_info.authenticated = True
                conn_info.user_id = user_info.get("user_id")

                # 更新分布式服务中的连接信息
                await self.register_connection(
                    conn_info.connection_id,
                    user_id=conn_info.user_id,
                    metadata=user_info,
                )

                _ = await self._safe_send_json(
                    websocket,
                    {
                        "action": "auth",
                        "status": "success",
                        "user_id": conn_info.user_id,
                    },
                )
            else:
                _ = await self._safe_send_json(
                    websocket, {"error": "Authentication failed"}
                )
        except Exception as e:
            _ = await self._safe_send_json(
                websocket, {"error": f"Authentication error: {str(e)}"}
            )

    async def _handle_subscribe(
        self,
        websocket: ProtocolWebSocket,
        conn_info: ConnectionInfo,
        ws_message: WebSocketMessage,
    ):
        """处理订阅请求"""
        if not ws_message.channel_name or not ws_message.type or not ws_message.event:
            _ = await self._safe_send_json(
                websocket, {"error": "Channel name, type and event are required for subscription"}
            )
            return

        try:
            # 检查频道权限
            if not self.channel_auth_handler(ws_message.channel_name, conn_info.user_id):
                _ = await self._safe_send_json(
                    websocket, {"error": f"Access denied to channel: {ws_message.channel_name}"}
                )
                return

            # 确保频道存在
            await self.ensure_channel(ws_message.channel_name)

            # 在分布式服务中添加订阅
            subscription_id = await self.add_subscription(
                conn_info.connection_id, ws_message.channel_name, ws_message.type, ws_message.event
            )

            # 本地记录订阅
            conn_info.subscribe_to(ws_message.channel_name, ws_message.type, ws_message.event)

            _ = await self._safe_send_json(
                websocket,
                {
                    "action": "subscribe",
                    "status": "success",
                    "channel_name": ws_message.channel_name,
                    "type": ws_message.type,
                    "event": ws_message.event,
                    "subscription_id": subscription_id,
                },
            )

        except Exception as e:
            _ = await self._safe_send_json(
                websocket, {"error": f"Subscription error: {str(e)}"}
            )

    async def _handle_unsubscribe(
        self,
        websocket: ProtocolWebSocket,
        conn_info: ConnectionInfo,
        ws_message: WebSocketMessage,
    ):
        """处理取消订阅请求"""
        if not ws_message.channel_name or not ws_message.type or not ws_message.event:
            _ = await self._safe_send_json(
                websocket, {"error": "Channel name, type and event are required for unsubscription"}
            )
            return

        try:
            # 在分布式服务中移除订阅
            await self.remove_subscription(
                conn_info.connection_id, ws_message.channel_name, ws_message.type, ws_message.event
            )

            # 本地移除订阅
            conn_info.unsubscribe_from(ws_message.channel_name, ws_message.type, ws_message.event)

            _ = await self._safe_send_json(
                websocket,
                {
                    "action": "unsubscribe",
                    "status": "success",
                    "channel_name": ws_message.channel_name,
                    "type": ws_message.type,
                    "event": ws_message.event,
                },
            )

        except Exception as e:
            _ = await self._safe_send_json(
                websocket, {"error": f"Unsubscription error: {str(e)}"}
            )

    async def _handle_send(
        self, websocket: ProtocolWebSocket, ws_message: WebSocketMessage
    ):
        """处理发送消息请求"""
        if not ws_message.channel_name or not ws_message.type or not ws_message.event or not ws_message.payload:
            _ = await self._safe_send_json(
                websocket,
                {"error": "Channel name, type, event, and payload are required for sending"},
            )
            return

        try:
            # 通过分布式服务广播消息
            subscriber_count = await self.broadcast_message(
                ws_message.channel_name, ws_message.type, ws_message.event, ws_message.payload
            )

            _ = await self._safe_send_json(
                websocket,
                {
                    "action": "send",
                    "status": "success",
                    "channel_name": ws_message.channel_name,
                    "subscriber_count": subscriber_count,
                },
            )

        except Exception as e:
            _ = await self._safe_send_json(
                websocket, {"error": f"Send error: {str(e)}"}
            )

    async def _cleanup_connection(self, connection_id: str):
        """清理连接资源"""
        try:
            # 在分布式服务中注销连接
            await self.unregister_connection(connection_id)
        except Exception as e:
            self.logger.error(f"Error unregistering connection {connection_id}: {e}")

        # 清理本地连接信息
        if connection_id in self.connection_info:
            del self.connection_info[connection_id]

        if connection_id in self.connections:
            del self.connections[connection_id]

    def _default_auth_handler(self, token: str) -> dict[str, Any] | None:
        """默认的认证处理器"""
        if token and len(token) > 10:
            return {"user_id": f"user_{hash(token) % 10000}", "authenticated": True}
        return None

    def _default_channel_auth_handler(self, channel_name: str, user_id: str | None) -> bool:
        """默认的频道权限检查器"""
        # 默认允许所有已认证用户访问所有频道
        return user_id is not None

    async def ensure_channel(self, channel_name: str) -> None:
        """确保频道存在"""
        try:
            await self.db.sql(
                f"""
                INSERT OR IGNORE INTO {self.channels_table}
                (channel_name, created_at, metadata)
                VALUES (:channel_name, CURRENT_TIMESTAMP, :metadata)
                """,
                {
                    "channel_name": channel_name,
                    "metadata": json.dumps({"auto_created": True}),
                },
            )
        except Exception as e:
            self.logger.error(f"Failed to ensure channel {channel_name}: {e}")

    async def register_connection(
        self,
        connection_id: str,
        user_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """注册新连接"""
        now = datetime.now(timezone.utc)

        _ = await self.db.sql(
            f"""
            INSERT OR REPLACE INTO {self.connections_table}
            (connection_id, service_id, user_id, authenticated, created_at, last_seen, metadata)
            VALUES (:connection_id, :service_id, :user_id, :authenticated, :created_at, :last_seen, :metadata)
            """,
            {
                "connection_id": connection_id,
                "service_id": self.service_id,
                "user_id": user_id,
                "authenticated": user_id is not None,
                "created_at": now.isoformat(),
                "last_seen": now.isoformat(),
                "metadata": json.dumps(metadata) if metadata else None,
            },
        )

        self.logger.info(f"Registered connection {connection_id} for user {user_id}")

    async def unregister_connection(self, connection_id: str) -> None:
        """注销连接"""
        async with self.db.transaction() as conn:
            # 删除订阅
            await conn.sql(
                f"DELETE FROM {self.subscriptions_table} WHERE connection_id = :connection_id",
                {"connection_id": connection_id},
            )

            # 删除连接
            await conn.sql(
                f"DELETE FROM {self.connections_table} WHERE connection_id = :connection_id",
                {"connection_id": connection_id},
            )

        self.logger.info(f"Unregistered connection {connection_id}")

    async def update_connection_heartbeat(self, connection_id: str) -> None:
        """更新连接心跳"""
        now = datetime.now(timezone.utc)

        await self.db.sql(
            f"UPDATE {self.connections_table} SET last_seen = :last_seen WHERE connection_id = :connection_id",
            {
                "connection_id": connection_id,
                "last_seen": now.isoformat(),
            },
        )

    async def add_subscription(self, connection_id: str, channel_name: str, type_: str, event: str) -> str:
        """添加订阅"""
        subscription_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await self.db.sql(
            f"""
            INSERT INTO {self.subscriptions_table}
            (id, connection_id, service_id, channel_name, type, event, created_at)
            VALUES (:id, :connection_id, :service_id, :channel_name, :type, :event, :created_at)
            """,
            {
                "id": subscription_id,
                "connection_id": connection_id,
                "service_id": self.service_id,
                "channel_name": channel_name,
                "type": type_,
                "event": event,
                "created_at": now.isoformat(),
            },
        )

        self.logger.info(f"Added subscription {subscription_id} for {channel_name}:{type_}:{event}")
        return subscription_id

    async def remove_subscription(
        self, connection_id: str, channel_name: str, type_: str, event: str
    ) -> None:
        """移除订阅"""
        await self.db.sql(
            f"""
            DELETE FROM {self.subscriptions_table}
            WHERE connection_id = :connection_id AND channel_name = :channel_name AND type = :type AND event = :event
            """,
            {
                "connection_id": connection_id,
                "channel_name": channel_name,
                "type": type_,
                "event": event,
            },
        )

        self.logger.info(
            f"Removed subscription for {connection_id} from {channel_name}:{type_}:{event}"
        )

    async def broadcast_message(
        self,
        channel_name: str,
        type_: str,
        event: str,
        payload: dict[str, Any],
        sender_id: str | None = None,
    ) -> int:
        """广播消息到所有订阅者"""
        message = RealtimeMessage(
            channel_name=channel_name,
            type=type_,
            event=event,
            payload=payload,
            sender_id=sender_id,
            message_id=str(uuid.uuid4()),
        )

        # 将消息放入队列
        item = MessageItem(data=message.to_json(), priority=0)
        await self.message_queue.put(item)

        # 获取订阅者数量（用于统计）
        result = await self.db.sql(
            f"""
            SELECT COUNT(*) as count FROM {self.subscriptions_table}
            WHERE channel_name = :channel_name AND type = :type AND event = :event
            """,
            {"channel_name": channel_name, "type": type_, "event": event},
        )

        subscriber_count = result.rows[0]["count"] if result.rows else 0

        self.logger.info(
            f"Broadcasted message to {subscriber_count} subscribers of {channel_name}:{type_}:{event}"
        )
        return subscriber_count

    async def get_connection_subscriptions(
        self, connection_id: str
    ) -> list[dict[str, str]]:
        """获取连接的所有订阅"""
        result = await self.db.sql(
            f"SELECT type, event FROM {self.subscriptions_table} WHERE connection_id = :connection_id",
            {"connection_id": connection_id},
        )

        return [{"type": row["type"], "event": row["event"]} for row in result.rows]

    async def get_service_stats(self) -> dict[str, Any]:
        """获取服务统计信息"""
        # 连接统计
        connections_result = await self.db.sql(
            f"""
            SELECT 
                COUNT(*) as total_connections,
                COUNT(CASE WHEN authenticated THEN 1 END) as authenticated_connections
            FROM {self.connections_table}
            WHERE service_id = :service_id
            """,
            {"service_id": self.service_id},
        )

        # 订阅统计
        subscriptions_result = await self.db.sql(
            f"SELECT COUNT(*) as total_subscriptions FROM {self.subscriptions_table} WHERE service_id = :service_id",
            {"service_id": self.service_id},
        )

        connections_stats = (
            connections_result.rows[0]
            if connections_result.rows
            else {"total_connections": 0, "authenticated_connections": 0}
        )
        subscriptions_stats = (
            subscriptions_result.rows[0]
            if subscriptions_result.rows
            else {"total_subscriptions": 0}
        )

        return {
            "service_id": self.service_id,
            "total_connections": connections_stats["total_connections"],
            "authenticated_connections": connections_stats["authenticated_connections"],
            "total_subscriptions": subscriptions_stats["total_subscriptions"],
        }

    async def _register_service(self) -> None:
        """注册服务实例"""
        import socket
        import os

        hostname = socket.gethostname()
        pid = os.getpid()
        now = datetime.now(timezone.utc)

        await self.db.sql(
            f"""
            INSERT OR REPLACE INTO {self.services_table}
            (service_id, hostname, pid, last_heartbeat, status, created_at)
            VALUES (:service_id, :hostname, :pid, :last_heartbeat, 'active', :created_at)
            """,
            {
                "service_id": self.service_id,
                "hostname": hostname,
                "pid": pid,
                "last_heartbeat": now.isoformat(),
                "created_at": now.isoformat(),
            },
        )

    async def _cleanup_loop(self) -> None:
        """清理循环"""
        while self.running:
            try:
                # 更新服务心跳
                await self.db.sql(
                    f"UPDATE {self.services_table} SET last_heartbeat = CURRENT_TIMESTAMP WHERE service_id = :service_id",
                    {"service_id": self.service_id},
                )

                # 清理过期连接
                cutoff_time = (
                    datetime.now(timezone.utc).timestamp() - self.connection_timeout
                )
                cutoff_datetime = datetime.fromtimestamp(cutoff_time, tz=timezone.utc)

                expired_connections = await self.db.sql(
                    f"SELECT connection_id FROM {self.connections_table} WHERE last_seen < :cutoff_time",
                    {"cutoff_time": cutoff_datetime.isoformat()},
                )

                if expired_connections.rows:
                    connection_ids = [
                        row["connection_id"] for row in expired_connections.rows
                    ]

                    async with self.db.transaction() as conn:
                        # 删除过期连接的订阅
                        for connection_id in connection_ids:
                            await conn.sql(
                                f"DELETE FROM {self.subscriptions_table} WHERE connection_id = :connection_id",
                                {"connection_id": connection_id},
                            )

                        # 删除过期连接
                        await conn.sql(
                            f"DELETE FROM {self.connections_table} WHERE last_seen < :cutoff_time",
                            {"cutoff_time": cutoff_datetime.isoformat()},
                        )

                    self.logger.info(
                        f"Cleaned up {len(connection_ids)} expired connections"
                    )

                await asyncio.sleep(self.heartbeat_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}", exc_info=True)
                await asyncio.sleep(self.heartbeat_interval)

    async def _message_router(self) -> None:
        """消息路由器"""
        while self.running:
            try:
                # 从队列获取消息
                item = await self.message_queue.get()
                message = RealtimeMessage.from_json(item.data)

                # 查找订阅了该频道的连接
                subscriptions = await self.db.sql(
                    f"""
                    SELECT DISTINCT s.connection_id, s.service_id, c.user_id
                    FROM {self.subscriptions_table} s
                    JOIN {self.connections_table} c ON s.connection_id = c.connection_id
                    WHERE s.channel_name = :channel_name AND s.type = :type AND s.event = :event
                    """,
                    {"channel_name": message.channel_name, "type": message.type, "event": message.event},
                )

                # 按服务分组路由消息
                service_routes: dict[str, list[str]] = {}
                for row in subscriptions.rows:
                    service_id = row["service_id"]
                    connection_id = row["connection_id"]

                    if service_id not in service_routes:
                        service_routes[service_id] = []
                    service_routes[service_id].append(connection_id)

                # 处理本服务的连接
                local_connections = service_routes.get(self.service_id, [])
                for connection_id in local_connections:
                    await self._send_message_to_connection(connection_id, message)

                # 为其他服务创建路由消息
                for target_service_id, connection_ids in service_routes.items():
                    if target_service_id == self.service_id:
                        continue  # 跳过本服务，已经处理了

                    route_message = {
                        "type": "route_message",
                        "target_service": target_service_id,
                        "connection_ids": connection_ids,
                        "message": message.to_json(),
                    }

                    # 通过 KV 存储发送路由消息
                    route_key = f"route:{target_service_id}:{uuid.uuid4().hex[:8]}"
                    await self.kv_store.set(route_key, json.dumps(route_message))

                await self.message_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Message routing error: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _send_message_to_connection(
        self, connection_id: str, message: RealtimeMessage
    ):
        """向指定连接发送消息"""
        websocket = self.connections.get(connection_id)
        if websocket and websocket.state == "connected":
            try:
                _ = await self._safe_send_json(
                    websocket,
                    {
                        "action": "message",
                        "channel_name": message.channel_name,
                        "type": message.type,
                        "event": message.event,
                        "payload": message.payload,
                        "sender_id": message.sender_id,
                        "timestamp": message.timestamp.isoformat(),
                    },
                )
            except Exception as e:
                self.logger.error(f"Failed to send message to {connection_id}: {e}")

    async def _route_listener(self):
        """监听其他服务的路由消息"""
        service_id = self.service_id

        while self.running:
            try:
                # 扫描路由消息
                key_iterable = await self.kv_store.list()
                async for key in key_iterable:
                    if key.startswith(f"route:{service_id}:"):
                        try:
                            route_data = await self.kv_store.get(key)
                            if route_data:
                                route_message = json.loads(route_data)
                                await self._process_route_message(route_message)
                                # 删除已处理的路由消息
                                await self.kv_store.delete(key)
                        except Exception as e:
                            self.logger.error(
                                f"Error processing route message {key}: {e}"
                            )

                await asyncio.sleep(0.1)  # 100ms 轮询间隔

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Route listener error: {e}")
                await asyncio.sleep(1)

    async def _process_route_message(self, route_message: dict[str, Any]):
        """处理路由消息"""
        try:
            connection_ids = route_message.get("connection_ids", [])
            message_data = route_message.get("message")

            if not message_data:
                return

            message = RealtimeMessage.from_json(message_data)

            # 向指定连接发送消息
            for connection_id in connection_ids:
                await self._send_message_to_connection(connection_id, message)

        except Exception as e:
            self.logger.error(f"Error processing route message: {e}")

    def get_stats(self) -> dict[str, Any]:
        """获取服务统计信息"""
        return {
            "service_id": self.service_id,
            "total_connections": len(self.connections),
            "authenticated_connections": sum(
                1 for conn in self.connection_info.values() if conn.authenticated
            ),
            "total_subscriptions": sum(
                len(conn.subscriptions) for conn in self.connection_info.values()
            ),
        }
