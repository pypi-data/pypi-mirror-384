from typing import Any, override
from collections.abc import AsyncIterable
from dataclasses import dataclass

from opendal import AsyncFile, Metadata, Entry, AsyncOperator

from .base import BaseStorage
from ..protocol.storage import PathBuf


@dataclass
class Config:
    operator: AsyncOperator


class OpenDALStorage(BaseStorage):
    def __init__(self, config: Config):
        self.operator = config.operator

    @override
    async def open(self, path: PathBuf, mode: str, **options: Any) -> AsyncFile:
        return await self.operator.open(path, mode, **options)

    @override
    async def read(self, path: PathBuf, **options: Any) -> bytes:
        return await self.operator.read(path, **options)

    @override
    async def write(self, path: PathBuf, bs: bytes, **options: Any) -> None:
        return await self.operator.write(path, bs, **options)

    @override
    async def stat(self, path: PathBuf, **kwargs) -> Metadata:
        return await self.operator.stat(path, **kwargs)

    @override
    async def create_dir(self, path: PathBuf) -> None:
        return await self.operator.create_dir(path)

    @override
    async def delete(self, path: PathBuf) -> None:
        return await self.operator.delete(path)

    @override
    async def exists(self, path: PathBuf) -> bool:
        return await self.operator.exists(path)

    @override
    async def list(self, path: PathBuf, **kwargs) -> AsyncIterable[Entry]:
        return await self.operator.list(path, **kwargs)

    @override
    async def scan(self, path: PathBuf, **kwargs) -> AsyncIterable[Entry]:
        return await self.operator.scan(path, **kwargs)

    @override
    async def copy(self, source: PathBuf, target: PathBuf) -> None:
        return await self.operator.copy(source, target)

    @override
    async def rename(self, source: PathBuf, target: PathBuf) -> None:
        return await self.operator.rename(source, target)

    @override
    async def remove_all(self, path: PathBuf) -> None:
        return await self.operator.remove_all(path)
