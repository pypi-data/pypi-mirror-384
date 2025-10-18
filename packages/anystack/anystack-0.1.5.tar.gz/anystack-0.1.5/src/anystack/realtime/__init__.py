"""
调度器抽象层实现
支持多种调度器后端的统一接口
"""

from dataclasses import dataclass
from typing import Literal, Any

from .base import BaseRealtime


@dataclass
class Config:
    type: Literal["distributed", "supabase"]
    config: dict[str, Any]


def create(config: Config) -> BaseRealtime[dict[str, Any]]:
    """创建调度器实例的工厂函数"""
    if config.type == "distributed":
        from .distributed.distributed import (
            DistributedRealtime,
            Config as DistributedConfig,
        )

        return DistributedRealtime(DistributedConfig(**config.config))
    elif config.type == "supabase":
        from .supabase import SupabaseRealtime, Config as SupabaseConfig

        return SupabaseRealtime(SupabaseConfig(**config.config))
    else:
        raise ValueError(f"Unsupported scheduler type: {config.type}")
