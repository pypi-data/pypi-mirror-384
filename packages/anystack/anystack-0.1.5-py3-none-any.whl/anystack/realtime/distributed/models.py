from dataclasses import dataclass, field
from typing import Any
from datetime import datetime
import json


@dataclass
class RealtimeMessage:
    """实时消息的基础数据结构"""

    channel_name: str  # 频道名称
    type: str  # broadcast, presence, db_changes 等
    event: str  # 事件名称
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    sender_id: str | None = None
    message_id: str | None = None

    def to_json(self) -> str:
        """转换为JSON字符串"""
        data = {
            "channel_name": self.channel_name,
            "type": self.type,
            "event": self.event,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "sender_id": self.sender_id,
            "message_id": self.message_id,
        }
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "RealtimeMessage":
        """从JSON字符串创建消息"""
        data = json.loads(json_str)
        return cls(
            channel_name=data["channel_name"],
            type=data["type"],
            event=data["event"],
            payload=data["payload"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            sender_id=data.get("sender_id"),
            message_id=data.get("message_id"),
        )


@dataclass
class WebSocketMessage:
    """WebSocket传输的消息格式"""

    action: str  # subscribe, unsubscribe, send, auth 等
    channel_name: str | None = None  # 频道名称
    type: str | None = None
    event: str | None = None
    payload: dict[str, Any] | None = None
    token: str | None = None  # 认证令牌

    def to_json(self) -> str:
        """转换为JSON字符串"""
        data = {
            "action": self.action,
            "channel_name": self.channel_name,
            "type": self.type,
            "event": self.event,
            "payload": self.payload,
            "token": self.token,
        }
        # 过滤掉None值
        filtered_data = {k: v for k, v in data.items() if v is not None}
        return json.dumps(filtered_data, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "WebSocketMessage":
        """从JSON字符串创建消息"""
        data = json.loads(json_str)
        return cls(
            action=data["action"],
            channel_name=data.get("channel_name"),
            type=data.get("type"),
            event=data.get("event"),
            payload=data.get("payload"),
            token=data.get("token"),
        )


@dataclass
class ConnectionInfo:
    """连接信息"""

    connection_id: str
    user_id: str | None = None
    subscriptions: set[str] = field(default_factory=set)
    authenticated: bool = False

    def subscribe_to(self, channel_name: str, type_: str, event: str) -> None:
        """订阅频道"""
        self.subscriptions.add(f"{channel_name}:{type_}:{event}")

    def unsubscribe_from(self, channel_name: str, type_: str, event: str) -> None:
        """取消订阅频道"""
        self.subscriptions.discard(f"{channel_name}:{type_}:{event}")

    def is_subscribed_to(self, channel_name: str, type_: str, event: str) -> bool:
        """检查是否订阅了指定频道"""
        return f"{channel_name}:{type_}:{event}" in self.subscriptions
