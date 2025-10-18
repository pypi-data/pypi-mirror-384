from abc import ABC, abstractmethod

from dataclasses import dataclass, field


@dataclass(slots=True)
class MigrationData:
    version: str
    sql: str
    description: str | None = None


class BaseMigration(ABC):
    @abstractmethod
    async def up(self) -> None: ...