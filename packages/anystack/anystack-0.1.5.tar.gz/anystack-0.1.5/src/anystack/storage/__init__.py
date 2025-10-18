from dataclasses import dataclass
from typing import Literal, Any

from .base import BaseStorage


@dataclass
class Config:
    type: Literal["opendal"]
    config: dict[str, Any]


def create(config: Config) -> BaseStorage:
    if config.type == "opendal":
        from .opendal import OpenDALStorage, Config as OpenDALConfig

        return OpenDALStorage(OpenDALConfig(**config.config))
    raise ValueError(f"Unsupported storage type: {config.type}")
