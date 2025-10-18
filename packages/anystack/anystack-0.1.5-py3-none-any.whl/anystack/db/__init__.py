from dataclasses import dataclass
from typing import Literal, Any

from .base import BaseDB


@dataclass
class Config:
    type: Literal["d1", "sqlalchemy"]
    config: dict[str, Any]


def create(config: Config) -> BaseDB:
    if config.type == "d1":
        from .d1 import D1DB, Config as D1Config

        return D1DB(D1Config(**config.config))
    elif config.type == "sqlalchemy":
        from .sqlalchemy import SQLAlchemyDB, Config as SQLAlchemyConfig

        return SQLAlchemyDB(SQLAlchemyConfig(**config.config))
    else:
        raise ValueError(f"Unsupported database type: {config.type}")
