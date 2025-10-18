"""
队列抽象层实现
支持多种队列后端的统一接口
"""

from dataclasses import dataclass
from typing import Literal, Any, TypeVar

from .base import BaseQueue, Item

T = TypeVar("T")

@dataclass
class Config:
    type: Literal["asyncio", "pgmq", "cloudflare", "db"]
    config: dict[str, Any]


def create(config: Config) -> BaseQueue[Item[T]]:
    if config.type == "asyncio":
        from .asyncio_queue import AsyncioQueue, Config as AsyncioConfig

        return AsyncioQueue(AsyncioConfig(**config.config))
    elif config.type == "pgmq":
        from .pgmq_queue import PGMQueue, Config as PGMQConfig

        return PGMQueue(PGMQConfig(**config.config))
    elif config.type == "cloudflare":
        from .cloudflare_queue import CloudflareQueue, Config as CloudflareConfig

        return CloudflareQueue(CloudflareConfig(**config.config))
    elif config.type == "db":
        from .db_queue import DBQueue, Config as DBConfig

        return DBQueue(DBConfig(**config.config))
    else:
        raise ValueError(f"Unsupported queue type: {config.type}")
