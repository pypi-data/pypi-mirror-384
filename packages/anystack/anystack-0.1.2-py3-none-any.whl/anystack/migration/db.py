from pathlib import Path

from .base import BaseMigration, MigrationData
from ..protocol.db import DB


class DBMigration(BaseMigration):
    def __init__(
        self,
        db: DB,
        migration: list[MigrationData] | str | Path,
        table_name: str = "migrations",
    ):
        self.db = db
        self.migration = self._load_migration(migration)
        self.table_name = table_name

    def _load_migration(
        self, dir_path: list[MigrationData] | str | Path
    ) -> list[MigrationData]:
        if isinstance(dir_path, list):
            return dir_path
        data: list[MigrationData] = []
        sql_files = sorted(Path(dir_path).glob("*.sql"))
        for file in sql_files:
            with open(file, "r") as f:
                data.append(
                    MigrationData(
                        version=file.stem,
                        sql=f.read(),
                        description=file.stem,
                    )
                )
        return data

    async def init_table_and_get_index(self) -> int:
        await self.db.sql(
            f"CREATE TABLE IF NOT EXISTS {self.table_name} (id INTEGER PRIMARY KEY, version TEXT NOT NULL)"
        )
        migration_index = await self.db.sql(f"SELECT COUNT(*) as count FROM {self.table_name}")
        return (migration_index.rows[0]["count"] or 0) if migration_index.rows else 0

    async def up(self) -> None:
        index = await self.init_table_and_get_index()
        for migration in self.migration[index:]:
            async with self.db.transaction() as conn:
                await conn.sql(migration.sql)
                await conn.sql(
                    f"INSERT INTO {self.table_name} (version) VALUES (:version)",
                    {"version": migration.version},
                )
