"""
Cloudflare Queues 适配器
使用 Cloudflare Queues 实现队列功能
"""

import json
import asyncio
from typing import Any, TypeVar
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

from .base import BaseQueue, Item

T = TypeVar("T")


@dataclass
class Config:
    account_id: str
    queue_name: str
    api_token: str
    maxsize: int = field(default=0)


class CloudflareQueue(BaseQueue[Item[T]]):
    """Cloudflare Queue 包装器，实现 Queue 协议"""

    def __init__(self, config: Config):
        self._account_id = config.account_id
        self._queue_name = config.queue_name
        self._api_token = config.api_token
        self._maxsize = config.maxsize
        self._base_url = f"https://api.cloudflare.com/client/v4/accounts/{config.account_id}/queues/{config.queue_name}"
        self._headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json",
        }
        self._client: httpx.AsyncClient | None = None
        self._message_count = 0

    async def _ensure_client(self):
        """确保 HTTP 客户端已初始化"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)

    async def _close_client(self):
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def qsize(self) -> int:
        """返回队列中的项目数量（近似值）"""
        await self._ensure_client()

        try:
            response = await self._client.get(
                f"{self._base_url}/stats", headers=self._headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get("result", {}).get("messages_ready", 0)
        except Exception:
            # 如果无法获取统计信息，返回近似值
            return self._message_count

    async def maxsize(self) -> int:
        """返回队列的最大大小，0表示无限制"""
        return self._maxsize

    async def empty(self) -> bool:
        """如果队列为空返回True"""
        size = await self.qsize()
        return size == 0

    async def full(self) -> bool:
        """如果队列已满返回True"""
        if self._maxsize <= 0:
            return False
        size = await self.qsize()
        return size >= self._maxsize

    async def put(self, item: Any):
        """将项目放入队列"""
        await self._ensure_client()

        # 如果有最大大小限制，检查队列是否已满
        while self._maxsize > 0:
            size = await self.qsize()
            if size < self._maxsize:
                break
            await asyncio.sleep(0.1)

        message_data = {
            "messages": [
                {
                    "body": json.dumps(item),
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
            ]
        }

        response = await self._client.post(
            f"{self._base_url}/messages", headers=self._headers, json=message_data
        )
        response.raise_for_status()
        self._message_count += 1

    async def get(self) -> Any:
        """从队列获取项目，如果队列为空则等待"""
        await self._ensure_client()

        while True:
            try:
                # 尝试获取消息
                response = await self._client.post(
                    f"{self._base_url}/messages/pull",
                    headers=self._headers,
                    json={"batch_size": 1, "visibility_timeout": 30},
                )
                response.raise_for_status()
                data = response.json()

                messages = data.get("result", {}).get("messages", [])
                if messages:
                    message = messages[0]
                    message_id = message["id"]
                    body = json.loads(message["body"])

                    # 确认消息已处理
                    await self._client.post(
                        f"{self._base_url}/messages/ack",
                        headers=self._headers,
                        json={"acks": [{"id": message_id}]},
                    )

                    self._message_count = max(0, self._message_count - 1)
                    return body

            except Exception:
                pass

            # 如果没有消息，等待一段时间后重试
            await asyncio.sleep(0.5)

    def put_nowait(self, item: Any):
        """立即将项目放入队列，如果队列已满则抛出异常"""
        raise NotImplementedError(
            "Cloudflare Queues does not support synchronous put_nowait"
        )

    def get_nowait(self) -> Any:
        """立即从队列获取项目，如果队列为空则抛出异常"""
        raise NotImplementedError(
            "Cloudflare Queues does not support synchronous get_nowait"
        )

    async def task_done(self):
        """指示之前排队的任务已完成"""
        # Cloudflare Queues 通过 ACK 机制处理任务完成
        pass

    async def join(self):
        """阻塞直到队列中的所有项目都被获取并处理"""
        # 等待队列变空
        while not await self.empty():
            await asyncio.sleep(0.5)
