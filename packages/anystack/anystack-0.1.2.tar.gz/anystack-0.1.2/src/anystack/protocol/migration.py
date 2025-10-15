

from typing import Any, Protocol, TypeAlias


class Migration(Protocol):

    async def up(self) -> None: ...
