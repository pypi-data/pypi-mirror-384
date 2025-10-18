from abc import ABC, abstractmethod
from typing import Any

from ..protocol.storage import (
    PathBuf,
    Metadata,
    Entry,
    AsyncIterable,
    AsyncFile,
)


class BaseStorage(ABC):
    @abstractmethod
    async def open(self, path: PathBuf, mode: str, **options: Any) -> AsyncFile: ...

    @abstractmethod
    async def read(self, path: PathBuf, **options: Any) -> bytes: ...

    @abstractmethod
    async def write(self, path: PathBuf, bs: bytes, **options: Any) -> None: ...

    @abstractmethod
    async def stat(self, path: PathBuf, **kwargs) -> Metadata: ...

    @abstractmethod
    async def create_dir(self, path: PathBuf) -> None: ...

    @abstractmethod
    async def delete(self, path: PathBuf) -> None: ...

    @abstractmethod
    async def exists(self, path: PathBuf) -> bool: ...

    @abstractmethod
    async def list(self, path: PathBuf, **kwargs) -> AsyncIterable[Entry]: ...

    @abstractmethod
    async def scan(self, path: PathBuf, **kwargs) -> AsyncIterable[Entry]: ...

    @abstractmethod
    async def copy(self, source: PathBuf, target: PathBuf) -> None: ...

    @abstractmethod
    async def rename(self, source: PathBuf, target: PathBuf) -> None: ...

    @abstractmethod
    async def remove_all(self, path: PathBuf) -> None: ...
