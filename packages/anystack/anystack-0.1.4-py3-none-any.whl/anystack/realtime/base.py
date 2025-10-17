from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar


T = TypeVar("T")


class BaseChannel[T](ABC):
    @abstractmethod
    async def send(self, type: str, event: str, payload: T) -> None: ...

    @abstractmethod
    async def on(self, type: str, event: str, callback: Callable[[T], Any]) -> None: ...

    @abstractmethod
    async def subscribe(self): ...

    @abstractmethod
    async def unsubscribe(self): ...

    @abstractmethod
    async def close(self) -> None: ...


class BaseRealtime[T](ABC):
    @abstractmethod
    async def channel(self, name: str, opts: dict[str, Any]) -> BaseChannel[T]: ...

    @abstractmethod
    async def get_channels(self) -> list[BaseChannel[T]]: ...

    @abstractmethod
    async def remove_channel(self, channel: BaseChannel[T]) -> None: ...

    @abstractmethod
    async def remove_all_channels(self) -> None: ...