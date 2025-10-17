"""
调度器抽象层实现
支持多种调度器后端的统一接口
"""

from dataclasses import dataclass
from typing import Literal, Any

from .base import BaseScheduler


@dataclass
class Config:
    type: Literal["distributed", "single"]
    config: dict[str, Any]


def create(config: Config) -> BaseScheduler:
    """创建调度器实例的工厂函数"""
    if config.type == "distributed":
        from .distributed.distributed import DistributedScheduler, Config as DistributedConfig

        return DistributedScheduler(DistributedConfig(**config.config))
    elif config.type == "single":
        from .single.single import SupabaseScheduler, Config as SingleConfig

        return SupabaseScheduler(SingleConfig(**config.config))
    else:
        raise ValueError(f"Unsupported scheduler type: {config.type}")
