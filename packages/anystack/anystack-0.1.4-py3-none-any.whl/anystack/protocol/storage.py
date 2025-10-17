import os
from collections.abc import AsyncIterable
from typing import Any, Protocol

from opendal import AsyncFile, Metadata, Entry

PathBuf = str | os.PathLike


class Storage(Protocol):


    async def open(self, path: PathBuf, mode: str, **options: Any) -> AsyncFile:
        ...


    async def read(self, path: PathBuf, **options: Any) -> bytes:
        ...

    async def write(self, path: PathBuf, bs: bytes, **options: Any) -> None:
        ...

    async def stat(self, path: PathBuf, **kwargs) -> Metadata:
        ...

    async def create_dir(self, path: PathBuf) -> None:
        ...

    async def delete(self, path: PathBuf) -> None:
        ...
        
    async def exists(self, path: PathBuf) -> bool:
        ...
    
    async def list(self, path: PathBuf, **kwargs) -> AsyncIterable[Entry]:
        ...
    
    async def scan(self, path: PathBuf, **kwargs) -> AsyncIterable[Entry]:
        ...

    async def copy(self, source: PathBuf, target: PathBuf) -> None:
        ...
        
    async def rename(self, source: PathBuf, target: PathBuf) -> None:
        ...
        
    async def remove_all(self, path: PathBuf) -> None:
        ...
