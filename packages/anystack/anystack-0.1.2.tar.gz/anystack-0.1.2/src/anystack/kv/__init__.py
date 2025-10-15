"""
KV存储抽象层实现
支持多种KV存储后端的统一接口
"""

from dataclasses import dataclass
from typing import Literal, Any

from .base import BaseKV


@dataclass
class Config:
    type: Literal["memory", "redis", "cloudflare", "postgresql", "postgresql_orm"]
    config: dict[str, Any]


def create(config: Config) -> BaseKV:
    """创建KV存储实例
    
    Args:
        config: KV存储配置
        
    Returns:
        BaseKV实例
        
    Raises:
        ValueError: 如果指定了不支持的存储类型
    """
    if config.type == "memory":
        from .memory import MemoryKV, Config as MemoryConfig
        
        memory_config = MemoryConfig(**config.config)
        return MemoryKV(memory_config)
    
    elif config.type == "redis":
        from .redis import RedisKV, Config as RedisConfig
        
        redis_config = RedisConfig(**config.config)
        return RedisKV(redis_config)
    
    elif config.type == "cloudflare":
        from .cloudflare_kv import CloudflareKV, Config as CloudflareConfig
        
        cloudflare_config = CloudflareConfig(**config.config)
        return CloudflareKV(cloudflare_config)
    
    elif config.type == "postgresql":
        from .postgresql import PostgreSQLKV, Config as PostgreSQLConfig
        
        postgresql_config = PostgreSQLConfig(**config.config)
        return PostgreSQLKV(postgresql_config)
    
    else:
        raise ValueError(f"Unsupported KV storage type: {config.type}")


# 导出主要类和函数
__all__ = [
    "BaseKV",
    "Config", 
    "create",
]
